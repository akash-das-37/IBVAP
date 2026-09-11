import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import requests

from backend.config import settings
from backend.core.auth import TenantContext, get_current_tenant

logger = logging.getLogger("ibvap.api.alerts")
router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

class AlertCreatePayload(BaseModel):
    alert_id: str
    event_type: str
    severity: Optional[str] = "HIGH"
    camera_id: str
    zone_id: Optional[str] = None
    zone_name: Optional[str] = None
    object_type: Optional[str] = None
    track_id: Optional[int] = None
    confidence: Optional[float] = None
    description: Optional[str] = None
    snapshot_path: Optional[str] = None
    status: Optional[str] = "NEW"
    timestamp: Optional[str] = None

@router.get("/")
def get_alerts(
    severity: Optional[str] = None,
    camera_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    tenant: TenantContext = Depends(get_current_tenant)
):
    """
    Returns alerts strictly scoped to the authenticated tenant's organization.
    Protected by Supabase RLS and server-side tenant filtering.
    """
    url = f"{settings.SUPABASE_URL}/rest/v1/alerts?organization_id=eq.{tenant.organization_id}&select=*&order=timestamp.desc&limit={limit}"
    if severity:
        url += f"&severity=eq.{severity.upper()}"
    if camera_id:
        url += f"&camera_id=eq.{camera_id}"
    if status:
        url += f"&status=eq.{status.upper()}"

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code != 200:
        logger.error(f"Failed to query tenant alerts: {res.status_code} {res.text}")
        return []
    return res.json()

@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    tenant: TenantContext = Depends(get_current_tenant)
):
    url = f"{settings.SUPABASE_URL}/rest/v1/alerts?alert_id=eq.{alert_id}&organization_id=eq.{tenant.organization_id}"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}",
        "Content-Type": "application/json"
    }
    res = requests.patch(url, headers=headers, json={"status": "ACKNOWLEDGED"}, timeout=15)
    if res.status_code not in [200, 204]:
        raise HTTPException(status_code=404, detail="Alert not found or unauthorized")
    return {"message": "Alert marked as acknowledged", "alert_id": alert_id}

@router.post("/")
def create_alert(
    alert: AlertCreatePayload,
    tenant: TenantContext = Depends(get_current_tenant)
):
    url = f"{settings.SUPABASE_URL}/rest/v1/alerts"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    payload = alert.model_dump()
    payload["organization_id"] = tenant.organization_id
    res = requests.post(url, headers=headers, json=payload, timeout=15)
    if res.status_code not in [200, 201]:
        raise HTTPException(status_code=400, detail=f"Failed to persist alert: {res.text}")
    return res.json()
