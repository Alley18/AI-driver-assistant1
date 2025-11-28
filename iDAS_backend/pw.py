import requests
from datetime import datetime

SERVER_IP = "127.0.0.1"   # Change to your server or API IP
USER_URL = f"http://{SERVER_IP}:5000/api/signup-route"

def get_users_payload():
    return {
        "email": "satoshi@gmail.com",
        "username": "ash",
        "password": "pikachu"
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


event_payload = get_users_payload()
send_payload(USER_URL, event_payload)


