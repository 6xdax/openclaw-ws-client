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

            # Use ChatSession helper
            from openclaw.helpers import ChatSession
            chat = ChatSession(client, session["sessionKey"])
            async for event in chat.stream_send("Hello!"):
                print(event)

            # Listen for events
            client.on("agent", lambda p: print(f"Agent event: {p}"))
"""

from .client import OpenClawClient, StreamEvent
from .agents import AgentsManager
from .sessions import SessionsManager
from .tools import ToolsManager
from .config import ConfigManager
from .nodes import NodesManager
from .helpers import ChatSession, Message, ToolCall
from .misc import HealthManager, LogsManager, SecretsManager, StatusManager, UsageManager
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

__version__ = "0.2.0"
__all__ = [
    # Core
    "OpenClawClient",
    "StreamEvent",
    # Managers
    "AgentsManager",
    "SessionsManager",
    "ToolsManager",
    "ConfigManager",
    "NodesManager",
    "HealthManager",
    "LogsManager",
    "SecretsManager",
    "StatusManager",
    "UsageManager",
    # Helpers
    "ChatSession",
    "Message",
    "ToolCall",
    # Exceptions
    "OpenClawError",
    "ConnectionError",
    "AuthenticationError",
    "AgentNotFoundError",
    "SessionNotFoundError",
    "ToolNotFoundError",
    "RequestError",
    "TimeoutError",
]
