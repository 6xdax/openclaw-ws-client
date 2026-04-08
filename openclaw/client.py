"""OpenClaw Gateway WebSocket Client"""

import os
import asyncio
import json
import base64
import random
import string
from typing import Optional, Any, Dict, Callable, AsyncIterator
from websockets.asyncio import client as ws_client

# Load .env if present
from dotenv import load_dotenv
load_dotenv()

from .exceptions import (
    OpenClawError,
    ConnectionError as OpenClawConnectionError,
    AuthenticationError,
    RequestError,
)
from .crypto_utils import load_openclaw_identity, sign_device_auth_v2
from .agents import AgentsManager
from .sessions import SessionsManager
from .tools import ToolsManager
from cryptography.hazmat.primitives import serialization


def gen_nonce(length: int = 32) -> str:
    """Generate random nonce"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


class OpenClawClient:
    """
    OpenClaw Gateway WebSocket Client

    Usage:
        client = OpenClawClient()
        await client.connect()
        agents = await client.agents.list()
        await client.close()
    """

    def __init__(
        self,
        url: str = None,
        token: str = None,
        device_id: str = None,
        client_id: str = "cli",
        client_mode: str = "probe",
        role: str = "operator",
        scopes: list = None,
        reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
    ):
        self.url = url or os.environ.get("OPENCLAW_URL", "ws://127.0.0.1:18789")
        self.token = token or os.environ.get("OPENCLAW_TOKEN", "")
        self.device_id = device_id or os.environ.get("OPENCLAW_DEVICE_ID", None)
        self.client_id = client_id
        self.client_mode = client_mode
        self.role = role
        self.scopes = scopes or ["operator.read"]
        self.reconnect = reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay

        self.ws: Optional[Any] = None
        self.device_token: Optional[str] = None
        self.private_key = None
        self.public_key = None
        self._device_id_from_key: Optional[str] = None
        self._pending_requests: Dict[str, asyncio.Future] = {}
        self._listening_task: Optional[asyncio.Task] = None
        self._event_handlers: Dict[str, Callable] = {}

        # Initialize managers
        self.agents = AgentsManager(self)
        self.sessions = SessionsManager(self)
        self.tools = ToolsManager(self)

    def _load_identity(self):
        """Load device identity from OpenClaw config"""
        self.private_key, self.public_key, self._device_id_from_key = load_openclaw_identity()
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
            challenge = await self.ws.recv()
            ch_data = json.loads(challenge)
            nonce = ch_data["payload"]["nonce"]
            ts = ch_data["payload"]["ts"]

            # 2. Build and send connect request
            payload = self._build_connect_request(nonce, ts)
            await self.ws.send(json.dumps(payload, separators=(",", ":")))

            # 3. Receive response
            resp = await self.ws.recv()
            resp_data = json.loads(resp)

            if not resp_data.get("ok", False):
                error = resp_data.get("error", {})
                raise AuthenticationError(
                    message=error.get("message", "Authentication failed"),
                    code=error.get("code"),
                    details=error.get("details"),
                )

            # 4. Success
            payload_type = resp_data.get("payload", {}).get("type")
            if payload_type == "hello-ok":
                self.device_token = resp_data.get("payload", {}).get("auth", {}).get("deviceToken")
                # Start listening for events
                self._listening_task = asyncio.create_task(self._listen())
                return True

            raise AuthenticationError(f"Unexpected response type: {payload_type}")

        except Exception as e:
            await self.ws.close()
            self.ws = None
            if isinstance(e, AuthenticationError):
                raise
            raise OpenClawConnectionError(f"Connection failed: {e}") from e

    def _build_connect_request(self, nonce: str, ts: int) -> dict:
        """Build signed connect request"""
        raw_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        public_key_b64 = base64.b64encode(raw_bytes).decode()

        sig = sign_device_auth_v2(
            device_id=self.device_id,
            client_id=self.client_id,
            client_mode=self.client_mode,
            role=self.role,
            scopes=self.scopes,
            signed_at_ms=ts,
            token=self.token or "",
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

    async def _send_request(self, method: str, params: dict = None, timeout: float = 30) -> dict:
        """
        Send request and wait for response.

        Args:
            method: RPC method name
            params: Method parameters
            timeout: Request timeout in seconds

        Returns:
            Response data

        Raises:
            RequestError: If request fails.
            TimeoutError: If request times out.
        """
        if self.ws is None:
            raise OpenClawConnectionError("Not connected")

        req_id = gen_nonce()
        req = {
            "type": "req",
            "id": req_id,
            "method": method,
            "params": params or {},
        }

        future = asyncio.Future()
        self._pending_requests[req_id] = future

        try:
            await self.ws.send(json.dumps(req, separators=(",", ":")))
            resp = await asyncio.wait_for(future, timeout=timeout)
            return resp
        except asyncio.TimeoutError:
            self._pending_requests.pop(req_id, None)
            raise TimeoutError(f"Request {method} timed out after {timeout}s")
        except Exception as e:
            self._pending_requests.pop(req_id, None)
            raise RequestError(f"Request {method} failed: {e}") from e

    async def _listen(self):
        """Listen for incoming messages and dispatch to handlers"""
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                msg_type = data.get("type") or data.get("event", "")

                if msg_type == "res" and "id" in data:
                    # Response to a pending request
                    req_id = data["id"]
                    future = self._pending_requests.pop(req_id, None)
                    if future and not future.done():
                        if data.get("ok"):
                            future.set_result(data.get("payload", {}))
                        else:
                            error = data.get("error", {})
                            future.set_exception(RequestError(
                                message=error.get("message", "Request failed"),
                                code=error.get("code"),
                                details=error.get("details"),
                            ))
                elif msg_type == "event":
                    # Event notification
                    event_name = data.get("event", "")
                    payload = data.get("payload", {})
                    handler = self._event_handlers.get(event_name)
                    if handler:
                        asyncio.create_task(handler(payload))
                elif msg_type == "res" and "id" not in data:
                    # Unsolicited response
                    pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            # Log error but don't crash
            print(f"[listen] Error: {e}")

    def on(self, event: str, handler: Callable):
        """
        Register event handler.

        Args:
            event: Event name (e.g., "agent", "session.tool")
            handler: Async function to handle the event
        """
        self._event_handlers[event] = handler

    async def close(self):
        """Close the connection"""
        if self._listening_task:
            self._listening_task.cancel()
            self._listening_task = None
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
