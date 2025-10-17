"""WebSocket endpoints for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str = "general"):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        self.active_connections[task_id].add(websocket)

    def disconnect(self, websocket: WebSocket, task_id: str = "general"):
        """Remove a WebSocket connection."""
        if task_id in self.active_connections:
            self.active_connections[task_id].discard(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def send_message(self, message: dict, task_id: str = "general"):
        """Send a message to all connections for a specific task."""
        if task_id not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[task_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, task_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        for task_id in list(self.active_connections.keys()):
            await self.send_message(message, task_id)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    General WebSocket endpoint for real-time updates.
    
    Clients can connect to receive broadcast messages about system events.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo back for testing
            await websocket.send_json({"type": "echo", "message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/{task_id}")
async def websocket_task_endpoint(websocket: WebSocket, task_id: str):
    """
    Task-specific WebSocket endpoint for indexing progress updates.
    
    Args:
        task_id: The indexing task ID to monitor
    """
    await manager.connect(websocket, task_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Clients can send heartbeat messages
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, task_id)


async def send_indexing_update(task_id: str, update: dict):
    """
    Send indexing progress update to connected clients.
    
    Args:
        task_id: The indexing task ID
        update: Progress update data
    """
    await manager.send_message(
        {"type": "indexing_progress", "task_id": task_id, **update}, task_id
    )
