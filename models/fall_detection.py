
import numpy as np

LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
LEFT_HIP,      RIGHT_HIP      = 11, 12

def is_fall_detected(keypoints, bbox, aspect_thresh=1.2, angle_thresh=45):
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    aspect_ratio = w / (h + 1e-6)
    s_conf = min(keypoints[LEFT_SHOULDER][2], keypoints[RIGHT_SHOULDER][2])
    h_conf = min(keypoints[LEFT_HIP][2],      keypoints[RIGHT_HIP][2])
    angle_deg = 0.0
    if s_conf > 0.3 and h_conf > 0.3:
        s_mid = [(keypoints[LEFT_SHOULDER][0]+keypoints[RIGHT_SHOULDER][0])/2,
                 (keypoints[LEFT_SHOULDER][1]+keypoints[RIGHT_SHOULDER][1])/2]
        h_mid = [(keypoints[LEFT_HIP][0]+keypoints[RIGHT_HIP][0])/2,
                 (keypoints[LEFT_HIP][1]+keypoints[RIGHT_HIP][1])/2]
        vec   = np.array(s_mid) - np.array(h_mid)
        cos_a = np.dot(vec, [0,-1]) / (np.linalg.norm(vec) + 1e-6)
        angle_deg = float(np.degrees(np.arccos(np.clip(cos_a, -1, 1))))
    fall = (aspect_ratio > aspect_thresh) and (angle_deg > angle_thresh)
    return fall, aspect_ratio, angle_deg
