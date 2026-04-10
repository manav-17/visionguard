"""
VisionGuard — MQTT Alert Publisher
Publishes hazard alerts to Mosquitto broker
"""
import json
import os
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("⚠️  paho-mqtt not installed — MQTT alerts disabled")


class MQTTPublisher:
    def __init__(self):
        self.host      = os.getenv("MQTT_HOST", "localhost")
        self.port      = int(os.getenv("MQTT_PORT", "1883"))
        self.client    = None
        self.connected = False
        self.topic_base = "visionguard/alerts"

    def connect(self):
        if not MQTT_AVAILABLE:
            return
        try:
            self.client = mqtt.Client(client_id="visionguard_api")
            self.client.on_connect    = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.connect_async(self.host, self.port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"⚠️  MQTT connection failed: {e}")

    def disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()

    def publish_alert(self, alert: dict):
        if not self.connected or not self.client:
            return
        alert_type = alert.get("type", "unknown")
        topic      = f"{self.topic_base}/{alert_type}"
        payload    = json.dumps({
            **alert,
            "timestamp": datetime.now().isoformat(),
            "source"   : "visionguard",
        })
        self.client.publish(topic, payload, qos=1)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print(f"✅ MQTT connected to {self.host}:{self.port}")
        else:
            print(f"⚠️  MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            print("⚠️  MQTT unexpectedly disconnected")
