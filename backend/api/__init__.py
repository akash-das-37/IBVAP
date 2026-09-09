from .routes_cameras import router as cameras_router
from .routes_zones import router as zones_router
from .routes_alerts import router as alerts_router
from .routes_events import router as events_router
from .routes_stream import router as stream_router

__all__ = [
    "cameras_router",
    "zones_router",
    "alerts_router",
    "events_router",
    "stream_router"
]
