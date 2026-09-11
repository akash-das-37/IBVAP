import time
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests

from backend.config import settings

logger = logging.getLogger("ibvap.auth")
security = HTTPBearer(auto_error=False)

class TenantContext(BaseModel):
    user_id: str
    email: str
    organization_id: str
    role: str = "operator"
    token: str

# In-memory TTL cache for verified tokens (60-second window to optimize performance)
_TOKEN_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 60

def resolve_tenant_context(token: str) -> TenantContext:
    """
    Validates Supabase JWT against Supabase Auth API and derives organization_id
    from the database organization_members table.
    """
    now = time.time()
    if token in _TOKEN_CACHE:
        cached = _TOKEN_CACHE[token]
        if now - cached["timestamp"] < CACHE_TTL_SECONDS:
            return cached["context"]
        else:
            del _TOKEN_CACHE[token]

    # 1. Validate JWT with Supabase Auth API
    user_url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {token}"
    }

    try:
        res = requests.get(user_url, headers=headers, timeout=15)
        if res.status_code != 200:
            logger.warning(f"Supabase Auth user lookup failed ({res.status_code}): {res.text[:200]}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired surveillance session token"
            )
        user_data = res.json()
        user_id = user_data.get("id")
        email = user_data.get("email", "")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error communicating with Supabase Auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unreachable"
        )

    # 2. Query organization_members for this authenticated user (using their own JWT with RLS)
    members_url = f"{settings.SUPABASE_URL}/rest/v1/organization_members?user_id=eq.{user_id}&select=organization_id,role"
    try:
        m_res = requests.get(members_url, headers=headers, timeout=15)
        if m_res.status_code != 200:
            logger.warning(f"Organization lookup failed ({m_res.status_code}): {m_res.text[:200]}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unable to verify organization membership"
            )
        memberships = m_res.json()
        if not memberships or not isinstance(memberships, list) or len(memberships) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not provisioned in any surveillance organization"
            )
        org_id = memberships[0]["organization_id"]
        role = memberships[0].get("role", "operator")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving organization membership: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal authorization error"
        )

    context = TenantContext(
        user_id=user_id,
        email=email,
        organization_id=org_id,
        role=role,
        token=token
    )

    _TOKEN_CACHE[token] = {
        "timestamp": now,
        "context": context
    }

    return context

async def get_current_tenant(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> TenantContext:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Surveillance authentication token missing. Please provide Authorization Bearer header."
        )
    return resolve_tenant_context(credentials.credentials)

def verify_ws_token(token: Optional[str]) -> Optional[TenantContext]:
    """Helper for authenticating WebSocket connections."""
    if not token:
        return None
    try:
        return resolve_tenant_context(token)
    except Exception as e:
        logger.warning(f"WebSocket token validation failed: {e}")
        return None
