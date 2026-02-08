import pytest
from unittest.mock import AsyncMock, MagicMock
from heater.evolution import EvolutionClient

@pytest.mark.asyncio
async def test_get_qrcode_v2_2():
    """Test getting QR code with Evolution API v2.2.x format (nested)."""
    client = EvolutionClient("http://test", "key")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "qrcode": {
            "base64": "v2.2-base64-string"
        }
    }
    client.client.get = AsyncMock(return_value=mock_response)

    qr = await client.get_qrcode("instance")
    assert qr == "v2.2-base64-string"

@pytest.mark.asyncio
async def test_get_qrcode_v2_3():
    """Test getting QR code with Evolution API v2.3.x format (top-level)."""
    client = EvolutionClient("http://test", "key")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "base64": "v2.3-base64-string"
    }
    client.client.get = AsyncMock(return_value=mock_response)

    qr = await client.get_qrcode("instance")
    assert qr == "v2.3-base64-string"

@pytest.mark.asyncio
async def test_get_qrcode_missing():
    """Test getting QR code when it is missing."""
    client = EvolutionClient("http://test", "key")

    mock_response = MagicMock()
    mock_response.json.return_value = {}
    client.client.get = AsyncMock(return_value=mock_response)

    qr = await client.get_qrcode("instance")
    assert qr is None
