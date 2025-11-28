# -----------------------------
# driver_webcam_RF.py (Webcam setup)
# Real-time driver monitoring using:
# - Mediapipe Face Mesh (EAR, MAR, head pose)
# - Random Forest classifier (normal / drowsy / distracted)
# - FSR sensor (hand on steering wheel)
# - DriverAlertSystem for alerts + logging
# -----------------------------

# ========== Imports & Basic Setup ==========
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'   # Silence TensorFlow INFO/WARN logs

import cv2                  # Webcam capture and drawing
import numpy as np          # Numeric operations (vectors, norms, means)
import mediapipe as mp      # Face landmarks (Face Mesh)
import joblib               # Load trained Random Forest model
import time                 # Timing for FSR "no hand" duration
from collections import deque, Counter  # Rolling windows & mode calculation

from driver_alert_system_RF import DriverAlertSystem  # Our alert / logging system
from fsr import read_fsr                              # FSR sensor interface


# ========== Mediapipe Face Mesh Setup ==========
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,          # Expecting video stream, not single images
    max_num_faces=1,                  # Track only one driver
    refine_landmarks=True,            # Higher-quality landmarks (eyes, lips, iris)
    min_detection_confidence=0.6,     # Face detection threshold
    min_tracking_confidence=0.6       # Landmark tracking threshold
)


# ========== EAR / MAR Helper Functions ==========
def eye_aspect_ratio(eye):
    """
    Compute Eye Aspect Ratio (EAR) from 6 eye landmarks.
    EAR = (vertical distance 1 + vertical distance 2) / (2 * horizontal distance)
    Lower EAR means eyes are more closed (drowsiness indicator).
    """
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))  # vertical pair 1
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))  # vertical pair 2
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))  # horizontal pair
    return (A + B) / (2.0 * C)


def mouth_aspect_ratio(mouth):
    """
    Compute Mouth Aspect Ratio (MAR) from mouth landmarks.
    Higher MAR means mouth is more open (yawning / talking indicator).
    """
    A = np.linalg.norm(np.array(mouth[13]) - np.array(mouth[19]))  # vertical
    C = np.linalg.norm(np.array(mouth[0]) - np.array(mouth[6]))    # horizontal
    return A / C if C != 0 else 0.0


# ========== Face Landmark Indices (Mediapipe) ==========
LEFT_EYE_IDX  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX = [
    78, 308, 13, 14, 87, 317, 82, 312, 81, 311,
    80, 310, 95, 324, 88, 318, 178, 402, 191, 415
]
NOSE_IDX = 1  # Nose tip landmark (used for head pose approximation)


# ========== Metric Smoothing (EAR / MAR) ==========
# Use short rolling windows to reduce noise and jitter from single frames.
SMOOTHING_WINDOW = 5
ear_values = deque(maxlen=SMOOTHING_WINDOW)   # last N EAR values
mar_values = deque(maxlen=SMOOTHING_WINDOW)   # last N MAR values


# ========== Model & Temporal State Smoothing ==========
# Load trained Random Forest classifier for driver state.
model = joblib.load('driver_random_forest_model_tuned.joblib')
label_map = {0: "normal", 1: "drowsy", 2: "distracted"}

# Use a 1-second window (30 frames at 30 FPS) to stabilize AI state.
STATE_WINDOW = 30
predicted_states = deque(maxlen=STATE_WINDOW)


# ========== Alert System & PERCLOS Setup ==========
system = DriverAlertSystem()
system.send_system_status("ON")   # Notify backend that system is running

closed_frames = 0                 # Number of frames where eyes are "closed"
total_frames = 0                  # Total processed frames
PERCLOS_WINDOW = 1800             # 60 seconds at 30 FPS (rolling PERCLOS)

flag = 0  # One-time flag to avoid spamming "No FSR detected" messages


# ========== Webcam Initialization ==========
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

print("Webcam opened successfully. Running... Press 'q' to quit.")


