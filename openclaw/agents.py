"""OpenClaw Agent Management"""

from typing import Dict, Any, List


class AgentsManager:
    """Manage OpenClaw Agents"""

    def __init__(self, client):
        self._client = client

    async def list(self) -> List[Dict[str, Any]]:
        """
        List all agents.

        Returns:
            List of agent objects
        """
        resp = await self._client._send_request("agents.list")
        return resp.get("agents", [])

    async def create(
        self,
        name: str,
        model: str = None,
        prompts: Dict[str, str] = None,
        skills: List[str] = None,
        **kwargs
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
        params = {"name": name}
        if model:
            params["model"] = model
        if prompts:
            params["prompts"] = prompts
        if skills:
            params["skills"] = skills
        params.update(kwargs)

        resp = await self._client._send_request("agents.create", params)
        return resp.get("agent", {})

    async def update(self, agent_id: str, **updates) -> Dict[str, Any]:
        """
        Update an existing agent.

        Args:
            agent_id: Agent ID to update
            **updates: Fields to update

        Returns:
            Updated agent object
        """
        params = {"agentId": agent_id, **updates}
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
        resp = await self._client._send_request("agents.files.list", {"agentId": agent_id})
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
        resp = await self._client._send_request("agents.files.get", {"agentId": agent_id, "path": path})
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
            {"agentId": agent_id, "path": path, "content": content}
        )
        return resp.get("ok", False)
