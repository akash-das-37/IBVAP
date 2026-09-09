import datetime
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.database.session import get_db
from backend.database.models import EventModel, AlertModel

router = APIRouter(prefix="/api/v1/events", tags=["Events"])

@router.get("/")
def get_events(
    camera_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=50, le=300),
    db: Session = Depends(get_db)
):
    query = db.query(EventModel)
    if camera_id:
        query = query.filter(EventModel.camera_id == camera_id)
    if event_type:
        query = query.filter(EventModel.event_type == event_type.upper())

    events = query.order_by(desc(EventModel.timestamp)).limit(limit).all()
    results = []
    for e in events:
        results.append({
            "event_id": e.event_id,
            "camera_id": e.camera_id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "event_type": e.event_type,
            "object_type": e.object_type,
            "track_id": e.track_id,
            "confidence": e.confidence,
            "plate_number": e.plate_number,
            "plate_confidence": e.plate_confidence,
            "zone_name": e.zone_name,
            "snapshot_path": e.snapshot_path
        })
    return results

@router.get("/stats")
def get_system_stats(db: Session = Depends(get_db)):
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    events_today = db.query(EventModel).filter(EventModel.timestamp >= today_start).count()
    active_alerts = db.query(AlertModel).filter(AlertModel.status == "NEW").count()
    critical_alerts = db.query(AlertModel).filter(AlertModel.severity == "CRITICAL", AlertModel.status == "NEW").count()

    return {
        "events_today": events_today,
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "ai_status": "Running"
    }
