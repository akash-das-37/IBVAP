import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import requests

from backend.config import settings
from backend.core.auth import TenantContext, get_current_tenant
from backend.services.pipeline import pipeline

logger = logging.getLogger("ibvap.api.cameras")
router = APIRouter(prefix="/api/v1/cameras", tags=["Cameras"])

class CameraCreate(BaseModel):
    camera_id: str
    name: str
    source_url: str
    location: Optional[str] = "Perimeter"
    site_id: Optional[str] = None
    enabled: Optional[bool] = True

class SourceSwitchRequest(BaseModel):
    source_url: str

@router.get("/")
def get_cameras(tenant: TenantContext = Depends(get_current_tenant)):
    """
    Returns cameras strictly scoped to the authenticated organization.
    Protected by Supabase RLS and server-side tenant filtering.
    """
    url = f"{settings.SUPABASE_URL}/rest/v1/cameras?organization_id=eq.{tenant.organization_id}&select=*&order=created_at.asc"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }
    res = requests.get(url, headers=headers, timeout=15)
    cameras = res.json() if res.status_code == 200 else []

    meta = pipeline.capture.get_metadata()
    results = []
    for cam in cameras:
        is_active = (cam.get("camera_id") == settings.CAMERA_ID)
        results.append({
            "id": cam.get("id"),
            "organization_id": cam.get("organization_id"),
            "site_id": cam.get("site_id"),
            "camera_id": cam.get("camera_id"),
            "name": cam.get("name"),
            "source_url": cam.get("source_url"),
            "location": cam.get("location"),
            "status": "ONLINE" if (is_active and meta["is_connected"]) else cam.get("status", "OFFLINE"),
            "fps": meta["fps"] if is_active else 0.0,
            "resolution": meta["resolution"] if is_active else "640x480",
            "type": meta["type"] if is_active else "webcam",
            "enabled": cam.get("enabled", True)
        })
    return results

@router.post("/")
def create_camera(cam: CameraCreate, tenant: TenantContext = Depends(get_current_tenant)):
    """Creates a new camera assigned strictly to the authenticated organization."""
    url = f"{settings.SUPABASE_URL}/rest/v1/cameras"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    payload = {
        "organization_id": tenant.organization_id,
        "camera_id": cam.camera_id,
        "name": cam.name,
        "source_url": cam.source_url,
        "location": cam.location,
        "site_id": cam.site_id,
        "status": "ONLINE",
        "enabled": cam.enabled if cam.enabled is not None else True
    }
    res = requests.post(url, headers=headers, json=payload, timeout=15)
    if res.status_code not in [200, 201]:
        raise HTTPException(status_code=400, detail=f"Failed to save camera: {res.text}")
    return res.json()

@router.put("/{camera_id}/source")
def switch_camera_source(
    camera_id: str,
    req: SourceSwitchRequest,
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Switches the camera source stream for the authenticated organization's camera."""
    url = f"{settings.SUPABASE_URL}/rest/v1/cameras?organization_id=eq.{tenant.organization_id}&camera_id=eq.{camera_id}"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}",
        "Content-Type": "application/json"
    }
    try:
        requests.patch(url, headers=headers, json={"source_url": req.source_url, "status": "ONLINE"}, timeout=15)
    except Exception as e:
        logger.warning(f"Failed to update camera in Supabase: {e}")

    # Immediately switch active edge camera capture source
    pipeline.set_camera_source(req.source_url)
    meta = pipeline.capture.get_metadata()

    return {
        "message": "Camera source updated",
        "camera_id": camera_id,
        "new_source": req.source_url,
        "is_connected": meta.get("is_connected", False),
        "source_type": meta.get("type", "stream")
    }
