import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.database.session import init_db
from backend.services.pipeline import pipeline
from backend.websocket.manager import manager
from backend.api import (
    cameras_router,
    zones_router,
    alerts_router,
    events_router,
    stream_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ibvap.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing IBVAP Database schema...")
    init_db()

    loop = asyncio.get_running_loop()
    logger.info("Starting IBVAP Analytics Pipeline...")
    pipeline.start(event_loop=loop)
    logger.info(f"IBVAP Platform online at http://{settings.HOST}:{settings.PORT}")

    yield

    # Shutdown
    logger.info("Shutting down IBVAP Analytics Pipeline...")
    pipeline.stop()
    logger.info("IBVAP terminated cleanly.")

app = FastAPI(
    title="IBVAP - Intelligent Border Video Analytics Platform",
    description="Edge-first software surveillance AI platform for automated border perimeter security.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Snapshot Images statically
os.makedirs("data/snapshots", exist_ok=True)
app.mount("/data/snapshots", StaticFiles(directory="data/snapshots"), name="snapshots")

# Include API Routers
app.include_router(cameras_router)
app.include_router(zones_router)
app.include_router(alerts_router)
app.include_router(events_router)
app.include_router(stream_router)

# Real-time WebSocket Endpoint
@app.websocket("/ws/alerts")
async def websocket_alerts_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep-alive receive ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# System Health Endpoint
@app.get("/api/v1/health", tags=["System"])
def health_check():
    meta = pipeline.capture.get_metadata()
    return {
        "status": "healthy",
        "platform": "IBVAP Edge v1.0.0",
        "camera_status": "ONLINE" if meta["is_connected"] else "OFFLINE",
        "fps": meta["fps"],
        "redis_active": pipeline.event_queue.is_redis_available,
        "queue_mode": "Redis" if pipeline.event_queue.is_redis_available else "In-Memory Buffer (Fallback)",
        "edge_device": "CPU"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=False)
