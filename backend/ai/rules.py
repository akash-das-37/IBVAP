import time
import logging
from typing import List, Dict, Any, Tuple, Optional
import cv2
import numpy as np

logger = logging.getLogger("ibvap.ai.rules")

def is_point_in_polygon(point: Tuple[int, int], polygon_points: List[List[int]]) -> bool:
    """
    Checks if a 2D point (x, y) is inside a polygon using OpenCV's pointPolygonTest.
    polygon_points: list of [x, y] coordinates.
    """
    if len(polygon_points) < 3:
        return False
    pts = np.array(polygon_points, dtype=np.int32)
    dist = cv2.pointPolygonTest(pts, (float(point[0]), float(point[1])), False)
    return dist >= 0

def is_bbox_in_polygon(bbox: List[int], polygon_points: List[List[int]]) -> bool:
    """
    Checks if a bounding box [x1, y1, x2, y2] intersects or enters a polygon.
    Tests center, head (upper body), feet (ground contact), corners,
    and checks if any polygon vertex is enclosed by the bbox.
    """
    if len(polygon_points) < 3 or len(bbox) != 4:
        return False

    x1, y1, x2, y2 = bbox
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2

    # Key test points of the target
    test_points = [
        (cx, cy),
        (cx, y1 + int((y2 - y1) * 0.2)),  # Head / upper torso
        (cx, max(y1, y2 - 4)),            # Feet / ground contact
        (x1, y1), (x2, y1), (x1, y2), (x2, y2)
    ]

    pts = np.array(polygon_points, dtype=np.int32)
    for pt in test_points:
        if cv2.pointPolygonTest(pts, (float(pt[0]), float(pt[1])), False) >= 0:
            return True

    # Also check if any polygon vertex is enclosed inside the bounding box
    for px, py in polygon_points:
        if x1 <= px <= x2 and y1 <= py <= y2:
            return True

    return False

def lines_intersect(p1: Tuple[int, int], p2: Tuple[int, int], p3: Tuple[int, int], p4: Tuple[int, int]) -> bool:
    """
    Determines whether line segment (p1, p2) intersects with line segment (p3, p4).
    Used for virtual tripwire / fence crossing.
    """
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))

