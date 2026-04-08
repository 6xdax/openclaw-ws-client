"""OpenClaw misc methods: health, logs, secrets, etc."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from .client import OpenClawClient


class HealthManager:
    """Manage OpenClaw health checks"""

    def __init__(self, client: "OpenClawClient") -> None:
        self._client = client

    async def check(self) -> Dict[str, Any]:
        """
        Perform health check.

        Returns:
            Health status
        """
        resp = await self._client._send_request("health", {})
        return resp


class LogsManager:
    """Manage OpenClaw logs"""

    def __init__(self, client: "OpenClawClient") -> None:
        self._client = client

    async def tail(self, lines: int = 50, filter_text: Optional[str] = None) -> str:
        """
        Get recent log lines.

        Args:
            lines: Number of lines to retrieve
            filter_text: Optional text to filter logs

        Returns:
            Log content as string
        """
        params: Dict[str, Any] = {"lines": lines}
        if filter_text:
            params["filter"] = filter_text
        resp = await self._client._send_request("logs.tail", params)
        return resp.get("logs", "")


class SecretsManager:
    """Manage OpenClaw secrets"""

    def __init__(self, client: "OpenClawClient") -> None:
        self._client = client

    async def resolve(self, keys: List[str]) -> Dict[str, str]:
        """
        Resolve secrets by keys.

        Args:
            keys: List of secret keys to resolve

        Returns:
            Dictionary of resolved secrets
        """
        resp = await self._client._send_request("secrets.resolve", {"keys": keys})
        return resp.get("secrets", {})

    async def reload(self) -> bool:
        """
        Reload secrets from storage.

        Returns:
            True if reloaded
        """
        resp = await self._client._send_request("secrets.reload", {})
        return resp.get("ok", False)


class StatusManager:
    """Manage OpenClaw status"""

    def __init__(self, client: "OpenClawClient") -> None:
        self._client = client

    async def get(self) -> Dict[str, Any]:
        """
        Get system status.

        Returns:
            System status
        """
        resp = await self._client._send_request("status", {})
        return resp


class UsageManager:
    """Manage OpenClaw usage stats"""

    def __init__(self, client: "OpenClawClient") -> None:
        self._client = client

    async def status(self) -> Dict[str, Any]:
        """
        Get usage status.

        Returns:
            Usage statistics
        """
        resp = await self._client._send_request("usage.status", {})
        return resp

    async def cost(self) -> Dict[str, Any]:
        """
        Get cost information.

        Returns:
            Cost statistics
        """
        resp = await self._client._send_request("usage.cost", {})
        return resp
