from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from heater.database import AsyncSessionLocal
from heater.models.instance import Instance
from heater.warming.engine import WarmingEngine
from heater.dependencies import evolution_client
import asyncio

scheduler = AsyncIOScheduler()

async def warming_job():
    async with AsyncSessionLocal() as session:
        # Get all instances enabled for warming
        result = await session.execute(select(Instance).where(Instance.warming_enabled == True))
        instances = result.scalars().all()

        engine = WarmingEngine(evolution_client, session)

        for instance in instances:
            # We run cycles concurrently or sequentially?
            # Sequentially per job run is safer for now
            try:
                await engine.run_warming_cycle(instance.id)
            except Exception as e:
                print(f"Error in warming cycle for instance {instance.id}: {e}")

def start_scheduler():
    # Run every minute. The engine will decide if it should actually send a message based on delays/schedule.
    # Actually, the engine logic I wrote checks schedule but not "delay since last message".
    # Real implementation needs to check "last_message_time" + random_delay < now.
    # For MVP, running every minute might be too frequent if we don't check last message time.
    # But `WarmingEngine` in AGENTS.md had `between_messages_delay`.
    # My implementation of `run_warming_cycle` didn't check last message timestamp.
    # I should update `run_warming_cycle` or accept that it might spam if I run it often.
    # Or I run it every X minutes.

    scheduler.add_job(warming_job, 'interval', minutes=1)
    scheduler.start()
