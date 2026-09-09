import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Camera Stream
    CAMERA_SOURCE: str = "0"
    CAMERA_ID: str = "CAM-01"
    CAMERA_NAME: str = "Main Perimeter Camera"
    CAMERA_LOCATION: str = "North Border Test Sector"
    MODE: str = "live"  # 'live' or 'demo'

    # AI Pipeline
    YOLO_MODEL: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.45
    IOU_THRESHOLD: float = 0.45
    ENABLE_LOW_LIGHT_CLAHE: bool = False
    ENABLE_ANPR: bool = True

    # Motion Filter
    MOTION_FILTER_ENABLED: bool = True
    MOTION_SENSITIVITY: int = 25
    MIN_MOTION_AREA: int = 500

    # Rule Engine
    DWELL_THRESHOLD_SECONDS: float = 10.0

    # Redis & Storage
    REDIS_URL: str = "redis://localhost:6379/0"
    DATABASE_URL: str = "sqlite:///./data/ibvap.db"
    SNAPSHOT_DIR: str = "data/snapshots"

    # Server Network
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_PORT: int = 5173
    DEBUG: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

# Global singleton
settings = Settings()

# Ensure required directories exist
os.makedirs("data/snapshots", exist_ok=True)
os.makedirs("data/demo_videos", exist_ok=True)
os.makedirs("data/events", exist_ok=True)
