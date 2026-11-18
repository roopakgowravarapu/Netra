"""
NETRA Unified Runner - Launch both Frontend and Backend with a single command.

Usage:
    python run.py
    or
    npm start / npm run dev
"""

import sys
import os
import subprocess
import signal
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

# Determine Python executable to use for backend
venv_python_win = ROOT_DIR / "backend" / "venv" / "Scripts" / "python.exe"
venv_python_unix = ROOT_DIR / "backend" / "venv" / "bin" / "python"

if venv_python_win.exists():
    PYTHON_EXEC = str(venv_python_win)
elif venv_python_unix.exists():
    PYTHON_EXEC = str(venv_python_unix)
else:
    PYTHON_EXEC = sys.executable

# Determine npm command on Windows vs POSIX
NPM_CMD = "npm.cmd" if sys.platform == "win32" else "npm"

def main():
    print("=" * 65)
    print("   NETRA: EXPLAINABLE AI DR SCREENING PLATFORM")
    print("   Starting Backend (FastAPI) and Frontend (Next.js)...")
    print("=" * 65)

    backend_cmd = [
        PYTHON_EXEC,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]

    frontend_cmd = [
        NPM_CMD,
        "--prefix",
        "frontend",
        "run",
        "dev",
    ]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)

    processes = []

    try:
        # Start Backend
        print("\n[1/2] Starting FastAPI Backend on http://localhost:8000 ...")
        p_backend = subprocess.Popen(
            backend_cmd,
            cwd=str(ROOT_DIR),
            env=env
        )
        processes.append(("Backend", p_backend))

        # Give backend a moment to bind
        time.sleep(1.5)

        # Start Frontend
        print("[2/2] Starting Next.js Frontend on http://localhost:3000 ...")
        p_frontend = subprocess.Popen(
            frontend_cmd,
            cwd=str(ROOT_DIR),
            env=env
        )
        processes.append(("Frontend", p_frontend))

        print("\n" + "=" * 65)
        print("   ✅ NETRA PLATFORM IS RUNNING!")
        print("   • Frontend UI:    http://localhost:3000")
        print("   • Backend API:    http://localhost:8000")
        print("   • API Swagger:    http://localhost:8000/docs")
        print("   • Health Status:  http://localhost:8000/health")
        print("=" * 65)
        print("   Press Ctrl+C to shut down both servers safely.\n")

        # Wait for either process to terminate
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"\n[!] Process {name} exited with code {ret}")
                    return
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\nShutting down Netra platform gracefully...")
    finally:
        for name, proc in processes:
            if proc.poll() is None:
                print(f"Terminating {name} (PID: {proc.pid})...")
                try:
                    if sys.platform == "win32":
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    else:
                        proc.terminate()
                except Exception:
                    pass
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
