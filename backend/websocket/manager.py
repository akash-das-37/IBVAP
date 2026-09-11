import json
import logging
from typing import Dict, List, Any, Optional
from fastapi import WebSocket

from backend.core.auth import verify_ws_token

logger = logging.getLogger("ibvap.websocket")

class ConnectionManager:
    """
    Tenant-aware WebSocket Connection Manager.
    Enforces that alerts and real-time surveillance feeds are dispatched
    EXCLUSIVELY to authorized clients belonging to the designated organization.
    """

    def __init__(self):
        # Maps organization_id -> List of active WebSockets
        self.org_connections: Dict[str, List[WebSocket]] = {}
        # Maps WebSocket -> metadata (organization_id, user_id, email)
        self.socket_meta: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> bool:
        """Accepts WebSocket and authenticates tenant context via token."""
        await websocket.accept()

        tenant = verify_ws_token(token) if token else None
        if tenant:
            self._register_socket(websocket, tenant.organization_id, tenant.user_id, tenant.email)
            try:
                from backend.services.pipeline import pipeline
                pipeline.alert_engine.register_org_token(tenant.organization_id, token)
            except Exception:
                pass
            logger.info(f"Authenticated WebSocket connected for Org {tenant.organization_id} (User: {tenant.email})")
            return True
        else:
            # Allow provisional connection to await an AUTH message
            logger.info("WebSocket connected in provisional mode awaiting authentication handshake.")
            return False

    def _register_socket(self, websocket: WebSocket, org_id: str, user_id: str, email: str):
        if org_id not in self.org_connections:
            self.org_connections[org_id] = []
        if websocket not in self.org_connections[org_id]:
            self.org_connections[org_id].append(websocket)

        self.socket_meta[websocket] = {
            "organization_id": org_id,
            "user_id": user_id,
            "email": email
        }

    def authenticate_socket(self, websocket: WebSocket, token: str) -> bool:
        """Authenticates a provisional socket via explicit handshake message."""
        tenant = verify_ws_token(token)
        if tenant:
            self._register_socket(websocket, tenant.organization_id, tenant.user_id, tenant.email)
            try:
                from backend.services.pipeline import pipeline
                pipeline.alert_engine.register_org_token(tenant.organization_id, token)
            except Exception:
                pass
            logger.info(f"WebSocket authenticated via handshake for Org {tenant.organization_id} ({tenant.email})")
            return True
        logger.warning("WebSocket handshake authentication failed with invalid token.")
        return False

    def disconnect(self, websocket: WebSocket):
        meta = self.socket_meta.pop(websocket, None)
        if meta:
            org_id = meta.get("organization_id")
            if org_id in self.org_connections and websocket in self.org_connections[org_id]:
                self.org_connections[org_id].remove(websocket)
                if not self.org_connections[org_id]:
                    del self.org_connections[org_id]
        logger.info(f"WebSocket disconnected. Active orgs connected: {len(self.org_connections)}")

    async def send_to_org(self, organization_id: str, message: Dict[str, Any]):
        """
        STRICT TENANT ISOLATION:
        Dispatches an alert/event EXCLUSIVELY to WebSockets authenticated for this organization_id.
        Clients belonging to other organizations will NEVER receive this message.
        """
        sockets = self.org_connections.get(organization_id, [])
        if not sockets:
            logger.debug(f"No active clients connected for Org {organization_id}")
            return

        disconnected = []
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug(f"Error sending message to tenant socket: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws)

    async def broadcast_stats(self, message: Dict[str, Any]):
        """Sends runtime telemetry (e.g. FPS / system health) to all authenticated clients."""
        for org_id, sockets in list(self.org_connections.items()):
            for ws in list(sockets):
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(ws)

manager = ConnectionManager()
