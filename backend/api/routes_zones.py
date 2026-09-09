import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import ZoneModel
from backend.services.pipeline import pipeline

router = APIRouter(prefix="/api/v1/zones", tags=["Zones"])

class ZonePayload(BaseModel):
    zone_id: str
    camera_id: Optional[str] = "CAM-01"
    name: str
    zone_type: str = "polygon"  # 'polygon' or 'tripwire'
    polygon_coords: Optional[List[List[int]]] = []
    line_coords: Optional[List[List[int]]] = []
    is_restricted: bool = True
    dwell_threshold: float = 10.0
    prohibited_directions: Optional[List[str]] = []
    color: str = "#ef4444"
    enabled: bool = True

def _refresh_pipeline_zones(db: Session):
    db_zones = db.query(ZoneModel).filter(ZoneModel.enabled == True).all()
    in_mem_zones = []
    for z in db_zones:
        in_mem_zones.append({
            "zone_id": z.zone_id,
            "name": z.name,
            "zone_type": z.zone_type,
            "polygon_coords": json.loads(z.polygon_coords) if z.polygon_coords else [],
            "line_coords": json.loads(z.line_coords) if z.line_coords else [],
            "is_restricted": z.is_restricted,
            "dwell_threshold": z.dwell_threshold,
            "prohibited_directions": json.loads(z.prohibited_directions) if z.prohibited_directions else [],
            "color": z.color,
            "enabled": z.enabled
        })
    pipeline.update_zones(in_mem_zones)

@router.get("/")
def get_zones(db: Session = Depends(get_db)):
    zones = db.query(ZoneModel).all()
    results = []
    for z in zones:
        results.append({
            "zone_id": z.zone_id,
            "camera_id": z.camera_id,
            "name": z.name,
            "zone_type": z.zone_type,
            "polygon_coords": json.loads(z.polygon_coords) if z.polygon_coords else [],
            "line_coords": json.loads(z.line_coords) if z.line_coords else [],
            "is_restricted": z.is_restricted,
            "dwell_threshold": z.dwell_threshold,
            "prohibited_directions": json.loads(z.prohibited_directions) if z.prohibited_directions else [],
            "color": z.color,
            "enabled": z.enabled
        })
    return results

@router.post("/")
def create_or_update_zone(zone: ZonePayload, db: Session = Depends(get_db)):
    existing = db.query(ZoneModel).filter(ZoneModel.zone_id == zone.zone_id).first()
    poly_str = json.dumps(zone.polygon_coords)
    line_str = json.dumps(zone.line_coords)
    dirs_str = json.dumps(zone.prohibited_directions)

    if existing:
        existing.name = zone.name
        existing.zone_type = zone.zone_type
        existing.polygon_coords = poly_str
        existing.line_coords = line_str
        existing.is_restricted = zone.is_restricted
        existing.dwell_threshold = zone.dwell_threshold
        existing.prohibited_directions = dirs_str
        existing.color = zone.color
        existing.enabled = zone.enabled
    else:
        new_zone = ZoneModel(
            zone_id=zone.zone_id,
            camera_id=zone.camera_id,
            name=zone.name,
            zone_type=zone.zone_type,
            polygon_coords=poly_str,
            line_coords=line_str,
            is_restricted=zone.is_restricted,
            dwell_threshold=zone.dwell_threshold,
            prohibited_directions=dirs_str,
            color=zone.color,
            enabled=zone.enabled
        )
        db.add(new_zone)

    db.commit()
    _refresh_pipeline_zones(db)
    return {"message": "Zone saved successfully", "zone_id": zone.zone_id}

@router.delete("/{zone_id}")
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    zone = db.query(ZoneModel).filter(ZoneModel.zone_id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    db.delete(zone)
    db.commit()
    _refresh_pipeline_zones(db)
    return {"message": "Zone deleted", "zone_id": zone_id}
