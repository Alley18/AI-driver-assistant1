import requests
import time

BACKEND_URL = "http://<BACKEND_IP_ADDRESS>:5000/driver-status"

def send_alert(eye_status, emotion):
    payload = {
        "eye_status": eye_status,
        "emotion": emotion,
        "timestamp": time.time()
    }
    try:
        response = requests.post(BACKEND_URL, json=payload)
        print(f"Sent: {eye_status} | Response: {response.status_code}")
    except:
        print("Backend unreachable")

if __name__ == "__main__":
    while True:
        send_alert("closed", "tired")
        time.sleep(5)