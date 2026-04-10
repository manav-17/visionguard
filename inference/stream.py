"""
VisionGuard — RTSP Stream Reader
Reads frames from WiFi CCTV and feeds to inference engine
"""
import cv2
import threading
import time
import numpy as np
from pathlib import Path


class RTSPStream:
    """
    Thread-safe RTSP stream reader.
    Drops stale frames — always returns the latest frame.
    """
    def __init__(self, source: str, reconnect_delay: int = 5):
        self.source          = source
        self.reconnect_delay = reconnect_delay
        self.frame           = None
        self.running         = False
        self.connected       = False
        self.fps             = 0
        self._lock           = threading.Lock()
        self._thread         = None

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        # Wait up to 10s for first frame
        for _ in range(100):
            if self.frame is not None:
                return True
            time.sleep(0.1)
        return False

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)

    def read(self):
        with self._lock:
            return self.frame.copy() if self.frame is not None else None

    def _read_loop(self):
        while self.running:
            cap = cv2.VideoCapture(self.source)
            if not cap.isOpened():
                print(f"⚠️  Cannot open stream: {self.source}")
                print(f"   Retrying in {self.reconnect_delay}s...")
                time.sleep(self.reconnect_delay)
                continue

            self.connected = True
            self.fps       = cap.get(cv2.CAP_PROP_FPS) or 25
            print(f"✅ Stream connected: {self.source} @ {self.fps:.0f} FPS")

            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("⚠️  Stream dropped — reconnecting...")
                    self.connected = False
                    break
                with self._lock:
                    self.frame = frame

            cap.release()
            if self.running:
                time.sleep(self.reconnect_delay)

    @property
    def is_connected(self):
        return self.connected


def get_stream(source: str = None) -> RTSPStream:
    """
    Returns configured stream.
    source examples:
      - "rtsp://admin:password@192.168.1.100:554/stream"
      - "rtsp://192.168.1.100:554/live"
      - 0  (webcam fallback)
      - "sample.mp4" (video file for testing)
    """
    import os
    if source is None:
        source = os.getenv("RTSP_URL", "0")

    # Convert "0" string to int for webcam
    if source == "0":
        source = 0
        print("📷 Using webcam (device 0)")
    else:
        print(f"📡 Connecting to RTSP stream: {source}")

    return RTSPStream(source)
