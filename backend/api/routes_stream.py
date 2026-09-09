import time
import cv2
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse

from backend.services.pipeline import pipeline

router = APIRouter(prefix="/api/v1/stream", tags=["Streaming"])

def generate_mjpeg():
    """Generates continuous MJPEG multipart stream from pipeline's latest annotated frame."""
    while True:
        jpeg_bytes = pipeline.get_latest_jpeg()
        if jpeg_bytes is not None:
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
        return Response(content=b"", status_code=503)
    return Response(content=jpeg_bytes, media_type="image/jpeg")

@router.get("/snapshot/raw")
def get_raw_snapshot():
    """Returns a clean unannotated camera frame — used as background for the zone editor canvas."""
    with pipeline._lock:
        raw_frame = pipeline.capture.current_frame
        if raw_frame is None:
            return Response(content=b"", status_code=503)
        frame_copy = raw_frame.copy()
    ret, buffer = cv2.imencode('.jpg', frame_copy, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ret:
        return Response(content=b"", status_code=503)
    return Response(content=buffer.tobytes(), media_type="image/jpeg",
                    headers={"Cache-Control": "no-store"})

