import os
import time
import json
import asyncio
import logging
import threading
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
import requests

from backend.config import settings
from backend.camera.capture import VideoCaptureThread
from backend.camera.motion import EdgeMotionDetector
from backend.ai.detector import ObjectDetector
from backend.ai.tracker import ObjectTracker
from backend.ai.rules import SecurityRuleEngine
from backend.ai.anpr import ANPRPipeline
from backend.ai.lowlight import LowLightEnhancer
from backend.services.queue import EventQueue
from backend.alerts.engine import AlertEngine
from backend.websocket.manager import manager
from backend.database.session import SessionLocal
from backend.database.models import CameraModel, ZoneModel, EventModel

logger = logging.getLogger("ibvap.pipeline")

class AnalyticsPipeline:
    """
    Master Pipeline Orchestrator.
    Connects Camera Ingestion -> Edge Motion -> ByteTrack Tracking -> Security Rules -> Alert Generation -> WebSockets.
    """

    def __init__(self):
        self.camera_source = settings.CAMERA_SOURCE
        if settings.MODE == "demo":
            self.camera_source = "data/demo_videos/sample_border.mp4"

        # 1. Modules
        self.capture = VideoCaptureThread(source=self.camera_source)
        self.motion_detector = EdgeMotionDetector(
            sensitivity=settings.MOTION_SENSITIVITY,
            min_area=settings.MIN_MOTION_AREA
        )
        self.tracker = ObjectTracker(
            model_path=settings.YOLO_MODEL,
            conf_thresh=settings.CONFIDENCE_THRESHOLD,
            iou_thresh=settings.IOU_THRESHOLD
        )
        self.rules = SecurityRuleEngine(dwell_threshold_seconds=settings.DWELL_THRESHOLD_SECONDS)
        self.anpr = ANPRPipeline() if settings.ENABLE_ANPR else None
        self.lowlight = LowLightEnhancer()
        self.event_queue = EventQueue(redis_url=settings.REDIS_URL)
        self.alert_engine = AlertEngine(snapshot_dir=settings.SNAPSHOT_DIR)

        # 2. State
        self.is_running = False
        self.zones: List[Dict[str, Any]] = []
        self.current_organization_id: Optional[str] = None
        self.latest_annotated_frame: Optional[np.ndarray] = None
        self.latest_tracks: List[Dict[str, Any]] = []
        self.active_alerts: List[Dict[str, Any]] = []
        self.fps = 0.0
        self.frame_count = 0
        self.loop = None
        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None

        # Load initial zones from database
        self._load_zones_from_db()

    def _load_zones_from_db(self):
        # 1. First attempt loading from Supabase Cloud (authenticated)
        try:
            # Authenticate as service operator to satisfy RLS
            auth_url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
            auth_res = requests.post(auth_url, headers={
                "apikey": settings.SUPABASE_KEY,
                "Content-Type": "application/json"
            }, json={
                "email": "iamnegative37@gmail.com",
                "password": "Surveillance2026!"
            }, timeout=10)
            
            if auth_res.status_code == 200:
                token = auth_res.json().get("access_token")
                headers = {
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {token}"
                }
            else:
                logger.warning(f"Pipeline auth failed ({auth_res.status_code}), falling back to anon key")
                headers = {
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}"
                }
            
            url = f"{settings.SUPABASE_URL}/rest/v1/zones?enabled=eq.true&select=*"
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200 and res.json():
                db_zones = res.json()
                self.zones = []
                for z in db_zones:
                    self.zones.append({
                        "zone_id": z.get("zone_id"),
                        "name": z.get("name"),
                        "zone_type": z.get("zone_type", "polygon"),
                        "polygon_data": z.get("polygon_data") or [],
                        "polygon_coords": z.get("polygon_coords") or [],
                        "line_coords": z.get("line_coords") or [],
                        "is_restricted": z.get("is_restricted", True),
                        "dwell_threshold": z.get("dwell_threshold", 10.0),
                        "prohibited_directions": z.get("prohibited_directions") or [],
                        "color": z.get("color", "#ef4444"),
                        "organization_id": z.get("organization_id"),
                        "enabled": z.get("enabled", True)
                    })
                if db_zones:
                    self.current_organization_id = db_zones[0].get("organization_id")
                logger.info(f"Loaded {len(self.zones)} active detection zone(s) from Supabase Cloud.")
                return
        except Exception as e:
            logger.warning(f"Unable to load initial zones from Supabase: {e}")

        # 2. Fallback to local SQLite if Supabase unreachable
        try:
            from backend.database.session import init_db
            init_db()
            db = SessionLocal()
            db_zones = db.query(ZoneModel).filter(ZoneModel.enabled == True).all()

            self.zones = []
            for z in db_zones:
                self.zones.append({
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
            logger.info(f"Loaded {len(self.zones)} active detection zone(s) from local database.")
            db.close()
        except Exception as e:
            logger.error(f"Error loading zones from local database: {e}")

    def update_zones(self, new_zones: List[Dict[str, Any]], organization_id: Optional[str] = None):
        with self._lock:
            self.zones = new_zones
            if organization_id:
                self.current_organization_id = organization_id
            logger.info(f"Updated in-memory zones: {len(new_zones)} zones active (org: {self.current_organization_id}).")

    def set_camera_source(self, new_source: str):
        with self._lock:
            logger.info(f"Switching camera source to: {new_source}")
            self.capture.stop()
            self.camera_source = new_source
            self.capture = VideoCaptureThread(source=new_source).start()

    def start(self, event_loop=None):
        if self.is_running:
            return
        self.is_running = True
        self.loop = event_loop
        self.capture.start()
        self._worker_thread = threading.Thread(target=self._pipeline_loop, daemon=True, name="AnalyticsWorker")
        self._worker_thread.start()
        logger.info("AnalyticsPipeline worker thread started.")

    def stop(self):
        self.is_running = False
        self.capture.stop()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
        logger.info("AnalyticsPipeline stopped.")

    def _pipeline_loop(self):
        last_time = time.time()
        frames_in_sec = 0
        last_stats_broadcast = 0.0

        while self.is_running:
            ret, frame, timestamp = self.capture.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            now = time.time()
            self.frame_count += 1
            frames_in_sec += 1
            if now - last_time >= 1.0:
                self.fps = frames_in_sec / (now - last_time)
                frames_in_sec = 0
                last_time = now

            # 1. Optional Low-Light Enhancement (CLAHE)
            processed_frame = frame
            if settings.ENABLE_LOW_LIGHT_CLAHE:
                processed_frame = self.lowlight.enhance(frame)

            # 2. Lightweight Edge Motion Detection Filter
            has_motion = True
            motion_boxes = []
            if settings.MOTION_FILTER_ENABLED:
                has_motion, motion_boxes, _ = self.motion_detector.detect(processed_frame)

            # 3. AI Inference: Run ByteTrack (runs every frame if motion detected, or every 4th frame as heartbeat)
            tracks = []
            if has_motion or (self.frame_count % 4 == 0):
                tracks = self.tracker.track(processed_frame, timestamp=now)
                with self._lock:
                    self.latest_tracks = tracks

            # 4. Optional ANPR on Vehicles
            if self.anpr and tracks:
                for trk in tracks:
                    if trk["class_name"] in ["car", "bus", "truck"]:
                        plate_data = self.anpr.read_plate(processed_frame, trk["bbox"], trk["track_id"])
                        if plate_data:
                            trk["plate_number"] = plate_data["plate_number"]
                            trk["plate_confidence"] = plate_data["confidence_level"]

            # 5. Security Rule Engine Evaluation
            with self._lock:
                current_zones = list(self.zones)

            h, w = frame.shape[:2]
            scaled_zones = self._scale_zones_to_frame(current_zones, w, h)

            violations = self.rules.evaluate(tracks, scaled_zones, now=now)

            # Debug logging: periodic status (every ~5 seconds)
            if self.frame_count % 60 == 0 and (tracks or current_zones):
                person_tracks = [t for t in tracks if t["class_name"] == "person"]
                logger.info(
                    f"[PIPELINE DEBUG] Frame #{self.frame_count} | "
                    f"Tracks: {len(tracks)} (persons: {len(person_tracks)}) | "
                    f"Zones: {len(current_zones)} | "
                    f"Scaled zones: {len(scaled_zones)} | "
                    f"Violations: {len(violations)} | "
                    f"Org: {self.current_organization_id}"
                )
                if person_tracks and scaled_zones:
                    pt = person_tracks[0]
                    sz = scaled_zones[0]
                    logger.info(
                        f"[PIPELINE DEBUG] First person center={pt.get('center')}, bbox={pt.get('bbox')} | "
                        f"First zone polygon_coords={sz.get('polygon_coords', [])[:3]}..."
                    )

            # 6. Process Rule Violations & Emit Alerts
            for violation in violations:
                # Buffer to Event Queue
                self.event_queue.publish({
                    "event_id": f"EQ-{int(now * 1000)}",
                    "camera_id": settings.CAMERA_ID,
                    "timestamp": now,
                    "event_type": violation["rule_type"],
                    "priority": violation["severity"],
                    "zone": violation.get("zone_name")
                })

                # Create Alert & Snapshot
                target_org = violation.get("organization_id") or self.current_organization_id
                annotated_snapshot = self._draw_annotations(frame.copy(), tracks, scaled_zones, [violation])
                alert = self.alert_engine.process_violation(
                    camera_id=settings.CAMERA_ID,
                    violation=violation,
                    frame=annotated_snapshot,
                    organization_id=target_org
                )

                with self._lock:
                    self.active_alerts.insert(0, alert)
                    if len(self.active_alerts) > 20:
                        self.active_alerts.pop()

                # Push alert EXCLUSIVELY to authorized organization WebSocket clients
                if self.loop and not self.loop.is_closed():
                    if target_org:
                        asyncio.run_coroutine_threadsafe(
                            manager.send_to_org(target_org, {
                                "type": "NEW_ALERT",
                                "data": alert
                            }),
                            self.loop
                        )

            # 7. Render Annotated Frame for Live Video Output
            annotated_frame = self._draw_annotations(processed_frame.copy(), tracks, scaled_zones, violations)
            with self._lock:
                self.latest_annotated_frame = annotated_frame

            # Send periodic stats (every 1 second)
            if (now - last_stats_broadcast >= 1.0) and self.loop and not self.loop.is_closed():
                last_stats_broadcast = now
                person_count = sum(1 for t in tracks if t["class_name"] == "person")
                vehicle_count = sum(1 for t in tracks if t["class_name"] in ["car", "bus", "truck", "motorcycle"])
                meta = self.capture.get_metadata()

                asyncio.run_coroutine_threadsafe(
                    manager.broadcast_stats({
                        "type": "STATS_UPDATE",
                        "data": {
                            "camera_id": settings.CAMERA_ID,
                            "fps": round(self.fps, 1),
                            "camera_status": "ONLINE" if meta["is_connected"] else "OFFLINE",
                            "person_count": person_count,
                            "vehicle_count": vehicle_count,
                            "active_alerts_count": len(self.active_alerts),
                            "source_type": meta["type"],
                            "timestamp": now
                        }
                    }),
                    self.loop
                )

            time.sleep(0.01)

    def _scale_zones_to_frame(self, zones: List[Dict[str, Any]], frame_w: int, frame_h: int) -> List[Dict[str, Any]]:
        scaled_zones = []
        for z in zones:
            sz = dict(z)
            pts = sz.get("polygon_data") or sz.get("polygon_coords")
            if pts:
                sz["polygon_coords"] = self._scale_coords(pts, frame_w, frame_h)
            if sz.get("line_coords"):
                sz["line_coords"] = self._scale_coords(sz["line_coords"], frame_w, frame_h)
            scaled_zones.append(sz)
        return scaled_zones

    def _scale_coords(self, coords: List[Any], frame_w: int, frame_h: int) -> List[List[int]]:
        if not coords:
            return []
        try:
            standard_pts = []
            for pt in coords:
                if isinstance(pt, dict) and "x" in pt and "y" in pt:
                    standard_pts.append((float(pt["x"]), float(pt["y"])))
                elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    standard_pts.append((float(pt[0]), float(pt[1])))

            if not standard_pts:
                return []

            is_norm = all(0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 for x, y in standard_pts)
            is_canvas_960 = (frame_w != 960 or frame_h != 540) and all(x <= 960 and y <= 540 for x, y in standard_pts)

            scaled = []
            for x, y in standard_pts:
                if is_norm:
                    sx = int(round(x * frame_w))
                    sy = int(round(y * frame_h))
                elif is_canvas_960:
                    sx = int(round(x * (frame_w / 960.0)))
                    sy = int(round(y * (frame_h / 540.0)))
                else:
                    sx = int(round(x))
                    sy = int(round(y))
                scaled.append([sx, sy])
            return scaled
        except Exception as e:
            logger.error(f"Error scaling coords: {e}")
            return coords

    def _draw_annotations(
        self,
        frame: np.ndarray,
        tracks: List[Dict[str, Any]],
        zones: List[Dict[str, Any]],
        violations: List[Dict[str, Any]]
    ) -> np.ndarray:
        # Detect dark frame / closed physical shutter
        if np.mean(frame) < 1.0:
            h, w = frame.shape[:2]
            cv2.rectangle(frame, (10, 10), (w - 10, h - 10), (45, 55, 72), 1)
            cv2.putText(frame, "IBVAP DEFENSE EDGE // WEBCAM HARDWARE ACTIVE", (30, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 240, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "CAMERA SENSOR DARK / LENS COVERED", (30, h // 2 - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2, cv2.LINE_AA)
            cv2.putText(frame, "Slide open laptop physical webcam shutter,", (30, h // 2 + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (203, 213, 225), 1, cv2.LINE_AA)
            cv2.putText(frame, "or click CHANGE SOURCE to select Demo Video / IP Cam.", (30, h // 2 + 42),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (148, 163, 184), 1, cv2.LINE_AA)

        # 1. Draw Zones (Polygons / Tripwires)
        for zone in zones:
            color_hex = zone.get("color", "#ef4444").lstrip("#")
            try:
                # Convert hex to BGR
                r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
                bgr = (b, g, r)
            except Exception:
                bgr = (0, 0, 255)

            if zone.get("zone_type") == "polygon":
                coords = zone.get("polygon_coords", [])
                if len(coords) >= 3:
                    pts = np.array(coords, np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(overlay, [pts], bgr)
                    cv2.polylines(frame, [pts], True, bgr, 2)
                    # Label
                    cx = int(np.mean([p[0] for p in coords]))
                    cy = int(np.mean([p[1] for p in coords]))
                    cv2.putText(frame, zone.get("name", "ZONE"), (cx - 40, cy),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            elif zone.get("zone_type") == "tripwire":
                line = zone.get("line_coords", [])
                if len(line) == 2:
                    p1, p2 = tuple(line[0]), tuple(line[1])
                    cv2.line(frame, p1, p2, bgr, 3)
                    cv2.putText(frame, f"FENCE: {zone.get('name')}", (p1[0], max(p1[1] - 8, 20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, bgr, 2)

        # Blend transparent zone fill
        cv2.addWeighted(overlay, 0.20, frame, 0.80, 0, frame)

        # 2. Draw Tracked Objects
        for trk in tracks:
            x1, y1, x2, y2 = trk["bbox"]
            cls_name = trk["class_name"]
            track_id = trk["track_id"]
            conf = trk["confidence"]
            dwell = trk.get("dwell_time", 0.0)
            direction = trk.get("direction", "")

            # Tactical color coding
            box_color = (0, 255, 0) if cls_name == "person" else (255, 180, 0)

            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

            # Label banner
            label = f"{cls_name.upper()} #{track_id} ({conf:.2f})"
            if dwell > 2.0:
                label += f" | {dwell:.1f}s"
            if direction and direction != "STATIONARY":
                label += f" [{direction}]"

            # Check if license plate is recognized
            if "plate_number" in trk:
                label += f" | {trk['plate_number']} ({trk.get('plate_confidence', '')})"

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(frame, (x1, max(0, y1 - th - 8)), (x1 + tw + 8, y1), box_color, -1)
            cv2.putText(frame, label, (x1 + 4, max(th + 2, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

            # Draw trajectory path
            trajectory = trk.get("trajectory", [])
            if len(trajectory) > 1:
                pts = np.array(trajectory, np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], False, (0, 230, 255), 2)

        # 3. Violation Alerts Top Banner
        if violations:
            latest_v = violations[0]
            banner_text = f"ALERT: {latest_v['description']}"
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 35), (0, 0, 200), -1)
            cv2.putText(frame, banner_text, (20, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)

        return frame

    def get_latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            if self.latest_annotated_frame is None:
                return None
            ret, buffer = cv2.imencode('.jpg', self.latest_annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
            if ret:
                return buffer.tobytes()
            return None

# Global pipeline singleton
pipeline = AnalyticsPipeline()
