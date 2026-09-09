import logging
from typing import List, Dict, Any, Optional
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger("ibvap.ai.detector")

# COCO classes relevant to border security & surveillance
TARGET_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

class ObjectDetector:
    """
    YOLOv8 Object Detector for IBVAP.
    Optimized for CPU edge inference with class filtering and confidence thresholds.
    """

    def __init__(self, model_path: str = "yolov8n.pt", conf_thresh: float = 0.45, iou_thresh: float = 0.45):
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.iou_thresh = iou_thresh
        self.model: Optional[YOLO] = None
        self._load_model()

    def _load_model(self):
        try:
            logger.info(f"Loading YOLO model from: {self.model_path} ...")
            self.model = YOLO(self.model_path)
            logger.info("YOLO model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}", exc_info=True)
            self.model = None

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs object detection on a single frame.
        Returns a list of detected objects with bounding boxes, classes, and confidences.
        """
        if self.model is None or frame is None or frame.size == 0:
            return []

        try:
            # Run inference targeting only security-relevant classes
            results = self.model.predict(
                source=frame,
                conf=self.conf_thresh,
                iou=self.iou_thresh,
                classes=list(TARGET_CLASSES.keys()),
                verbose=False,
                device="cpu"
            )

            detections = []
            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for i in range(len(boxes)):
                    xyxy = boxes.xyxy[i].cpu().numpy()
                    conf = float(boxes.conf[i].cpu().numpy())
                    cls_id = int(boxes.cls[i].cpu().numpy())
                    cls_name = TARGET_CLASSES.get(cls_id, "unknown")

                    x1, y1, x2, y2 = map(int, xyxy)
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)

                    detections.append({
                        "bbox": [x1, y1, x2, y2],
                        "confidence": round(conf, 3),
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "center": (cx, cy)
                    })

            return detections
        except Exception as e:
            logger.error(f"Error during YOLO object detection: {e}")
            return []
