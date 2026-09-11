import os
import uuid
import time
import datetime
import logging
import concurrent.futures
import threading
from typing import Optional, Dict, Any, List
import cv2
import numpy as np
import requests

from backend.config import settings
from backend.database.session import SessionLocal
from backend.database.models import AlertModel, EventModel

logger = logging.getLogger("ibvap.alerts")

# Known operator accounts per surveillance tenant organization
_ORG_OPERATORS = {
    "11111111-1111-1111-1111-111111111111": ("iamnegative37@gmail.com", "Surveillance2026!"),
    "22222222-2222-2222-2222-222222222222": ("akashdas200x@gmail.com", "Surveillance2026!"),
}
_DEFAULT_OPERATOR = ("iamnegative37@gmail.com", "Surveillance2026!")

class AlertEngine:
    """
    Synthesizes rule violations and security triggers into structured alerts.
    Persists alert records, uploads evidence snapshots to Supabase Cloud Storage,
    grades severity, and forwards alerts.
    
    IMPORTANT: Uses authenticated Supabase JWT per organization (not the anon key)
    for all writes so that RLS policies based on auth.uid() are satisfied for the tenant.
    """

    def __init__(self, snapshot_dir: str = "data/snapshots"):
        self.snapshot_dir = snapshot_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="SupabaseSnapshotWorker")
        
        # Cached authenticated JWTs keyed by organization_id: { org_id: { "token": str, "expiry": float } }
        self._org_tokens: Dict[str, Dict[str, Any]] = {}
        self._auth_lock = threading.Lock()

    def register_org_token(self, organization_id: str, token: str, expires_in: int = 3600):
        """Allows active tenant sessions (from WebSockets or REST) to register their valid JWT directly."""
        if not organization_id or not token:
            return
        with self._auth_lock:
            self._org_tokens[organization_id] = {
                "token": token,
                "expiry": time.time() + expires_in
            }
        logger.info(f"AlertEngine cached operator token for org {organization_id}")

    def _get_authenticated_headers(self, organization_id: Optional[str] = None) -> Dict[str, str]:
        """
        Returns Supabase REST headers using an authenticated user JWT for the specified organization.
        The anon key alone cannot satisfy RLS policies that check auth.uid().
        This method retrieves a cached session token or authenticates as the org's service operator.
        """
        now = time.time()
        
        # 1. Return cached token if valid
        if organization_id and organization_id in self._org_tokens:
            cached = self._org_tokens[organization_id]
            if now < (cached["expiry"] - 120):
                return {
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {cached['token']}",
                    "Content-Type": "application/json"
                }
        
        with self._auth_lock:
            if organization_id and organization_id in self._org_tokens:
                cached = self._org_tokens[organization_id]
                if now < (cached["expiry"] - 120):
                    return {
                        "apikey": settings.SUPABASE_KEY,
                        "Authorization": f"Bearer {cached['token']}",
                        "Content-Type": "application/json"
                    }
            
            # 2. Determine credentials for this tenant
            creds = _ORG_OPERATORS.get(organization_id, _DEFAULT_OPERATOR)
            email, password = creds
            try:
                auth_url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
                res = requests.post(auth_url, headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Content-Type": "application/json"
                }, json={
                    "email": email,
                    "password": password
                }, timeout=10)
                
                if res.status_code == 200:
                    data = res.json()
                    token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    if organization_id:
                        self._org_tokens[organization_id] = {
                            "token": token,
                            "expiry": now + expires_in
                        }
                    logger.info(f"AlertEngine authenticated as {email} for org {organization_id}, JWT valid for {expires_in}s")
                    return {
                        "apikey": settings.SUPABASE_KEY,
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                else:
                    logger.error(f"AlertEngine auth failed for {email} ({res.status_code}): {res.text[:200]}")
            except Exception as e:
                logger.error(f"AlertEngine auth exception for {email}: {e}")
        
        # Fallback to anon key
        return {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

    def _upload_snapshot_to_supabase(self, jpeg_bytes: bytes, filename: str, organization_id: Optional[str] = None):
        try:
            url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.SUPABASE_STORAGE_BUCKET}/{filename}"
            auth_headers = self._get_authenticated_headers(organization_id)
            headers = {
                "Authorization": auth_headers["Authorization"],
                "apikey": settings.SUPABASE_KEY,
                "Content-Type": "image/jpeg",
                "x-upsert": "true"
            }
            res = requests.post(url, headers=headers, data=jpeg_bytes, timeout=10)
            if res.status_code in [200, 201]:
                logger.info(f"Uploaded evidence snapshot {filename} to Supabase Storage.")
            else:
                logger.warning(f"Supabase Storage snapshot upload returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to upload snapshot {filename} to Supabase Storage: {e}")
            headers = {
                "Authorization": auth_headers["Authorization"],
                "apikey": settings.SUPABASE_KEY,
                "Content-Type": "image/jpeg",
                "x-upsert": "true"
            }
            res = requests.post(url, headers=headers, data=jpeg_bytes, timeout=10)
            if res.status_code in [200, 201]:
                logger.info(f"Uploaded evidence snapshot {filename} to Supabase Storage.")
            else:
                logger.warning(f"Supabase Storage snapshot upload returned {res.status_code}: {res.text}")
        except Exception as e:
            logger.error(f"Failed to upload snapshot {filename} to Supabase Storage: {e}")

    def process_violation(
        self,
        camera_id: str,
        violation: Dict[str, Any],
        frame: Optional[np.ndarray] = None,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates an alert from a rule violation candidate, uploads snapshot to Supabase Cloud, and commits to DB.
        """
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
        rule_type = violation.get("rule_type", "INTRUSION")
        severity = violation.get("severity", "HIGH")
        obj_type = violation.get("object_type", "unknown")
        track_id = violation.get("track_id")
        conf = float(violation.get("confidence", 0.0))
        zone_id = violation.get("zone_id")
        zone_name = violation.get("zone_name", "Perimeter")
        desc = violation.get("description", f"{severity} Alert: {rule_type} by {obj_type}")
        now_dt = datetime.datetime.utcnow()
        now_iso = now_dt.isoformat()

        # Upload snapshot to Supabase Cloud Storage if frame is available
        snapshot_url = None
        if frame is not None and frame.size > 0:
            filename = f"{alert_id}_{int(time.time())}.jpg"
            snapshot_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_STORAGE_BUCKET}/{filename}"
            
            # Encode frame as JPEG
            ret, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ret:
                jpeg_bytes = buf.tobytes()
                # Submit upload task asynchronously (non-blocking for real-time video pipeline)
                self._executor.submit(self._upload_snapshot_to_supabase, jpeg_bytes, filename, organization_id)

            # Local backup cache
            try:
                local_path = os.path.join(self.snapshot_dir, filename)
                cv2.imwrite(local_path, frame)
            except Exception as e:
                logger.debug(f"Local snapshot backup failed: {e}")

        alert_dict = {
            "alert_id": alert_id,
            "organization_id": organization_id,
            "event_type": rule_type,
            "severity": severity,
            "camera_id": camera_id,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "object_type": obj_type,
            "track_id": track_id,
            "confidence": conf,
            "description": desc,
            "snapshot_path": snapshot_url,
            "timestamp": now_iso,
            "status": "NEW"
        }

        # Persist directly to Supabase if organization_id is known
        if organization_id:
            def _persist_to_supabase():
                try:
                    headers = self._get_authenticated_headers(organization_id)
                    
                    # Insert Alert
                    alert_res = requests.post(
                        f"{settings.SUPABASE_URL}/rest/v1/alerts",
                        headers=headers,
                        json={
                            "alert_id": alert_id,
                            "organization_id": organization_id,
                            "event_type": rule_type,
                            "severity": severity,
                            "camera_id": camera_id,
                            "zone_id": zone_id,
                            "zone_name": zone_name,
                            "object_type": obj_type,
                            "track_id": track_id,
                            "confidence": conf,
                            "description": desc,
                            "snapshot_path": snapshot_url,
                            "status": "NEW",
                            "timestamp": now_iso
                        },
                        timeout=15
                    )
                    if alert_res.status_code not in [200, 201]:
                        logger.error(f"Alert insert failed ({alert_res.status_code}): {alert_res.text[:200]}")
                        return
                        
                    # Insert Audit Event
                    event_res = requests.post(
                        f"{settings.SUPABASE_URL}/rest/v1/events",
                        headers=headers,
                        json={
                            "event_id": event_id,
                            "organization_id": organization_id,
                            "camera_id": camera_id,
                            "timestamp": now_iso,
                            "event_type": rule_type,
                            "object_type": obj_type,
                            "track_id": track_id,
                            "confidence": conf,
                            "zone_name": zone_name,
                            "snapshot_path": snapshot_url
                        },
                        timeout=15
                    )
                    if event_res.status_code not in [200, 201]:
                        logger.error(f"Event insert failed ({event_res.status_code}): {event_res.text[:200]}")
                        
                    logger.info(f"Persisted alert {alert_id} & event {event_id} to Supabase for org {organization_id}")
                except Exception as ex:
                    logger.error(f"Failed to persist alert to Supabase: {ex}")

            self._executor.submit(_persist_to_supabase)

        return alert_dict
