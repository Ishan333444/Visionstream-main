import subprocess
import sys
import time

import requests


HOST = "127.0.0.1"
PORT = 8000
API_URL = f"http://{HOST}:{PORT}"


backend = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app:app",
        "--host",
        HOST,
        "--port",
        str(PORT),
    ]
)

print("Starting VisionStream backend...")

# Wait for backend readiness
backend_ready = False

for _ in range(60):
    if backend.poll() is not None:
        print("Backend stopped unexpectedly.")
        break

    try:
        response = requests.get(
            f"{API_URL}/",
            timeout=1,
        )

        if response.ok:
            backend_ready = True
            break

    except requests.RequestException:
        pass

    time.sleep(0.5)


if not backend_ready:
    print("Backend failed to become ready.")

    if backend.poll() is None:
        backend.terminate()

    try:
        backend.wait(timeout=5)
    except subprocess.TimeoutExpired:
        backend.kill()

    sys.exit(1)


print("Backend ready.")

dashboard = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "dashboard/app.py",
    ]
)

print("=" * 60)
print("VisionStream started successfully!")
print("Backend API : http://127.0.0.1:8000")
print("Dashboard   : http://localhost:8501")
print("=" * 60)


try:
    backend.wait()

except KeyboardInterrupt:
    print("\nStopping VisionStream...")

finally:
    if backend.poll() is None:
        backend.terminate()

    if dashboard.poll() is None:
        dashboard.terminate()

    try:
        backend.wait(timeout=5)
    except subprocess.TimeoutExpired:
        backend.kill()

    try:
        dashboard.wait(timeout=5)
    except subprocess.TimeoutExpired:
        dashboard.kill()