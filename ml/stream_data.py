import requests
import time

# Use Port 8000 as per Ali's latest update
BACKEND_URL = "http://127.0.0.1:8000/driver-status" 

def get_live_telemetry():
    """
    AI Lead's bridge: This will eventually be replaced by real 
    values from vision_node.py
    """
    return {
        "eye_opening": 0.05,        # 5% (Very tired)
        "is_yawning": True,
        "emotion": "Tired",
        "gaze": "Forward",
        "confidence": 92.0
    }

def send_status(eye_status, emotion, confidence):
    """
    Ali's backend logic: Sends data to the Flask/FastAPI server.
    """
    payload = {
        "eye_status": eye_status,
        "emotion": emotion,
        "confidence": confidence,
        "timestamp": time.time()
    }

    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=5)
        print(f"🚀 Data Pushed: {emotion} | Server Response: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"⚠️ Backend unreachable: {e}")
        return "Offline"

if __name__ == "__main__":
    print("--- ADAMS Stream Integration Test ---")
    # Test the logic
    data = get_live_telemetry()
    send_status(
        eye_status="closed" if data["eye_opening"] < 0.2 else "open",
        emotion=data["emotion"],
        confidence=data["confidence"]
    )