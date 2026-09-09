import re
import logging
from typing import Optional, Dict, Any, List
import cv2
import numpy as np

logger = logging.getLogger("ibvap.ai.anpr")

class ANPRPipeline:
    """
    Automatic Number Plate Recognition (ANPR) pipeline.
    Crops candidate plate regions from vehicle bounding boxes, applies contrast enhancement,
    and runs EasyOCR with confidence calibration and multi-frame voting.
    """

    def __init__(self, languages: List[str] = ["en"], min_conf: float = 0.45):
        self.min_conf = min_conf
        self.reader = None
        self._languages = languages
        self._init_ocr()
        # Per-track plate cache: track_id -> list of (plate_text, confidence)
        self.track_plate_history: Dict[int, List[Dict[str, Any]]] = {}

    def _init_ocr(self):
        try:
            import easyocr
            logger.info("Initializing EasyOCR reader for ANPR (CPU mode)...")
            self.reader = easyocr.Reader(self._languages, gpu=False, verbose=False)
            logger.info("EasyOCR reader initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None

    def _preprocess_plate_crop(self, crop: np.ndarray) -> np.ndarray:
        """Preprocesses cropped plate region to optimize character contrast for OCR."""
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        # Resize to standard height for consistent OCR font sizing
        h, w = gray.shape[:2]
        if h > 0:
            scale = 70.0 / h
            gray = cv2.resize(gray, (int(w * scale), 70), interpolation=cv2.INTER_CUBIC)
        # Bilateral filter to smooth noise while keeping edges sharp
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
        # Contrast stretching
        norm = cv2.normalize(filtered, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        return norm

    def read_plate(self, frame: np.ndarray, bbox: List[int], track_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Extracts and recognizes license plate from a vehicle bounding box.
        """
        if self.reader is None or frame is None or frame.size == 0:
            return None

        x1, y1, x2, y2 = bbox
        h = y2 - y1
        w = x2 - x1

        if w < 50 or h < 40:
            return None

        # Candidate plate region: lower 45% of vehicle, centered 80% horizontally
        plate_y1 = max(0, int(y1 + 0.55 * h))
        plate_y2 = min(frame.shape[0], y2)
        plate_x1 = max(0, int(x1 + 0.10 * w))
        plate_x2 = min(frame.shape[1], int(x2 - 0.10 * w))

        crop = frame[plate_y1:plate_y2, plate_x1:plate_x2]
        if crop.size == 0 or crop.shape[0] < 15 or crop.shape[1] < 30:
            return None

        try:
            preprocessed = self._preprocess_plate_crop(crop)
            results = self.reader.readtext(preprocessed, detail=1, paragraph=False)

            if not results:
                return None

            best_text = ""
            best_conf = 0.0

            for (_, text, conf) in results:
                # Clean alphanumeric characters and hyphens/spaces
                clean_txt = re.sub(r'[^A-Za-z0-9]', '', text).upper()
                if len(clean_txt) >= 4 and conf > best_conf:
                    best_text = clean_txt
                    best_conf = float(conf)

            if not best_text:
                return None

            # Calibrate confidence: do not invent 100% confidence
            is_high_conf = (best_conf >= self.min_conf and len(best_text) >= 5)
            confidence_level = "High Confidence" if is_high_conf else "Low Confidence"

            reading = {
                "plate_number": best_text,
                "raw_confidence": round(best_conf, 3),
                "confidence_level": confidence_level,
                "crop_bbox": [plate_x1, plate_y1, plate_x2, plate_y2]
            }

            # Multi-frame aggregation
            if track_id is not None:
                if track_id not in self.track_plate_history:
                    self.track_plate_history[track_id] = []
                self.track_plate_history[track_id].append(reading)

                # Return reading with highest confidence observed across frames for this track
                aggregated = max(self.track_plate_history[track_id], key=lambda x: x["raw_confidence"])
                return aggregated

            return reading

        except Exception as e:
            logger.debug(f"ANPR reading exception: {e}")
            return None
