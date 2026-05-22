"""
Dashboard WebSocket Manager
===========================
Manages WebSocket connections and broadcast messaging.
"""

import json
import asyncio
from typing import Dict, List, Optional
from collections import deque

from fastapi import WebSocket


class DashboardWebsocket:
    """Manages WebSocket connections for real-time dashboard updates."""

    _instance: Optional["DashboardWebsocket"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.active_connections: List[WebSocket] = []
        self.message_history: deque = deque(maxlen=500)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        # Send recent history to catch up
        for msg in self.message_history:
            try:
                await websocket.send_text(json.dumps(msg))
            except Exception:
                break

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, websocket: WebSocket, message: Dict) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception:
            self.disconnect(websocket)

    async def broadcast_async(self, message: Dict) -> None:
        """Broadcast a message to all connected clients (async)."""
        self.message_history.append(message)
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    @classmethod
    def broadcast(cls, message: Dict) -> None:
        """Synchronous wrapper for broadcasting."""
        instance = cls()
        if not instance.active_connections:
            instance.message_history.append(message)
            return
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(instance.broadcast_async(message))
        except RuntimeError:
            # No running loop
            pass

    def connection_count(self) -> int:
        """Return number of active connections."""
        return len(self.active_connections)
