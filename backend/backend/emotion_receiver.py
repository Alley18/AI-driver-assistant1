from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class DriverStatus(BaseModel):
    eye_status: Optional[str] = None
    emotion: str
    confidence: float
    timestamp: Optional[float] = None

@app.get("/")
def home():
    return {"message": "Driver status receiver is running"}

@app.post("/driver-status")
def receive_driver_status(data: DriverStatus):
    print("\n--- DRIVER STATUS RECEIVED ---")
    print(f"Eye status: {data.eye_status}")
    print(f"Emotion: {data.emotion}")
    print(f"Confidence: {data.confidence}")
    print(f"Timestamp: {data.timestamp}")

    action = "monitoring"

    if data.eye_status == "closed":
        action = "alert_drowsy"
        print("ALERT: Eyes closed - possible drowsiness")
    elif data.emotion in ["sad", "angry", "fear"]:
        action = "alert_emotion"
        print("ALERT: Driver not in good emotional state")
    else:
        print("Driver normal")

    return {
        "status": "received",
        "action": action
    }