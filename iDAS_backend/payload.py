import requests
from datetime import datetime

SERVER_IP = "127.0.0.1"   # Change to your server or API IP
RES_URL = f"http://{SERVER_IP}:5000/api/kucing-event"
STATE_URL = f"http://{SERVER_IP}:5000/api/kucing-state"

def get_state_payload():
    return {
        "state": {
            "timestamp": datetime.now().isoformat(),
            "driver_state": "Mildly Fatigued"
        }
    }

def get_event_payload():
    return {
        "event": {
            "timestamp": datetime.now().isoformat(),
            "alert_level": 2,
            "type": "Pitch deviation >3s",
            "ear": 0.404,
            "mar": 0.0,
            "perclos": 0.086,
            "pitch": 35.33,
            "yaw": 23.08,
            "roll": 4.71
        }
    }

def send_payload(url, payload):
    """Send a payload to the server endpoint."""
    try:
        response = requests.post(url, json=payload)
        print(f"[{datetime.now().isoformat()}] Sent to {url}")
        print(payload)
        print("\nResponse:", response.status_code, response.text)
    except Exception as e:
        print("Error sending:", e)

# -------------------------------
# SIMPLE PERIODIC LOOP
# -------------------------------
while True:
    #sensor_data = get_sensor_data()

    # Build both payloads
    event_payload = get_event_payload()
    state_payload = get_state_payload()

    # Uncomment if you want to send
    send_payload(RES_URL, event_payload)
    send_payload(STATE_URL, state_payload)

    # Wait before next inference cycle
    #time.sleep(0.5)
    exit()

