import uuid
import logging
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import requests

from backend.config import settings
from backend.core.auth import TenantContext, get_current_tenant
from backend.services.pipeline import pipeline

logger = logging.getLogger("ibvap.api.zones")
router = APIRouter(prefix="/api/v1/zones", tags=["Zones"])

class ZonePayload(BaseModel):
    zone_id: str
    camera_id: Optional[str] = None
    site_id: Optional[str] = None
    name: str
    zone_type: str = "polygon"  # 'polygon' or 'tripwire'
    polygon_data: Optional[List[Dict[str, Any]]] = []
    polygon_coords: Optional[List[Any]] = []
    line_coords: Optional[List[Any]] = []
    is_restricted: bool = True
    dwell_threshold: float = 10.0
    prohibited_directions: Optional[List[str]] = []
    color: str = "#ef4444"
    enabled: bool = True

def _refresh_pipeline_zones(tenant: TenantContext):
    """Reloads active enabled zones for the current tenant into the live AI detection pipeline."""
    try:
        url = f"{settings.SUPABASE_URL}/rest/v1/zones?organization_id=eq.{tenant.organization_id}&enabled=eq.true&select=*"
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {tenant.token}"
        }
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            db_zones = res.json()
            in_mem_zones = []
            for z in db_zones:
                in_mem_zones.append({
                    "zone_id": z.get("zone_id"),
                    "name": z.get("name"),
                    "zone_type": z.get("zone_type", "polygon"),
                    "polygon_data": z.get("polygon_data") or [],
                    "polygon_coords": z.get("polygon_coords") or [],
                    "line_coords": z.get("line_coords") or [],
                    "is_restricted": z.get("is_restricted", True),
                    "dwell_threshold": z.get("dwell_threshold", 10.0),
                    "prohibited_directions": z.get("prohibited_directions") or [],
                    "color": z.get("color", "#ef4444"),
                    "organization_id": z.get("organization_id") or tenant.organization_id,
                    "enabled": z.get("enabled", True)
                })
            pipeline.update_zones(in_mem_zones, organization_id=tenant.organization_id)
            pipeline.alert_engine.register_org_token(tenant.organization_id, tenant.token)
            logger.info(f"Pipeline updated with {len(in_mem_zones)} zones for org {tenant.organization_id}")
    except Exception as e:
        logger.error(f"Failed to refresh pipeline zones from Supabase: {e}")

@router.get("/")
def get_zones(
    camera_id: Optional[str] = None,
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Returns zones strictly scoped to the authenticated organization."""
    url = f"{settings.SUPABASE_URL}/rest/v1/zones?organization_id=eq.{tenant.organization_id}&select=*&order=created_at.asc"
    if camera_id:
        url += f"&camera_id=eq.{camera_id}"

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code != 200:
        logger.error(f"Failed to query zones: {res.status_code} {res.text}")
        return []
    
    zones = res.json()
    _refresh_pipeline_zones(tenant)
    return zones

@router.post("/")
def create_or_update_zone(
    zone: ZonePayload,
    tenant: TenantContext = Depends(get_current_tenant)
):
    """
    Saves or updates a zone strictly within the authenticated organization.
    Enforces USER -> ORGANIZATION -> SITE -> CAMERA -> ZONE hierarchy.
    """
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }

    # 1. Resolve camera UUID and site UUID
    camera_uuid = None
    site_uuid = zone.site_id

    # Check if zone.camera_id is already a valid UUID
    if zone.camera_id:
        try:
            uuid.UUID(str(zone.camera_id))
            camera_uuid = str(zone.camera_id)
        except ValueError:
            camera_uuid = None

    # Fetch camera record for this organization to get exact database UUID and site_id
    c_res = requests.get(
        f"{settings.SUPABASE_URL}/rest/v1/cameras?organization_id=eq.{tenant.organization_id}&select=id,site_id,camera_id",
        headers=headers,
        timeout=15
    )
    if c_res.status_code == 200 and c_res.json():
        cams = c_res.json()
        matched = None
        if camera_uuid:
            matched = next((c for c in cams if c.get("id") == camera_uuid), None)
        if not matched and zone.camera_id:
            matched = next((c for c in cams if c.get("camera_id") == zone.camera_id), None)
        if not matched:
            matched = cams[0]
        
        camera_uuid = matched.get("id")
        if not site_uuid:
            site_uuid = matched.get("site_id")

    if not camera_uuid:
        raise HTTPException(
            status_code=400,
            detail="No registered camera found for this organization. Provision a camera before creating zones."
        )

    # 2. Normalize coordinates into polygon_data [{"x": ..., "y": ...}]
    norm_polygon_data = []
    coords_list = []

    input_pts = zone.polygon_data or zone.polygon_coords or []
    for pt in input_pts:
        if isinstance(pt, dict) and "x" in pt and "y" in pt:
            x = float(pt["x"])
            y = float(pt["y"])
            if x > 1.0 or y > 1.0:
                x = round(x / 960.0, 4)
                y = round(y / 540.0, 4)
            norm_polygon_data.append({"x": x, "y": y})
            coords_list.append([x, y])
        elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
            x = float(pt[0])
            y = float(pt[1])
            if x > 1.0 or y > 1.0:
                x = round(x / 960.0, 4)
                y = round(y / 540.0, 4)
            norm_polygon_data.append({"x": x, "y": y})
            coords_list.append([x, y])

    payload = {
        "organization_id": tenant.organization_id,
        "site_id": site_uuid,
        "camera_id": camera_uuid,
        "zone_id": zone.zone_id,
        "name": zone.name,
        "zone_type": zone.zone_type,
        "polygon_data": norm_polygon_data,
        "polygon_coords": coords_list,
        "line_coords": zone.line_coords or [],
        "is_restricted": zone.is_restricted,
        "dwell_threshold": zone.dwell_threshold,
        "prohibited_directions": zone.prohibited_directions or [],
        "color": zone.color,
        "enabled": zone.enabled
    }

    url = f"{settings.SUPABASE_URL}/rest/v1/zones?on_conflict=organization_id,zone_id"
    post_headers = {
        **headers,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    res = requests.post(url, headers=post_headers, json=payload, timeout=15)
    if res.status_code not in [200, 201]:
        logger.error(f"Failed to save zone to Supabase: {res.status_code} {res.text}")
        raise HTTPException(status_code=400, detail=f"Failed to save zone in database: {res.text}")

    _refresh_pipeline_zones(tenant)
    saved_records = res.json()
    saved = saved_records[0] if isinstance(saved_records, list) and saved_records else payload

    return {
        "message": "Zone saved successfully",
        "zone_id": zone.zone_id,
        "camera_id": camera_uuid,
        "site_id": site_uuid,
        "data": saved
    }

@router.delete("/{zone_id}")
def delete_zone(
    zone_id: str,
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Deletes a zone strictly from the authenticated organization."""
    url = f"{settings.SUPABASE_URL}/rest/v1/zones?organization_id=eq.{tenant.organization_id}&zone_id=eq.{zone_id}"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }
    res = requests.delete(url, headers=headers, timeout=15)
    if res.status_code not in [200, 204]:
        raise HTTPException(status_code=404, detail="Zone not found or unauthorized")

    _refresh_pipeline_zones(tenant)
    return {"message": "Zone deleted", "zone_id": zone_id}
