"""OpenClaw Tools / Plugins Management"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from .client import OpenClawClient


class ToolsManager:
    """Manage OpenClaw Tools"""

    __slots__ = ("_client",)

    def __init__(self, client: "OpenClawClient") -> None:
        self._client: "OpenClawClient" = client

    async def catalog(self) -> List[Dict[str, Any]]:
        """
        List all available tools in the catalog.

        Returns:
            List of tool definitions
        """
        resp: Dict[str, Any] = await self._client._send_request("tools.catalog")
        return resp.get("tools", [])

    async def effective(self) -> List[Dict[str, Any]]:
        """
        Get the list of tools that are currently effective (enabled).

        Returns:
            List of enabled tool definitions
        """
        resp = await self._client._send_request("tools.effective")
        return resp.get("tools", [])

    async def enable(self, name: str) -> bool:
        """
        Enable a tool.

        Args:
            name: Tool name

        Returns:
            True if enabled successfully
        """
        resp = await self._client._send_request("tools.enable", {"name": name})
        return resp.get("ok", False)

    async def disable(self, name: str) -> bool:
        """
        Disable a tool.

        Args:
            name: Tool name

        Returns:
            True if disabled successfully
        """
        resp = await self._client._send_request("tools.disable", {"name": name})
        return resp.get("ok", False)
