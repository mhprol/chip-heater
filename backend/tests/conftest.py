import os
# Set environment variables for testing before importing app
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["EVOLUTION_URL"] = "http://mock-evolution"
os.environ["EVOLUTION_API_KEY"] = "mock-key"
os.environ["JWT_SECRET"] = "testsecret"
os.environ["REDIS_URL"] = "redis://mock"

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

# Now import app modules
from heater.main import app
from heater.database import Base, get_db
from heater.dependencies import get_evolution
from heater.config import settings

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Use in-memory SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Patch AsyncSessionLocal where it is used directly (e.g. background tasks)
    # We need to target the module where it is imported.
    # We patch it to return a session from OUR engine.
    # Note: side_effect=SessionLocal makes the mock call SessionLocal() when called.

    # We need to ensure modules are loaded so patch works on them
    # heater.api.webhooks is imported by heater.main

    with patch("heater.api.webhooks.AsyncSessionLocal", side_effect=SessionLocal), \
         patch("heater.scheduler.AsyncSessionLocal", side_effect=SessionLocal):

        async with SessionLocal() as session:
            yield session

    await engine.dispose()

@pytest.fixture(scope="function")
def mock_evolution():
    client = MagicMock()
    # Async methods need to be AsyncMock
    client.create_instance = AsyncMock(return_value={"instance": {"key": "test"}})
    client.get_qrcode = AsyncMock(return_value="base64qrcode")
    client.send_text = AsyncMock(return_value={"key": {"id": "MSG_ID_123"}})
    client.send_reaction = AsyncMock(return_value={"status": "ok"})
    client.set_presence = AsyncMock(return_value={"status": "ok"})
    return client

@pytest_asyncio.fixture(scope="function")
async def client(db_session, mock_evolution) -> AsyncGenerator[AsyncClient, None]:
    # Override dependencies
    async def override_get_db():
        yield db_session

    def override_get_evolution():
        return mock_evolution

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_evolution] = override_get_evolution

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers():
    from heater.api.auth import create_access_token
    token = create_access_token(data={"sub": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def create_user(db_session):
    from heater.models.user import User
    from heater.api.auth import get_password_hash
    user = User(email="test@example.com", hashed_password=get_password_hash("password"))
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
