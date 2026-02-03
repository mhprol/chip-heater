from fastapi import APIRouter, Request, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from heater.database import get_db, AsyncSessionLocal
from heater.models.instance import Instance

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

async def update_instance_status(instance_name: str, status: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Instance).where(Instance.name == instance_name))
        instance = result.scalars().first()
        if instance:
            if status == "open" or status == "connected":
                instance.status = "connected"
            elif status == "close" or status == "disconnected":
                instance.status = "disconnected"
            elif status == "connecting":
                instance.status = "connecting"
            else:
                # Log unknown status but update anyway?
                # instance.status = status
                pass
            await db.commit()

@router.post("/evolution")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    # print(f"Received webhook: {data}")

    # Evolution API 2.0+ structure varies.
    # Typically: { "event": "connection.update", "instance": "name", "data": { "state": "open" } }

    event = data.get("event") or data.get("type")
    instance_name = data.get("instance")

    if event == "connection.update":
        payload = data.get("data", {})
        state = payload.get("state") or payload.get("status")
        # reason = payload.get("reason")

        if instance_name and state:
            background_tasks.add_task(update_instance_status, instance_name, state)

    return {"status": "ok"}
