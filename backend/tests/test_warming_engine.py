import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from heater.warming.engine import WarmingEngine
from heater.models.instance import Instance
from heater.models.message import Message
from sqlalchemy import select

@pytest.fixture
def engine_instance(db_session, mock_evolution):
    return WarmingEngine(evolution=mock_evolution, db=db_session)

@pytest.mark.asyncio
async def test_select_peer_logic(engine_instance, db_session):
    # Setup instances
    # Need user first because of FK? If SQLite FKs are enforced (they are not by default in SQLAlchemy unless configured)
    # But create_async_engine might not enforce them or user_id=1 might be fine if table empty
    # Best practice is to create user.
    from heater.models.user import User
    user = User(email="t@t.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    me = Instance(name="me", phone_number="111111", user_id=user.id, status="connected")
    p1 = Instance(name="p1", phone_number="222222", user_id=user.id, status="connected") # Old interaction
    p2 = Instance(name="p2", phone_number="333333", user_id=user.id, status="connected") # Recent interaction
    db_session.add_all([me, p1, p2])
    await db_session.commit()

    # Log interactions
    # p2 talked recently
    msg2 = Message(instance_id=me.id, peer_number=p2.phone_number, created_at=datetime.utcnow() - timedelta(minutes=1))
    # p1 talked long ago
    msg1 = Message(instance_id=me.id, peer_number=p1.phone_number, created_at=datetime.utcnow() - timedelta(days=1))

    db_session.add_all([msg1, msg2])
    await db_session.commit()

    # Test selection distribution
    counts = {"p1": 0, "p2": 0}
    peers = [p1, p2]

    # Run multiple times to verify weighted random
    for _ in range(100):
        selected = await engine_instance._select_peer(me, peers)
        if selected.id == p1.id:
            counts["p1"] += 1
        else:
            counts["p2"] += 1

    # p1 should be selected significantly more because weight = delta (time since last msg)
    # p1 delta ~ 86400s
    # p2 delta ~ 60s
    assert counts["p1"] > counts["p2"]
    assert counts["p1"] > 80 # Should be very high

@pytest.mark.asyncio
async def test_run_warming_cycle_checks(engine_instance, db_session, mock_evolution):
    from heater.models.user import User
    user = User(email="t2@t.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Setup
    me = Instance(
        name="me_warm",
        phone_number="111111",
        user_id=user.id,
        status="connected",
        warming_enabled=True,
        daily_limit=10,
        messages_today=0,
        schedule_start="00:00",
        schedule_end="23:59"
    )
    peer = Instance(name="peer", phone_number="222222", user_id=user.id, status="connected", warming_enabled=True)
    db_session.add_all([me, peer])
    await db_session.commit()

    # Mock random to choose private_message (index 0 usually for private_message if weights favor it, but here we force it)
    # The code does: random.choices(["private_message", "reaction"], weights=[0.8, 0.2])[0]
    # We need to patch random.choices to return ["private_message"]
    # BUT random.choices is also used in _select_peer.
    # _select_peer is called first, then activity selection.

    with patch("random.choices", side_effect=[[peer], ["private_message"]]):
        # Mock ContentGenerator
        with patch("heater.warming.engine.ContentGenerator.casual_message", return_value="Hello"):
            # Mock HumanBehavior typing delay
            with patch("heater.warming.engine.HumanBehavior.typing_delay", new_callable=AsyncMock) as mock_delay:
                mock_delay.return_value = 0.001

                await engine_instance.run_warming_cycle(me.id)

    # Verify evolution called
    mock_evolution.send_text.assert_called()

    # Verify stats updated
    await db_session.refresh(me)
    assert me.messages_today == 1
    assert me.messages_total == 1
    assert me.last_active_at is not None

@pytest.mark.asyncio
async def test_run_warming_cycle_limit_reached(engine_instance, db_session, mock_evolution):
    from heater.models.user import User
    user = User(email="t3@t.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    me = Instance(
        name="me_limit",
        phone_number="111111",
        user_id=user.id,
        status="connected",
        warming_enabled=True,
        daily_limit=10,
        messages_today=10, # Limit reached
        schedule_start="00:00",
        schedule_end="23:59"
    )
    db_session.add(me)
    await db_session.commit()

    await engine_instance.run_warming_cycle(me.id)

    mock_evolution.send_text.assert_not_called()

@pytest.mark.asyncio
async def test_send_reaction(engine_instance, db_session, mock_evolution):
    from heater.models.user import User
    user = User(email="t4@t.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    me = Instance(name="me_react", phone_number="111111", user_id=user.id)
    peer = Instance(name="peer_react", phone_number="222222", user_id=user.id)
    db_session.add_all([me, peer])
    await db_session.commit()

    # Create a message to react to
    msg = Message(
        instance_id=peer.id,
        peer_number=me.phone_number,
        content="Hello",
        external_id="MSG_FROM_PEER",
        created_at=datetime.utcnow()
    )
    db_session.add(msg)
    await db_session.commit()

    await engine_instance.send_reaction(me, peer)

    mock_evolution.send_reaction.assert_called_once()
    args = mock_evolution.send_reaction.call_args[0]
    assert args[0] == "me_react"
    assert args[1]["id"] == "MSG_FROM_PEER"
    # verify DB log
    result = await db_session.execute(select(Message).where(Message.message_type == "reaction"))
    reaction_msg = result.scalars().first()
    assert reaction_msg is not None
    assert reaction_msg.instance_id == me.id
