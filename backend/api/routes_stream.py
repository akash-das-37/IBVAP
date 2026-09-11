import time
import cv2
import numpy as np
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from backend.services.pipeline import pipeline

router = APIRouter(prefix="/api/v1/stream", tags=["Streaming"])

_standby_frame_bytes = None

def get_standby_frame() -> bytes:
    """Generates a tactical placeholder frame when the camera is connecting or re-initializing."""
    global _standby_frame_bytes
    if _standby_frame_bytes is None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (13, 17, 23)  # Dark tactical slate (#0d1117)
        # Tactical border
        cv2.rectangle(frame, (12, 12), (628, 468), (40, 50, 65), 1)
        # Radar scan line placeholder
        cv2.line(frame, (12, 240), (628, 240), (0, 100, 120), 1)
        # Text
        cv2.putText(frame, "IBVAP DEFENSE EDGE // CONNECTING FEED...", (80, 220),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, "INITIALIZING IP WEBCAM / SENSOR HARDWARE", (110, 260),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (148, 163, 184), 1, cv2.LINE_AA)
        cv2.putText(frame, "ENSURE SMARTPHONE IP WEBCAM APP IS ACTIVE ON NETWORK", (70, 300),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 116, 139), 1, cv2.LINE_AA)
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if ret:
            _standby_frame_bytes = buffer.tobytes()
        else:
            _standby_frame_bytes = b""
    return _standby_frame_bytes

def generate_mjpeg():
    """Generates continuous MJPEG multipart stream from pipeline's latest annotated frame."""
    while True:
        jpeg_bytes = pipeline.get_latest_jpeg()
        if jpeg_bytes is None:
            jpeg_bytes = get_standby_frame()

        if jpeg_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS throttle to maintain low CPU load

@router.get("/video_feed")
def video_feed():
    """MJPEG Live video stream with real-time AI bounding boxes, tracking IDs, and zone overlays."""
    return StreamingResponse(
        generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/snapshot")
def get_snapshot():
    """Returns the latest annotated JPEG snapshot."""
    jpeg_bytes = pipeline.get_latest_jpeg()
    if jpeg_bytes is None:
        jpeg_bytes = get_standby_frame()
    return Response(content=jpeg_bytes, media_type="image/jpeg")

@router.get("/snapshot/raw")
def get_raw_snapshot():
    """Returns a clean unannotated camera frame — used as background for the zone editor canvas."""
    with pipeline._lock:
        raw_frame = pipeline.capture.current_frame
        if raw_frame is None:
            return Response(content=get_standby_frame(), media_type="image/jpeg",
                            headers={"Cache-Control": "no-store"})
        frame_copy = raw_frame.copy()
    ret, buffer = cv2.imencode('.jpg', frame_copy, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ret:
        return Response(content=get_standby_frame(), media_type="image/jpeg",
                        headers={"Cache-Control": "no-store"})
    return Response(content=buffer.tobytes(), media_type="image/jpeg",
                    headers={"Cache-Control": "no-store"})
