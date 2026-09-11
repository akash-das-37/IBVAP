import os
import sys
import time
import subprocess
import signal

def cleanup_stale_ports(ports=(8000, 5173)):
    """Terminates any orphan background processes holding server ports or camera handles."""
    my_pid = os.getpid()
    for port in ports:
        try:
            cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"'
            output = subprocess.check_output(cmd, shell=True, text=True).strip()
            pids = [int(p.strip()) for p in output.split() if p.strip().isdigit()]
            for pid in pids:
                if pid > 0 and pid != my_pid:
                    print(f"[Cleanup] Terminating stale process PID {pid} on port {port}...")
                    subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, capture_output=True)
        except Exception:
            pass

def main():
    print("==================================================================")
    print("  IBVAP — Intelligent Border Video Analytics Platform (Defense Edge)")
    print("==================================================================")
    print("Pre-flight check: Releasing hardware and ports...")
    cleanup_stale_ports()

    print("\nStarting IBVAP Backend & Frontend Services...\n")

    # 1. Start FastAPI Backend
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--http", "h11"]
    print("[1/2] Launching FastAPI Backend on http://localhost:8000 ...")
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
        if backend_proc.poll() is None:
            subprocess.run(f"taskkill /F /T /PID {backend_proc.pid}", shell=True, capture_output=True)
        if frontend_proc.poll() is None:
            subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, capture_output=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
