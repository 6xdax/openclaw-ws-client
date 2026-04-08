"""Convenience classes and helpers for OpenClaw SDK"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional, Any, Dict, AsyncIterator, Callable
from dataclasses import dataclass
from .client import StreamEvent

if TYPE_CHECKING:
    from .client import OpenClawClient


@dataclass
class Message:
    """A message in a chat session"""
    role: str  # "user", "agent", "system"
    text: str
    timestamp: Optional[int] = None


@dataclass
class ToolCall:
    """A tool call during agent execution"""
    name: str
    input_data: Dict[str, Any]
    output: Optional[str] = None
    phase: Optional[str] = None  # "start", "result", "error"


class ChatSession:
    """
    Convenience class for chat sessions with streaming support.

    Usage:
        async with OpenClawClient() as client:
            chat = ChatSession(client, session_key)
            async for chunk in chat.stream_send("Hello!"):
                print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        client: "OpenClawClient",
        session_key: str,
    ):
        self.client = client
        self.session_key = session_key
        self._handlers: Dict[str, Callable] = {}

    async def send(
        self,
        text: str,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a message (non-streaming).

        Args:
            text: Message text
            stream: Ignored (for compatibility)

        Returns:
            Response data
        """
        return await self.client.sessions.send(self.session_key, text, stream=False)

    async def stream_send(
        self,
        text: str,
    ) -> AsyncIterator[StreamEvent]:
        """
        Send a message and stream the response.

        Args:
            text: Message text

        Yields:
            StreamEvent objects
        """
        async for event in self.client.send_message_stream(self.session_key, text):
            yield event

    async def stream_text(self) -> AsyncIterator[str]:
        """
        Stream only text chunks from agent responses.

        Yields:
            Text strings as they arrive
        """
        async for event in self.stream_send(""):
            if event.type == "text":
                # Extract text from various event data formats
                data = event.data
                if isinstance(data, dict):
                    text = data.get("text") or data.get("content") or data.get("delta", "")
                else:
                    text = str(data)
                if text:
                    yield text

    async def on_event(self, event_type: str, handler: Callable):
        """
        Register an event handler for this session.

        Args:
            event_type: Event type (e.g., "agent", "session.tool")
            handler: Callback function(payload)
        """
        self._handlers[event_type] = handler
        self.client.on(event_type, handler)

    async def reset(self) -> bool:
        """Reset the session (clear history)."""
        return await self.client.sessions.reset(self.session_key)

    async def abort(self) -> bool:
        """Abort ongoing execution."""
        return await self.client.sessions.abort(self.session_key)

    async def preview(self, limit: int = 10) -> list:
        """Get message preview."""
        return await self.client.sessions.preview(self.session_key, limit)

    async def patch(self, **kwargs) -> Dict[str, Any]:
        """Update session metadata."""
        return await self.client.sessions.patch(self.session_key, **kwargs)

    async def compact(self) -> bool:
        """Compact the session."""
        return await self.client.sessions.compact(self.session_key)

    def subscribe(self) -> bool:
        """Subscribe to session events (non-blocking)."""
        # Note: This is sync because it just registers the subscription
        # The actual event flow goes through client's events() iterator
        return True  # Subscription is handled by the client's listen loop
