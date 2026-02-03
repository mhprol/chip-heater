from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from heater.database import get_db
from heater.models.instance import Instance
from heater.models.user import User
from heater.api.auth import get_current_user
from heater.dependencies import get_evolution, EvolutionClient
from heater import schemas

router = APIRouter(prefix="/instances", tags=["instances"])

@router.post("/", response_model=schemas.InstanceResponse)
async def create_instance(
    instance_data: schemas.InstanceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    evolution: EvolutionClient = Depends(get_evolution)
):
    """Create new WhatsApp instance"""
    # Create in Evolution API
    try:
        await evolution.create_instance(instance_data.name)
    except Exception as e:
        # Log error but might be okay if it already exists or we want to sync
        print(f"Error creating instance in Evolution: {e}")

    # Create in DB
    db_instance = Instance(user_id=user.id, name=instance_data.name)
    db.add(db_instance)
    await db.commit()
    await db.refresh(db_instance)
    return db_instance

@router.get("/", response_model=list[schemas.InstanceResponse])
async def list_instances(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Instance).where(Instance.user_id == user.id))
    return result.scalars().all()

@router.get("/{instance_id}/qrcode")
async def get_qrcode(
    instance_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    evolution: EvolutionClient = Depends(get_evolution)
):
    """Get QR code for WhatsApp connection"""
    result = await db.execute(select(Instance).where(Instance.id == instance_id, Instance.user_id == user.id))
    instance = result.scalars().first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    qr = await evolution.get_qrcode(instance.name)
    return {"qrcode": qr}

@router.post("/{instance_id}/warming/start")
async def start_warming(
    instance_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start warming for an instance"""
    result = await db.execute(select(Instance).where(Instance.id == instance_id, Instance.user_id == user.id))
    instance = result.scalars().first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    instance.warming_enabled = True
    await db.commit()
    return {"status": "warming started"}

@router.post("/{instance_id}/warming/stop")
async def stop_warming(
    instance_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop warming for an instance"""
    result = await db.execute(select(Instance).where(Instance.id == instance_id, Instance.user_id == user.id))
    instance = result.scalars().first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")

    instance.warming_enabled = False
    await db.commit()
    return {"status": "warming stopped"}
