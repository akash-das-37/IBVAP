import time
import logging
import threading
from typing import Tuple, Optional
import cv2
import numpy as np

logger = logging.getLogger("ibvap.camera")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class VideoCaptureThread:
    """
    High-performance threaded video capture for IBVAP.
    Decouples frame reading from processing to prevent RTSP buffer latency/drift.
    Supports Smartphone RTSP, HTTP MJPEG, local webcams, and MP4 files.
    """

    def __init__(self, source: str, loop_video: bool = True, reconnect_delay: float = 2.0):
        self.raw_source = source
        self.loop_video = loop_video
        self.reconnect_delay = reconnect_delay

        # Identify source type
        self.is_webcam = False
        self.is_file = False
        self.is_network_stream = False
        self.parsed_source = self._parse_source(source)

        self.cap: Optional[cv2.VideoCapture] = None
        self.current_frame: Optional[np.ndarray] = None
        self.last_frame_time = 0.0
        self.fps = 0.0
        self.frame_count = 0
        self.is_connected = False
        self.is_running = False

        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def _parse_source(self, src: str):
        # Check if integer string
        if isinstance(src, int) or (isinstance(src, str) and src.strip().isdigit()):
            self.is_webcam = True
            logger.info(f"Source identified as Local Webcam (Index {src})")
            return int(src)
        
        src_str = str(src).strip()
        if src_str.startswith("rtsp://") or src_str.startswith("http://") or src_str.startswith("https://"):
            self.is_network_stream = True
            logger.info(f"Source identified as Network IP/RTSP Stream: {src_str}")
            return src_str
        
        self.is_file = True
        logger.info(f"Source identified as Local Video File: {src_str}")
        return src_str

    def start(self):
        if self.is_running:
            return self
        self.is_running = True
        self._thread = threading.Thread(target=self._capture_worker, daemon=True, name="VideoCaptureWorker")
        self._thread.start()
        logger.info(f"VideoCaptureThread started for source: {self.raw_source}")
        return self

    def _open_capture(self) -> bool:
        if self.cap is not None:
            self.cap.release()

        logger.info(f"Connecting to video source: {self.parsed_source} ...")
        
        if self.is_network_stream:
            # Optimize RTSP buffer size to 1 frame to eliminate latency
            self.cap = cv2.VideoCapture(self.parsed_source, cv2.CAP_FFMPEG)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        elif self.is_webcam:
            self.cap = cv2.VideoCapture(self.parsed_source, cv2.CAP_DSHOW) # DirectShow for fast Windows webcam
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(self.parsed_source)
        else:
            self.cap = cv2.VideoCapture(self.parsed_source)

        if self.cap and self.cap.isOpened():
            self.is_connected = True
            logger.info("Camera connection successfully established.")
            return True
        else:
            self.is_connected = False
            logger.warning(f"Failed to open video source: {self.parsed_source}")
            return False

    def _capture_worker(self):
        fps_timer = time.time()
        frames_in_second = 0

        while self.is_running:
            if self.cap is None or not self.cap.isOpened() or not self.is_connected:
                if not self._open_capture():
                    time.sleep(self.reconnect_delay)
                    continue

            ret, frame = self.cap.read()
            now = time.time()

            if not ret or frame is None or frame.size == 0:
                if self.is_file and self.loop_video:
                    logger.info("Reached end of demo video. Looping back to start...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    time.sleep(0.02)
                    continue
                else:
                    logger.warning("Stream read returned empty frame or disconnected. Attempting reconnect...")
                    self.is_connected = False
                    time.sleep(self.reconnect_delay)
                    continue

            # Ingested a valid frame
            with self._lock:
                self.current_frame = frame
                self.last_frame_time = now
                self.frame_count += 1

            frames_in_second += 1
            if now - fps_timer >= 1.0:
                self.fps = frames_in_second / (now - fps_timer)
                frames_in_second = 0
                fps_timer = now

            # If playing a local file, throttle to realistic 25-30 FPS so it doesn't spin at 1000 FPS
            if self.is_file:
                time.sleep(0.033)

        if self.cap is not None:
            self.cap.release()
            self.is_connected = False
            logger.info("VideoCaptureThread released resources and terminated.")

    def read(self) -> Tuple[bool, Optional[np.ndarray], float]:
        """
        Returns:
            ret: bool (True if frame is fresh)
            frame: np.ndarray (latest captured BGR frame)
            timestamp: float (UNIX timestamp of frame acquisition)
        """
        with self._lock:
            if self.current_frame is None:
                return False, None, 0.0
            return True, self.current_frame.copy(), self.last_frame_time

    def get_metadata(self) -> dict:
        width, height = 0, 0
        if self.current_frame is not None:
            height, width = self.current_frame.shape[:2]
        return {
            "source": str(self.raw_source),
            "is_connected": self.is_connected,
            "fps": round(self.fps, 1),
            "frame_count": self.frame_count,
            "resolution": f"{width}x{height}",
            "type": "webcam" if self.is_webcam else ("rtsp" if self.is_network_stream else "file")
        }

    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("VideoCaptureThread stopped.")
