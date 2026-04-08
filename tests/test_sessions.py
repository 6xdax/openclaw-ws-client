"""Tests for sessions module"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from openclaw.sessions import SessionsManager


@pytest.fixture
def mock_client():
    """Create a mock OpenClawClient"""
    client = MagicMock()
    client._send_request = AsyncMock()
    return client


@pytest.fixture
def sessions_manager(mock_client):
    """Create a SessionsManager with mock client"""
    return SessionsManager(mock_client)


@pytest.mark.asyncio
async def test_list_sessions(sessions_manager, mock_client):
    """Test listing sessions"""
    mock_response = {
        "sessions": [
            {"sessionKey": "sess-1", "title": "Session 1"},
            {"sessionKey": "sess-2", "title": "Session 2"},
        ]
    }
    mock_client._send_request.return_value = mock_response

    result = await sessions_manager.list()

    assert len(result) == 2
    assert result[0]["sessionKey"] == "sess-1"
    mock_client._send_request.assert_called_once_with("sessions.list")


@pytest.mark.asyncio
async def test_create_session(sessions_manager, mock_client):
    """Test creating a session"""
    mock_response = {
        "session": {"sessionKey": "new-session", "title": "New Session"}
    }
    mock_client._send_request.return_value = mock_response

    result = await sessions_manager.create(
        agent_id="agent-1",
        title="New Session",
    )

    assert result["sessionKey"] == "new-session"
    call_args = mock_client._send_request.call_args
    assert call_args[0][1]["agentId"] == "agent-1"
    assert call_args[0][1]["title"] == "New Session"


@pytest.mark.asyncio
async def test_create_session_without_agent(sessions_manager, mock_client):
    """Test creating a session without agent_id"""
    mock_response = {"session": {"sessionKey": "new-session"}}
    mock_client._send_request.return_value = mock_response

    result = await sessions_manager.create(title="Just a title")

    call_args = mock_client._send_request.call_args
    assert "agentId" not in call_args[0][1]
    assert call_args[0][1]["title"] == "Just a title"


@pytest.mark.asyncio
async def test_delete_session(sessions_manager, mock_client):
    """Test deleting a session"""
    mock_client._send_request.return_value = {"ok": True}

    result = await sessions_manager.delete("sess-1")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][1] == {"sessionKey": "sess-1"}


@pytest.mark.asyncio
async def test_send_message(sessions_manager, mock_client):
    """Test sending a message"""
    mock_client._send_request.return_value = {"ok": True}

    result = await sessions_manager.send("sess-1", "Hello, world!")

    assert result is not None
    call_args = mock_client._send_request.call_args
    assert call_args[0][1]["sessionKey"] == "sess-1"
    assert call_args[0][1]["text"] == "Hello, world!"
    assert call_args[0][1]["stream"] is True


@pytest.mark.asyncio
async def test_subscribe(sessions_manager, mock_client):
    """Test subscribing to session events"""
    mock_client._send_request.return_value = {"ok": True}

    result = await sessions_manager.subscribe("sess-1")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][1] == {"sessionKey": "sess-1"}


@pytest.mark.asyncio
async def test_subscribe_all(sessions_manager, mock_client):
    """Test subscribing to all session events"""
    mock_client._send_request.return_value = {"ok": True}

    result = await sessions_manager.subscribe()

    call_args = mock_client._send_request.call_args
    assert call_args[0][1] == {}


@pytest.mark.asyncio
async def test_abort(sessions_manager, mock_client):
    """Test aborting a session"""
    mock_client._send_request.return_value = {"ok": True}

    result = await sessions_manager.abort("sess-1")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][0] == "sessions.abort"


@pytest.mark.asyncio
async def test_reset(sessions_manager, mock_client):
    """Test resetting a session"""
    mock_client._send_request.return_value = {"ok": True}

    result = await sessions_manager.reset("sess-1")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][0] == "sessions.reset"


@pytest.mark.asyncio
async def test_patch_session(sessions_manager, mock_client):
    """Test patching session metadata"""
    mock_response = {"session": {"sessionKey": "sess-1", "title": "New Title", "pinned": True}}
    mock_client._send_request.return_value = mock_response

    result = await sessions_manager.patch("sess-1", title="New Title", pinned=True)

    call_args = mock_client._send_request.call_args
    assert call_args[0][1]["title"] == "New Title"
    assert call_args[0][1]["pinned"] is True


@pytest.mark.asyncio
async def test_compact(sessions_manager, mock_client):
    """Test compacting a session"""
    mock_client._send_request.return_value = {"ok": True}

    result = await sessions_manager.compact("sess-1")

    assert result is True
    call_args = mock_client._send_request.call_args
    assert call_args[0][0] == "sessions.compact"


@pytest.mark.asyncio
async def test_preview(sessions_manager, mock_client):
    """Test previewing session messages"""
    mock_response = {
        "messages": [
            {"role": "user", "text": "Hello"},
            {"role": "agent", "text": "Hi there!"},
        ]
    }
    mock_client._send_request.return_value = mock_response

    result = await sessions_manager.preview("sess-1", limit=5)

    assert len(result) == 2
    call_args = mock_client._send_request.call_args
    assert call_args[0][1]["limit"] == 5
