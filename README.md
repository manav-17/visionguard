# VisionGuard — Industrial Worker Safety Monitoring System

> Real-time CV-based worker safety system with full edge deployment architecture  
> M.Tech Data Science Project | Computer Vision + Architecture Deployment

![Python](https://img.shields.io/badge/Python-3.12-blue)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-green)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-teal)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Problem Statement

Every year, 1000+ workers die in Indian factories from preventable accidents.
Helmet violations, falls, and zone breaches go undetected in real time.
VisionGuard solves this with an open-source, edge-deployed AI safety system.

---

##  Project Structure
```
visionguard/
├── VisionGuard_Training.ipynb  ← Colab training notebook
├── models/                        ← ONNX models (from Colab)
│   ├── ppe_detector.onnx
│   ├── pose_detector.onnx
│   ├── class_map.json
│   ├── model_meta.yaml
│   └── fall_detection.py
├── inference/
│   ├── engine.py                  ← Core CV pipeline
│   └── stream.py                  ← RTSP stream reader
├── api/
│   └── main.py                    ← FastAPI + WebSocket
├── alerts/
│   └── mqtt_publisher.py          ← MQTT alert publisher
├── dashboard/
│   └── app.py                     ← Streamlit live dashboard
├── deployment/
│   └── mosquitto.conf             ← MQTT broker config
├── docker-compose.yml             ← 3 containers
├── Dockerfile.api
├── Dockerfile.dashboard
├── requirements.api.txt
├── requirements.dashboard.txt
├── .env.example
└── run.sh                         ← One command startup

---

##  Quick Start

### 1. Add models
```bash
unzip ~/Downloads/visionguard_models.zip -d models/
```

### 2. Configure camera
```bash
cp .env.example .env
# Edit RTSP_URL — use 0 for webcam
nano .env
```

### 3. Run everything
```bash
bash run.sh
```

### 4. Open dashboard
http://localhost:8501

---

## CV Pipeline

| Stage | Technology | Purpose |
|-------|-----------|---------|
| Frame ingestion | OpenCV RTSP | WiFi CCTV / webcam stream |
| PPE Detection | YOLOv8s (fine-tuned) | Helmet, vest, mask detection |
| Pose Estimation | YOLOv8-Pose | 17 keypoint fall detection |
| Tracking | ByteTrack | Persistent worker IDs |
| Hazard logic | Custom rules engine | Temporal alert filtering |
| Export | ONNX FP32 | Cross-platform edge inference |

**Detected hazards:**
- 🔴 No hardhat
- 🔴 No safety vest
- 🔴 Worker fall (pose-based)
- 🟡 Vehicle/machinery proximity

---

##  Model Results

| Metric | Score |
|--------|-------|
| mAP50 | **0.782** |
| Precision | **0.917** |
| Recall | 0.701 |
| Inference Speed | ~334ms CPU |
| Training Epochs | 50 |
| Dataset | 2605 images, 10 classes |

---

##  Deployment Architecture

| Container | Technology | Port |
|-----------|-----------|------|
| Inference + API | FastAPI + ONNX Runtime | 8000 |
| Live Dashboard | Streamlit | 8501 |
| Alert Broker | MQTT Mosquitto | 1883 |

---

##  API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service health check |
| `/status` | GET | Stream + inference stats |
| `/alerts` | GET | Alert history with timestamps |
| `/detections` | GET | Current frame detections |
| `/snapshot` | GET | Latest annotated frame (base64) |
| `/ws` | WS | Real-time frame + alert streaming |
| `/docs` | GET | Interactive Swagger UI |

---

## Academic Reference

**Title:** A Unified Multi-Hazard Detection Architecture for Industrial Safety Monitoring on Edge Devices

**Models:**
- Jocher et al., *YOLOv8*, Ultralytics, 2023
- Zhang et al., *ByteTrack*, ECCV 2022
- Dataset: Construction Site Safety, Roboflow Universe

---

##  Troubleshooting

**Webcam not working in Docker:**
```bash
# Run API locally instead
RTSP_URL=0 MQTT_HOST=localhost python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Run dashboard locally:**
```bash
streamlit run dashboard/app.py
```

**View logs:**
```bash
docker-compose logs -f
```

**Rebuild after code changes:**
```bash
docker-compose up --build
```

