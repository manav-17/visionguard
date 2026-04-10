"""
VisionGuard — FastAPI Backend
REST API + WebSocket for real-time alerts and stream
"""
import asyncio
import base64
import json
import time
from collections import deque
from datetime import datetime
from typing import List

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import threading
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from inference.engine import run_inference
from inference.stream import get_stream
from alerts.mqtt_publisher import MQTTPublisher

app = FastAPI(
    title       = "VisionGuard API",
    description = "Industrial Worker Safety Monitoring",
    version     = "1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

alert_history: deque        = deque(maxlen=100)
latest_result: dict         = {}
stream                      = None
mqtt                        = None
ws_clients: List[WebSocket] = []
processing                  = False
frame_count                 = 0

@app.on_event("startup")
async def startup():
    global stream, mqtt, processing
    print("🚀 Starting VisionGuard API...")
    mqtt = MQTTPublisher()
    mqtt.connect()
    stream    = get_stream()
    connected = stream.start()
    if not connected:
        print("⚠️  Stream not available — will retry automatically")
    processing = True
    thread = threading.Thread(target=inference_loop, daemon=True)
    thread.start()
    print("✅ VisionGuard API ready")

@app.on_event("shutdown")
async def shutdown():
    global processing
    processing = False
    if stream: stream.stop()
    if mqtt:   mqtt.disconnect()

def inference_loop():
    global latest_result, frame_count
    frame_interval = 1.0 / 15
    while processing:
        t0    = time.time()
        frame = stream.read() if stream else None
        if frame is None:
            time.sleep(0.1)
            continue
        try:
            result        = run_inference(frame)
            latest_result = result
            frame_count  += 1
            for alert in result["alerts"]:
                alert["timestamp"] = datetime.now().isoformat()
                alert_history.appendleft(alert)
                if mqtt: mqtt.publish_alert(alert)
                asyncio.run(broadcast_alert(alert))
        except Exception as e:
            print(f"Inference error: {e}")
        elapsed = time.time() - t0
        if frame_interval - elapsed > 0:
            time.sleep(frame_interval - elapsed)

async def broadcast_alert(alert: dict):
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_text(json.dumps({"type": "alert", "data": alert}))
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.remove(ws)

@app.get("/")
def root():
    return {"service": "VisionGuard", "status": "running",
            "stream": stream.is_connected if stream else False}

@app.get("/status")
def status():
    return {
        "stream_connected"  : stream.is_connected if stream else False,
        "frames_processed"  : frame_count,
        "total_alerts"      : len(alert_history),
        "last_inference_ms" : latest_result.get("inference_ms", 0),
    }

@app.get("/alerts")
def get_alerts(limit: int = 20):
    return {"alerts": list(alert_history)[:limit]}

@app.get("/detections")
def get_detections():
    if not latest_result:
        return {"detections": [], "poses": []}
    return {
        "detections"   : latest_result.get("detections", []),
        "poses"        : [{k: v for k, v in p.items() if k != "keypoints"}
                          for p in latest_result.get("poses", [])],
        "inference_ms" : latest_result.get("inference_ms", 0),
    }

@app.get("/snapshot")
def snapshot():
    if not latest_result or "annotated_frame" not in latest_result:
        return JSONResponse({"error": "No frame available"}, status_code=503)
    _, buf  = cv2.imencode(".jpg", latest_result["annotated_frame"],
                           [cv2.IMWRITE_JPEG_QUALITY, 85])
    img_b64 = base64.b64encode(buf).decode()
    return {"image": f"data:image/jpeg;base64,{img_b64}"}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.append(ws)
    try:
        while True:
            await asyncio.sleep(0.1)
            if latest_result and "annotated_frame" in latest_result:
                _, buf  = cv2.imencode(".jpg", latest_result["annotated_frame"],
                                       [cv2.IMWRITE_JPEG_QUALITY, 70])
                img_b64 = base64.b64encode(buf).decode()
                await ws.send_text(json.dumps({
                    "type"         : "frame",
                    "image"        : f"data:image/jpeg;base64,{img_b64}",
                    "alerts"       : latest_result.get("alerts", []),
                    "inference_ms" : latest_result.get("inference_ms", 0),
                }))
    except WebSocketDisconnect:
        ws_clients.remove(ws)
