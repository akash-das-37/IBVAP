import os
import uuid
import time
import datetime
import logging
from typing import Optional, Dict, Any, List
import cv2
import numpy as np

from backend.database.session import SessionLocal
from backend.database.models import AlertModel, EventModel

logger = logging.getLogger("ibvap.alerts")

class AlertEngine:
    """
    Synthesizes rule violations and security triggers into structured alerts.
    Persists alert records & annotated snapshots, grades severity, and forwards alerts.
    """

    def __init__(self, snapshot_dir: str = "data/snapshots"):
        self.snapshot_dir = snapshot_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def process_violation(
        self,
        camera_id: str,
        violation: Dict[str, Any],
        frame: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Creates an alert from a rule violation candidate, stores snapshot, and commits to DB.
        """
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"
        rule_type = violation.get("rule_type", "INTRUSION")
        severity = violation.get("severity", "HIGH")
        obj_type = violation.get("object_type", "unknown")
        track_id = violation.get("track_id")
        conf = float(violation.get("confidence", 0.0))
        zone_id = violation.get("zone_id")
        zone_name = violation.get("zone_name", "Perimeter")
        desc = violation.get("description", f"{severity} Alert: {rule_type} by {obj_type}")
        now_dt = datetime.datetime.utcnow()

        # Save snapshot if frame is available
        snapshot_rel_path = None
        if frame is not None and frame.size > 0:
            filename = f"{alert_id}_{int(time.time())}.jpg"
            full_path = os.path.join(self.snapshot_dir, filename)
            try:
                # Save snapshot to disk
                cv2.imwrite(full_path, frame)
                snapshot_rel_path = f"/data/snapshots/{filename}"
            except Exception as e:
                logger.error(f"Failed to save alert snapshot: {e}")

        alert_dict = {
            "alert_id": alert_id,
            "event_type": rule_type,
            "severity": severity,
            "camera_id": camera_id,
            "zone_id": zone_id,
            "zone_name": zone_name,
            "object_type": obj_type,
            "track_id": track_id,
            "confidence": conf,
            "description": desc,
            "snapshot_path": snapshot_rel_path,
            "timestamp": now_dt.isoformat(),
            "status": "NEW"
        }

        # Persist to SQLite Database
        db = SessionLocal()
        try:
            db_alert = AlertModel(
                alert_id=alert_id,
                event_type=rule_type,
                severity=severity,
                camera_id=camera_id,
                zone_id=zone_id,
                zone_name=zone_name,
                object_type=obj_type,
                track_id=track_id,
                confidence=conf,
                description=desc,
                snapshot_path=snapshot_rel_path,
                timestamp=now_dt,
                status="NEW"
            )
            db.add(db_alert)

            # Also create corresponding audit event record
            event_id = f"EVT-{uuid.uuid4().hex[:8].upper()}"
            db_event = EventModel(
                event_id=event_id,
                camera_id=camera_id,
                timestamp=now_dt,
                event_type=rule_type,
                object_type=obj_type,
                track_id=track_id,
                confidence=conf,
                zone_name=zone_name,
                snapshot_path=snapshot_rel_path
            )
            db.add(db_event)
            db.commit()
            logger.info(f"Generated Alert {alert_id} [{severity}] - {desc}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error persisting alert {alert_id} to database: {e}")
        finally:
            db.close()

        return alert_dict
