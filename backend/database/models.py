import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from .session import Base

class CameraModel(Base):
    __tablename__ = "cameras"

    camera_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    source_url = Column(String(255), nullable=False)
    location = Column(String(100), default="Main Perimeter")
    status = Column(String(20), default="OFFLINE")  # ONLINE, OFFLINE, ERROR
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class ZoneModel(Base):
    __tablename__ = "zones"

    zone_id = Column(String(50), primary_key=True, index=True)
    camera_id = Column(String(50), index=True, default="CAM-01")
    name = Column(String(100), nullable=False)
    zone_type = Column(String(20), default="polygon")  # polygon or tripwire
    polygon_coords = Column(Text, default="[]")  # JSON string [[x, y], ...]
    line_coords = Column(Text, default="[]")     # JSON string [[x1, y1], [x2, y2]]
    is_restricted = Column(Boolean, default=True)
    dwell_threshold = Column(Float, default=10.0)
    prohibited_directions = Column(Text, default="[]")  # JSON string ["LEFT", ...]
    color = Column(String(20), default="#ef4444")  # Hex color for canvas overlay
    enabled = Column(Boolean, default=True)

class EventModel(Base):
    __tablename__ = "events"

    event_id = Column(String(50), primary_key=True, index=True)
    camera_id = Column(String(50), index=True, default="CAM-01")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # MOTION, DETECTION, ZONE_ENTRY, PLATE_READ
    object_type = Column(String(50), nullable=True)             # person, car, etc.
    track_id = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.0)
    plate_number = Column(String(50), nullable=True)
    plate_confidence = Column(String(20), nullable=True)
    zone_name = Column(String(100), nullable=True)
    snapshot_path = Column(String(255), nullable=True)

class AlertModel(Base):
    __tablename__ = "alerts"

    alert_id = Column(String(50), primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # INTRUSION, LOITERING, TRIPWIRE_CROSSING, DIRECTION_VIOLATION
    severity = Column(String(20), default="HIGH", index=True)    # LOW, MEDIUM, HIGH, CRITICAL
    camera_id = Column(String(50), index=True, default="CAM-01")
    zone_id = Column(String(50), nullable=True)
    zone_name = Column(String(100), nullable=True)
    object_type = Column(String(50), nullable=False)
    track_id = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.0)
    description = Column(String(255), nullable=False)
    snapshot_path = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    status = Column(String(20), default="NEW", index=True)       # NEW, ACKNOWLEDGED, RESOLVED
