"""OpenClaw SDK Exceptions"""


class OpenClawError(Exception):
    """Base exception for OpenClaw SDK"""
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ConnectionError(OpenClawError):
    """WebSocket connection error"""
    pass


class AuthenticationError(OpenClawError):
    """Authentication failed"""
    pass


class AgentNotFoundError(OpenClawError):
    """Agent not found"""
    pass


class SessionNotFoundError(OpenClawError):
    """Session not found"""
    pass


class ToolNotFoundError(OpenClawError):
    """Tool not found"""
    pass


class RequestError(OpenClawError):
    """Request to gateway failed"""
    pass


class TimeoutError(OpenClawError):
    """Request timed out"""
    pass
