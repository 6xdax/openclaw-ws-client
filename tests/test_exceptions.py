"""Tests for exceptions module"""

import pytest
from openclaw.exceptions import (
    OpenClawError,
    ConnectionError,
    AuthenticationError,
    AgentNotFoundError,
    SessionNotFoundError,
    ToolNotFoundError,
    RequestError,
    TimeoutError,
)


def test_openclaw_error():
    """Test base OpenClawError"""
    err = OpenClawError("Test error", code="TEST", details={"key": "value"})
    assert err.message == "Test error"
    assert err.code == "TEST"
    assert err.details == {"key": "value"}
    assert str(err) == "Test error"


def test_openclaw_error_default():
    """Test OpenClawError with defaults"""
    err = OpenClawError("Test error")
    assert err.message == "Test error"
    assert err.code is None
    assert err.details == {}


def test_connection_error():
    """Test ConnectionError"""
    err = ConnectionError("Connection failed")
    assert isinstance(err, OpenClawError)
    assert err.message == "Connection failed"


def test_authentication_error():
    """Test AuthenticationError"""
    err = AuthenticationError("Auth failed", code="AUTH_FAILED")
    assert isinstance(err, OpenClawError)
    assert err.code == "AUTH_FAILED"


def test_agent_not_found_error():
    """Test AgentNotFoundError"""
    err = AgentNotFoundError("Agent not found", code="AGENT_NOT_FOUND")
    assert isinstance(err, OpenClawError)
    assert "Agent not found" in str(err)


def test_session_not_found_error():
    """Test SessionNotFoundError"""
    err = SessionNotFoundError("Session not found")
    assert isinstance(err, OpenClawError)


def test_tool_not_found_error():
    """Test ToolNotFoundError"""
    err = ToolNotFoundError("Tool not found")
    assert isinstance(err, OpenClawError)


def test_request_error():
    """Test RequestError"""
    err = RequestError("Request failed", code="REQUEST_FAILED")
    assert isinstance(err, OpenClawError)
    assert err.code == "REQUEST_FAILED"


def test_timeout_error():
    """Test TimeoutError"""
    err = TimeoutError("Request timed out")
    assert isinstance(err, OpenClawError)