# ========== Main Loop ==========
try:
    while True:
        # --- 1. Read frame from webcam ---
        ret, frame = cap.read()
        if not ret:
            break

        # Mirror the frame
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert to RGB for Mediapipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        total_frames += 1

        # Default metric values for this frame
        ear = mar = perclos = pitch = yaw = roll = 0.0
        stable_state = "normal"

        # --- 2. If a face is detected, compute features ---
        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark

            # ----- 2.1 Extract eye and mouth landmarks (pixel coordinates) -----
            left_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in LEFT_EYE_IDX]
            right_eye = [(int(lm[i].x * w), int(lm[i].y * h)) for i in RIGHT_EYE_IDX]
            mouth = [(int(lm[i].x * w), int(lm[i].y * h)) for i in MOUTH_IDX]

            # ----- 2.2 Compute EAR & MAR from landmarks -----
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear_raw = (left_ear + right_ear) / 2.0     # average EAR of both eyes
            mar_raw = mouth_aspect_ratio(mouth)

            # ----- 2.3 Apply smoothing over last few frames -----
            ear_values.append(ear_raw)
            mar_values.append(mar_raw)
            ear = np.mean(ear_values)
            mar = np.mean(mar_values)

            # ----- 2.4 PERCLOS calculation (percentage of time eyes closed) -----
            # Define "closed" when EAR below threshold (e.g., 0.2).
            if ear < 0.2:
                closed_frames += 1

            # Maintain rolling window by removing oldest "closed" frames
            if total_frames > PERCLOS_WINDOW:
                closed_frames = max(0, closed_frames - 1)

            # PERCLOS = closed_frames / number of frames in last 60 seconds
            perclos = closed_frames / min(total_frames, PERCLOS_WINDOW)

            # ----- 2.5 Head pose approximation (pitch / yaw / roll) -----
            # Use eye centers and nose position to estimate basic head rotation.
            left_eye_center = np.mean(left_eye, axis=0)
            right_eye_center = np.mean(right_eye, axis=0)

            dx = right_eye_center[0] - left_eye_center[0]
            dy = right_eye_center[1] - left_eye_center[1]

            # Roll: tilt of the head (ear to shoulder)
            roll = np.degrees(np.arctan2(dy, dx)) if dx != 0 else 0.0

            # Nose point
            nose = lm[NOSE_IDX]
            nose_pt = np.array([int(nose.x * w), int(nose.y * h)])

            # Pitch: head up/down relative to eye line
            pitch = np.degrees(np.arctan2(nose_pt[1] - (left_eye_center[1] + right_eye_center[1]) / 2.0, max(abs(dx), 1)))

            # Yaw: head left/right relative to eye center
            yaw = np.degrees(np.arctan2(nose_pt[0] - (left_eye_center[0] + right_eye_center[0]) / 2.0, max(abs(dx), 1)))

            # ----- 2.6 FSR sensor: check if hand is on steering wheel -----
            try:
                hand_on_wheel, fsr_value = read_fsr()  # Read boolean + raw value

                # --- Hand is NOT on wheel ---
                if not hand_on_wheel:
                    # Start timer once when hand first leaves
                    if 'no_hand_start' not in locals() or no_hand_start is None:
                        no_hand_start = time.time()
                    else:
                        elapsed = time.time() - no_hand_start

                        # If hand has been off the wheel for more than 5 seconds
                        if elapsed > 5:
                            # Send one-time alert and log event
                            if not locals().get('hand_alert_sent', False):
                                print(f"[ALERT] No hand detected for {elapsed:.1f}s!")
                                system.log_state_change(
                                    "no_hand",
                                    reason="Hands off steering >5s",
                                    ear=ear,
                                    mar=mar,
                                    perclos=perclos,
                                    pitch=pitch,
                                    yaw=yaw,
                                    roll=roll
                                )
                                hand_alert_sent = True

                            # Keep buzzer sounding as long as hand is off
                            system.play_continuous_buzzer()

                # --- Hand returns to wheel ---
                else:
                    # If we had previously sent an alert, clear it and stop buzzer
                    if locals().get('hand_alert_sent', False):
                        print("[INFO] Hand returned to steering wheel — stopping buzzer.")
                        hand_alert_sent = False

                    # Reset timer
                    no_hand_start = None

                # Reset “no FSR detected” message flag when FSR becomes available
                flag = 0

            except Exception as e:
                # Only print the missing-FSR message once
                if flag == 0:
                    print("No FSR detected:", e)
                    flag = 1

            # ----- 2.7 AI Prediction: build feature vector and classify state -----
            feature_vector = [ear, mar, perclos, pitch, yaw, roll]
            predicted_state = model.predict([feature_vector])[0]
            predicted_state_str = label_map.get(predicted_state, "Unknown")

            # ----- 2.8 Temporal smoothing of AI state over 1 second -----
            predicted_states.append(predicted_state_str)
            if len(predicted_states) == STATE_WINDOW:
                counts = Counter(predicted_states)
                dominant_state, dominant_count = counts.most_common(1)[0]
                dominant_ratio = dominant_count / STATE_WINDOW

                # Only accept a state if it appears in at least 60% of the last second
                if dominant_ratio >= 0.6:
                    stable_state = dominant_state

            # ----- 2.9 Update alert system with current metrics and AI state -----
            system.update(ear=ear, mar=mar, perclos=perclos, pitch=pitch, yaw=yaw, roll=roll, ai_state=stable_state)

            # ----- 2.10 Draw eye and mouth landmarks on the frame (Driver will not see this) -----
            for (x, y) in left_eye + right_eye + mouth:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

        # --- 3. Overlay text information on video frame (Driver will not see this) ---
        cv2.putText(frame, f"EAR: {ear:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"MAR: {mar:.2f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"PERCLOS: {perclos:.2f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Show FSR value if available, otherwise show fallback text
        try:
            cv2.putText(frame, f"FSR: {fsr_value:.2f}", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        except:
            cv2.putText(frame, "FSR: No FSR detected", (10, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(frame, f"Pitch:{pitch:.1f} Yaw:{yaw:.1f} Roll:{roll:.1f}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"State: {stable_state}", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # --- 4. Show window and handle quit key ---
        cv2.imshow("ADAMS", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# ========== Error Handling & Cleanup ==========
except Exception as e:
    print("Unexpected error:", e)

finally:
    # Release webcam safely
    if 'cap' in locals() and cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()

    # Notify backend that system is off and save session log
    try:
        system.send_system_status("OFF")
        system.save_log("driver_webcam_session")
    except Exception as e:
        print("Error saving log:", e)

print("Program terminated safely.")