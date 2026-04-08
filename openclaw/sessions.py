"""OpenClaw Session Management"""

from typing import Dict, Any, List


class SessionsManager:
    """Manage OpenClaw Sessions"""

    def __init__(self, client):
        self._client = client

    async def list(self) -> List[Dict[str, Any]]:
        """
        List all sessions.

        Returns:
            List of session objects
        """
        resp = await self._client._send_request("sessions.list")
        return resp.get("sessions", [])

    async def create(
        self,
        agent_id: str = None,
        title: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new session.

        Args:
            agent_id: Agent ID to use for this session
            title: Session title
            **kwargs: Additional session configuration

        Returns:
            Created session object with sessionKey
        """
        params = {}
        if agent_id:
            params["agentId"] = agent_id
        if title:
            params["title"] = title
        params.update(kwargs)

        resp = await self._client._send_request("sessions.create", params)
        return resp.get("session", {})

    async def delete(self, session_key: str) -> bool:
        """
        Delete a session.

        Args:
            session_key: Session key to delete

        Returns:
            True if deleted successfully
        """
        resp = await self._client._send_request("sessions.delete", {"sessionKey": session_key})
        return resp.get("ok", False)

    async def send(
        self,
        session_key: str,
        text: str,
        stream: bool = True
    ) -> Dict[str, Any]:
        """
        Send a message to a session.

        Args:
            session_key: Session key
            text: Message text
            stream: Whether to stream the response

        Returns:
            Response data
        """
        params = {"sessionKey": session_key, "text": text, "stream": stream}
        resp = await self._client._send_request("sessions.send", params)
        return resp

    async def subscribe(self, session_key: str = None) -> bool:
        """
        Subscribe to session events.

        Args:
            session_key: Optional specific session to subscribe to

        Returns:
            True if subscribed successfully
        """
        params = {}
        if session_key:
            params["sessionKey"] = session_key
        resp = await self._client._send_request("sessions.subscribe", params)
        return resp.get("ok", False)

    async def messages_subscribe(self, session_key: str) -> bool:
        """
        Subscribe to messages for a specific session.

        Args:
            session_key: Session key to subscribe to

        Returns:
            True if subscribed successfully
        """
        resp = await self._client._send_request(
            "sessions.messages.subscribe",
            {"sessionKey": session_key}
        )
        return resp.get("ok", False)

    async def abort(self, session_key: str) -> bool:
        """
        Abort ongoing execution in a session.

        Args:
            session_key: Session key

        Returns:
            True if aborted successfully
        """
        resp = await self._client._send_request("sessions.abort", {"sessionKey": session_key})
        return resp.get("ok", False)

    async def reset(self, session_key: str) -> bool:
        """
        Reset a session (clear history).

        Args:
            session_key: Session key to reset

        Returns:
            True if reset successfully
        """
        resp = await self._client._send_request("sessions.reset", {"sessionKey": session_key})
        return resp.get("ok", False)

    async def patch(
        self,
        session_key: str,
        title: str = None,
        pinned: bool = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update session metadata.

        Args:
            session_key: Session key
            title: New title
            pinned: Whether to pin the session
            **kwargs: Additional fields to update

        Returns:
            Updated session object
        """
        params = {"sessionKey": session_key}
        if title is not None:
            params["title"] = title
        if pinned is not None:
            params["pinned"] = pinned
        params.update(kwargs)

        resp = await self._client._send_request("sessions.patch", params)
        return resp.get("session", {})

    async def compact(self, session_key: str) -> bool:
        """
        Compact a session (reduce context size).

        Args:
            session_key: Session key

        Returns:
            True if compacted successfully
        """
        resp = await self._client._send_request("sessions.compact", {"sessionKey": session_key})
        return resp.get("ok", False)

    async def preview(self, session_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get a preview of session messages.

        Args:
            session_key: Session key
            limit: Number of recent messages to return

        Returns:
            List of message objects
        """
        resp = await self._client._send_request(
            "sessions.preview",
            {"sessionKey": session_key, "limit": limit}
        )
        return resp.get("messages", [])

    async def compaction_list(self, session_key: str) -> List[Dict[str, Any]]:
        """
        List compaction history for a session.

        Args:
            session_key: Session key

        Returns:
            List of compaction records
        """
        resp = await self._client._send_request(
            "sessions.compaction.list",
            {"sessionKey": session_key}
        )
        return resp.get("compactions", [])

    async def compaction_get(self, session_key: str, compaction_id: str) -> Dict[str, Any]:
        """
        Get a specific compaction record.

        Args:
            session_key: Session key
            compaction_id: Compaction ID

        Returns:
            Compaction record
        """
        resp = await self._client._send_request(
            "sessions.compaction.get",
            {"sessionKey": session_key, "compactionId": compaction_id}
        )
        return resp.get("compaction", {})

    async def compaction_branch(
        self,
        session_key: str,
        compaction_id: str
    ) -> Dict[str, Any]:
        """
        Branch a new session from a compaction point.

        Args:
            session_key: Source session key
            compaction_id: Compaction ID to branch from

        Returns:
            New session object
        """
        resp = await self._client._send_request(
            "sessions.compaction.branch",
            {"sessionKey": session_key, "compactionId": compaction_id}
        )
        return resp.get("session", {})

    async def compaction_restore(
        self,
        session_key: str,
        compaction_id: str
    ) -> bool:
        """
        Restore a session from a compaction.

        Args:
            session_key: Session key
            compaction_id: Compaction ID to restore

        Returns:
            True if restored successfully
        """
        resp = await self._client._send_request(
            "sessions.compaction.restore",
            {"sessionKey": session_key, "compactionId": compaction_id}
        )
        return resp.get("ok", False)