class SecurityRuleEngine:
    """
    Evaluates tracking data against security zones and policies:
    1. Restricted Zone Intrusion (Object inside polygon)
    2. Virtual Fence / Tripwire Crossing (Trajectory crosses line)
    3. Dwell / Loitering Detection (Track remains inside zone > dwell threshold)
    4. Prohibited Direction of Movement (Object travels in restricted direction)
    """

    def __init__(self, dwell_threshold_seconds: float = 10.0):
        self.dwell_threshold = dwell_threshold_seconds
        # Maps (track_id, zone_id) -> timestamp when object entered zone
        self.zone_dwell_tracker: Dict[Tuple[int, str], float] = {}
        # Cooldown cache to prevent spamming duplicate alerts every frame: maps (track_id, rule_type, zone_id) -> last_alert_time
        self.alert_cooldowns: Dict[Tuple[int, str, str], float] = {}
        self.cooldown_period = 8.0  # seconds between repeated alerts for the same track & zone

    def _is_cooling_down(self, track_id: int, rule_type: str, zone_id: str, now: float) -> bool:
        key = (track_id, rule_type, zone_id)
        last_time = self.alert_cooldowns.get(key, 0.0)
        if (now - last_time) < self.cooldown_period:
            return True
        self.alert_cooldowns[key] = now
        return False

    def evaluate(self, tracks: List[Dict[str, Any]], zones: List[Dict[str, Any]], now: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Evaluates active tracks against configured zones.
        Returns a list of generated rule violations / alert candidates.
        """
        if now is None:
            now = time.time()

        generated_violations = []
        active_track_ids = {t["track_id"] for t in tracks}

        # Cleanup stale dwell trackers
        stale_keys = [k for k in self.zone_dwell_tracker if k[0] not in active_track_ids]
        for k in stale_keys:
            del self.zone_dwell_tracker[k]

        for track in tracks:
            track_id = track["track_id"]
            obj_class = track["class_name"]
            center = track["center"]
            bbox = track.get("bbox", [])
            conf = track["confidence"]
            direction = track["direction"]
            trajectory = track.get("trajectory", [])

            for zone in zones:
                if not zone.get("enabled", True):
                    continue

                zone_id = zone.get("zone_id", "default_zone")
                zone_name = zone.get("name", "Restricted Area")
                zone_org = zone.get("organization_id")
                zone_type = zone.get("zone_type", "polygon") # 'polygon' or 'tripwire'
                prohibited_directions = zone.get("prohibited_directions", [])
                target_classes = zone.get("target_classes", ["person", "car", "motorcycle", "bus", "truck"])

                # Check if this object class is relevant to this zone
                if target_classes and obj_class not in target_classes:
                    continue

                # -------------------------------------------------------------
                # 1. Virtual Fence / Tripwire Line Crossing
                # -------------------------------------------------------------
                if zone_type == "tripwire":
                    line = zone.get("line_coords", [])
                    if len(line) == 2 and len(trajectory) >= 2:
                        p1, p2 = line[0], line[1]
                        # Check last movement segment
                        traj_p1 = trajectory[-2]
                        traj_p2 = trajectory[-1]
                        if lines_intersect(traj_p1, traj_p2, p1, p2):
                            if not self._is_cooling_down(track_id, "TRIPWIRE_CROSSING", zone_id, now):
                                generated_violations.append({
                                    "rule_type": "TRIPWIRE_CROSSING",
                                    "severity": "CRITICAL",
                                    "zone_id": zone_id,
                                    "zone_name": zone_name,
                                    "organization_id": zone_org,
                                    "track_id": track_id,
                                    "object_type": obj_class,
                                    "confidence": conf,
                                    "center": center,
                                    "description": f"Intrusion: {obj_class.capitalize()} #{track_id} breached virtual fence '{zone_name}'",
                                    "timestamp": now
                                })

                # -------------------------------------------------------------
                # 2. Polygon Zone Intrusion & Dwell / Loitering
                # -------------------------------------------------------------
                elif zone_type == "polygon":
                    polygon = zone.get("polygon_coords", [])
                    is_inside = is_point_in_polygon(center, polygon)
                    if not is_inside and bbox:
                        is_inside = is_bbox_in_polygon(bbox, polygon)

                    dwell_key = (track_id, zone_id)
                    if is_inside:
                        # Register entry time if not already inside
                        if dwell_key not in self.zone_dwell_tracker:
                            self.zone_dwell_tracker[dwell_key] = now

                        dwell_duration = now - self.zone_dwell_tracker[dwell_key]

                        # Rule 2A: Zone Intrusion Alert
                        if not self._is_cooling_down(track_id, "ZONE_INTRUSION", zone_id, now):
                            severity = "HIGH" if zone.get("is_restricted", True) else "MEDIUM"
                            generated_violations.append({
                                "rule_type": "ZONE_INTRUSION",
                                "severity": severity,
                                "zone_id": zone_id,
                                "zone_name": zone_name,
                                "organization_id": zone_org,
                                "track_id": track_id,
                                "object_type": obj_class,
                                "confidence": conf,
                                "center": center,
                                "description": f"Unauthorized {obj_class.capitalize()} #{track_id} entered {zone_name}",
                                "timestamp": now
                            })

                        # Rule 2B: Loitering / Dwell Alert
                        zone_dwell_limit = zone.get("dwell_threshold", self.dwell_threshold)
                        if dwell_duration >= zone_dwell_limit:
                            if not self._is_cooling_down(track_id, "LOITERING", zone_id, now):
                                generated_violations.append({
                                    "rule_type": "LOITERING",
                                    "severity": "HIGH",
                                    "zone_id": zone_id,
                                    "zone_name": zone_name,
                                    "organization_id": zone_org,
                                    "track_id": track_id,
                                    "object_type": obj_class,
                                    "confidence": conf,
                                    "center": center,
                                    "dwell_time": round(dwell_duration, 1),
                                    "description": f"Loitering Alert: {obj_class.capitalize()} #{track_id} remained in {zone_name} for {round(dwell_duration, 1)}s (Limit: {zone_dwell_limit}s)",
                                    "timestamp": now
                                })

                        # Rule 2C: Prohibited Direction Alert
                        if prohibited_directions and direction in prohibited_directions:
                            if not self._is_cooling_down(track_id, "DIRECTION_VIOLATION", zone_id, now):
                                generated_violations.append({
                                    "rule_type": "DIRECTION_VIOLATION",
                                    "severity": "MEDIUM",
                                    "zone_id": zone_id,
                                    "zone_name": zone_name,
                                    "organization_id": zone_org,
                                    "track_id": track_id,
                                    "object_type": obj_class,
                                    "confidence": conf,
                                    "center": center,
                                    "direction": direction,
                                    "description": f"Direction Violation: {obj_class.capitalize()} #{track_id} moving in prohibited direction '{direction}' inside {zone_name}",
                                    "timestamp": now
                                })
                    else:
                        # Track exited polygon
                        if dwell_key in self.zone_dwell_tracker:
                            del self.zone_dwell_tracker[dwell_key]

        return generated_violations
