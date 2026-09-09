import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger("ibvap.websocket")

class ConnectionManager:
    """
    Manages active WebSocket client connections and broadcasts live alerts and events.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Remaining: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcasts a JSON message to all connected clients."""
        if not self.active_connections:
            return

        disconnected_clients = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Error sending message to client: {e}")
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)

manager = ConnectionManager()
