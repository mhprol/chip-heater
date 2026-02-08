import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, db_session):
    payload = {"email": "newuser@example.com", "password": "password123"}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_register_existing_user(client: AsyncClient, create_user):
    payload = {"email": "test@example.com", "password": "password123"}
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, create_user):
    # create_user uses "password" as password (defined in conftest.py)
    payload = {"username": "test@example.com", "password": "password"}
    response = await client.post("/auth/token", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, create_user):
    payload = {"username": "test@example.com", "password": "wrongpassword"}
    response = await client.post("/auth/token", data=payload)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_access(client: AsyncClient, create_user, auth_headers):
    # Without token
    response = await client.get("/instances/")
    assert response.status_code == 401

    # With token
    response = await client.get("/instances/", headers=auth_headers)
    assert response.status_code == 200
