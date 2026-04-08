"""
OpenClaw Python SDK

A Python client library for OpenClaw Gateway.

Usage:
    import asyncio
    from openclaw import OpenClawClient

    async def main():
        async with OpenClawClient() as client:
            # List agents
            agents = await client.agents.list()
            print(agents)

            # Create session
            session = await client.sessions.create(agent_id="my-agent")
            print(session)

            # Send message
            await client.sessions.send(session["sessionKey"], "Hello!")

            # Listen for events
            client.on("agent", lambda p: print(f"Agent event: {p}"))
"""

from .client import OpenClawClient
from .agents import AgentsManager
from .sessions import SessionsManager
from .tools import ToolsManager
from .exceptions import (
    OpenClawError,
    ConnectionError,
    AuthenticationError,
    AgentNotFoundError,
    SessionNotFoundError,
    ToolNotFoundError,
    RequestError,
    TimeoutError,
)

__version__ = "0.1.0"
__all__ = [
    "OpenClawClient",
    "AgentsManager",
    "SessionsManager",
    "ToolsManager",
    "OpenClawError",
    "ConnectionError",
    "AuthenticationError",
    "AgentNotFoundError",
    "SessionNotFoundError",
    "ToolNotFoundError",
    "RequestError",
    "TimeoutError",
]
