import time
from backend.camera.capture import VideoCaptureThread

def test_webcam():
    print("Testing VideoCaptureThread('0')...")
    cam = VideoCaptureThread("0")
    cam.start()

    success = False
    for i in range(10):
        time.sleep(0.5)
        ret, frame, ts = cam.read()
        meta = cam.get_metadata()
        print(f"Attempt {i+1}: ret={ret}, shape={frame.shape if frame is not None else None}, fps={meta.get('fps')}")
        if ret and frame is not None:
            print(f"SUCCESS: Webcam capture verified! Frame size: {frame.shape}")
            success = True
            break

    cam.stop()
    print("Camera stopped cleanly.")
    return success

if __name__ == "__main__":
    test_webcam()
