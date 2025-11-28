import requests
from datetime import datetime

SERVER_IP = "127.0.0.1"   # Change to your server or API IP
USER_URL = f"http://{SERVER_IP}:5000/api/login-route"

def get_users_payload():
    return {
        "username": "meow@gmail.com",
        "password": "425"
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
    event_payload = get_users_payload()

    # Uncomment if you want to send
    send_payload(USER_URL, event_payload)

    # Wait before next inference cycle
    #time.sleep(0.5)
    exit()

