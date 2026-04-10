import requests
import time

# Update this with the real IP when ready
BACKEND_URL = "http://127.0.0.1:5000/driver-status" 

def get_live_telemetry():
    # In the future, this will pull from the actual camera
    return {
        "eye_opening": 0.05,        # 5% (Very tired)
        "is_yawning": True,
        "emotion": "Tired",
        "gaze": "Forward"
    }

def send_to_backend(payload):
    """
    Your teammate's logic for sending data to the server.
    We will call this inside the AI Brain loop.
    """
    try:
        response = requests.post(BACKEND_URL, json=payload)
        return response.status_code
    except:
        return "Offline"

if __name__ == "__main__":
    # Test the loop
    data = get_live_telemetry()
    print(f"Testing Local Data: {data}")
    # status = send_to_backend(data)
    # print(f"Backend Status: {status}")