import datetime
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import requests

from backend.config import settings
from backend.core.auth import TenantContext, get_current_tenant

logger = logging.getLogger("ibvap.api.events")
router = APIRouter(prefix="/api/v1/events", tags=["Events"])

class EventCreatePayload(BaseModel):
    event_id: str
    camera_id: str
    timestamp: Optional[str] = None
    event_type: str
    object_type: Optional[str] = None
    track_id: Optional[int] = None
    confidence: Optional[float] = None
    plate_number: Optional[str] = None
    plate_confidence: Optional[str] = None
    zone_name: Optional[str] = None
    snapshot_path: Optional[str] = None

@router.get("/")
def get_events(
    camera_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=50, le=300),
    tenant: TenantContext = Depends(get_current_tenant)
):
    """
    Returns events strictly scoped to the authenticated tenant's organization.
    Protected by Supabase RLS and server-side tenant filtering.
    """
    url = f"{settings.SUPABASE_URL}/rest/v1/events?organization_id=eq.{tenant.organization_id}&select=*&order=timestamp.desc&limit={limit}"
    if camera_id:
        url += f"&camera_id=eq.{camera_id}"
    if event_type:
        url += f"&event_type=eq.{event_type.upper()}"

    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code != 200:
        logger.error(f"Failed to query tenant events: {res.status_code} {res.text}")
        return []
    return res.json()

@router.post("/")
def create_event(
    event: EventCreatePayload,
    tenant: TenantContext = Depends(get_current_tenant)
):
    url = f"{settings.SUPABASE_URL}/rest/v1/events"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    payload = event.model_dump()
    payload["organization_id"] = tenant.organization_id
    res = requests.post(url, headers=headers, json=payload, timeout=15)
    if res.status_code not in [200, 201]:
        raise HTTPException(status_code=400, detail=f"Failed to persist event: {res.text}")
    return res.json()

@router.get("/stats")
def get_system_stats(tenant: TenantContext = Depends(get_current_tenant)):
    """
    Computes real-time tactical stats strictly isolated to the authenticated organization.
    """
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}",
        "Prefer": "count=exact"
    }

    try:
        # 1. Events today for this organization
        ev_url = f"{settings.SUPABASE_URL}/rest/v1/events?organization_id=eq.{tenant.organization_id}&timestamp=gte.{today_start}&select=id"
        ev_res = requests.get(ev_url, headers=headers, timeout=15)
        events_today = int(ev_res.headers.get("content-range", "0-0/0").split("/")[-1]) if ev_res.status_code == 200 else 0

        # 2. Active alerts for this organization
        al_url = f"{settings.SUPABASE_URL}/rest/v1/alerts?organization_id=eq.{tenant.organization_id}&status=eq.NEW&select=id"
        al_res = requests.get(al_url, headers=headers, timeout=15)
        active_alerts = int(al_res.headers.get("content-range", "0-0/0").split("/")[-1]) if al_res.status_code == 200 else 0

        # 3. Critical alerts for this organization
        crit_url = f"{settings.SUPABASE_URL}/rest/v1/alerts?organization_id=eq.{tenant.organization_id}&status=eq.NEW&severity=eq.CRITICAL&select=id"
        crit_res = requests.get(crit_url, headers=headers, timeout=15)
        critical_alerts = int(crit_res.headers.get("content-range", "0-0/0").split("/")[-1]) if crit_res.status_code == 200 else 0
    except Exception as e:
        logger.error(f"Error computing tenant stats: {e}")
        events_today, active_alerts, critical_alerts = 0, 0, 0

    return {
        "events_today": events_today,
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "organization_id": tenant.organization_id,
        "ai_status": "Running (Tenant Isolated)"
    }
