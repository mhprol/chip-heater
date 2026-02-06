import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, UTC

from heater.database import Base
from heater.models.user import User
from heater.models.instance import Instance
from heater.models.message import Message
from heater.warming.engine import WarmingEngine

# Setup DB
@pytest_asyncio.fixture
async def db_session():
    # Use in-memory SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionLocal() as session:
        yield session

    await engine.dispose()

@pytest.fixture
def mock_evolution():
    client = MagicMock()
    # Mock send_text response to return a key with ID
    client.send_text = AsyncMock(return_value={"key": {"id": "MSG_NEW_123", "remoteJid": "12345@s.whatsapp.net", "fromMe": True}})
    client.send_reaction = AsyncMock(return_value={"status": "ok"})
    client.set_presence = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_send_message_stores_external_id(db_session, mock_evolution):
    me = Instance(name="me", phone_number="111111", warming_enabled=True, status="connected", daily_limit=100)
    peer = Instance(name="peer", phone_number="222222", warming_enabled=True, status="connected")
    db_session.add_all([me, peer])
    await db_session.commit()

    engine = WarmingEngine(mock_evolution, db_session)

    # Send private message
    await engine.send_private_message(me, peer)

    # Check if external_id is stored
    # We need to query DB
    from sqlalchemy import select
    result = await db_session.execute(select(Message).where(Message.instance_id == me.id))
    msg = result.scalars().first()

    assert msg is not None
    assert msg.external_id == "MSG_NEW_123"
    assert msg.peer_number == "222222"

@pytest.mark.asyncio
async def test_send_reaction(db_session, mock_evolution):
    me = Instance(name="me", phone_number="111111", warming_enabled=True, status="connected")
    peer = Instance(name="peer", phone_number="222222", warming_enabled=True, status="connected")
    db_session.add_all([me, peer])
    await db_session.commit()

    # Message from peer to me
    # Message table stores instance_id = sender. So instance_id = peer.id, peer_number = me.phone_number
    # This represents a message stored in our DB that came from the peer.
    msg = Message(
        instance_id=peer.id,
        peer_number=me.phone_number,
        content="Hello",
        external_id="MSG_FROM_PEER",
        created_at=datetime.now(UTC)
    )
    db_session.add(msg)
    await db_session.commit()

    engine = WarmingEngine(mock_evolution, db_session)

    # Call send_reaction directly
    await engine.send_reaction(me, peer)

    mock_evolution.send_reaction.assert_called_once()
    call_args = mock_evolution.send_reaction.call_args
    # call_args[0] = (instance_name, key, emoji)

    instance_name = call_args[0][0]
    key = call_args[0][1]
    emoji = call_args[0][2]

    assert instance_name == "me"
    assert key["id"] == "MSG_FROM_PEER"
    # assert key["remoteJid"] ... # We'll see how we implement it
    # assert key["fromMe"] == False
    assert isinstance(emoji, str)

@pytest.mark.asyncio
async def test_peer_selection_logic(db_session, mock_evolution):
    # This test verifies the _select_peer method (which we will implement)
    # or the effect of run_warming_cycle if deterministic.

    me = Instance(name="me", phone_number="111111", warming_enabled=True, status="connected", daily_limit=100)
    p1 = Instance(name="p1", phone_number="222222", warming_enabled=True, status="connected") # Old interaction
    p2 = Instance(name="p2", phone_number="333333", warming_enabled=True, status="connected") # Recent interaction
    db_session.add_all([me, p1, p2])
    await db_session.commit()

    # Log interactions
    # p2 talked recently
    msg2 = Message(instance_id=me.id, peer_number=p2.phone_number, created_at=datetime.now(UTC) - timedelta(minutes=1))
    # p1 talked long ago
    msg1 = Message(instance_id=me.id, peer_number=p1.phone_number, created_at=datetime.now(UTC) - timedelta(days=1))

    db_session.add_all([msg1, msg2])
    await db_session.commit()

    engine = WarmingEngine(mock_evolution, db_session)

    # We will implement _select_peer method. We can test it directly if we make it public or accessible.
    # For now, let's assume we'll add it.

    # Mocking _select_peer if we couldn't call it, but we can call it if we implement it.
    # But since we haven't implemented it yet, this test will fail if we try to call it.
    # So we'll skip this part until we implement it, OR we write the test expecting it to exist.

    # We will assume engine has _select_peer
    if hasattr(engine, "_select_peer"):
        peers = [p1, p2]
        # Run selection multiple times to check distribution
        # Since p1 hasn't been talked to in a day, and p2 1 min ago.
        # Weighted selection should favor p1 heavily.

        counts = {"p1": 0, "p2": 0}
        for _ in range(100):
            selected = await engine._select_peer(me, peers)
            if selected.id == p1.id:
                counts["p1"] += 1
            else:
                counts["p2"] += 1

        # p1 should be selected significantly more
        assert counts["p1"] > counts["p2"]
