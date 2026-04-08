"""OpenClaw Node Management"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, List, Optional

if TYPE_CHECKING:
    from .client import OpenClawClient


class NodesManager:
    """Manage OpenClaw nodes"""

    def __init__(self, client: "OpenClawClient") -> None:
        self._client = client

    async def list(self) -> List[Dict[str, Any]]:
        """
        List all nodes.

        Returns:
            List of node objects
        """
        resp = await self._client._send_request("node.list", {})
        return resp.get("nodes", [])

    async def describe(self, node_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Describe a node.

        Args:
            node_id: Optional node ID (uses local node if not provided)

        Returns:
            Node description
        """
        params = {"nodeId": node_id} if node_id else {}
        resp = await self._client._send_request("node.describe", params)
        return resp.get("node", resp)

    async def pair_request(self, info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Request node pairing.

        Args:
            info: Optional pairing info

        Returns:
            Pairing response
        """
        resp = await self._client._send_request("node.pair.request", info or {})
        return resp

    async def pair_list(self) -> List[Dict[str, Any]]:
        """
        List pending pair requests.

        Returns:
            List of pending pair requests
        """
        resp = await self._client._send_request("node.pair.list", {})
        return resp.get("pairs", [])

    async def pair_approve(self, request_id: str) -> bool:
        """
        Approve a pair request.

        Args:
            request_id: Pair request ID

        Returns:
            True if approved
        """
        resp = await self._client._send_request("node.pair.approve", {"requestId": request_id})
        return resp.get("ok", False)

    async def pair_reject(self, request_id: str) -> bool:
        """
        Reject a pair request.

        Args:
            request_id: Pair request ID

        Returns:
            True if rejected
        """
        resp = await self._client._send_request("node.pair.reject", {"requestId": request_id})
        return resp.get("ok", False)

    async def pair_verify(self, request_id: str) -> Dict[str, Any]:
        """
        Verify a pair request.

        Args:
            request_id: Pair request ID

        Returns:
            Verification response
        """
        resp = await self._client._send_request("node.pair.verify", {"requestId": request_id})
        return resp

    async def pending_enqueue(self, node_id: str, item: Dict[str, Any]) -> bool:
        """
        Enqueue an item to a node's pending queue.

        Args:
            node_id: Target node ID
            item: Item to enqueue

        Returns:
            True if enqueued
        """
        resp = await self._client._send_request(
            "node.pending.enqueue", {"nodeId": node_id, "item": item}
        )
        return resp.get("ok", False)

    async def pending_drain(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Drain a node's pending queue.

        Args:
            node_id: Target node ID

        Returns:
            List of drained items
        """
        resp = await self._client._send_request("node.pending.drain", {"nodeId": node_id})
        return resp.get("items", [])
