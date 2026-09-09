from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import CameraModel
from backend.services.pipeline import pipeline
from backend.config import settings

router = APIRouter(prefix="/api/v1/cameras", tags=["Cameras"])

class CameraCreate(BaseModel):
    camera_id: str
    name: str
    source_url: str
    location: Optional[str] = "Perimeter"

class SourceSwitchRequest(BaseModel):
    source_url: str

@router.get("/")
def get_cameras(db: Session = Depends(get_db)):
    meta = pipeline.capture.get_metadata()
    cameras = db.query(CameraModel).all()

    # Ensure default camera exists in DB
    if not cameras:
        default_cam = CameraModel(
            camera_id=settings.CAMERA_ID,
            name=settings.CAMERA_NAME,
            source_url=str(pipeline.camera_source),
            location=settings.CAMERA_LOCATION,
            status="ONLINE" if meta["is_connected"] else "OFFLINE",
            enabled=True
        )
        db.add(default_cam)
        db.commit()
        cameras = [default_cam]

    results = []
    for cam in cameras:
        # Dynamic runtime stats
        is_active = (cam.camera_id == settings.CAMERA_ID)
        results.append({
            "camera_id": cam.camera_id,
            "name": cam.name,
            "source_url": cam.source_url,
            "location": cam.location,
            "status": "ONLINE" if (is_active and meta["is_connected"]) else "OFFLINE",
            "fps": meta["fps"] if is_active else 0.0,
            "resolution": meta["resolution"] if is_active else "0x0",
            "type": meta["type"] if is_active else "rtsp",
            "enabled": cam.enabled
        })
    return results

@router.post("/")
def create_camera(cam: CameraCreate, db: Session = Depends(get_db)):
    existing = db.query(CameraModel).filter(CameraModel.camera_id == cam.camera_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Camera ID already exists")
    new_cam = CameraModel(
        camera_id=cam.camera_id,
        name=cam.name,
        source_url=cam.source_url,
        location=cam.location,
        status="OFFLINE"
    )
    db.add(new_cam)
    db.commit()
    return {"message": "Camera created", "camera_id": cam.camera_id}

@router.put("/{camera_id}/source")
def switch_camera_source(camera_id: str, req: SourceSwitchRequest, db: Session = Depends(get_db)):
    cam = db.query(CameraModel).filter(CameraModel.camera_id == camera_id).first()
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    cam.source_url = req.source_url
    db.commit()

    if camera_id == settings.CAMERA_ID:
        pipeline.set_camera_source(req.source_url)

    return {"message": "Camera source updated", "camera_id": camera_id, "new_source": req.source_url}
