import cv2
import mediapipe as mp
import numpy as np
import time
import winsound  # for Windows alert

# -------------------------
# Mediapipe Face Mesh Setup
# -------------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

# -------------------------
# Eye & Mouth Aspect Ratio Functions
# -------------------------
def eye_aspect_ratio(eye):
    A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5]))
    B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4]))
    C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
    return (A + B) / (2.0 * C)

def mouth_aspect_ratio(mouth):
    A = np.linalg.norm(np.array(mouth[13]) - np.array(mouth[19]))
    C = np.linalg.norm(np.array(mouth[0]) - np.array(mouth[6]))
    return A / C

# -------------------------
# Landmark Indices
# -------------------------
LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
MOUTH_IDX = [78, 308, 13, 14, 87, 317, 82, 312, 81, 311, 80, 310, 95, 324, 88, 318, 178, 402, 191, 415]

# -------------------------
# Parameters
# -------------------------
EAR_THRESHOLD = 0.25
MAR_THRESHOLD = 0.4
HEAD_TILT_THRESHOLD = 25  # degrees
DROWSY_TIME_LIMIT = 3.0  # seconds
YAWN_TIME_LIMIT = 1.5    # seconds
TILT_TIME_LIMIT = 3.0    # seconds
BUZZER_INTERVAL = 1.0    # beep every 1 second

# -------------------------
# State Variables
# -------------------------
closed_start_time = None
yawn_start_time = None
tilt_start_time = None
alert_drowsy = False
alert_yawn = False
alert_tilt = False
last_beep_time = 0

# -------------------------
# Webcam
# -------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()
print("Webcam opened successfully. Running... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            # -------------------------
            # Get landmarks
            # -------------------------
            left_eye = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in LEFT_EYE_IDX]
            right_eye = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in RIGHT_EYE_IDX]
            mouth = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in MOUTH_IDX]

            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            mar = mouth_aspect_ratio(mouth)

            # Head tilt angle
            left_eye_center = np.mean(left_eye, axis=0)
            right_eye_center = np.mean(right_eye, axis=0)
            dx = right_eye_center[0] - left_eye_center[0]
            dy = right_eye_center[1] - left_eye_center[1]
            angle = np.degrees(np.arctan2(dy, dx))

            # Draw landmarks
            for (x, y) in left_eye + right_eye + mouth:
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

            # -------------------------
            # Drowsiness Detection
            # -------------------------
            if ear < EAR_THRESHOLD:
                if closed_start_time is None:
                    closed_start_time = time.time()
                    alert_drowsy = False
                elapsed = time.time() - closed_start_time
                cv2.putText(frame, f"Eyes closed: {elapsed:.1f}s", (30, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                if elapsed >= DROWSY_TIME_LIMIT:
                    cv2.putText(frame, "DROWSY!", (30, 90),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    if not alert_drowsy:
                        print("[ALERT] Driver drowsy!")
                        winsound.Beep(1000, 500)
                        alert_drowsy = True

                    # Repeated buzzer
                    if time.time() - last_beep_time >= BUZZER_INTERVAL:
                        winsound.Beep(1000, 500)
                        last_beep_time = time.time()
            else:
                if closed_start_time is not None:
                    total_time = time.time() - closed_start_time
                    if total_time >= DROWSY_TIME_LIMIT:
                        print(f"Eyes were closed for {total_time:.2f} seconds.")
                closed_start_time = None
                alert_drowsy = False

            # -------------------------
            # Yawning Detection
            # -------------------------
            if mar > MAR_THRESHOLD:
                if yawn_start_time is None:
                    yawn_start_time = time.time()
                    alert_yawn = False
                yawn_elapsed = time.time() - yawn_start_time
                if yawn_elapsed >= YAWN_TIME_LIMIT:
                    cv2.putText(frame, "YAWNING!", (30, 160),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    if not alert_yawn:
                        print("[ALERT] Yawning!")
                        winsound.Beep(1200, 400)
                        alert_yawn = True
                    last_beep_time = time.time()
            else:
                yawn_start_time = None
                alert_yawn = False

            # -------------------------
            # Head Tilt Detection
            # -------------------------
            if abs(angle) > HEAD_TILT_THRESHOLD:
                if tilt_start_time is None:
                    tilt_start_time = time.time()
                    alert_tilt = False
                tilt_duration = time.time() - tilt_start_time
                cv2.putText(frame, f"Head Tilt: {angle:.1f} deg ({tilt_duration:.1f}s)", (30, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)
                if tilt_duration >= TILT_TIME_LIMIT:
                    cv2.putText(frame, "DISTRACTED!", (30, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
                    if not alert_tilt:
                        print("[ALERT] Driver distracted!")
                        winsound.Beep(800, 500)
                        alert_tilt = True

                    # Repeated buzzer
                    if time.time() - last_beep_time >= BUZZER_INTERVAL:
                        winsound.Beep(800, 500)
                        last_beep_time = time.time()
            else:
                if tilt_start_time is not None:
                    total_tilt_time = time.time() - tilt_start_time
                    if total_tilt_time >= TILT_TIME_LIMIT:
                        print(f"Head tilted for {total_tilt_time:.2f} seconds.")
                tilt_start_time = None
                alert_tilt = False
                cv2.putText(frame, f"Head Angle: {angle:.1f}", (30, 200),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # -------------------------
            # Show EAR, MAR
            # -------------------------
            cv2.putText(frame, f"EAR: {ear:.2f}  MAR: {mar:.2f}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    cv2.imshow("Driver Monitoring", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Program ended.")