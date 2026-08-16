"""WebSocket manager — real-time message delivery to connected clients."""

import json
import logging
from collections import defaultdict
from typing import Dict, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        # user_id -> set[WebSocket]
        self._connections: Dict[int, Set[WebSocket]] = defaultdict(set)

    def get_user_channel(self, user_id: int) -> str:
        """Get channel name for user subscriptions."""
        return f"user.{user_id}"

    async def connect(self, websocket: WebSocket, user_id: int) -> bool:
        """Accept WebSocket connection for a user."""
        await websocket.accept()
        self._connections[user_id].add(websocket)
        logger.info(
            "WS connected: user=%d, total=%d",
            user_id,
            len(self._connections[user_id]),
        )
        return True

    def disconnect(self, websocket: WebSocket, user_id: int) -> None:
        """Remove WebSocket connection for a user."""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
            logger.info(
                "WS disconnected: user=%d, remaining=%d",
                user_id,
                len(self._connections.get(user_id, set())),
            )

    async def send_to_user(self, user_id: int, data: dict) -> None:
        """Send JSON data to a specific user's WebSocket."""
        connections = self._connections.get(user_id, set())
        disconnected = set()

        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.error("WS send error user=%d: %s", user_id, e)
                disconnected.add(ws)

        for ws in disconnected:
            self._connections[user_id].discard(ws)

    async def broadcast_to_conversation(
        self,
        conversation_id: int,
        data: dict,
        exclude_user_id: int | None = None,
    ) -> None:
        """Broadcast data to all connected users (filter by conversation in production)."""
        for user_id, connections in self._connections.items():
            if user_id == exclude_user_id:
                continue
            for ws in connections:
                try:
                    await ws.send_json(data)
                except Exception as e:
                    logger.error(
                        "WS broadcast error conv=%d user=%d: %s",
                        conversation_id,
                        user_id,
                        e,
                    )

    def get_active_users(self) -> list:
        """Return list of user_ids with active WebSocket connections."""
        return list(self._connections.keys())

    def get_connection_count(self, user_id: int) -> int:
        """Return number of active connections for a user."""
        return len(self._connections.get(user_id, set()))


# Global singleton
ws_manager = WebSocketManager()
