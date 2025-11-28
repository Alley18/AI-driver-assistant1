# -----------------------------
# driver_alert_system_RF.py
# DriverAlertSystem:
# - Monitors EAR / MAR / PERCLOS / head pose + AI state
# - Detects: prolonged eye closure, yawning, drowsy, distracted
# - Controls buzzer + vibration motor
# - Logs events and sends them to backend server
# -----------------------------

# ========== Imports ==========
import time
import json
import RPi.GPIO as GPIO
GPIO.setwarnings(False)     # Ignore GPIO warnings (e.g., reusing pins)

import warnings
warnings.filterwarnings(action='ignore', category=UserWarning)

from datetime import datetime
from pathlib import Path


class DriverAlertSystem:
    """
    This class encapsulates all alert logic:
    - thresholds and timers
    - GPIO control for buzzer and motor
    - event logging and HTTP communication
    """

    # ================== Server / Device Configuration ==================
    SERVER_IP = "172.19.23.220"  # IP address of backend server
    RES_URL   = f"http://{SERVER_IP}:5000/api/kucing-event"   # event endpoint
    STATE_URL = f"http://{SERVER_IP}:5000/api/kucing-state"   # state endpoint
    HARDWARE_ID = "ADAMS-001"  # Unique ID of this device

    # ================== Constructor ==================
    def __init__(self, log_dir="./logs"):

        # ---------- Driver state ----------
        self.current_state = "normal"

        # ---------- Eye closure detection ----------
        self.ear_closed_threshold = 0.18   # below this EAR -> eyes considered closed
        self.ear_closed_duration  = 2.0    # must stay closed for 2 seconds
        self.closed_start_time = None      # when eyes first detected as closed

        # ---------- Yawning detection ----------
        self.mar_yawn_threshold = 0.5      # above this MAR -> mouth considered wide open
        self.mar_duration       = 1.5      # must stay open for 1.5 seconds
        self.yawn_start_time = None        # when yawn started

        # ---------- Yawn info cooldown (to avoid spamming) ----------
        self.info_last_trigger = {"yawn": 0}  # last time a yawn was reported
        self.info_cooldown     = 15           # minimum seconds between yawn logs

        # ---------- Drowsy alert cooldown ----------
        self.drowsy_last_trigger    = {"drowsy": 0}
        self.drowsy_alert_cooldown  = 15      # minimum seconds between drowsy alerts

        # ---------- Distraction debounce ----------
        self.distracted_min_duration = 2.0
        self.distracted_start_time   = None

        # ---------- Alert flags (what is currently active) ----------
        self.alert_active = {
            "eyes_closed": False,
            "distracted": False,
            "drowsy": False
        }

        # ---------- Logging setup ----------
        self.alert_log = []              # list of event dicts during this session
        self._last_logged_state = None   # last driver_state written
        self.log_dir = Path(log_dir)     # directory for JSON logs
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # ---------- Hardware / GPIO config ----------
        self.I2C_BUS   = 1
        self.BUZZER_PIN = 17             # GPIO17 -> buzzer
        self.MOTOR_PIN  = 18             # GPIO18 -> vibration motor

        GPIO.setmode(GPIO.BCM)           # Use BCM pin numbering
        GPIO.setup(self.MOTOR_PIN,  GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.BUZZER_PIN, GPIO.OUT, initial=GPIO.LOW)

    # ================== System ON/OFF event ==================
    def send_system_status(self, status: str):
        """
        Send system ON/OFF event to backend with timestamp and device_id.
        """
        import requests

        payload = {
            "event": {
                "timestamp": datetime.now().isoformat(),
                "type": status,          # "ON" or "OFF"
                "device_id": self.HARDWARE_ID
            }
        }

        try:
            response = requests.post(self.RES_URL, json=payload)
            print(f"[{datetime.now().isoformat()}] System {status} sent ({response.status_code})")
        except Exception as e:
            print(f"[WARN] Failed to send system {status} event:", e)

    # =========================================================
    #   MAIN UPDATE (called once per frame)
    # =========================================================
    def update(self, ear, mar, perclos, pitch, yaw, roll, ai_state=None):
        """
        Main entry point per frame.
        Inputs:
        - raw metrics: EAR, MAR, PERCLOS, pitch, yaw, roll
        - ai_state: "normal", "drowsy", or "distracted" (from Random Forest)

        This will:
        - check prolonged eye closure,
        - check yawning,
        - apply AI-based state handling,
        - and return the current state.
        """
        now = time.time()

        # 1) Check if eyes have been closed for too long
        self.check_eyes_closed(now, ear, mar, perclos, pitch, roll, yaw)

        # 2) Check for yawning (informational log only)
        self.check_yawn(now, mar, ear, mar, perclos, pitch, yaw, roll)

        # 3) Handle AI-predicted state (drowsy / distracted / normal)
        if ai_state is not None:
            self.handle_ai_state(ai_state, ear, mar, perclos, pitch, roll, yaw)

        return self.current_state

    # =========================================================
    #   EYE CLOSURE DETECTION
    # =========================================================
    def check_eyes_closed(self, now, ear, mar, perclos, pitch, roll, yaw):
        """
        Detect prolonged eye closure using EAR.
        Condition: EAR < threshold for at least ear_closed_duration seconds.
        Action: mark eyes_closed alert, start continuous buzzer, log event.
        """
        if ear < self.ear_closed_threshold:
            # Eyes just became “closed”
            if self.closed_start_time is None:
                self.closed_start_time = now
            # Eyes have been closed for long enough
            elif now - self.closed_start_time >= self.ear_closed_duration:
                if not self.alert_active.get("eyes_closed", False):
                    self.alert_active["eyes_closed"] = True
                    print("[BUZZER] Eyes closed for too long") # debugging on terminal (driver will not see this)
                    self.log_state_change(
                        self.current_state,
                        reason="Eyes closed for too long",
                        ear=ear, mar=mar, perclos=perclos,
                        pitch=pitch, roll=roll, yaw=yaw
                    )
                # While eyes are still closed, keep buzzing
                self.play_continuous_buzzer()
        else:
            # Eyes reopened: clear alert and log recovery
            if self.alert_active.get("eyes_closed", False):
                self.alert_active["eyes_closed"] = False
                print("[INFO] Eyes reopened — recovered.") # debugging on terminal (driver will not see this)
                self.log_state_change(
                    self.current_state,
                    reason="Eyes reopened",
                    ear=ear, mar=mar, perclos=perclos,
                    pitch=pitch, roll=roll, yaw=yaw
                )
            # Reset timer
            self.closed_start_time = None

    # =========================================================
    #   AI-BASED STATE HANDLING (normal / drowsy / distracted)
    # =========================================================
    def handle_ai_state(self, ai_state, ear, mar, perclos, pitch, roll, yaw):
        """
        Process AI model output and trigger:
        - drowsiness alerts (short buzzer pattern),
        - distraction alerts (continuous buzzer),
        - and recovery logs when returning to normal.
        """
        now = time.time()

        # ---------- DROWSY ----------
        if ai_state == "drowsy":
            # Only trigger if cooldown passed
            if now - self.drowsy_last_trigger["drowsy"] > self.drowsy_alert_cooldown:
                if not self.alert_active["drowsy"]:
                    self.alert_active["drowsy"] = True
                    # Log event + explicit driver_state
                    self.log_state_change(
                        "drowsy",
                        reason="Drowsiness",
                        ear=ear, mar=mar, perclos=perclos,
                        pitch=pitch, yaw=yaw, roll=roll
                    )
                    self.log_state_change("drowsy", force_log_state=True)
                    print("[ALERT] Drowsiness detected") # debugging on terminal (driver will not see this)
                    self.drowsy_last_trigger["drowsy"] = now
                    self.sound_drowsy_buzzer()
            # If drowsy, reset distraction timer
            self.distracted_start_time = None

        # ---------- DISTRACTED ----------
        elif ai_state == "distracted":
            # Start or accumulate distracted duration
            if self.distracted_start_time is None:
                self.distracted_start_time = now
            elif now - self.distracted_start_time >= self.distracted_min_duration:
                if not self.alert_active["distracted"]:
                    self.alert_active["distracted"] = True
                    self.log_state_change(
                        "distracted",
                        reason="Distraction",
                        ear=ear, mar=mar, perclos=perclos,
                        pitch=pitch, yaw=yaw, roll=roll
                    )
                    self.log_state_change("distracted", force_log_state=True)
                    print("[ALERT] Distraction detected") # debugging on terminal (driver will not see this)
                # Continuous buzzer while distracted
                self.play_continuous_buzzer()

        # ---------- NORMAL ----------
        elif ai_state == "normal":
            # No longer distracted: clear flag and log recovery
            self.distracted_start_time = None

            if self.alert_active.get("distracted"):
                self.alert_active["distracted"] = False
                print("[INFO] Recovered from distraction.") # debugging on terminal (driver will not see this)
                self.log_state_change(
                    "normal",
                    reason="Recovered from distraction",
                    ear=ear, mar=mar, perclos=perclos,
                    pitch=pitch, roll=roll, yaw=yaw
                )
                self.log_state_change("normal", force_log_state=True)

            # No longer drowsy: clear flag and log recovery
            if self.alert_active.get("drowsy"):
                self.alert_active["drowsy"] = False
                print("[INFO] Recovered from drowsiness.") # debugging on terminal (driver will not see this)
                self.log_state_change(
                    "normal",
                    reason="Recovered from drowsiness",
                    ear=ear, mar=mar, perclos=perclos,
                    pitch=pitch, roll=roll, yaw=yaw
                )
                self.log_state_change("normal", force_log_state=True)

    # =========================================================
    #   YAWNING DETECTION (info only)
    # =========================================================
    def check_yawn(self, now, mar, ear, mar_val, perclos, pitch, yaw, roll):
        """
        Detect yawning using MAR.
        Condition: MAR > threshold for mar_duration seconds.
        Action: print info + log event, but no buzzer.
        """
        if mar > self.mar_yawn_threshold:
            if self.yawn_start_time is None:
                self.yawn_start_time = now
            elif now - self.yawn_start_time >= self.mar_duration:
                # Only log if cooldown period has passed
                if now - self.info_last_trigger["yawn"] > self.info_cooldown:
                    print("[INFO] Yawn detected") # debugging on terminal (driver will not see this)
                    self.info_last_trigger["yawn"] = now
                    self.log_state_change(
                        self.current_state,
                        reason="Yawn",
                        ear=ear, mar=mar_val, perclos=perclos,
                        pitch=pitch, yaw=yaw, roll=roll
                    )
        else:
            # Mouth closed again: reset timer
            self.yawn_start_time = None

    # =========================================================
    #   SOUND ALERTS (buzzer + vibration motor)
    # =========================================================
    def play_continuous_buzzer(self):
        """
        Single beep+vibration pulse.
        Caller (e.g., main loop) can call this repeatedly to create continuous effect.
        """
        try:
            GPIO.output(self.BUZZER_PIN, GPIO.HIGH)
            GPIO.output(self.MOTOR_PIN, GPIO.HIGH)
            time.sleep(0.05)
            GPIO.output(self.BUZZER_PIN, GPIO.LOW)
            GPIO.output(self.MOTOR_PIN, GPIO.LOW)
        except Exception:
            print("[BEEP]")

    def sound_drowsy_buzzer(self):
        """
        Short pattern: three quick buzzes + vibrations to indicate drowsiness.
        """
        for _ in range(3):
            try:
                GPIO.output(self.BUZZER_PIN, GPIO.HIGH)
                GPIO.output(self.MOTOR_PIN, GPIO.HIGH)
                time.sleep(0.05)
                GPIO.output(self.BUZZER_PIN, GPIO.LOW)
                GPIO.output(self.MOTOR_PIN, GPIO.LOW)
            except Exception:
                print("[BEEP]")

    # =========================================================
    #   LOGGING + BACKEND COMMUNICATION
    # =========================================================
    def log_state_change(self, state, reason=None, ear=None, mar=None, perclos=None,
                         pitch=None, yaw=None, roll=None, force_log_state=False):
        """
        Add a log entry to alert_log and send it to backend.
        Two modes:
        - If reason is provided: log an event with metrics.
        - If reason is None: log the overall driver_state.
        force_log_state=True forces logging even if state is unchanged.
        """

        # Only log when:
        # - forced, or
        # - state changed, or
        # - there is a specific reason (event)
        if force_log_state or state != self._last_logged_state or reason is not None:
            timestamp = datetime.now().isoformat()
            log_entry = {"timestamp": timestamp}

            if reason:
                # Event entry with metrics
                log_entry.update({
                    "event":     reason,
                    "device_id": self.HARDWARE_ID,
                    "ear":      round(ear, 3)   if ear      is not None else None,
                    "mar":      round(mar, 3)   if mar      is not None else None,
                    "perclos":  round(perclos, 3) if perclos  is not None else None,
                    "pitch":    round(pitch, 2) if pitch    is not None else None,
                    "yaw":      round(yaw, 2)   if yaw      is not None else None,
                    "roll":     round(roll, 2)  if roll     is not None else None,
                })
            else:
                # Pure state entry
                log_entry["driver_state"] = state

            # Store locally
            self.alert_log.append(log_entry)
            self._last_logged_state = state

            # ---- Send to backend REST API ----
            try:
                SERVER_IP  = "172.19.23.220"  # local override (could reuse class constants)
                RES_URL    = f"http://{SERVER_IP}:5000/api/kucing-event"
                STATE_URL  = f"http://{SERVER_IP}:5000/api/kucing-state"
                import requests

                if reason:
                    # Event payload (with metrics)
                    result_payload = {
                        "event": {
                            "timestamp": timestamp,
                            "type":      reason,
                            "device_id": self.HARDWARE_ID,
                            "ear":      round(ear, 3)   if ear      is not None else None,
                            "mar":      round(mar, 3)   if mar      is not None else None,
                            "perclos":  round(perclos, 3) if perclos  is not None else None,
                            "pitch":    round(pitch, 2) if pitch    is not None else None,
                            "yaw":      round(yaw, 2)   if yaw      is not None else None,
                            "roll":     round(roll, 2)  if roll     is not None else None,
                        }
                    }
                    response = requests.post(RES_URL, json=result_payload)
                    print(f"[{timestamp}] Sent result payload ({response.status_code})")

                else:
                    # State payload (no metrics, just driver_state)
                    state_payload = {
                        "state": {
                            "timestamp":    timestamp,
                            "driver_state": state,
                            "device_id":    self.HARDWARE_ID
                        }
                    }
                    response = requests.post(STATE_URL, json=state_payload)
                    print(f"[{timestamp}] Sent state payload ({response.status_code})")

            except Exception as e:
                print("[WARN] Failed to send payload:", e)