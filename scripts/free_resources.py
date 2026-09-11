import os
import sys
import subprocess

def free_ports_and_processes():
    print("Checking for stale python processes holding port 8000 or 5173...")
    current_pid = os.getpid()
    
    # Check port 8000 and 5173
    cmd = 'powershell -Command "Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique"'
    try:
        output = subprocess.check_output(cmd, shell=True, text=True).strip()
        pids = [int(p.strip()) for p in output.split() if p.strip().isdigit()]
        for pid in pids:
            if pid > 0 and pid != current_pid:
                print(f"Terminating conflicting process PID {pid} on port...")
                subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
    except Exception as e:
        print(f"Port check exception: {e}")

    print("Resources cleanup complete.")

if __name__ == "__main__":
    free_ports_and_processes()
