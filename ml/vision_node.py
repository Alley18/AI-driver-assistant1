import cv2
import requests
import time
from deepface import DeepFace

# Configuration
BACKEND_URL = "http://127.0.0.1:8000/driver-status"
DETECTION_INTERVAL = 3  # Seconds between emotion checks to save CPU

def start_vision():
    print("--- ADAMS Vision Node Initialized ---")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Error: Could not detect a camera.")
        return

    last_sent_time = 0
    current_emotion_text = "Detecting..."

    print("Action: Press 'q' or 'ESC' to close the window.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        current_time = time.time()

        # Run Heavy ML Logic only every X seconds
        if current_time - last_sent_time > DETECTION_INTERVAL:
            try:
                # Analyze emotion using DeepFace
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

                # Prepare Data for Backend
                payload = {
                    "eye_status": "open", # Placeholder until EAR logic is added
                    "emotion": emotion,
                    "confidence": confidence,
                    "timestamp": current_time
                }

                # Push to Backend
                try:
                    response = requests.post(BACKEND_URL, json=payload, timeout=5)
                    print(f"Sent: {emotion} | Response: {response.status_code}")
                except Exception as e:
                    print("Backend send error:", e)

            except Exception as e:
                current_emotion_text = "Detection Error"
                print("ML Error:", e)

            last_sent_time = current_time

        # Visual Overlay
        cv2.putText(frame, f"ADAMS Emotion: {current_emotion_text}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        cv2.imshow('ADAMS Driver Feed', frame)

        # Exit handler
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_vision()