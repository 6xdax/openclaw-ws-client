"""Tests for tools module"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from openclaw.tools import ToolsManager


@pytest.fixture
def mock_client():
    """Create a mock OpenClawClient"""
    client = MagicMock()
    client._send_request = AsyncMock()
    return client


@pytest.fixture
def tools_manager(mock_client):
    """Create a ToolsManager with mock client"""
    return ToolsManager(mock_client)


@pytest.mark.asyncio
async def test_catalog(tools_manager, mock_client):
    """Test listing tool catalog"""
    mock_response = {
        "tools": [
            {"name": "weather", "description": "Get weather info"},
            {"name": "calculator", "description": "Perform calculations"},
        ]
    }
    mock_client._send_request.return_value = mock_response

    result = await tools_manager.catalog()

    assert len(result) == 2
    assert result[0]["name"] == "weather"
    mock_client._send_request.assert_called_once_with("tools.catalog")


@pytest.mark.asyncio
async def test_effective(tools_manager, mock_client):
    """Test listing effective tools"""
    mock_response = {
        "tools": [
            {"name": "weather", "enabled": True},
        ]
    }
    mock_client._send_request.return_value = mock_response

    result = await tools_manager.effective()

    assert len(result) == 1
    assert result[0]["name"] == "weather"
    mock_client._send_request.assert_called_once_with("tools.effective")


@pytest.mark.asyncio
async def test_enable(tools_manager, mock_client):
    """Test enabling a tool"""
    mock_client._send_request.return_value = {"ok": True}

    result = await tools_manager.enable("weather")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][0] == "tools.enable"
    assert call_args[0][1] == {"name": "weather"}


@pytest.mark.asyncio
async def test_disable(tools_manager, mock_client):
    """Test disabling a tool"""
    mock_client._send_request.return_value = {"ok": True}

    result = await tools_manager.disable("calculator")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][0] == "tools.disable"
    assert call_args[0][1] == {"name": "calculator"}
