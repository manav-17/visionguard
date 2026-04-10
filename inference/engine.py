import cv2
import numpy as np
import onnxruntime as ort
import yaml, json, time
from pathlib import Path
from collections import defaultdict

#Load config
BASE_DIR   = Path(__file__).parent.parent
MODEL_DIR  = BASE_DIR / "models"

with open(MODEL_DIR / "class_map.json") as f:
    CLASS_MAP = json.load(f)
with open(MODEL_DIR / "model_meta.yaml") as f:
    META = yaml.safe_load(f)

NAMES         = CLASS_MAP["names"]
ALERT_CLASSES = set(CLASS_MAP["alert_classes"])
HAZARD_RULES  = META["hazard_rules"]
ALERT_FRAMES  = HAZARD_RULES["alert_frame_window"]   # N consecutive frames
FALL_ASPECT   = HAZARD_RULES["fall_aspect_thresh"]
FALL_ANGLE    = HAZARD_RULES["fall_angle_thresh"]

# Keypoint indices (COCO)
L_SHOULDER, R_SHOULDER = 5, 6
L_HIP,      R_HIP      = 11, 12

# Alert class indices
ALERT_IDX = {i for i, n in enumerate(NAMES) if n in ALERT_CLASSES}


#ONNX Sessions 
def load_model(path: str):
    providers = ["CPUExecutionProvider"]
    sess = ort.InferenceSession(str(path), providers=providers)
    return sess

ppe_session  = load_model(MODEL_DIR / "ppe_detector.onnx")
pose_session = load_model(MODEL_DIR / "pose_detector.onnx")
print("✅ Models loaded")


#Preprocessing
def preprocess(frame: np.ndarray, size: int = 640):
    img = cv2.resize(frame, (size, size))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))[np.newaxis]
    return img


#PPE Postprocess
def postprocess_ppe(output, orig_h, orig_w, conf_thresh=0.4, iou_thresh=0.45):

    preds = output[0][0].T  # (8400, 14)
    boxes, scores, class_ids = [], [], []

    for pred in preds:
        cls_scores = pred[4:]
        class_id   = int(np.argmax(cls_scores))
        confidence = float(cls_scores[class_id])
        if confidence < conf_thresh:
            continue
        cx, cy, w, h = pred[:4]
        x1 = int((cx - w / 2) * orig_w / 640)
        y1 = int((cy - h / 2) * orig_h / 640)
        x2 = int((cx + w / 2) * orig_w / 640)
        y2 = int((cy + h / 2) * orig_h / 640)
        boxes.append([x1, y1, x2 - x1, y2 - y1])
        scores.append(confidence)
        class_ids.append(class_id)

    # NMS
    indices = cv2.dnn.NMSBoxes(boxes, scores, conf_thresh, iou_thresh)
    detections = []
    for i in (indices.flatten() if len(indices) else []):
        x, y, w, h = boxes[i]
        detections.append({
            "bbox"       : [x, y, x + w, y + h],
            "class_id"   : class_ids[i],
            "class_name" : NAMES[class_ids[i]],
            "confidence" : scores[i],
            "is_alert"   : class_ids[i] in ALERT_IDX,
        })
    return detections


#Pose Postprocess 
def postprocess_pose(output, orig_h, orig_w, conf_thresh=0.4):
    
    preds = output[0][0].T  # (8400, 56)
    results = []
    boxes, scores = [], []

    candidates = []
    for pred in preds:
        conf = float(pred[4])
        if conf < conf_thresh:
            continue
        cx, cy, w, h = pred[:4]
        x1 = int((cx - w / 2) * orig_w / 640)
        y1 = int((cy - h / 2) * orig_h / 640)
        x2 = int((cx + w / 2) * orig_w / 640)
        y2 = int((cy + h / 2) * orig_h / 640)
        kpts_raw = pred[5:].reshape(17, 3)
        kpts = kpts_raw.copy()
        kpts[:, 0] *= orig_w / 640
        kpts[:, 1] *= orig_h / 640
        boxes.append([x1, y1, x2 - x1, y2 - y1])
        scores.append(conf)
        candidates.append({"bbox": [x1, y1, x2, y2], "keypoints": kpts})

    indices = cv2.dnn.NMSBoxes(boxes, scores, conf_thresh, 0.45)
    for i in (indices.flatten() if len(indices) else []):
        c = candidates[i]
        fall, aspect, angle = is_fall(c["keypoints"], c["bbox"])
        c["fall"]   = fall
        c["aspect"] = aspect
        c["angle"]  = angle
        results.append(c)
    return results


# Fall Detection 
def is_fall(keypoints, bbox):
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    aspect = w / (h + 1e-6)

    s_conf = min(keypoints[L_SHOULDER][2], keypoints[R_SHOULDER][2])
    h_conf = min(keypoints[L_HIP][2],      keypoints[R_HIP][2])
    angle  = 0.0

    if s_conf > 0.3 and h_conf > 0.3:
        s_mid = np.array([
            (keypoints[L_SHOULDER][0] + keypoints[R_SHOULDER][0]) / 2,
            (keypoints[L_SHOULDER][1] + keypoints[R_SHOULDER][1]) / 2,
        ])
        h_mid = np.array([
            (keypoints[L_HIP][0] + keypoints[R_HIP][0]) / 2,
            (keypoints[L_HIP][1] + keypoints[R_HIP][1]) / 2,
        ])
        vec   = s_mid - h_mid
        cos_a = np.dot(vec, [0, -1]) / (np.linalg.norm(vec) + 1e-6)
        angle = float(np.degrees(np.arccos(np.clip(cos_a, -1, 1))))

    fall = (aspect > FALL_ASPECT) and (angle > FALL_ANGLE)
    return fall, aspect, angle


