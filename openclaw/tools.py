"""OpenClaw Tools / Plugins Management"""

from typing import Dict, Any, List


class ToolsManager:
    """Manage OpenClaw Tools"""

    def __init__(self, client):
        self._client = client

    async def catalog(self) -> List[Dict[str, Any]]:
        """
        List all available tools in the catalog.

        Returns:
            List of tool definitions
        """
        resp = await self._client._send_request("tools.catalog")
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
