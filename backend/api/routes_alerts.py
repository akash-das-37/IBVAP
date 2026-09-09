from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.session import get_db
from backend.database.models import AlertModel

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

@router.get("/")
def get_alerts(
    severity: Optional[str] = None,
    camera_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(AlertModel)
    if severity:
        query = query.filter(AlertModel.severity == severity.upper())
    if camera_id:
        query = query.filter(AlertModel.camera_id == camera_id)
    if status:
        query = query.filter(AlertModel.status == status.upper())

    alerts = query.order_by(desc(AlertModel.timestamp)).limit(limit).all()
    results = []
    for a in alerts:
        results.append({
            "alert_id": a.alert_id,
            "event_type": a.event_type,
            "severity": a.severity,
            "camera_id": a.camera_id,
            "zone_id": a.zone_id,
            "zone_name": a.zone_name,
            "object_type": a.object_type,
            "track_id": a.track_id,
            "confidence": a.confidence,
            "description": a.description,
            "snapshot_path": a.snapshot_path,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "status": a.status
        })
    return results

@router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(AlertModel).filter(AlertModel.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "ACKNOWLEDGED"
    db.commit()
    return {"message": "Alert marked as acknowledged", "alert_id": alert_id}
