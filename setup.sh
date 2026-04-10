#!/bin/bash
# VisionGuard — Mac Setup & Run Script
# Run this once after cloning: bash setup.sh

set -e
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔══════════════════════════════════════╗"
echo "║   VisionGuard — Setup Script         ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── Check models ─────────────────────────────────────────────────────────────
echo "Checking models..."
if [ ! -f "models/ppe_detector.onnx" ] || [ ! -f "models/pose_detector.onnx" ]; then
    echo -e "${YELLOW}⚠️  Models not found in models/ folder${NC}"
    echo "Please unzip visionguard_models.zip:"
    echo "  unzip ~/Downloads/visionguard_models.zip -d models/"
    exit 1
fi
echo -e "${GREEN}✅ Models found${NC}"

# ── Create .env ───────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}📝 Created .env from template${NC}"
    echo ""
    echo "IMPORTANT: Edit .env and set your RTSP_URL:"
    echo "  nano .env"
    echo ""
    echo "Your CCTV RTSP URL is usually shown in the camera's mobile app."
    echo "Common format: rtsp://admin:password@192.168.x.x:554/stream"
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi

# ── Create __init__ files ─────────────────────────────────────────────────────
touch inference/__init__.py alerts/__init__.py api/__init__.py dashboard/__init__.py

# ── Build and start ───────────────────────────────────────────────────────────
echo ""
echo "Building Docker containers..."
docker-compose build

echo ""
echo "Starting all services..."
docker-compose up -d

echo ""
echo -e "${GREEN}✅ VisionGuard is running!${NC}"
echo ""
echo "┌─────────────────────────────────────────┐"
echo "│  Dashboard  →  http://localhost:8501     │"
echo "│  API        →  http://localhost:8000     │"
echo "│  API Docs   →  http://localhost:8000/docs│"
echo "│  Grafana    →  http://localhost:3000     │"
echo "│             →  admin / visionguard       │"
echo "│  Prometheus →  http://localhost:9090     │"
echo "└─────────────────────────────────────────┘"
echo ""
echo "To view logs:  docker-compose logs -f"
echo "To stop:       docker-compose down"
