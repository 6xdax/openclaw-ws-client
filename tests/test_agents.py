"""Tests for agents module"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openclaw.agents import AgentsManager


@pytest.fixture
def mock_client():
    """Create a mock OpenClawClient"""
    client = MagicMock()
    client._send_request = AsyncMock()
    return client


@pytest.fixture
def agents_manager(mock_client):
    """Create an AgentsManager with mock client"""
    return AgentsManager(mock_client)


@pytest.mark.asyncio
async def test_list_agents(agents_manager, mock_client):
    """Test listing agents"""
    mock_response = {
        "agents": [
            {"agentId": "agent-1", "name": "Agent 1"},
            {"agentId": "agent-2", "name": "Agent 2"},
        ]
    }
    mock_client._send_request.return_value = mock_response

    result = await agents_manager.list()

    assert len(result) == 2
    assert result[0]["agentId"] == "agent-1"
    mock_client._send_request.assert_called_once_with("agents.list")


@pytest.mark.asyncio
async def test_create_agent(agents_manager, mock_client):
    """Test creating an agent"""
    mock_response = {
        "agent": {"agentId": "new-agent", "name": "New Agent"}
    }
    mock_client._send_request.return_value = mock_response

    result = await agents_manager.create(
        name="New Agent",
        model="minimax-m2.7",
        skills=["weather"],
    )

    assert result["agentId"] == "new-agent"
    mock_client._send_request.assert_called_once()
    call_args = mock_client._send_request.call_args
    assert call_args[0][0] == "agents.create"
    assert call_args[0][1]["name"] == "New Agent"
    assert call_args[0][1]["model"] == "minimax-m2.7"
    assert call_args[0][1]["skills"] == ["weather"]


@pytest.mark.asyncio
async def test_update_agent(agents_manager, mock_client):
    """Test updating an agent"""
    mock_response = {
        "agent": {"agentId": "agent-1", "name": "Updated Name"}
    }
    mock_client._send_request.return_value = mock_response

    result = await agents_manager.update("agent-1", name="Updated Name")

    assert result["name"] == "Updated Name"
    call_args = mock_client._send_request.call_args
    assert call_args[0][1]["agentId"] == "agent-1"
    assert call_args[0][1]["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_agent(agents_manager, mock_client):
    """Test deleting an agent"""
    mock_client._send_request.return_value = {"ok": True}

    result = await agents_manager.delete("agent-1")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][1] == {"agentId": "agent-1"}


@pytest.mark.asyncio
async def test_files_list(agents_manager, mock_client):
    """Test listing agent files"""
    mock_response = {"files": ["prompts/system.txt", "prompts/intro.txt"]}
    mock_client._send_request.return_value = mock_response

    result = await agents_manager.files_list("agent-1")

    assert len(result) == 2
    assert "prompts/system.txt" in result


@pytest.mark.asyncio
async def test_files_get(agents_manager, mock_client):
    """Test getting agent file content"""
    mock_response = {"content": "System prompt content"}
    mock_client._send_request.return_value = mock_response

    result = await agents_manager.files_get("agent-1", "prompts/system.txt")

    assert result == "System prompt content"
    call_args = mock_client._send_request.call_args
    assert call_args[0][1]["path"] == "prompts/system.txt"


@pytest.mark.asyncio
async def test_files_set(agents_manager, mock_client):
    """Test setting agent file content"""
    mock_client._send_request.return_value = {"ok": True}

    result = await agents_manager.files_set(
        "agent-1", "prompts/system.txt", "New content"
    )

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][1]["content"] == "New content"