#Draw Annotations 
COLORS = {
    # Alert classes — warm/red tones
    "NO-Hardhat"    : (0,   50,  255),   # Red
    "NO-Safety Vest": (0,   140, 255),   # Orange
    "NO-Mask"       : (0,   0,   200),   # Dark red

    # Safe classes — cool/green tones
    "Hardhat"       : (0,   220, 0),     # Green
    "Safety Vest"   : (0,   255, 180),   # Cyan green
    "Mask"          : (180, 255, 0),     # Yellow green
    "Person"        : (255, 200, 0),     # Cyan blue

    # Info classes
    "Safety Cone"   : (0,   200, 255),   # Yellow
    "machinery"     : (200, 100, 255),   # Purple
    "vehicle"       : (255, 150, 50),    # Light blue

    # Pose
    "fall"          : (0,   0,   255),   # Red
    "pose"          : (0,   130, 255),   # Orange
}

SKELETON = [
    (5,6),(5,7),(7,9),(6,8),(8,10),
    (5,11),(6,12),(11,12),(11,13),(13,15),(12,14),(14,16)
]

def draw_ppe(frame, detections):
    for d in detections:
        x1, y1, x2, y2 = d["bbox"]
        class_name = d["class_name"]

        # Get color for this class
        color = COLORS.get(class_name, (200, 200, 200))

        # Draw box — thicker for alerts
        thickness = 3 if d["is_alert"] else 2
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

        # Draw corner accents for alert classes
        if d["is_alert"]:
            corner = 12
            cv2.line(frame, (x1, y1), (x1+corner, y1), color, 3)
            cv2.line(frame, (x1, y1), (x1, y1+corner), color, 3)
            cv2.line(frame, (x2, y1), (x2-corner, y1), color, 3)
            cv2.line(frame, (x2, y1), (x2, y1+corner), color, 3)
            cv2.line(frame, (x1, y2), (x1+corner, y2), color, 3)
            cv2.line(frame, (x1, y2), (x1, y2-corner), color, 3)
            cv2.line(frame, (x2, y2), (x2-corner, y2), color, 3)
            cv2.line(frame, (x2, y2), (x2, y2-corner), color, 3)

        # Label background + text
        label = f"{class_name} {d['confidence']:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1-22), (x1+tw+8, y1), color, -1)
        cv2.putText(frame, label, (x1+4, y1-6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    return frame

def draw_pose(frame, poses):
    for p in poses:
        kpts = p["keypoints"]
        color = COLORS["fall"] if p["fall"] else COLORS["pose"]
        for a, b in SKELETON:
            if kpts[a][2] > 0.3 and kpts[b][2] > 0.3:
                pt1 = (int(kpts[a][0]), int(kpts[a][1]))
                pt2 = (int(kpts[b][0]), int(kpts[b][1]))
                cv2.line(frame, pt1, pt2, color, 2)
        for kp in kpts:
            if kp[2] > 0.3:
                cv2.circle(frame, (int(kp[0]), int(kp[1])), 3, color, -1)
        if p["fall"]:
            x1, y1 = p["bbox"][0], p["bbox"][1]
            cv2.putText(frame, "⚠ FALL DETECTED", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS["fall"], 2)
    return frame


# Temporal Alert Filter
class AlertTracker:
    def __init__(self, window=ALERT_FRAMES):
        self.window   = window
        self.counters = defaultdict(int)
        self.active   = set()

    def update(self, hazard_key: str, detected: bool) -> bool:
        if detected:
            self.counters[hazard_key] += 1
            if self.counters[hazard_key] >= self.window:
                self.active.add(hazard_key)
                return True
        else:
            self.counters[hazard_key] = 0
            self.active.discard(hazard_key)
        return False


#Main Inference Function
alert_tracker = AlertTracker()

def run_inference(frame: np.ndarray) -> dict:
  
    t0 = time.time()
    h, w = frame.shape[:2]
    inp  = preprocess(frame)

    # Run models
    ppe_out  = ppe_session.run(None,  {"images": inp})
    pose_out = pose_session.run(None, {"images": inp})

    detections = postprocess_ppe(ppe_out,  h, w)
    poses      = postprocess_pose(pose_out, h, w)

    # Build alerts
    alerts = []

    # PPE alerts
    for d in detections:
        if d["is_alert"]:
            key = d["class_name"]
            if alert_tracker.update(key, True):
                alerts.append({
                    "type"       : "ppe_violation",
                    "message"    : f"{d['class_name']} detected",
                    "confidence" : round(d["confidence"], 2),
                    "bbox"       : d["bbox"],
                })
        else:
            alert_tracker.update(d["class_name"], False)

    # Fall alerts
    for i, p in enumerate(poses):
        key = f"fall_{i}"
        if alert_tracker.update(key, p["fall"]):
            alerts.append({
                "type"       : "fall",
                "message"    : "Worker fall detected",
                "confidence" : round(float(p["aspect"]), 2),
                "bbox"       : p["bbox"],
            })

    # Annotate frame
    annotated = frame.copy()
    annotated = draw_ppe(annotated, detections)
    annotated = draw_pose(annotated, poses)

    # Status overlay
    status_color = (0, 0, 255) if alerts else (0, 200, 0)
    status_text  = f"⚠ {len(alerts)} ALERT(S)" if alerts else "✓ ALL SAFE"
    cv2.putText(annotated, status_text, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, status_color, 2)

    inference_ms = round((time.time() - t0) * 1000, 1)

    return {
        "annotated_frame" : annotated,
        "detections"      : detections,
        "poses"           : poses,
        "alerts"          : alerts,
        "inference_ms"    : inference_ms,
    }
