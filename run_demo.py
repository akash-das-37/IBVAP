import os
import sys
import time
import subprocess
import signal

def main():
    print("==================================================================")
    print("  IBVAP — Intelligent Border Video Analytics Platform (Defense Edge)")
    print("==================================================================")
    print("Starting IBVAP Backend & Frontend Services...\n")

    # 1. Start FastAPI Backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    print("[1/2] Launching FastAPI Backend on http://localhost:8000 (with auto-reload) ...")
    backend_proc = subprocess.Popen(backend_cmd)

    time.sleep(3.0)

    # 2. Start Frontend Dev Server
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    frontend_cmd = "npm run dev"
    print("[2/2] Launching React Tactical Dashboard on http://localhost:5173 ...")
    frontend_proc = subprocess.Popen(frontend_cmd, shell=True, cwd=frontend_dir)

    print("\n==================================================================")
    print("  IBVAP SYSTEM READY & SURVEILLANCE RUNNING")
    print("==================================================================")
    print("  Tactical Dashboard   : http://localhost:5173")
    print("  Live MJPEG Stream    : http://localhost:8000/api/v1/stream/video_feed")
    print("  Swagger API Docs     : http://localhost:8000/docs")
    print("  System Health Check  : http://localhost:8000/api/v1/health")
    print("==================================================================")
    print("Press Ctrl+C to safely shut down both backend and frontend.\n")

    def signal_handler(sig, frame):
        print("\nInitiating graceful IBVAP shutdown...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
