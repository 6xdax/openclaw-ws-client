"""OpenClaw Agent Management"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from .client import OpenClawClient


class AgentsManager:
    """Manage OpenClaw Agents"""

    __slots__ = ("_client",)

    def __init__(self, client: "OpenClawClient") -> None:
        self._client: "OpenClawClient" = client

    async def list(self) -> List[Dict[str, Any]]:
        """
        List all agents.

        Returns:
            List of agent objects
        """
        resp: Dict[str, Any] = await self._client._send_request("agents.list")
        return resp.get("agents", [])

    async def create(
        self,
        name: str,
        model: Optional[str] = None,
        prompts: Optional[Dict[str, str]] = None,
        skills: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a new agent.

        Args:
            name: Agent name
            model: Model to use (e.g., "minimax-m2.7")
            prompts: Prompt templates (e.g., {"system": "...", "intro": "..."})
            skills: List of skill names to enable
            **kwargs: Additional agent configuration

        Returns:
            Created agent object
        """
        params: Dict[str, Any] = {"name": name}
        if model is not None:
            params["model"] = model
        if prompts is not None:
            params["prompts"] = prompts
        if skills is not None:
            params["skills"] = skills
        params.update(kwargs)

        resp = await self._client._send_request("agents.create", params)
        return resp.get("agent", {})

    async def update(self, agent_id: str, **updates: Any) -> Dict[str, Any]:
        """
        Update an existing agent.

        Args:
            agent_id: Agent ID to update
            **updates: Fields to update

        Returns:
            Updated agent object
        """
        params: Dict[str, Any] = {"agentId": agent_id, **updates}
        resp = await self._client._send_request("agents.update", params)
        return resp.get("agent", {})

    async def delete(self, agent_id: str) -> bool:
        """
        Delete an agent.

        Args:
            agent_id: Agent ID to delete

        Returns:
            True if deleted successfully
        """
        resp = await self._client._send_request("agents.delete", {"agentId": agent_id})
        return resp.get("ok", False)

    async def files_list(self, agent_id: str) -> List[str]:
        """
        List files associated with an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of file paths
        """
        resp = await self._client._send_request(
            "agents.files.list", {"agentId": agent_id}
        )
        return resp.get("files", [])

    async def files_get(self, agent_id: str, path: str) -> str:
        """
        Get file content from an agent.

        Args:
            agent_id: Agent ID
            path: File path

        Returns:
            File content
        """
        resp = await self._client._send_request(
            "agents.files.get", {"agentId": agent_id, "path": path}
        )
        return resp.get("content", "")

    async def files_set(self, agent_id: str, path: str, content: str) -> bool:
        """
        Set file content for an agent.

        Args:
            agent_id: Agent ID
            path: File path
            content: File content

        Returns:
            True if set successfully
        """
        resp = await self._client._send_request(
            "agents.files.set",
            {"agentId": agent_id, "path": path, "content": content},
        )
        return resp.get("ok", False)
