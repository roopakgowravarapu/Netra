"""
NETRA Unified Runner - Launch both Frontend and Backend with a single command.

Usage:
    python run.py
    python run.py --reload    (enables hot-reloading for development)
"""

import os
import sys
import time
import socket
import signal
import subprocess
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


def is_port_in_use(port: int) -> bool:
    """Checks whether a TCP port is currently open and accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def free_port(port: int):
    """Frees an occupied port by terminating any stale listening process on Windows/POSIX."""
    if not is_port_in_use(port):
        return

    if sys.platform == "win32":
        try:
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in line:
                    pid = parts[-1]
                    if pid and pid != "0":
                        print(f"[*] Port {port} occupied by stale process PID {pid}. Terminating...")
                        subprocess.run(
                            f"taskkill /F /PID {pid}",
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
            time.sleep(0.5)
        except Exception:
            pass
    else:
        try:
            subprocess.run(f"fuser -k {port}/tcp", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        except Exception:
            pass


def main():
    print("=" * 65)
    print("   NETRA: EXPLAINABLE AI DR SCREENING PLATFORM")
    print("   Starting Backend (FastAPI) and Frontend (Next.js)...")
    print("=" * 65)

    # 1. Clean up stale processes on ports 8000 and 3000 to prevent startup collision
    free_port(8000)
    free_port(3000)

    # Check if developer hot-reload was requested
    enable_reload = "--reload" in sys.argv or "--dev" in sys.argv

    backend_cmd = [
        PYTHON_EXEC,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]

    # Only enable reload if explicitly requested, and restrict watch directories
    # so file writes to outputs/ (heatmaps, reports) do NOT trigger an automated restart crash!
    if enable_reload:
        backend_cmd.extend([
            "--reload",
            "--reload-dir",
            str(ROOT_DIR / "backend"),
            "--reload-dir",
            str(ROOT_DIR / "src"),
        ])

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

        # Wait for backend socket to become reachable
        for _ in range(20):
            if is_port_in_use(8000):
                break
            time.sleep(0.3)

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
        print("   • Doctor Portal:  http://localhost:3000/doctor")
        print("   • API Swagger:    http://localhost:8000/docs")
        print("   • Health Status:  http://localhost:8000/health")
        print("=" * 65)
        print("   Press Ctrl+C to shut down both servers safely.\n")

        # Monitor processes
        while True:
            for name, proc in processes:
                ret = proc.poll()
                if ret is not None:
                    print(f"\n[!] Notice: {name} process terminated with exit code {ret}.")
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
