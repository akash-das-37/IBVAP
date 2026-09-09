"""Camera ingestion and edge motion detection module."""
from .capture import VideoCaptureThread
from .motion import EdgeMotionDetector

__all__ = ["VideoCaptureThread", "EdgeMotionDetector"]
