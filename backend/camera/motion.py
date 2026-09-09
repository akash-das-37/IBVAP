from typing import List, Tuple, Optional
import cv2
import numpy as np

class EdgeMotionDetector:
    """
    Lightweight edge-level motion and activity detector.
    Reduces compute by verifying frame dynamics before triggering heavy neural network inference.
    """

    def __init__(self, sensitivity: int = 25, min_area: int = 500, history: int = 100):
        self.sensitivity = sensitivity
        self.min_area = min_area
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=history,
            varThreshold=sensitivity,
            detectShadows=True
        )
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    def detect(self, frame: np.ndarray, zone_mask: Optional[np.ndarray] = None) -> Tuple[bool, List[dict], np.ndarray]:
        """
        Processes frame and returns:
            - has_motion: bool
            - motion_boxes: List of {'bbox': [x, y, w, h], 'area': float, 'center': (cx, cy)}
            - fg_mask: np.ndarray (for debugging or UI visualization)
        """
        if frame is None or frame.size == 0:
            return False, [], np.zeros((100, 100), dtype=np.uint8)

        # 1. Downsample for fast edge evaluation
        h, w = frame.shape[:2]
        small_frame = cv2.resize(frame, (480, int(480 * h / w)))
        sh, sw = small_frame.shape[:2]
        scale_x = w / sw
        scale_y = h / sh

        # 2. Gaussian blur to suppress camera sensor noise
        blurred = cv2.GaussianBlur(small_frame, (5, 5), 0)

        # 3. Compute foreground mask
        fg_mask = self.bg_subtractor.apply(blurred)

        # Remove shadows (value 127) and keep only true motion (value 255)
        _, fg_thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)

        # Apply morphological operations to connect components and remove speckles
        fg_cleaned = cv2.morphologyEx(fg_thresh, cv2.MORPH_OPEN, self.kernel)
        fg_cleaned = cv2.morphologyEx(fg_cleaned, cv2.MORPH_DILATE, self.kernel, iterations=2)

        # If zone_mask is provided, restrict motion detection to zone
        if zone_mask is not None:
            small_mask = cv2.resize(zone_mask, (sw, sh), interpolation=cv2.INTER_NEAREST)
            fg_cleaned = cv2.bitwise_and(fg_cleaned, small_mask)

        # 4. Find contours
        contours, _ = cv2.findContours(fg_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_boxes = []
        has_motion = False

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Scale min_area relative to downsampled dimensions
            scaled_min_area = self.min_area / (scale_x * scale_y)
            if area >= scaled_min_area:
                has_motion = True
                x, y, bw, bh = cv2.boundingRect(cnt)
                # Map back to original resolution
                orig_x = int(x * scale_x)
                orig_y = int(y * scale_y)
                orig_w = int(bw * scale_x)
                orig_h = int(bh * scale_y)
                cx = orig_x + orig_w // 2
                cy = orig_y + orig_h // 2

                motion_boxes.append({
                    "bbox": [orig_x, orig_y, orig_w, orig_h],
                    "area": area * (scale_x * scale_y),
                    "center": (cx, cy)
                })

        return has_motion, motion_boxes, fg_cleaned
