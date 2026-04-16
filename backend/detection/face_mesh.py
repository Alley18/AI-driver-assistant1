import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import os

# EAR threshold logic
EAR_THRESHOLD = 0.25
CLOSED_FRAMES_THRESHOLD = 10 

class EyeDetector:
    def __init__(self):
        # 1. Path to the model file (Download link below)
        model_path = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        
        # 2. Configure the Modern Tasks API
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=1)
        self.detector = vision.FaceLandmarker.create_from_options(options)
        self.closed_frame_count = 0

    def _ear(self, landmarks, eye_indices):
        # Modern landmarks are objects, accessed directly
        pts = [(landmarks[i].x, landmarks[i].y) for i in eye_indices]
        A = np.linalg.norm(np.array(pts[1]) - np.array(pts[5]))
        B = np.linalg.norm(np.array(pts[2]) - np.array(pts[4]))
        C = np.linalg.norm(np.array(pts[0]) - np.array(pts[3]))
        return (A + B) / (2.0 * C) if C != 0 else 0.0

    def analyze(self, frame):
        rgb_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        detection_result = self.detector.detect(rgb_frame)

        if not detection_result.face_landmarks:
            self.closed_frame_count = 0
            return {"eye_opening": 1.0, "is_drowsy": False, "ear_value": 0.30, "face_detected": False}

        # MediaPipe Tasks uses a slightly different landmark list (478 points)
        # Left Eye indices: [362, 385, 387, 263, 373, 380]
        # Right Eye indices: [33, 160, 158, 133, 153, 144]
        lm = detection_result.face_landmarks[0]
        
        left_ear = self._ear(lm, [362, 385, 387, 263, 373, 380])
        right_ear = self._ear(lm, [33, 160, 158, 133, 153, 144])
        avg_ear = (left_ear + right_ear) / 2.0

        if avg_ear < EAR_THRESHOLD:
            self.closed_frame_count += 1
        else:
            self.closed_frame_count = 0

        return {
            "eye_opening": round(min(avg_ear / 0.35, 1.0), 2),
            "is_drowsy": self.closed_frame_count >= CLOSED_FRAMES_THRESHOLD,
            "ear_value": round(avg_ear, 3),
            "face_detected": True
        }

    def draw_overlay(self, frame, eye_data):
        color = (0, 0, 255) if eye_data["is_drowsy"] else (0, 255, 0)
        cv2.putText(frame, f"EAR: {eye_data['ear_value']:.2f}", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return frame