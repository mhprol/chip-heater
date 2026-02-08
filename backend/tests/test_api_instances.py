import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_instance(client: AsyncClient, create_user, auth_headers, mock_evolution):
    response = await client.post("/instances/", json={"name": "test_instance"}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_instance"
    assert "id" in data
    mock_evolution.create_instance.assert_called_once_with("test_instance")

@pytest.mark.asyncio
async def test_list_instances(client: AsyncClient, create_user, auth_headers):
    # Create first
    await client.post("/instances/", json={"name": "inst1"}, headers=auth_headers)
    await client.post("/instances/", json={"name": "inst2"}, headers=auth_headers)

    response = await client.get("/instances/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Note: DB is fresh per function, but if creating multiple instances, ensure order or check existence
    assert len(data) == 2
    names = [inst["name"] for inst in data]
    assert "inst1" in names
    assert "inst2" in names

@pytest.mark.asyncio
async def test_get_qrcode(client: AsyncClient, create_user, auth_headers, mock_evolution):
    # Create instance
    create_resp = await client.post("/instances/", json={"name": "qr_instance"}, headers=auth_headers)
    instance_id = create_resp.json()["id"]

    response = await client.get(f"/instances/{instance_id}/qrcode", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["qrcode"] == "base64qrcode"
    mock_evolution.get_qrcode.assert_called_once_with("qr_instance")

@pytest.mark.asyncio
async def test_start_warming(client: AsyncClient, create_user, auth_headers):
    # Create instance
    create_resp = await client.post("/instances/", json={"name": "warm_instance"}, headers=auth_headers)
    instance_id = create_resp.json()["id"]

    # Start warming
    response = await client.post(f"/instances/{instance_id}/warming/start", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "warming started"

    # Stop warming
    stop_resp = await client.post(f"/instances/{instance_id}/warming/stop", headers=auth_headers)
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "warming stopped"

@pytest.mark.asyncio
async def test_instance_not_found(client: AsyncClient, create_user, auth_headers):
    response = await client.get("/instances/999/qrcode", headers=auth_headers)
    assert response.status_code == 404
