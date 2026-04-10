#!/bin/bash
# VisionGuard — One Command Startup
# Run: bash run.sh

set -e
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔══════════════════════════════════════╗"
echo "║      VisionGuard — Starting...       ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── Check models ─────────────────────────────────────────────────────────────
if [ ! -f "models/ppe_detector.onnx" ] || [ ! -f "models/pose_detector.onnx" ]; then
    echo -e "${RED}❌ Models not found in models/ folder${NC}"
    echo "Run: unzip ~/Downloads/visionguard_models.zip -d models/"
    exit 1
fi
echo -e "${GREEN}✅ Models found${NC}"

# ── Check Docker ──────────────────────────────────────────────────────────────
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Desktop is not running${NC}"
    echo "Please open Docker Desktop first"
    exit 1
fi
echo -e "${GREEN}✅ Docker running${NC}"

# ── Start MQTT via Docker ─────────────────────────────────────────────────────
echo "Starting MQTT broker..."
docker-compose up -d mqtt
echo -e "${GREEN}✅ MQTT broker started${NC}"

# ── Install dependencies if needed ───────────────────────────────────────────
echo "Checking Python dependencies..."
pip install fastapi uvicorn opencv-python numpy "onnxruntime>=1.24.1" \
    paho-mqtt pyyaml websockets python-multipart streamlit requests \
    websocket-client -q
echo -e "${GREEN}✅ Dependencies ready${NC}"

# ── Start API in background ───────────────────────────────────────────────────
echo "Starting inference API..."
RTSP_URL=0 MQTT_HOST=localhost python -m uvicorn api.main:app \
    --host 0.0.0.0 --port 8000 &
API_PID=$!
echo -e "${GREEN}✅ API starting (PID: $API_PID)${NC}"

# ── Wait for API to be ready ──────────────────────────────────────────────────
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is ready!${NC}"
        break
    fi
    sleep 1
done

# ── Start Dashboard ───────────────────────────────────────────────────────────
echo "Starting dashboard..."
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ VisionGuard is fully running!        ║${NC}"
echo -e "${GREEN}║                                          ║${NC}"
echo -e "${GREEN}║  Dashboard → http://localhost:8501       ║${NC}"
echo -e "${GREEN}║  API Docs  → http://localhost:8000/docs  ║${NC}"
echo -e "${GREEN}║                                          ║${NC}"
echo -e "${GREEN}║  Press Ctrl+C to stop everything        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Open browser automatically
sleep 2
open http://localhost:8501

# Run dashboard (this stays in foreground)
streamlit run dashboard/app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false

# ── Cleanup on exit ───────────────────────────────────────────────────────────
echo ""
echo "Shutting down..."
kill $API_PID 2>/dev/null
docker-compose stop mqtt 2>/dev/null
echo "✅ VisionGuard stopped"
