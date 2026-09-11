import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import requests

from backend.config import settings
from backend.core.auth import TenantContext, get_current_tenant

logger = logging.getLogger("ibvap.api.sites")
router = APIRouter(prefix="/api/v1/sites", tags=["Sites"])

class SitePayload(BaseModel):
    site_id: str
    name: str
    location: Optional[str] = None

@router.get("/")
def get_sites(tenant: TenantContext = Depends(get_current_tenant)):
    """Returns sites strictly scoped to the authenticated organization."""
    url = f"{settings.SUPABASE_URL}/rest/v1/sites?organization_id=eq.{tenant.organization_id}&select=*&order=created_at.asc"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code != 200:
        logger.error(f"Failed to query sites: {res.status_code} {res.text}")
        return []
    return res.json()

@router.post("/")
def create_or_update_site(
    site: SitePayload,
    tenant: TenantContext = Depends(get_current_tenant)
):
    """Creates or updates a surveillance site strictly inside the authenticated organization."""
    url = f"{settings.SUPABASE_URL}/rest/v1/sites"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    payload = {
        "organization_id": tenant.organization_id,
        "site_id": site.site_id,
        "name": site.name,
        "location": site.location
    }
    res = requests.post(url, headers=headers, json=payload, timeout=15)
    if res.status_code not in [200, 201]:
        raise HTTPException(status_code=400, detail=f"Failed to save site: {res.text}")
    return res.json()

@router.delete("/{site_id}")
def delete_site(
    site_id: str,
    tenant: TenantContext = Depends(get_current_tenant)
):
    url = f"{settings.SUPABASE_URL}/rest/v1/sites?organization_id=eq.{tenant.organization_id}&site_id=eq.{site_id}"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {tenant.token}"
    }
    res = requests.delete(url, headers=headers, timeout=15)
    if res.status_code not in [200, 204]:
        raise HTTPException(status_code=404, detail="Site not found or unauthorized")
    return {"message": "Site deleted", "site_id": site_id}
