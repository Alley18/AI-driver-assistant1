import cv2
import requests
import time
from deepface import DeepFace

# CRITICAL: If the Pi is sending to another laptop, change 127.0.0.1 
# to the actual IP address of the Backend laptop!
BACKEND_URL = "http://172.19.0.28:8000/driver-status"

print("Starting ADAMS Vision Node...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Error: Cannot open camera")
    exit()

last_sent_time = 0
current_emotion_text = "Detecting..."

print("Camera started. Press 'q' or 'ESC' to exit.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to grab frame")
        break

    current_time = time.time()

    # Only run heavy detection every 3 seconds to avoid lagging the Pi
    if current_time - last_sent_time > 3:
        print("Running Emotion Analysis...")

        try:
            result = DeepFace.analyze(
                img_path=frame,
                actions=["emotion"],
                enforce_detection=False
            )

            if isinstance(result, list):
                result = result[0]

            emotion = result["dominant_emotion"]
            confidence = float(result["emotion"][emotion])

            current_emotion_text = f"{emotion} ({confidence:.1f}%)"
            print(f"Detected: {current_emotion_text}")

            payload = {
                "eye_status": "open", # Placeholder until EAR logic is added
                "emotion": emotion,
                "confidence": confidence,
                "timestamp": time.time()
            }

            try:
                # Sending data to the Backend
                response = requests.post(BACKEND_URL, json=payload, timeout=5)
                print("Backend Response:", response.status_code)
            except Exception as e:
                print("📡 Backend send error (Is the server running?):", e)

        except Exception as e:
            current_emotion_text = "Error"
            print("ML Detection error:", e)

        last_sent_time = current_time

    # Draw status on the screen
    cv2.putText(frame, f"Emotion: {current_emotion_text}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("ADAMS - Driver Monitor", frame)

    if cv2.waitKey(1) & 0xFF in [ord("q"), 27]:
        break

cap.release()
cv2.destroyAllWindows()