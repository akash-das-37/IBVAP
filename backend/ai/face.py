"""
Facial Recognition Subsystem Architecture.
NOTE: In accordance with IBVAP design principles, face detection and face recognition are distinct.
Full face recognition requires an enrolled gallery database and metric embeddings (e.g. ArcFace/InsightFace).
This module defines the architectural interface for future integration without asserting false recognition capabilities.
"""
import logging
from typing import Optional, Dict, Any, List
import numpy as np

logger = logging.getLogger("ibvap.ai.face")

class FaceRecognitionModule:
    """
    Architectural interface for future Face Recognition expansion.
    Status: PLANNED (Architectural Stub).
    """

    def __init__(self, gallery_db_path: Optional[str] = None):
        self.is_active = False
        self.gallery_db_path = gallery_db_path
        logger.info("FaceRecognitionModule initialized in PLANNED state (no enrolled gallery).")

    def detect_faces(self, frame: np.ndarray, person_bbox: List[int]) -> List[List[int]]:
        """Placeholder for future localized face detection inside person bounding boxes."""
        return []

    def recognize_face(self, face_crop: np.ndarray) -> Optional[Dict[str, Any]]:
        """Placeholder for future 512-D embedding extraction and gallery cosine similarity matching."""
        return None
