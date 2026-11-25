"""
run.py — Entry point for KrishiMitra: Voice-First Multilingual Agricultural Assistant.

Usage:
    python run.py backend       # Start FastAPI backend (also serves built React UI at http://localhost:8000)
    python run.py web           # Start React Vite dev server (http://localhost:5173)
    python run.py streamlit     # Start legacy Streamlit UI (http://localhost:8501)
    python run.py all           # Start FastAPI backend + React Vite dev server (or built UI + backend)
"""

import sys
import subprocess
import time
import os
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from backend.config import settings


def _get_python_exe() -> str:
    venv_py = Path(PROJECT_ROOT) / "venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def start_backend() -> subprocess.Popen:
    py = _get_python_exe()
    cmd = [
        py, "-m", "uvicorn",
        "backend.main:app",
        "--host", settings.API_HOST,
        "--port", str(settings.API_PORT),
    ]
    print(f"[run.py] Starting FastAPI backend on http://localhost:{settings.API_PORT}")
    return subprocess.Popen(cmd, cwd=PROJECT_ROOT)


def start_web_dev() -> subprocess.Popen:
    web_dir = os.path.join(PROJECT_ROOT, "frontend-web")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    cmd = [npm_cmd, "run", "dev"]
    print("[run.py] Starting React + Vite dev server on http://localhost:5173")
    return subprocess.Popen(cmd, cwd=web_dir)


def start_streamlit() -> subprocess.Popen:
    py = _get_python_exe()
    frontend_script = os.path.join(PROJECT_ROOT, "frontend", "app.py")
    cmd = [
        py, "-m", "streamlit", "run",
        frontend_script,
        "--server.port", str(settings.FRONTEND_PORT),
        "--server.address", "0.0.0.0",
    ]
    print(f"[run.py] Starting Streamlit frontend on http://localhost:{settings.FRONTEND_PORT}")
    return subprocess.Popen(cmd, cwd=PROJECT_ROOT)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python run.py [backend|web|streamlit|all]")
        sys.exit(1)

    mode = sys.argv[1].lower()
    processes: list[subprocess.Popen] = []

    if mode == "backend":
        processes.append(start_backend())
    elif mode in ("web", "frontend"):
        processes.append(start_web_dev())
    elif mode == "streamlit":
        processes.append(start_streamlit())
    elif mode == "all":
        processes.append(start_backend())
        time.sleep(2)
        if os.path.exists(os.path.join(PROJECT_ROOT, "frontend-web", "node_modules")):
            processes.append(start_web_dev())
        else:
            print("[run.py] Note: Serving built React UI directly from http://localhost:8000")
    else:
        print(f"Unknown mode: {mode!r}. Choose backend, web, streamlit, or all.")
        sys.exit(1)

    print("[run.py] Press Ctrl+C to stop all services.")
    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        print("\n[run.py] Shutting down...")
        for p in processes:
            p.terminate()
        for p in processes:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()


if __name__ == "__main__":
    main()
