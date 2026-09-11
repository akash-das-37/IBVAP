import time
import logging
import threading
import re
from typing import Tuple, Optional
import cv2
import numpy as np

logger = logging.getLogger("ibvap.camera")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

class VideoCaptureThread:
    """
    High-performance threaded video capture for IBVAP.
    Decouples frame reading from processing to prevent RTSP buffer latency/drift.
    Supports Smartphone IP Webcam (HTTP MJPEG/RTSP), local webcams, and MP4 files.
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
        # 1. Local Webcam Index (e.g. 0, 1, 2)
        if isinstance(src, int):
            self.is_webcam = True
            logger.info(f"Source identified as Local Webcam (Index {src})")
            return src

        src_str = str(src).strip().strip('"').strip("'")
        if src_str.isdigit():
            self.is_webcam = True
            logger.info(f"Source identified as Local Webcam (Index {src_str})")
            return int(src_str)

        # 2. Fix protocol typos (e.g., "http:/192.168.1.5" -> "http://192.168.1.5")
        if src_str.startswith("http:/") and not src_str.startswith("http://"):
            src_str = "http://" + src_str[6:].lstrip("/")
        elif src_str.startswith("https:/") and not src_str.startswith("https://"):
            src_str = "https://" + src_str[7:].lstrip("/")
        elif src_str.startswith("rtsp:/") and not src_str.startswith("rtsp://"):
            src_str = "rtsp://" + src_str[6:].lstrip("/")

        # 3. Detect IP address or hostname without scheme (e.g., "192.168.1.50:8080" or "10.0.0.5:8080/video")
        ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?(/.*)?$')
        if ip_pattern.match(src_str):
            src_str = "http://" + src_str

        # 4. Network stream (RTSP, HTTP, HTTPS)
        if src_str.startswith("rtsp://") or src_str.startswith("http://") or src_str.startswith("https://"):
            self.is_network_stream = True

            # Auto-append endpoint for popular Android IP Webcam apps:
            # Android "IP Webcam" displays "http://192.168.x.x:8080" on phone screen, but MJPEG stream is at "/video"
            clean_url = src_str.rstrip('/')
            if re.search(r':8080$', clean_url):
                src_str = clean_url + "/video"
                logger.info(f"Auto-normalized IP Webcam URL to include video endpoint: {src_str}")
            elif re.search(r':4747$', clean_url):
                # DroidCam
                src_str = clean_url + "/video"
                logger.info(f"Auto-normalized DroidCam URL to include video endpoint: {src_str}")

            logger.info(f"Source identified as Network IP/RTSP Stream: {src_str}")
            return src_str

        # 5. Local video file
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
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        logger.info(f"Connecting to video source: {self.parsed_source} ...")

        if self.is_network_stream:
            # For network streams (HTTP MJPEG or RTSP), try FFMPEG backend first, then fallback to CAP_ANY
            backends = [cv2.CAP_FFMPEG, cv2.CAP_ANY]
            for backend in backends:
                try:
                    cap = cv2.VideoCapture(self.parsed_source, backend)
                    if cap and cap.isOpened():
                        # Set buffer size to 1 to eliminate frame latency
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        self.cap = cap
                        self.is_connected = True
                        logger.info(f"Successfully connected to network camera with backend {backend}: {self.parsed_source}")
                        return True
                    else:
                        if cap is not None:
                            cap.release()
                except Exception as e:
                    logger.warning(f"Error opening with backend {backend}: {e}")

            self.is_connected = False
            logger.warning(f"Failed to connect to network camera: {self.parsed_source}")
            return False

        elif self.is_webcam:
            # On Windows, try DirectShow first for fast webcam capture, fallback to default
            self.cap = cv2.VideoCapture(self.parsed_source, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                if self.cap is not None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                self.cap = cv2.VideoCapture(self.parsed_source)
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            self.cap = cv2.VideoCapture(self.parsed_source)

        if self.cap and self.cap.isOpened():
            self.is_connected = True
            logger.info(f"Camera connection successfully established for {self.parsed_source}.")
            return True
        else:
            self.is_connected = False
            logger.warning(f"Failed to open video source: {self.parsed_source}")
            return False

    def _capture_worker(self):
        fps_timer = time.time()
        frames_in_second = 0
        consecutive_failures = 0

        while self.is_running:
            if self.cap is None or not self.cap.isOpened() or not self.is_connected:
                if not self._open_capture():
                    time.sleep(self.reconnect_delay)
                    continue
                consecutive_failures = 0

            try:
                ret, frame = self.cap.read()
            except Exception as e:
                logger.warning(f"Exception while reading frame from {self.parsed_source}: {e}")
                ret, frame = False, None

            now = time.time()

            if not ret or frame is None or frame.size == 0:
                if self.is_file and self.loop_video:
                    logger.info("Reached end of demo video. Looping back to start...")
                    try:
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    except Exception:
                        pass
                    time.sleep(0.02)
                    continue
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        logger.warning(f"Stream read failed {consecutive_failures} consecutive times. Re-initializing connection...")
                        self.is_connected = False
                        if self.cap is not None:
                            try:
                                self.cap.release()
                            except Exception:
                                pass
                            self.cap = None
                        time.sleep(self.reconnect_delay)
                    else:
                        time.sleep(0.1)
                    continue

            # Successfully ingested a valid frame
            consecutive_failures = 0
            with self._lock:
                self.current_frame = frame
                self.last_frame_time = now
                self.frame_count += 1
                self.is_connected = True

            frames_in_second += 1
            if now - fps_timer >= 1.0:
                self.fps = frames_in_second / (now - fps_timer)
                frames_in_second = 0
                fps_timer = now

            # Throttle local video file playback to ~30 FPS
            if self.is_file:
                time.sleep(0.033)

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
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
        with self._lock:
            if self.current_frame is not None:
                height, width = self.current_frame.shape[:2]
        return {
            "source": str(self.raw_source),
            "parsed_source": str(self.parsed_source),
            "is_connected": self.is_connected,
            "fps": round(self.fps, 1),
            "frame_count": self.frame_count,
            "resolution": f"{width}x{height}",
            "type": "webcam" if self.is_webcam else ("rtsp" if self.is_network_stream else "file")
        }

    def stop(self):
        self.is_running = False
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        if self._thread and self._thread.is_alive():
            if threading.current_thread() != self._thread:
                self._thread.join(timeout=2.0)
        self.is_connected = False
        logger.info("VideoCaptureThread stopped and hardware released.")
