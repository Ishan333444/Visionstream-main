# VisionStream

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.142-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.65-red)
![YOLO](https://img.shields.io/badge/YOLO-v11-orange)

> **A modular real-time computer vision surveillance platform featuring object detection, tracking, analytics, live dashboards, and REST APIs.**

---

## Highlights

- ⚡ Real-time object detection using YOLO11
- 🎯 Multi-object tracking with ByteTrack
- 🚶 Entry / Exit counting
- 🚷 Intrusion detection
- ⏱️ Dwell time monitoring
- 🌡️ Heatmap generation
- 👥 Crowd density estimation
- 📊 Live analytics dashboard
- 📹 MJPEG video streaming
- 🗄️ SQLite event logging
- 📤 CSV event export
- 🖱️ Interactive camera calibration
- 🌐 REST API built with FastAPI
- ⚙️ Configurable compute device and camera source

---

# Overview

VisionStream is a real-time AI surveillance platform built using **YOLO11**, **FastAPI**, **Streamlit**, and **OpenCV**. It detects and tracks objects in a live camera feed while generating real-time analytics including entry/exit counting, intrusion detection, dwell time analysis, crowd density estimation, and heatmap visualization.

The application exposes analytics through a FastAPI backend and provides a Streamlit dashboard for live monitoring.

---

# Architecture

```text
                    Camera
                       │
                       ▼
                YOLO11 Detector
                       │
                       ▼
              Multi-Object Tracker
                       │
                       ▼
              Analytics Processing
         ┌─────────┬─────────┬─────────┐
         ▼         ▼         ▼         ▼
   Line Counter  Intrusion  Heatmap  Dwell Timer
         │
         ▼
    SQLite Database
         │
         ▼
      FastAPI API
         │
         ▼
  Streamlit Dashboard
```

---

# Features

- Real-time object detection
- Multi-object tracking
- Entry / Exit counting
- Intrusion detection
- Dwell time analytics
- Crowd density monitoring
- Heatmap visualization
- Event logging
- REST API
- Live dashboard
- Interactive calibration tool
- MJPEG live video feed
- CSV event export

---

# Project Structure

```text
VisionStream/
│
├── backend/
│   ├── analytics/
│   ├── api/
│   ├── config/
│   ├── detector/
│   ├── engine/
│   ├── schemas/
│   ├── services/
│   ├── tracker/
│   └── visualization/
│
├── dashboard/
├── models/
├── tools/
│   └── calibration/
├── requirements.txt
├── run.py
└── README.md
```

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/Ishan333444/Visionstream-main
cd VisionStream-main
```

## 2. Create the Python environment

VisionStream currently targets **Python 3.11**.

Using Conda:

```bash
conda create -n visionstream python=3.11
conda activate visionstream
```

## 3. Install VisionStream dependencies

The standard installation includes the PyTorch versions tested with VisionStream:

```bash
pip install -r requirements.txt
```

The current tested PyTorch stack is:

- PyTorch 2.14.1
- TorchVision 0.29.1
- TorchAudio 2.14.1

> **Hardware note:** the exact PyTorch wheel/build can depend on your hardware and operating system. The versions above are the versions used to test VisionStream. If you need a CUDA or ROCm-specific PyTorch build, install the appropriate hardware-specific build from the official PyTorch instructions before installing the remaining dependencies.

---

# Configuration

Runtime settings are located in:

```text
backend/config/settings.py
```

Important settings include:

```python
DEVICE = "auto"
CAMERA_SOURCE = 0
```

### Compute device

`DEVICE` supports:

- `auto` — use CUDA when available, otherwise CPU
- `cpu` — force CPU inference
- `cuda` — explicitly require a CUDA-compatible PyTorch device

For a portable installation:

```python
DEVICE = "auto"
```

The tested environment uses PyTorch 2.14.1 and supports CPU inference. With `auto`, VisionStream uses CUDA when the installed PyTorch build reports a CUDA-capable device; otherwise it falls back to CPU.

### Camera source

The default camera source is:

```python
CAMERA_SOURCE = 0
```

Change it if another camera index or supported OpenCV video source is required.

---

# Running VisionStream

Start the complete application with:

```bash
python run.py
```

The launcher starts:

- Vision Engine
- FastAPI Backend
- Streamlit Dashboard

The backend is checked for readiness before the dashboard is launched.

Once running:

```text
Backend API : http://127.0.0.1:8000
Dashboard   : http://localhost:8501
```

The FastAPI interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

The SQLite database is created automatically under:

```text
backend/data/visionstream.db
```

---

# Camera Calibration

Before using the system for the first time, or whenever the camera position changes:

```bash
python tools/calibration/calibrator.py
```

Calibration steps:

1. Press **SPACE** to freeze the frame.
2. Click **two points** to create the entry/exit line.
3. Click **three or more points** to create the intrusion zone.
4. Press **Enter** to save.

Calibration is stored in:

```text
backend/config/calibration.json
```

---

# Dashboard

The Streamlit dashboard provides:

- Live camera feed
- Current people count
- Entry / Exit statistics
- Intrusion monitoring
- Crowd density
- Heatmap visualization
- Event history
- CSV export

During startup, the dashboard waits for the VisionStream engine to become healthy before requesting analytics data.

---

# REST API

VisionStream exposes a REST API using FastAPI.

| Endpoint | Description |
|----------|-------------|
| `/` | API status |
| `/health` | Backend/engine health |
| `/stats` | Current statistics |
| `/analytics` | Analytics summary |
| `/events` | Recent events |
| `/video_feed` | MJPEG video stream |

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Technologies Used

- Python 3.11
- YOLO11 (Ultralytics)
- OpenCV
- FastAPI
- Streamlit
- SQLite
- NumPy
- Pandas
- Matplotlib
- SciPy
- ByteTrack

---

# Troubleshooting

### Camera does not open

Check:

```python
CAMERA_SOURCE = 0
```

in:

```text
backend/config/settings.py
```

Try another camera index if multiple cameras are connected.

### CUDA device error

If using:

```python
DEVICE = "cuda"
```

the installed PyTorch build must provide a compatible CUDA device.

For a CPU-only machine, use:

```python
DEVICE = "cpu"
```

or:

```python
DEVICE = "auto"
```

### Dashboard opens before analytics are available

This is expected during startup. The dashboard waits for the VisionStream engine to report a healthy state before requesting statistics and events.

### Database errors after manual changes

The database is initialized automatically when the FastAPI backend starts.

It can also be initialized manually:

```bash
python -m backend.services.init_db
```

---

# Future Improvements

- Multi-camera support
- Face recognition integration
- Alert notifications
- WebRTC streaming
- Person re-identification
- Role-based authentication
- Cloud deployment
- Docker support

---

# Author

**Ishan**

GitHub: https://github.com/coolknifer333444
