import subprocess
import sys
import time
import os


def main():
    args = sys.argv[1:]
    cwd = os.path.dirname(os.path.abspath(__file__)) or "."

    if "--frontend" in args:
        _run_frontend(cwd)
        return

    if "--backend" in args:
        _run_backend(cwd)
        return

    # Default: run both
    print("[EvoLLM] Starting backend (FastAPI on :8000) ...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=cwd,
    )

    time.sleep(2)

    print("[EvoLLM] Starting frontend (NiceGUI on :8080) ...")
    frontend = subprocess.Popen(
        [sys.executable, "-m", "frontend.main"],
        cwd=cwd,
    )

    try:
        frontend.wait()
    except KeyboardInterrupt:
        print("\n[EvoLLM] Shutting down ...")
    finally:
        backend.terminate()
        frontend.terminate()


def _run_backend(cwd: str):
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=cwd,
    )


def _run_frontend(cwd: str):
    subprocess.run(
        [sys.executable, "-m", "frontend.main"],
        cwd=cwd,
    )


if __name__ == "__main__":
    main()
