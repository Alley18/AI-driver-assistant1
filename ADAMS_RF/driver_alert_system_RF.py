# ------------------------
# driver_alert_system_RF.py
# ------------------------
import time
import json
import winsound
from datetime import datetime
from pathlib import Path

class DriverAlertSystem:
    def __init__(self, log_dir="./logs"):
        """
        Simplified alert system to complement AI model output.
        Alerts only for:
          1. Eyes closed too long
          2. Distracted state
          3. Drowsy state
        """
        # ---------------- STATE ---------------- #
        self.current_state = "normal"

        # ---------------- EYE CLOSURE ---------------- #
        self.ear_closed_threshold = 0.18      # EAR below this = eyes closed
        self.ear_closed_duration = 2.0       # seconds
        self.closed_start_time = None

        # ---------------- YAWNING ---------------- #
        self.mar_yawn_threshold = 0.5
        self.mar_duration = 1.5  # seconds

        # ---------------- INFO COOLDOWN ---------------- #
        self.info_last_trigger = {"yawn": 0}
        self.info_cooldown = 15  # seconds between yawn alerts
        self.yawn_start_time = None

        # ---------------- Drowsy alert cooldown ---------------- #
        self.drowsy_last_trigger = {"drowsy": 0}
        self.drowsy_alert_cooldown = 15  # seconds between drowsy alerts

        # ---------------- Distracted debounce ---------------- #
        self.distracted_min_duration = 2.0  # seconds
        self.distracted_start_time = None

        # ---------------- ALERT FLAGS ---------------- #
        self.alert_active = {
            "eyes_closed": False,
            "distracted": False,
            "drowsy": False
        }

        # ---------------- LOGGING ---------------- #
        self.alert_log = []
        self._last_logged_state = None
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    # =========================================================
    #   MAIN UPDATE
    # =========================================================
    def update(self, ear, mar, perclos, pitch, yaw, roll, ai_state=None):
        """
        Called once per frame.
        AI-based state should be passed in (e.g., "normal", "drowsy", "distracted").
        """
        now = time.time()

        # --- Check prolonged eye closure ---
        self.check_eyes_closed(now, ear, mar, perclos, pitch, roll, yaw)

        # --- Check for yawning ---
        self.check_yawn(now, mar, ear, mar, perclos, pitch, yaw, roll)

        # --- Handle AI-based driver state ---
        if ai_state is not None:
            self.handle_ai_state(ai_state, ear, mar, perclos, pitch, yaw, roll)

        return self.current_state

    # =========================================================
    #   EYE CLOSURE DETECTION
    # =========================================================
    def check_eyes_closed(self, now, ear, mar, perclos, pitch, roll, yaw):
        """Check for prolonged eye closure (>2 seconds)."""
        if ear < self.ear_closed_threshold:
            if self.closed_start_time is None:
                self.closed_start_time = now
            elif now - self.closed_start_time >= self.ear_closed_duration:
                if not self.alert_active.get("eyes_closed", False):
                    self.alert_active["eyes_closed"] = True
                    print("[BUZZER] Eyes closed for too long")
                    self.log_state_change(self.current_state, reason="Eyes closed for too long",
                               ear=ear, mar=mar, perclos=perclos, pitch=pitch, roll=roll, yaw=yaw)
                self.play_continuous_buzzer()
        else:
            # Reset when eyes reopen
            if self.alert_active.get("eyes_closed", False):
                self.alert_active["eyes_closed"] = False
                print("[INFO] Eyes reopened — recovered.")
                self.log_state_change(self.current_state, reason="Eyes reopened",
                               ear=ear, mar=mar, perclos=perclos, pitch=pitch, roll=roll, yaw=yaw)
            self.closed_start_time = None
    
    # =========================================================
    #   AI-BASED STATE HANDLING
    # =========================================================
    def handle_ai_state(self, ai_state, ear, mar, perclos, pitch, roll, yaw):
        """Process AI model output (normal / drowsy / distracted) and trigger actions."""
        now = time.time()

        # --- Handle DROWSY state ---
        if ai_state == "drowsy":
            if now - self.drowsy_last_trigger["drowsy"] > self.drowsy_alert_cooldown:
                if not self.alert_active["drowsy"]:
                    self.alert_active["drowsy"] = True
                    self.log_state_change("drowsy", reason="Drowsiness",
                                ear=ear, mar=mar, perclos=perclos, pitch=pitch, yaw=yaw, roll=roll)
                    self.log_state_change("drowsy", force_log_state=True)
                    print("[ALERT] Drowsiness detected")
                    self.drowsy_last_trigger["drowsy"] = now
                    self.sound_drowsy_buzzer()
            # Reset distraction timer if switching off distraction!
            self.distracted_start_time = None

        # --- Handle DISTRACTED state ---
        elif ai_state == "distracted":
            if self.distracted_start_time is None:
                self.distracted_start_time = now
            elif now - self.distracted_start_time >= self.distracted_min_duration:
                if not self.alert_active["distracted"]:
                    self.alert_active["distracted"] = True
                    self.log_state_change("distracted", reason="Distraction",
                                ear=ear, mar=mar, perclos=perclos, pitch=pitch, yaw=yaw, roll=roll)
                    self.log_state_change("distracted", force_log_state=True)
                    print("[ALERT] Distraction detected")
                self.play_continuous_buzzer()
 
        # --- Handle NORMAL state ---
        elif ai_state == "normal":
            self.distracted_start_time = None
            normal_transition = False
            if self.alert_active.get("distracted"):
                self.alert_active["distracted"] = False
                print("[INFO] Recovered from distraction.")
                self.log_state_change("normal", reason="Recovered from distraction",
                               ear=ear, mar=mar, perclos=perclos, pitch=pitch, roll=roll, yaw=yaw)
                self.log_state_change("normal", force_log_state=True)

            if self.alert_active.get("drowsy"):
                self.alert_active["drowsy"] = False
                print("[INFO] Recovered from drowsiness.")
                self.log_state_change("normal", reason="Recovered from drowsiness",
                               ear=ear, mar=mar, perclos=perclos, pitch=pitch, roll=roll, yaw=yaw)
                self.log_state_change("normal", force_log_state=True)

    # =========================================================
    #   YAWNING DETECTION
    # =========================================================
    def check_yawn(self, now, mar, ear, mar_val, perclos, pitch, yaw, roll):
        """Detect yawning events (no buzzer, info only)"""
        if mar > self.mar_yawn_threshold:
            if self.yawn_start_time is None:
                self.yawn_start_time = now
            elif now - self.yawn_start_time >= self.mar_duration:
                if now - self.info_last_trigger["yawn"] > self.info_cooldown:
                    print("[INFO] Yawn detected")
                    self.info_last_trigger["yawn"] = now
                    self.log_state_change(self.current_state, reason="Yawn",
                               ear=ear, mar=mar_val, perclos=perclos,pitch=pitch, yaw=yaw, roll=roll)
        else:
            self.yawn_start_time = None

    # =========================================================
    #   SOUND ALERTS
    # =========================================================
    def play_continuous_buzzer(self):
        winsound.Beep(600, 300)

    def sound_drowsy_buzzer(self):
        for _ in range(3):
            winsound.Beep(750, 300)

    # =========================================================
    #   LOGGING
    # =========================================================
    def log_state_change(self, state, reason=None, ear=None, mar=None, perclos=None,
                         pitch=None, yaw=None, roll=None, force_log_state=False):

        if force_log_state or state != self._last_logged_state or reason is not None:
            timestamp = datetime.now().isoformat()
            log_entry = {"timestamp": timestamp}
            
            if reason:
                log_entry.update({
                    "event": reason,
                    "ear": round(ear, 3) if ear is not None else None,
                    "mar": round(mar, 3) if mar is not None else None,
                    "perclos": round(perclos, 3) if perclos is not None else None,
                    "pitch": round(pitch, 2) if pitch is not None else None,
                    "yaw": round(yaw, 2) if yaw is not None else None,
                    "roll": round(roll, 2) if roll is not None else None,
                })
            else:
                log_entry["driver_state"] = state
            
            self.alert_log.append(log_entry)
            self._last_logged_state = state

    def save_log(self, session_name=None):
        """Save all logged events to a JSON file."""
        if not self.alert_log:
            print("No alerts to save.")
            return

        if session_name is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            session_name = f"session_{timestamp}"

        file_path = self.log_dir / f"{session_name}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.alert_log, f, indent=2)

        print(f"Log saved to {file_path}")
        self.alert_log.clear()