# ------------------------
# driver_webcam_RF.py
# ------------------------
import cv2
import numpy as np
import mediapipe as mp
import joblib
from collections import deque, Counter
from driver_alert_system_RF import DriverAlertSystem

# ------------------------
# Mediapipe Face Mesh Setup
# ------------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# ------------------------
# EAR, MAR Calculation
# ------------------------
def eye_aspect_ratio(eye):
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(mouth):
    A = np.linalg.norm(np.array(mouth[13]) - np.array(mouth[19]))
    C = np.linalg.norm(np.array(mouth[0]) - np.array(mouth[6]))
    return A / C if C != 0 else 0.0

# ------------------------
# Landmark Indices
# ------------------------
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX = [78, 308, 13, 14, 87, 317, 82, 312, 81, 311, 80, 310, 95, 324, 88, 318, 178, 402, 191, 415]
NOSE_IDX = 1

# ------------------------
# Metric Smoothing
# ------------------------
SMOOTHING_WINDOW = 5
ear_values = deque(maxlen=SMOOTHING_WINDOW)
mar_values = deque(maxlen=SMOOTHING_WINDOW)

# ------------------------
# Model & State Smoothing
# ------------------------
model = joblib.load('driver_random_forest_model_tuned.joblib')
label_map = {0: "normal", 1: "drowsy", 2: "distracted"}

STATE_WINDOW = 30  # ~1 sec at 30 FPS
predicted_states = deque(maxlen=STATE_WINDOW)

# ------------------------
# Initialize Alert System
# ------------------------
system = DriverAlertSystem()

closed_frames = 0
total_frames = 0
PERCLOS_WINDOW = 1800  # ~60s at 30 FPS

# ------------------------
# Webcam Setup
# ------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()
print("Webcam opened successfully. Running... Press 'q' to quit.")

# ------------------------
# Main Loop
# ------------------------
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        total_frames += 1
        ear = mar = perclos = pitch = yaw = roll = 0.0
        stable_state = "normal"

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark

            # Extract landmarks
            left_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in LEFT_EYE_IDX]
            right_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in RIGHT_EYE_IDX]
            mouth = [(int(lm[i].x * w), int(lm[i].y * h)) for i in MOUTH_IDX]

            # EAR / MAR calculations
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear_raw = (left_ear + right_ear) / 2.0
            mar_raw = mouth_aspect_ratio(mouth)

            # Smoothing
            ear_values.append(ear_raw)
            mar_values.append(mar_raw)
            ear = np.mean(ear_values)
            mar = np.mean(mar_values)

            # PERCLOS (rolling window)
            if ear < 0.2:
                closed_frames += 1
            if total_frames > PERCLOS_WINDOW:
                closed_frames = max(0, closed_frames - 1)
            perclos = closed_frames / min(total_frames, PERCLOS_WINDOW)

            # Head pose estimation
            left_eye_center = np.mean(left_eye, axis=0)
            right_eye_center = np.mean(right_eye, axis=0)
            dx = right_eye_center[0] - left_eye_center[0]
            dy = right_eye_center[1] - left_eye_center[1]
            roll = np.degrees(np.arctan2(dy, dx)) if dx != 0 else 0.0
            nose = lm[NOSE_IDX]
            nose_pt = np.array([int(nose.x * w), int(nose.y * h)])
            pitch = np.degrees(np.arctan2(nose_pt[1] - (left_eye_center[1] + right_eye_center[1]) / 2.0, max(abs(dx), 1)))
            yaw = np.degrees(np.arctan2(nose_pt[0] - (left_eye_center[0] + right_eye_center[0]) / 2.0, max(abs(dx), 1)))

            # AI Prediction
            feature_vector = [ear, mar, perclos, pitch, yaw, roll]
            predicted_state = model.predict([feature_vector])[0]
            predicted_state_str = label_map.get(predicted_state, "Unknown")

            # Temporal smoothing
            predicted_states.append(predicted_state_str)
            if len(predicted_states) == STATE_WINDOW:
                counts = Counter(predicted_states)
                dominant_state, dominant_count = counts.most_common(1)[0]
                dominant_ratio = dominant_count / STATE_WINDOW
                if dominant_ratio >= 0.6:
                    stable_state = dominant_state

            # Update system
            system.update(ear, mar, perclos, pitch, yaw, roll, ai_state=stable_state)

            for (x, y) in left_eye + right_eye + mouth:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # Display
        cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"MAR: {mar:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"PERCLOS: {perclos:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Pitch:{pitch:.1f} Yaw:{yaw:.1f} Roll:{roll:.1f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"State: {stable_state}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("ADAMS", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print("Unexpected error:", e)

finally:
    cap.release()
    cv2.destroyAllWindows()
    try:
        system.save_log("driver_webcam_session")
    except Exception as e:
        print("Error saving log:", e)

print("Program terminated safely.")