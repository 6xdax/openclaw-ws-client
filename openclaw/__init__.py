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

            # Send message with streaming
            async for event in client.send_message_stream(session["sessionKey"], "Hello!"):
                if event.type == "text":
                    print(event.data.get("text", ""), end="", flush=True)
                elif event.type == "tool":
                    print(f"\\n[Tool: {event.data.get('name')}]")

            # Listen for events
            client.on("agent", lambda p: print(f"Agent event: {p}"))
"""

from .client import OpenClawClient, StreamEvent
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
    "StreamEvent",
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
