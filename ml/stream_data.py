import requests
import time

BACKEND_URL = "http://127.0.0.1:8000/driver-status"

def send_status(eye_status, emotion, confidence):
    payload = {
        "eye_status": eye_status,
        "emotion": emotion,
        "confidence": confidence,
        "timestamp": time.time()
    }

    try:
        response = requests.post(BACKEND_URL, json=payload)
        print("Sent:", payload)
        print("Response:", response.json())
    except Exception as e:
        print("Backend unreachable:", e)

if __name__ == "__main__":
    while True:
        send_status("closed", "sad", 88.5)
        time.sleep(5)