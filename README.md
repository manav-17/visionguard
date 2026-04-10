# VisionGuard — Industrial Worker Safety Monitoring

> Real-time CV-based worker safety system with full edge deployment architecture
> M.Tech Data Science Project | Computer Vision + Architecture Deployment

---

##  Project Structure

```
visionguard/
├── models/                    ← ONNX models (from Colab)
│   ├── ppe_detector.onnx
│   ├── pose_detector.onnx
│   ├── class_map.json
│   ├── model_meta.yaml
│   └── fall_detection.py
├── inference/
│   ├── engine.py              ← Core CV pipeline
│   └── stream.py              ← RTSP stream reader
├── api/
│   └── main.py                ← FastAPI + WebSocket
├── alerts/
│   └── mqtt_publisher.py      ← MQTT alert publisher
├── dashboard/
│   └── app.py                 ← Streamlit live dashboard
├── deployment/
│   ├── mosquitto.conf         ← MQTT broker config
│   └── prometheus/
│       └── prometheus.yml     ← Metrics config
├── docker-compose.yml         ← All 5 containers
├── Dockerfile.api
├── Dockerfile.dashboard
├── requirements.api.txt
├── requirements.dashboard.txt
├── .env.example
└── setup.sh                   ← One-command setup
```

---

## Quick Start

### 1. Add models
```bash
unzip ~/Downloads/visionguard_models.zip -d models/
```

### 2. Configure CCTV
```bash
cp .env.example .env
# Edit RTSP_URL with your camera's stream URL
nano .env
```

### 3. Run everything
```bash
bash setup.sh
```

### 4. Open dashboard
```
http://localhost:8501
```

---

##  CV Pipeline

| Stage | Technology | Purpose |
|-------|-----------|---------|
| Frame ingestion | OpenCV RTSP | WiFi CCTV stream |
| PPE Detection | YOLOv8s (fine-tuned) | Helmet, vest, mask detection |
| Pose Estimation | YOLOv8-Pose | 17 keypoint fall detection |
| Tracking | ByteTrack | Persistent worker IDs |
| Hazard logic | Custom rules engine | Temporal alert filtering |
| Export | ONNX FP32 | Cross-platform inference |

**Detected hazards:**
- 🔴 No hardhat
- 🔴 No safety vest
- 🔴 No mask
- 🔴 Worker fall (pose-based)
- 🟡 Vehicle/machinery proximity
- 🟡 Safety cone zone breach

---

## Deployment Architecture

| Container | Technology | Port |
|-----------|-----------|------|
| Inference + API | FastAPI + ONNX Runtime | 8000 |
| Live Dashboard | Streamlit | 8501 |
| Alert Broker | MQTT Mosquitto | 1883 |

---

##  API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service status |
| `/status` | GET | Stream + inference stats |
| `/alerts` | GET | Recent alert history |
| `/detections` | GET | Current frame detections |
| `/snapshot` | GET | Latest annotated frame (base64) |
| `/metrics` | GET | Prometheus metrics |
| `/ws` | WS | Real-time frame + alert stream |
| `/docs` | GET | Interactive API docs |

---

##  Academic Reference

**Title:** A Unified Multi-Hazard Detection Architecture for Industrial Safety Monitoring on Edge Devices

**Models:**
- Jocher et al., *YOLOv8*, Ultralytics, 2023
- Zhang et al., *ByteTrack*, ECCV 2022
- Dataset: Construction Site Safety, Roboflow Universe

**Training results:**
- mAP50: 0.761
- Precision: 0.848
- Recall: 0.677
- Inference: ~6ms/frame

---

##  Troubleshooting

**Stream not connecting:**
```bash
# Test RTSP URL directly
ffplay rtsp://admin:password@192.168.1.100:554/stream

# Or use webcam for testing
RTSP_URL=0 docker-compose up
```

**View logs:**
```bash
docker-compose logs -f api
docker-compose logs -f dashboard
```

**Rebuild after code changes:**
```bash
docker-compose up --build
```
