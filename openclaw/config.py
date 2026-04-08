"""OpenClaw Config Management"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, Optional

if TYPE_CHECKING:
    from .client import OpenClawClient


class ConfigManager:
    """Manage OpenClaw configuration"""

    def __init__(self, client: "OpenClawClient") -> None:
        self._client = client

    async def get(self, key: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration.

        Args:
            key: Optional specific key to get

        Returns:
            Configuration object or specific value
        """
        params = {"key": key} if key else {}
        resp = await self._client._send_request("config.get", params)
        return resp.get("config", resp)

    async def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Configuration value

        Returns:
            True if successful
        """
        resp = await self._client._send_request("config.set", {"key": key, "value": value})
        return resp.get("ok", False)

    async def patch(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        """
        Patch configuration with partial update.

        Args:
            patch: Partial configuration to merge

        Returns:
            Updated configuration
        """
        resp = await self._client._send_request("config.patch", {"patch": patch})
        return resp.get("config", resp)

    async def schema(self) -> Dict[str, Any]:
        """
        Get configuration schema.

        Returns:
            Configuration schema
        """
        resp = await self._client._send_request("config.schema", {})
        return resp.get("schema", resp)
