# 🛡️ IBVAP — Intelligent Border Video Analytics Platform

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00ffff.svg?style=for-the-badge&logo=yolo&logoColor=white)](https://github.com/ultralytics/ultralytics)
[![ByteTrack](https://img.shields.io/badge/ByteTrack-Multi--Object_Tracking-ff0055.svg?style=for-the-badge)](https://github.com/ifzhang/ByteTrack)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-646CFF.svg?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-06B6D4.svg?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

<br/>

> **"We are not replacing the operator. We are reducing the video they need to watch."**

*A defense-grade, software-defined computer vision surveillance platform that retrofits legacy CCTV, RTSP streams, and field smartphones with real-time AI perimeter security analytics without requiring camera hardware replacement.*

</div>

---

## 📋 Table of Contents
1. [Executive Summary & Problem Statement](#-executive-summary--problem-statement)
2. [Core Capabilities & Features](#-core-capabilities--features)
3. [System Architecture](#-system-architecture)
4. [Technology Stack](#-technology-stack)
5. [Directory Structure](#-directory-structure)
6. [Quick Start Guide](#-quick-start-guide)
7. [Smartphone Camera Field Prototyping](#-smartphone-camera-field-prototyping)
8. [Interactive Restricted Zone & Virtual Fence Editor](#-interactive-restricted-zone--virtual-fence-editor)
9. [Demonstrated Surveillance Scenarios](#-demonstrated-surveillance-scenarios)
10. [REST API & WebSocket Specifications](#-rest-api--websocket-specifications)
11. [Hardware Requirements & Benchmarks](#-hardware-requirements--benchmarks)
12. [Future Roadmap](#-future-roadmap)
13. [License & Ethical Use](#-license--ethical-use)

---

## 🎯 Executive Summary & Problem Statement

### The Problem with Traditional Border & Perimeter CCTV
* **Human Operator Fatigue:** Human attention drops significantly after just 20 minutes of watching multiple static video monitors.
* **Cost of Hardware Replacement:** Upgrading thousands of legacy analog or basic RTSP/IP cameras to proprietary "smart" AI cameras requires millions of dollars in capital expenditure and cabling.
* **Network & Cloud Latency:** Streaming raw 4K/1080p video feeds to centralized cloud servers consumes massive bandwidth and introduces unacceptable alert delays in mission-critical perimeter defense.

### The IBVAP Solution
**IBVAP (Intelligent Border Video Analytics Platform)** is an edge-first, vendor-agnostic software layer that connects to standard RTSP, ONVIF, HTTP, or USB video feeds. It performs on-premise AI inference, automated tracking, security rule checks, and instant telemetry broadcast — turning any conventional camera into an autonomous security sensor.

```
+---------------------+      RTSP / HTTP Feed      +-----------------------------------------+
| Legacy CCTV /       | -------------------------> | IBVAP Edge Surveillance Engine          |
| Smartphone Camera   |                            |  - YOLOv8 Object Detection              |
+---------------------+                            |  - ByteTrack Multi-Object Tracking      |
                                                   |  - Polygon Intrusion & Virtual Tripwire |
                                                   |  - ANPR License Plate Extraction        |
                                                   +--------------------+--------------------+
                                                                        | WebSocket Alerts
                                                                        v
                                                   +-----------------------------------------+
                                                   | Tactical Real-Time Cyber Dashboard      |
                                                   +-----------------------------------------+
```

---

## ⚡ Core Capabilities & Features

### 1. Multi-Class Edge Detection & Tracking
* **YOLOv8 Real-Time Inference:** High-accuracy detection of tactical targets: `person`, `car`, `motorcycle`, `bus`, `truck`.
* **ByteTrack Multi-Object Tracking:** Assigns persistent, non-drifting track IDs across occlusion, lighting changes, and camera motion.
* **Motion-Triggered Edge Conservation:** Built-in MOG2 background subtractor filters static frames to reduce CPU/GPU power consumption on edge nodes.

### 2. Spatial Security Rule Engine
* **Convex & Concave Polygon Zones:** Interactive restricted sectors defined by arbitrary multi-vertex polygons.
* **Virtual Tripwires / Fences:** Directional tripwires detecting crossing events via 2D vector ray-casting and segment intersection.
* **Loitering & Dwell Timers:** Tracks duration spent by targets inside sensitive zones with configurable dwell thresholds.
* **Prohibited Direction Detection:** Computes displacement vectors to identify targets moving against authorized traffic flow.

### 3. Dynamic Resolution Scaling Engine
* **Resolution-Independent Calibration:** Draw boundary zones on a standardized responsive UI canvas; the backend mathematically maps and scales all vertices to match the camera's native sensor resolution (`1920×1080`, `1280×720`, `4K`, etc.).

### 4. Automatic Number Plate Recognition (ANPR)
* **Vehicle Crop & Contrast Enhancement:** Automatically isolates candidate vehicle bounding boxes.
* **EasyOCR Deep Learning Engine:** Reads alphanumeric license plates in challenging environmental conditions with confidence scoring.

### 5. Tactical Command Dashboard
* **Glassmorphism Defense HUD:** Built with React 18, Vite, and Tailwind CSS.
* **Sub-Second WebSocket Telemetry:** Live alerts, trajectory history, and live telemetry push updates without polling.
* **Evidence Snapshot Storage:** Automatic capture and preservation of full-resolution violation frames with HUD overlays.
* **Dynamic Source Hot-Swapping:** Switch between smartphone Wi-Fi feeds, local webcams, and synthetic video loops in real time without restarting the platform.

---

## 🏗️ System Architecture

```
                                  +-----------------------------+
                                  |   Smartphone IP Camera /    |
                                  |     Standard CCTV RTSP      |
                                  +--------------+--------------+
                                                 | RTSP / HTTP Video Stream
                                                 v
+-----------------------------------------------------------------------------------------------+
| LAPTOP / EDGE NODE                                                                            |
|                                                                                               |
|  +-----------------------------------------------------------------------------------------+  |
|  | 1. Video Ingestion Layer (backend/camera/capture.py)                                    |  |
|  |    - Threaded buffer-drained capture (eliminates RTSP network latency lag)              |  |
|  |    - Dynamic source switching (Smartphone RTSP | Webcam | Demo Video Loop)               |  |
|  |    - Optional CLAHE contrast enhancement (backend/ai/lowlight.py)                       |  |
|  +-------------------------------------+---------------------------------------------------+  |
|                                        | Frame (BGR)                                          |
|                                        v                                                      |
|  +-----------------------------------------------------------------------------------------+  |
|  | 2. Lightweight Edge Activity Detector (backend/camera/motion.py)                        |  |
|  |    - Background Subtraction (MOG2) & contour area thresholding                          |  |
|  |    - Bypasses inference during idle static scenes to conserve compute                   |  |
|  +-------------------------------------+---------------------------------------------------+  |
|                                        | Active Motion Frame                                  |
|                                        v                                                      |
|  +-----------------------------------------------------------------------------------------+  |
|  | 3. Central Event Queue (backend/services/queue.py)                                      |  |
|  |    - Dual Driver: Redis Queue (Primary) <-> High-Performance In-Memory Buffer (Fallback) |  |
|  +-------------------------------------+---------------------------------------------------+  |
|                                        | Queued Event                                         |
|                                        v                                                      |
|  +-----------------------------------------------------------------------------------------+  |
|  | 4. AI Analytics Pipeline (backend/ai/)                                                  |  |
|  |    - Object Detector: YOLOv8n (person, car, motorcycle, bus, truck)                     |  |
|  |    - Multi-Object Tracker: ByteTrack (stable track IDs, trajectories)                   |  |
|  |    - Security Rule Engine:                                                              |  |
|  |        * Virtual Fence Crossing (Ray-casting / line-segment intersection)               |  |
|  |        * Restricted Polygon Intrusion (Point-in-polygon verification)                   |  |
|  |        * Dwell / Loitering Timer (dwell_time > threshold)                               |  |
|  |        * Prohibited Direction Detection (movement displacement vectors)                 |  |
|  |    - ANPR Module: Vehicle Crop -> EasyOCR -> Confidence calibration                     |  |
|  +-------------------------------------+---------------------------------------------------+  |
|                                        | Alerts & Annotated Frames                            |
|                                        v                                                      |
|  +-----------------------------------------------------------------------------------------+  |
|  | 5. Platform Core & Storage (backend/alerts/, backend/database/)                         |  |
|  |    - Alert Engine: Severity grading (LOW, MEDIUM, HIGH, CRITICAL)                       |  |
|  |    - Evidence Storage: Saves full-frame violation snapshots (data/snapshots/)            |  |
|  |    - Database: SQLite (SQLAlchemy models: cameras, zones, events, alerts)               |  |
|  |    - FastAPI REST Server & WebSocket Broadcaster (Sub-second push)                      |  |
|  |    - MJPEG Streamer: Annotated real-time live feed with HUD overlays                    |  |
|  +-------------------------------------+---------------------------------------------------+  |
+----------------------------------------|------------------------------------------------------+
                                         | REST / WebSockets / MJPEG Stream
                                         v
+-----------------------------------------------------------------------------------------------+
| TACTICAL CLIENT DASHBOARD (frontend/)                                                         |
|  - React 18 + Vite + Tailwind CSS dark surveillance interface                                 |
|  - Live Monitor with real-time bounding boxes, track IDs, and zone overlays                   |
|  - Active Alerts Console with instant audio-visual flash and snapshot evidence                |
|  - Interactive Zone Configurator (Polygon boundaries, dwell thresholds)                      |
|  - Historical Audit Trail with CSV export and incident filtering                             |
+-----------------------------------------------------------------------------------------------+
```

---

## 💻 Technology Stack

| Domain | Technology / Library | Purpose |
|---|---|---|
| **Deep Learning** | `YOLOv8n` (Ultralytics) | Real-time object detection & categorization |
| **Object Tracking** | `ByteTrack` / `Supervision` | Multi-target trajectory analysis and persistent IDs |
| **Optical Recognition**| `EasyOCR` + `PyTorch` | Edge-optimized automatic number plate recognition |
| **Computer Vision** | `OpenCV (cv2)` | Frame decoding, spatial geometry, CLAHE contrast |
| **Backend API** | `FastAPI` + `Uvicorn` | Asynchronous REST endpoints & MJPEG multipart stream |
| **Real-Time Push** | Native WebSockets | Telemetry and alert broadcast engine |
| **Database** | `SQLite` + `SQLAlchemy` | Structured storage for zones, events, and audit logs |
| **Event Bus** | In-Memory / `Redis` | Resilient pub/sub event pipeline |
| **Frontend UI** | `React 18` + `Vite` | Component-driven reactive dashboard |
| **Styling & HUD** | `TailwindCSS` + `Lucide React` | Cyberpunk/defense surveillance aesthetic |

---

## 📂 Directory Structure

```
IBVAP/
├── .env                        # Active runtime configuration
├── .env.example                # Configuration template
├── requirements.txt            # Python edge dependencies
├── run_demo.py                 # Single-command launcher (Backend + Frontend)
├── test_camera.py              # Standalone camera & motion verification utility
├── generate_demo_video.py      # Generates synthetic CCTV border demo video
├── README.md                   # System documentation & setup guide
│
├── backend/
│   ├── main.py                 # FastAPI application & startup lifecycle
│   ├── config.py               # Pydantic BaseSettings environment loader
│   ├── api/                    # REST routes (cameras, zones, alerts, events, stream)
│   │   ├── routes_cameras.py   # Camera status and source switching endpoints
│   │   ├── routes_zones.py     # Zone CRUD and in-memory reload endpoints
│   │   ├── routes_alerts.py    # Alert querying and manual acknowledgment
│   │   ├── routes_events.py    # Event audit logs and statistical aggregation
│   │   └── routes_stream.py    # Real-time MJPEG live feed and raw snapshot feeds
│   ├── ai/
│   │   ├── detector.py         # YOLOv8n object detection engine
│   │   ├── tracker.py          # ByteTrack multi-object tracking
│   │   ├── rules.py            # Polygon intrusion, tripwire & loitering rules
│   │   ├── anpr.py             # Vehicle license plate extraction & OCR
│   │   ├── lowlight.py         # CLAHE contrast enhancement preprocessor
│   │   └── face.py             # Architectural interface for future face recognition
│   ├── camera/
│   │   ├── capture.py          # Threaded OpenCV capture with auto-reconnect
│   │   └── motion.py           # Lightweight MOG2 edge motion filter
│   ├── alerts/
│   │   └── engine.py           # Alert synthesis, snapshot persistence & DB logging
│   ├── database/
│   │   ├── session.py          # SQLAlchemy SQLite connection & sessionmaker
│   │   └── models.py           # Camera, Zone, Event, Alert DB models
│   ├── services/
│   │   ├── queue.py            # Dual-driver Redis / In-Memory Event Queue
│   │   └── pipeline.py         # Master orchestrator joining capture, AI, rules & stream
│   └── websocket/
│       └── manager.py          # Real-time WebSocket connection manager
│
├── frontend/
│   ├── package.json            # React & Tailwind dependencies
│   ├── vite.config.js          # Vite bundler configuration
│   ├── tailwind.config.js      # Surveillance tactical dark theme
│   └── src/
│       ├── App.jsx             # Main dashboard shell & WebSocket listener
│       ├── components/         # Header, Sidebar, MetricsGrid, LiveFeed, AlertsCard
│       ├── pages/              # Dashboard, LiveMonitor, Alerts, EventHistory, Cameras, Zones
│       └── services/           # REST API & auto-reconnecting WebSocket client
│
└── data/
    ├── snapshots/              # Stored violation snapshot images
    ├── demo_videos/            # Sample border CCTV video loops
    └── ibvap.db                # SQLite audit database
```

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python:** `3.10` or higher
* **Node.js:** `18.x` or higher
* **Git** installed on system

### Step 1: Clone Repository
```powershell
git clone https://github.com/your-username/IBVAP.git
cd IBVAP
```

### Step 2: Set Up Python Virtual Environment
```powershell
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### Step 3: Set Up Frontend
```powershell
cd frontend
npm install
cd ..
```

### Step 4: Configure Environment
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
*(Default settings use webcam index `0` and an in-memory queue, requiring zero external services to run).*

### Step 5: Launch IBVAP
Run the unified system launcher:
```powershell
python run_demo.py
```
This starts both the FastAPI backend (`http://localhost:8000`) and the Vite React frontend (`http://localhost:5173`).

---

## 📱 Smartphone Camera Field Prototyping

IBVAP is designed to treat any smartphone camera as a professional CCTV/RTSP source.

### Android Setup:
1. Connect your smartphone and laptop to the **same Wi-Fi network** (or connect your laptop to your phone's Wi-Fi hotspot).
2. Install **IP Webcam** (by Pavel Khlebovich) from Google Play.
3. Open the app, scroll to the bottom, and tap **"Start server"**.
4. Note the IP displayed on your phone (e.g. `http://192.168.1.50:8080`).
5. Open the IBVAP web dashboard (`http://localhost:5173`), click **"CHANGE SOURCE"**, and enter:
   ```
   http://192.168.1.50:8080/video
   ```
   or RTSP stream:
   ```
   rtsp://192.168.1.50:8080/h264_pcm.sdp
   ```
6. Click **"Apply Source"** — the live feed updates instantly with real-time AI analytics.

### iOS (iPhone) Setup:
1. Install **Live-Reporter** or **IP Camera Lite** from the App Store.
2. Start the RTSP or HTTP stream.
3. Enter the provided RTSP address into the IBVAP source switcher modal.

---

## 🗺️ Interactive Restricted Zone & Virtual Fence Editor

IBVAP features an in-browser spatial boundary editor:

1. Navigate to the **Zones** tab on the navigation bar.
2. Click **"CREATE NEW ZONE"** or select an existing zone.
3. Click **"START DRAWING"** and click on your camera feed to define the boundary:
   * **Polygon:** Click 3 or 4 points enclosing the forbidden sector (doorway, perimeter fence, restricted road).
   * **Virtual Fence / Tripwire:** Click 2 points to draw a tripwire line.
4. Set rule parameters:
   * **Zone Name:** Custom sector tag (e.g., `North Perimeter Gate`).
   * **Dwell Limit (Sec):** Minimum time a target can remain before triggering a Loitering Alert.
   * **Overlay Color:** Visual hex code for tactical HUD rendering.
5. Click **"SAVE & APPLY TO AI ENGINE"**.
6. The boundary is instantly active on the AI engine — no system restart required!

---

## 🎬 Demonstrated Surveillance Scenarios

### Scenario 1: Perimeter Intrusion
* Target approaches an unauthorized border sector.
* YOLOv8 detects the target (`person`, confidence > 0.50).
* ByteTrack assigns a persistent track ID (e.g., `PERSON #137`).
* As the target enters the configured polygon, a **CRITICAL Intrusion Alert** is generated.
* A high-resolution evidence snapshot is saved with bounding box and trajectory overlays.

### Scenario 2: Loitering & Suspicious Activity
* Target remains stationary or paces inside a restricted sector for longer than the configured threshold (e.g., > 1.0s).
* The dwell timer triggers a **HIGH Severity Loitering Alert** displaying exact loitering duration.

### Scenario 3: ANPR Vehicle Checkpoint
* A vehicle enters the camera view.
* The system crops the vehicle region, applies CLAHE contrast optimization, and executes EasyOCR.
* The vehicle's license plate number and confidence score are displayed in the HUD and logged to the SQLite audit database.

---

## 🔌 REST API & WebSocket Specifications

### REST Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health check and uptime status |
| `GET` | `/api/v1/cameras/` | List all configured camera streams and status |
| `PUT` | `/api/v1/cameras/{id}/source` | Hot-swap camera source (RTSP / HTTP / Webcam) |
| `GET` | `/api/v1/zones/` | Retrieve all active detection zones |
| `POST`| `/api/v1/zones/` | Create or update a detection zone |
| `DELETE`| `/api/v1/zones/{id}` | Delete a detection zone |
| `GET` | `/api/v1/alerts/` | Retrieve recent alerts with pagination and filters |
| `PUT` | `/api/v1/alerts/{id}/ack` | Acknowledge an active security alert |
| `GET` | `/api/v1/events/` | Audit trail of all detections and intrusions |
| `GET` | `/api/v1/events/stats` | Aggregated 24-hour tactical statistics |
| `GET` | `/api/v1/stream/video_feed` | Live MJPEG stream with AI HUD overlays |
| `GET` | `/api/v1/stream/snapshot/raw` | Clean, unannotated camera snapshot |

### WebSocket Telemetry (`ws://localhost:8000/ws`)
Subscribers receive real-time JSON frames:
```json
{
  "type": "NEW_ALERT",
  "data": {
    "alert_id": "ALT-7B0289E6",
    "event_type": "LOITERING",
    "severity": "HIGH",
    "camera_id": "CAM-01",
    "zone_name": "Custom Border Sector",
    "object_type": "person",
    "track_id": 137,
    "confidence": 0.86,
    "description": "Person #137 remained in Custom Border Sector for 1.1s",
    "snapshot_url": "/data/snapshots/ALT-7B0289E6_1788984165.jpg",
    "timestamp": 1788984165.0
  }
}
```

---

## ⚙️ Hardware Requirements & Benchmarks

| Hardware Profile | Resolution | Inference Engine | Edge FPS |
|---|---|---|---|
| **Standard Laptop (Intel i5/i7, CPU Only)** | 1080p (1920×1080) | YOLOv8n (PyTorch CPU) | ~15 – 22 FPS |
| **Edge GPU (NVIDIA GTX 1650 / RTX 3050)** | 1080p (1920×1080) | YOLOv8n (CUDA) | ~45 – 60 FPS |
| **Embedded Edge (Jetson Orin Nano)** | 1080p (1920×1080) | TensorRT FP16 | ~35 – 45 FPS |

---

## 🔮 Future Roadmap

- [ ] **Multi-Camera PTZ Tracking:** Hand-off tracking between adjacent cameras across large border zones.
- [ ] **Thermal / IR Sensor Ingestion:** Support for FLIR and long-wave infrared sensors for complete zero-light nighttime detection.
- [ ] **Edge Drone Ingestion:** Stream direct RTSP telemetry from airborne patrol UAVs.
- [ ] **Facial Recognition Watchlist:** Vector-embedding matching against law-enforcement databases.

---

## 📄 License & Ethical Use

This project is licensed under the **MIT License**.

> **Ethical Surveillance Statement:** IBVAP is engineered for perimeter protection, infrastructure security, and border preservation. Users are responsible for adhering to applicable regional and international privacy regulations regarding video surveillance and automated data collection.
