import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger("ibvap.ai.tracker")

TARGET_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

class TrackRecord:
    def __init__(self, track_id: int, class_name: str, bbox: List[int], center: Tuple[int, int], conf: float, timestamp: float):
        self.track_id = track_id
        self.class_name = class_name
        self.bbox = bbox
        self.center = center
        self.confidence = conf
        self.first_seen = timestamp
        self.last_seen = timestamp
        self.trajectory: List[Tuple[int, int, float]] = [(center[0], center[1], timestamp)]
        self.direction = "STATIONARY"

    def update(self, bbox: List[int], center: Tuple[int, int], conf: float, timestamp: float):
        self.bbox = bbox
        self.center = center
        self.confidence = conf
        self.last_seen = timestamp
        self.trajectory.append((center[0], center[1], timestamp))
        if len(self.trajectory) > 50:
            self.trajectory.pop(0)
        self.direction = self._calculate_direction()

    @property
    def dwell_time(self) -> float:
        return max(0.0, self.last_seen - self.first_seen)

    def _calculate_direction(self) -> str:
        if len(self.trajectory) < 4:
            return "STATIONARY"
        # Compare center 4 frames ago to current center
        prev_x, prev_y, _ = self.trajectory[-4]
        curr_x, curr_y, _ = self.trajectory[-1]
        dx = curr_x - prev_x
        dy = curr_y - prev_y

        dist_sq = dx * dx + dy * dy
        if dist_sq < 100:  # < 10 pixels movement threshold
            return "STATIONARY"

        if abs(dx) > abs(dy):
            return "RIGHT" if dx > 0 else "LEFT"
        else:
            return "DOWN" if dy > 0 else "UP"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "class_name": self.class_name,
            "bbox": self.bbox,
            "center": self.center,
            "confidence": self.confidence,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "dwell_time": round(self.dwell_time, 1),
            "direction": self.direction,
            "trajectory": [(x, y) for x, y, _ in self.trajectory[-20:]]
        }

class ObjectTracker:
    """
    ByteTrack Object Tracker wrapper using YOLOv8 tracking engine.
    Maintains persistent IDs, trajectories, dwell times, and movement directions.
    """

    def __init__(self, model_path: str = "yolov8n.pt", conf_thresh: float = 0.45, iou_thresh: float = 0.45):
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        self.model: Optional[YOLO] = None
        self.tracks: Dict[int, TrackRecord] = {}
        self.track_timeout = 5.0  # Expire inactive tracks after 5 seconds
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Initializing YOLO tracking engine with: {self.model_path} ...")
            self.model = YOLO(self.model_path)
            logger.info("YOLO ByteTrack engine ready.")
        except Exception as e:
            logger.error(f"Failed to load YOLO tracking model: {e}")
            self.model = None

    def track(self, frame: np.ndarray, timestamp: Optional[float] = None) -> List[Dict[str, Any]]:
        if self.model is None or frame is None or frame.size == 0:
            return []

        if timestamp is None:
            timestamp = time.time()

        active_track_ids = set()
        results_list = []

        try:
            # Run Ultralytics with ByteTrack tracker
            results = self.model.track(
                source=frame,
                conf=self.conf_thresh,
                iou=self.iou_thresh,
                classes=list(TARGET_CLASSES.keys()),
                persist=True,
                tracker="bytetrack.yaml",
                verbose=False,
                device="cpu"
            )

            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for i in range(len(boxes)):
                    xyxy = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    cls_name = TARGET_CLASSES.get(cls_id, "unknown")

                    # If tracker has not assigned an ID yet, use temporary fallback
                    track_id = int(boxes.id[i].cpu().numpy()) if boxes.id is not None else (i + 1000)
                    active_track_ids.add(track_id)

                    x1, y1, x2, y2 = map(int, xyxy)
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    if track_id in self.tracks:
                        self.tracks[track_id].update([x1, y1, x2, y2], (cx, cy), round(conf, 3), timestamp)
                    else:
                        self.tracks[track_id] = TrackRecord(
                            track_id=track_id,
                            class_name=cls_name,
                            bbox=[x1, y1, x2, y2],
                            center=(cx, cy),
                            conf=round(conf, 3),
                            timestamp=timestamp
                        )

                    results_list.append(self.tracks[track_id].to_dict())

            # Cleanup expired tracks
            expired = [tid for tid, trk in self.tracks.items() if (timestamp - trk.last_seen) > self.track_timeout]
            for tid in expired:
                del self.tracks[tid]

            return results_list

        except Exception as e:
            logger.error(f"Error during ByteTrack tracking: {e}")
            return []
