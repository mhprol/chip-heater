from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from heater.database import engine, Base
from heater.config import settings
from heater.api import auth, instances, webhooks
from heater.scheduler import start_scheduler, scheduler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start scheduler
    start_scheduler()

    yield

    # Shutdown scheduler
    scheduler.shutdown()

app = FastAPI(title="Chip Heater", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(instances.router)
app.include_router(webhooks.router)

@app.get("/")
async def root():
    return {"message": "Chip Heater API"}
