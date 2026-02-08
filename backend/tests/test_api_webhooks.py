import pytest
from httpx import AsyncClient
from sqlalchemy import select
from heater.models.instance import Instance
from heater.models.user import User
import asyncio

@pytest.mark.asyncio
async def test_webhook_connection_update_connected(client: AsyncClient, db_session, create_user):
    # Ensure user exists (create_user fixture creates one, likely id=1)
    user = create_user # This returns the user object

    # Create instance in DB
    inst = Instance(name="hook_inst", status="disconnected", user_id=user.id)
    db_session.add(inst)
    await db_session.commit()

    payload = {
        "event": "connection.update",
        "instance": "hook_inst",
        "data": {
            "state": "open"
        }
    }

    response = await client.post("/webhooks/evolution", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    # Wait for background task execution
    await asyncio.sleep(0.1)

    await db_session.refresh(inst)
    assert inst.status == "connected"

@pytest.mark.asyncio
async def test_webhook_connection_update_disconnected(client: AsyncClient, db_session, create_user):
    user = create_user
    inst = Instance(name="hook_inst_2", status="connected", user_id=user.id)
    db_session.add(inst)
    await db_session.commit()

    payload = {
        "event": "connection.update",
        "instance": "hook_inst_2",
        "data": {
            "state": "close"
        }
    }

    response = await client.post("/webhooks/evolution", json=payload)
    assert response.status_code == 200

    await asyncio.sleep(0.1)

    await db_session.refresh(inst)
    assert inst.status == "disconnected"

@pytest.mark.asyncio
async def test_webhook_unknown_instance(client: AsyncClient):
    payload = {
        "event": "connection.update",
        "instance": "unknown_inst",
        "data": {
            "state": "open"
        }
    }
    response = await client.post("/webhooks/evolution", json=payload)
    assert response.status_code == 200
