"""OpenClaw Gateway WebSocket Client"""

from __future__ import annotations

import os
import asyncio
import json
import base64
import random
import string
from typing import (
    Optional,
    Any,
    Dict,
    Callable,
    AsyncIterator,
    List,
    Union,
    Literal,
)
from websockets.asyncio import client as ws_client
from dataclasses import dataclass

# Load .env if present
from dotenv import load_dotenv

load_dotenv()

from .exceptions import (
    OpenClawError,
    ConnectionError as OpenClawConnectionError,
    AuthenticationError,
    RequestError,
    TimeoutError as OpenClawTimeoutError,
)
from .crypto_utils import load_openclaw_identity, sign_device_auth_v2
from .agents import AgentsManager
from .sessions import SessionsManager
from .tools import ToolsManager
from cryptography.hazmat.primitives import serialization


def gen_nonce(length: int = 32) -> str:
    """Generate random nonce"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


@dataclass
class StreamEvent:
    """Stream event from OpenClaw"""
    type: str  # "text", "tool", "agent", "session"
    data: Dict[str, Any]
    session_key: Optional[str] = None


class OpenClawClient:
    """
    OpenClaw Gateway WebSocket Client

    Usage:
        async with OpenClawClient() as client:
            agents = await client.agents.list()
            await client.close()
    """

    __slots__ = (
        "url",
        "token",
        "device_id",
        "client_id",
        "client_mode",
        "role",
        "scopes",
        "reconnect",
        "max_reconnect_attempts",
        "reconnect_delay",
        "ws",
        "device_token",
        "private_key",
        "public_key",
        "_device_id_from_key",
        "_pending_requests",
        "_listening_task",
        "_event_handlers",
        "_stream_queue",
        "_reconnect_count",
        "_should_reconnect",
        "agents",
        "sessions",
        "tools",
    )

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        device_id: Optional[str] = None,
        client_id: str = "cli",
        client_mode: str = "probe",
        role: str = "operator",
        scopes: Optional[List[str]] = None,
        reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
    ) -> None:
        """
        Initialize OpenClaw client.

        Args:
            url: Gateway WebSocket URL (default: ws://127.0.0.1:18789)
            token: Gateway auth token
            device_id: Device ID (auto-derived from key if not provided)
            client_id: Client identifier
            client_mode: Client mode (probe, cli, webchat, etc.)
            role: Client role (operator, etc.)
            scopes: List of permission scopes
            reconnect: Enable auto-reconnect
            max_reconnect_attempts: Max reconnection attempts
            reconnect_delay: Initial delay between reconnections (seconds)
        """
        self.url: str = url or os.environ.get("OPENCLAW_URL", "ws://127.0.0.1:18789")
        self.token: str = token or os.environ.get("OPENCLAW_TOKEN", "")
        self.device_id: Optional[str] = device_id or os.environ.get(
            "OPENCLAW_DEVICE_ID", None
        )
        self.client_id: str = client_id
        self.client_mode: str = client_mode
        self.role: str = role
        self.scopes: List[str] = scopes or ["operator.read"]
        self.reconnect: bool = reconnect
        self.max_reconnect_attempts: int = max_reconnect_attempts
        self.reconnect_delay: float = reconnect_delay

        # WebSocket state
        self.ws: Optional[Any] = None
        self.device_token: Optional[str] = None

        # Cryptographic keys
        self.private_key: Any = None
        self.public_key: Any = None
        self._device_id_from_key: Optional[str] = None

        # Request tracking
        self._pending_requests: Dict[str, asyncio.Future[Dict[str, Any]]] = {}

        # Event handling
        self._listening_task: Optional[asyncio.Task[None]] = None
        self._event_handlers: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

        # Streaming
        self._stream_queue: asyncio.Queue[StreamEvent] = asyncio.Queue()
        self._reconnect_count: int = 0
        self._should_reconnect: bool = True

        # Managers
        self.agents: AgentsManager = AgentsManager(self)
        self.sessions: SessionsManager = SessionsManager(self)
        self.tools: ToolsManager = ToolsManager(self)

    def _load_identity(self) -> None:
        """Load device identity from OpenClaw config"""
        (
            self.private_key,
            self.public_key,
            self._device_id_from_key,
        ) = load_openclaw_identity()
        if self.device_id is None:
            self.device_id = self._device_id_from_key

    async def connect(self) -> bool:
        """
        Connect to OpenClaw Gateway and authenticate.

        Returns:
            True if connected successfully.

        Raises:
            OpenClawConnectionError: If connection fails.
            AuthenticationError: If authentication fails.
        """
        if self.private_key is None:
            self._load_identity()

        try:
            self.ws = await ws_client.connect(
                self.url,
                additional_headers={"Origin": "http://127.0.0.1:18789"},
            )
        except Exception as e:
            raise OpenClawConnectionError(f"Failed to connect: {e}") from e

        try:
            # 1. Receive challenge
            challenge: Union[str, bytes] = await self.ws.recv()
            ch_data: Dict[str, Any] = json.loads(challenge)
            nonce: str = ch_data["payload"]["nonce"]
            ts: int = ch_data["payload"]["ts"]

            # 2. Build and send connect request
            payload: Dict[str, Any] = self._build_connect_request(nonce, ts)
            await self.ws.send(json.dumps(payload, separators=(",", ":")))

            # 3. Receive response
            resp: Union[str, bytes] = await self.ws.recv()
            resp_data: Dict[str, Any] = json.loads(resp)

            if not resp_data.get("ok", False):
                error: Dict[str, Any] = resp_data.get("error", {})
                raise AuthenticationError(
                    message=error.get("message", "Authentication failed"),
                    code=error.get("code"),
                    details=error.get("details"),
                )

            # 4. Success
            payload_type: str = resp_data.get("payload", {}).get("type")
            if payload_type == "hello-ok":
                self.device_token = resp_data.get("payload", {}).get("auth", {}).get(
                    "deviceToken"
                )
                # Start listening for events
                self._listening_task = asyncio.create_task(self._listen())
                self._reconnect_count = 0
                return True

            raise AuthenticationError(f"Unexpected response type: {payload_type}")

        except Exception as e:
            if self.ws is not None:
                await self.ws.close()
            self.ws = None
            if isinstance(e, AuthenticationError):
                raise
            raise OpenClawConnectionError(f"Connection failed: {e}") from e

    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.

        Returns:
            True if reconnected successfully.
        """
        if not self.reconnect:
            return False

        if self._reconnect_count >= self.max_reconnect_attempts:
            print(f"[reconnect] Max attempts ({self.max_reconnect_attempts}) reached")
            return False

        self._reconnect_count += 1
        delay = self.reconnect_delay * (2 ** (self._reconnect_count - 1))
        print(f"[reconnect] Attempt {self._reconnect_count}/{self.max_reconnect_attempts} in {delay}s...")

        await asyncio.sleep(delay)

        try:
            return await self.connect()
        except Exception as e:
            print(f"[reconnect] Failed: {e}")
            return await self._reconnect()

    def _build_connect_request(self, nonce: str, ts: int) -> Dict[str, Any]:
        """Build signed connect request"""
        raw_bytes: bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        public_key_b64: str = base64.b64encode(raw_bytes).decode()

        sig: str = sign_device_auth_v2(
            device_id=self.device_id,  # type: ignore
            client_id=self.client_id,
            client_mode=self.client_mode,
            role=self.role,
            scopes=self.scopes,
            signed_at_ms=ts,
            token=self.token,
            nonce=nonce,
            private_key=self.private_key,
        )

        return {
            "type": "req",
            "id": gen_nonce(),
            "method": "connect",
            "params": {
                "minProtocol": 3,
                "maxProtocol": 3,
                "client": {
                    "id": self.client_id,
                    "version": "1.0.0",
                    "platform": "linux",
                    "mode": self.client_mode,
                },
                "role": self.role,
                "scopes": self.scopes,
                "caps": [],
                "commands": [],
                "permissions": {},
                "auth": {"token": self.token},
                "locale": "zh-CN",
                "userAgent": f"{self.client_id}/1.0.0",
                "device": {
                    "id": self.device_id,
                    "publicKey": public_key_b64,
                    "signature": sig,
                    "signedAt": ts,
                    "nonce": nonce,
                },
            },
        }

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Send request and wait for response.

        Args:
            method: RPC method name
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Response data

        Raises:
            OpenClawConnectionError: If not connected.
            OpenClawTimeoutError: If request times out.
            RequestError: If request fails.
        """
        if self.ws is None:
            raise OpenClawConnectionError("Not connected")

        req_id: str = gen_nonce()
        req: Dict[str, Any] = {
            "type": "req",
            "id": req_id,
            "method": method,
            "params": params or {},
        }

        future: asyncio.Future[Dict[str, Any]] = asyncio.Future()
        self._pending_requests[req_id] = future

        try:
            await self.ws.send(json.dumps(req, separators=(",", ":")))
            resp: Dict[str, Any] = await asyncio.wait_for(future, timeout=timeout)
            return resp
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            raise OpenClawTimeoutError(
                f"Request {method} timed out after {timeout}s"
            )
        except Exception as e:
            self._pending_requests.pop(req_id, None)
            raise RequestError(f"Request {method} failed: {e}") from e

    async def _listen(self) -> None:
        """Listen for incoming messages and dispatch to handlers"""
        try:
            async for msg in self.ws:  # type: ignore
                data: Dict[str, Any] = json.loads(msg)
                msg_type: str = data.get("type") or data.get("event", "")

                if msg_type == "res" and "id" in data:
                    # Response to a pending request
                    req_id: str = data["id"]
                    future: Optional[asyncio.Future[Dict[str, Any]]] = (
                        self._pending_requests.pop(req_id, None)
                    )
                    if future is not None and not future.done():
                        if data.get("ok"):
                            future.set_result(data.get("payload", {}))
                        else:
                            error: Dict[str, Any] = data.get("error", {})
                            future.set_exception(
                                RequestError(
                                    message=error.get("message", "Request failed"),
                                    code=error.get("code"),
                                    details=error.get("details"),
                                )
                            )
                elif msg_type == "event":
                    # Event notification - dispatch to stream queue
                    event_name: str = data.get("event", "")
                    payload: Dict[str, Any] = data.get("payload", {})

                    # Create stream event based on event type
                    if event_name == "agent":
                        stream_type = "text"
                        session_key = payload.get("sessionKey")
                    elif event_name == "session.tool":
                        stream_type = "tool"
                        session_key = payload.get("sessionKey")
                    elif event_name == "session.message":
                        stream_type = "message"
                        session_key = payload.get("sessionKey")
                    else:
                        stream_type = event_name
                        session_key = payload.get("sessionKey")

                    event = StreamEvent(
                        type=stream_type,
                        data=payload,
                        session_key=session_key,
                    )
                    await self._stream_queue.put(event)

                    # Also call registered handler
                    handler: Optional[Callable[[Dict[str, Any]], Any]] = (
                        self._event_handlers.get(event_name)
                    )
                    if handler is not None:
                        asyncio.create_task(handler(payload))
                elif msg_type == "res" and "id" not in data:
                    # Unsolicited response
                    pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Log error but don't crash
            print(f"[listen] Error: {e}")
            # Attempt reconnect if enabled
            if self.reconnect and self._should_reconnect:
                await self._reconnect()

    async def events(self) -> AsyncIterator[StreamEvent]:
        """
        Async iterator for streaming events.

        Usage:
            async with OpenClawClient() as client:
                await client.sessions.subscribe("session-key")
                async for event in client.events():
                    print(event.type, event.data)

        Yields:
            StreamEvent objects with type, data, and session_key
        """
        while self._should_reconnect:
            try:
                event = await asyncio.wait_for(
                    self._stream_queue.get(),
                    timeout=60.0
                )
                yield event
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                continue

    async def send_message_stream(
        self,
        session_key: str,
        text: str,
    ) -> AsyncIterator[StreamEvent]:
        """
        Send a message and stream the response.

        This is a convenience method that:
        1. Sends the message
        2. Yields stream events as they arrive

        Usage:
            async with OpenClawClient() as client:
                async for event in client.send_message_stream("sess-key", "Hello!"):
                    if event.type == "text":
                        print(event.data.get("text"), end="", flush=True)
                    elif event.type == "tool":
                        print(f"\\n[Using tool: {event.data.get('name')}]")

        Args:
            session_key: Session key
            text: Message text

        Yields:
            StreamEvent objects
        """
        # Subscribe to the session
        await self.sessions.messages_subscribe(session_key)

        # Send the message
        await self._send_request("sessions.send", {
            "sessionKey": session_key,
            "text": text,
            "stream": True,
        })

        # Yield events until we get a completion signal or timeout
        async for event in self.events():
            if event.session_key == session_key:
                yield event

    def on(
        self, event: str, handler: Callable[[Dict[str, Any]], Any]
    ) -> None:
        """
        Register event handler.

        Args:
            event: Event name (e.g., "agent", "session.tool")
            handler: Async function to handle the event
        """
        self._event_handlers[event] = handler

    async def close(self) -> None:
        """Close the connection"""
        self._should_reconnect = False
        if self._listening_task is not None:
            self._listening_task.cancel()
            self._listening_task = None
        if self.ws is not None:
            await self.ws.close()
            self.ws = None

    async def __aenter__(self) -> "OpenClawClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
