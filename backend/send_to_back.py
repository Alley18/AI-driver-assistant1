import requests
import time

BACKEND_URL = "http://172.19.0.28:8000/driver-status"

while True:
    data = {
        "eye_status": "closed",
        "emotion": "sad",
        "confidence": 80.0,
        "timestamp": time.time()
    }

    try:
        response = requests.post(BACKEND_URL, json=data)
        print("Sent:", data)
        print("Response:", response.json())
    except Exception as e:
        print("Error:", e)

    time.sleep(5)