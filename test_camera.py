import sys
import os
import time
import argparse
import cv2

# Add current directory to path
sys.path.insert(0, os.path.abspath("."))

from backend.camera.capture import VideoCaptureThread
from backend.camera.motion import EdgeMotionDetector
from backend.config import settings

def main():
    parser = argparse.ArgumentParser(description="IBVAP Phase 1: Camera Ingestion & Motion Verification")
    parser.add_argument("--source", type=str, default=None,
                        help="Video source: RTSP URL, HTTP URL, webcam index (0), or video file path")
    parser.add_argument("--no-motion", action="store_true", help="Disable motion detection overlay")
    args = parser.parse_args()

    # Determine source
    source = args.source
    if not source:
        if settings.MODE == "demo" or not os.path.exists(".env"):
            source = "data/demo_videos/sample_border.mp4"
        else:
            source = settings.CAMERA_SOURCE

    print("==================================================")
    print("  IBVAP: Camera Ingestion & Motion Test (Phase 1) ")
    print("==================================================")
    print(f"Testing Source       : {source}")
    print(f"Motion Filter Enabled: {not args.no_motion}")
    print("Press 'q' or ESC in the preview window to exit.")
    print("==================================================")

    capture = VideoCaptureThread(source=source).start()
    motion_detector = EdgeMotionDetector(
        sensitivity=settings.MOTION_SENSITIVITY,
        min_area=settings.MIN_MOTION_AREA
    )

    time.sleep(1.0) # Wait for camera handshake

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame, timestamp = capture.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            display = frame.copy()
            h, w = display.shape[:2]

            has_motion = False
            motion_boxes = []
            if not args.no_motion:
                has_motion, motion_boxes, fg_mask = motion_detector.detect(frame)
                # Draw motion boxes in yellow
                for mb in motion_boxes:
                    bx, by, bw, bh = mb["bbox"]
                    cv2.rectangle(display, (bx, by), (bx + bw, by + bh), (0, 230, 255), 2)
                    cv2.putText(display, "MOTION", (bx, max(by - 6, 15)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 255), 1)

            # Metadata Overlay
            meta = capture.get_metadata()
            status_color = (0, 255, 0) if meta["is_connected"] else (0, 0, 255)
            status_txt = "CONNECTED" if meta["is_connected"] else "DISCONNECTED"

            cv2.putText(display, f"IBVAP EDGE SURVEILLANCE | CAM: {settings.CAMERA_ID}", (15, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(display, f"STATUS: {status_txt} | TYPE: {meta['type'].upper()} | FPS: {meta['fps']}", (15, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
            cv2.putText(display, f"RESOLUTION: {meta['resolution']} | MOTION: {'DETECTED' if has_motion else 'IDLE'}", (15, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 230, 255) if has_motion else (180, 180, 180), 1)

            cv2.imshow("IBVAP - Camera & Edge Motion Feed (Press Q to quit)", display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break

    except KeyboardInterrupt:
        print("\nStopping camera test...")
    finally:
        capture.stop()
        cv2.destroyAllWindows()
        elapsed = time.time() - start_time
        print(f"\nTest finished: Processed {frame_count} frames in {elapsed:.1f}s (Avg {frame_count / max(elapsed, 0.1):.1f} FPS)")

if __name__ == "__main__":
    main()
