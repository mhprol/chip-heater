import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_evolution_api_create_error(client: AsyncClient, create_user, auth_headers, mock_evolution):
    # Mock create_instance failure
    mock_evolution.create_instance.side_effect = Exception("API connection failed")

    # The current implementation in api/instances.py catches exception
    response = await client.post("/instances/", json={"name": "failed_api"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "failed_api"
    # It should still be created in DB

@pytest.mark.asyncio
async def test_engine_send_message_error(db_session, mock_evolution):
    # Setup
    from heater.models.instance import Instance
    from heater.warming.engine import WarmingEngine
    from heater.models.message import Message
    from sqlalchemy import select

    from heater.models.user import User
    user = User(email="e@e.com", hashed_password="pw")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    me = Instance(name="me_err", phone_number="111111", user_id=user.id, status="connected")
    peer = Instance(name="peer_err", phone_number="222222", user_id=user.id, status="connected")
    db_session.add_all([me, peer])
    await db_session.commit()

    mock_evolution.send_text.side_effect = Exception("Evolution failure")

    engine = WarmingEngine(mock_evolution, db_session)

    # Mock ContentGenerator and HumanBehavior to avoid delays and randomness
    with patch("heater.warming.engine.ContentGenerator.casual_message", return_value="Hello"), \
         patch("heater.warming.engine.HumanBehavior.typing_delay", new_callable=AsyncMock) as mock_delay:
        mock_delay.return_value = 0.0

        # Run send_private_message directly
        await engine.send_private_message(me, peer)

    # Should handle exception and not crash
    # Should not log success message in DB
    result = await db_session.execute(select(Message).where(Message.instance_id == me.id))
    messages = result.scalars().all()
    assert len(messages) == 0

@pytest.mark.asyncio
async def test_auth_invalid_token(client: AsyncClient):
    response = await client.get("/instances/", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_malformed_webhook(client: AsyncClient):
    # Send weird JSON
    response = await client.post("/webhooks/evolution", content="not json", headers={"Content-Type": "application/json"})
    # We updated the endpoint to return 200 with error status
    assert response.status_code == 200
    assert response.json()["status"] == "error"

    # Send valid JSON but missing fields
    response = await client.post("/webhooks/evolution", json={"foo": "bar"})
    # Implementation handles missing fields gracefully (doesn't crash)
    assert response.status_code == 200
