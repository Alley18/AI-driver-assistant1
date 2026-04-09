import cv2
import requests
import time
from deepface import DeepFace

BACKEND_URL = "http://127.0.0.1:8000/driver-status"

print("Starting vision node...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Cannot open camera")
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

    if current_time - last_sent_time > 3:
        print("Trying emotion detection...")

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

            current_emotion_text = f"{emotion} ({confidence:.1f})"
            print("Detected:", current_emotion_text)

            payload = {
                "eye_status": "open",
                "emotion": emotion,
                "confidence": confidence,
                "timestamp": time.time()
            }

            try:
                response = requests.post(BACKEND_URL, json=payload, timeout=5)
                print("Sent to backend:", response.json())
            except Exception as e:
                print("Backend send error:", e)

        except Exception as e:
            current_emotion_text = "Error"
            print("Emotion detection error:", e)

        last_sent_time = current_time

    cv2.putText(
        frame,
        f"Emotion: {current_emotion_text}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("Emotion Camera", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q") or key == 27:
        print("Closing camera...")
        break

cap.release()
cv2.destroyAllWindows()