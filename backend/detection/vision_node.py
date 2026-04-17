"""
ADAMS Vision Pipeline
=====================
Main orchestration module for the Advanced Driver Alertness Monitoring System.
Coordinates real-time eye tracking, emotion analysis, and AI-driven safety alerts.

Authors : ADAMS Team
Version : 2.1.0
"""

import cv2
import time
import json
import sys
import os
import threading
import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto

# ---------------------------------------------------------------------------
# Path bootstrap — ensures sibling packages are importable when run directly
# ---------------------------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from deepface import DeepFace
from backend.detection.face_mesh import EyeDetector
from ai_engine.brain import AdamsBrain
from ai_engine.voice_engine import AdamsVoice
from ai_engine.logger import log_event

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("adams.pipeline")

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
EMOTION_INTERVAL: float = 4.0
AI_COOLDOWN_DROWSY: float = 8.0
AI_COOLDOWN_DISTRACTED: float = 6.0
AI_COOLDOWN_EMOTION: float = 10.0
DROWSY_CONFIRM_SEC: float = 2.0
DISTRACTION_CONFIRM_SEC: float = 1.5
VOICE_ALERT_COOLDOWN: float = 4.0
CAMERA_INDEX: int = 0

# Maps DeepFace emotion labels → ADAMS driver-state categories
EMOTION_MAP: dict[str, str] = {
    "angry": "Angry",
    "disgust": "Angry",
    "fear": "Stressed",
    "sad": "Stressed",
    "happy": "Happy",
    "surprise": "Neutral",
    "neutral": "Neutral",
}

HIGH_RISK_EMOTIONS: frozenset[str] = frozenset({"Angry", "Stressed"})


class AlertTrigger(Enum):
    """Identifies what caused a full AI response to fire."""
    DROWSY = auto()
    DISTRACTED = auto()
    EMOTION = auto()
    VOICE_DROWSY = auto()
    VOICE_DISTRACTED = auto()


# ---------------------------------------------------------------------------
# Shared pipeline state
# ---------------------------------------------------------------------------
@dataclass
class PipelineState:
    current_emotion: str = "Neutral"
    current_confidence: float = 0.0
    last_emotion_time: float = 0.0
    last_voice_alert: float = 0.0
    last_ai_time_drowsy: float = 0.0
    last_ai_time_distracted: float = 0.0
    last_ai_time_emotion: float = 0.0
    drowsy_since: Optional[float] = None
    distracted_since: Optional[float] = None
    ai_speaking: bool = False


# ---------------------------------------------------------------------------
# Main pipeline class
# ---------------------------------------------------------------------------
class AdamsVisionPipeline:
    """
    Real-time driver monitoring pipeline.
    """

    def __init__(self) -> None:
        logger.info("Initialising ADAMS Vision Pipeline …")

        self.eye_detector = EyeDetector()
        self.brain = AdamsBrain()
        self.voice = AdamsVoice()
        self.state = PipelineState()

        logger.info("All subsystems online. Press 'q' or ESC to quit.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_eye_opening_percent(self, eye_data: dict) -> int:
        try:
            return int(float(eye_data.get("eye_opening", 0.0)) * 100)
        except Exception:
            return 0

    def _build_structured_event(
        self,
        *,
        trigger: str,
        level: str,
        message: str,
        eye_data: dict,
        buzzer: bool,
    ) -> dict:
        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "trigger": trigger,
            "input": str(eye_data.get("input", "")),
            "level": level,
            "message": message,
            "spoken_text": message,
            "buzzer": buzzer,
            "driver_state": trigger,
            "emotion": self.state.current_emotion,
            "emotion_confidence": round(self.state.current_confidence, 2),
            "eye_opening": self._safe_eye_opening_percent(eye_data),
            "is_drowsy": bool(eye_data.get("is_drowsy", False)),
            "is_distracted": bool(eye_data.get("is_distracted", False)),
            "yaw_deg": float(eye_data.get("yaw_deg", 0.0)),
        }

    def _log_structured_event(
        self,
        *,
        trigger: str,
        level: str,
        message: str,
        eye_data: dict,
        buzzer: bool,
        raw_response: Optional[str] = None,
    ) -> None:
        """
        Writes a structured JSON event so backend/frontend can read live alerts.
        """
        event = self._build_structured_event(
            trigger=trigger,
            level=level,
            message=message,
            eye_data=eye_data,
            buzzer=buzzer,
        )

        try:
            log_event(
                json.dumps(event, ensure_ascii=False),
                raw_response if raw_response is not None else json.dumps({"message": message}, ensure_ascii=False),
            )
        except Exception:
            logger.exception("Failed to log structured event")

    def _run_emotion_detection(self, frame) -> None:
        def _detect(snapshot) -> None:
            try:
                results = DeepFace.analyze(
                    img_path=snapshot,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )
                result = results[0] if isinstance(results, list) else results
                raw_label: str = result["dominant_emotion"]
                self.state.current_emotion = EMOTION_MAP.get(raw_label, "Neutral")
                self.state.current_confidence = float(result["emotion"][raw_label])
                logger.debug(
                    "Emotion → %s (%.1f%%)",
                    self.state.current_emotion,
                    self.state.current_confidence,
                )
            except Exception:
                logger.exception("Emotion detection failed")

        threading.Thread(target=_detect, args=(frame.copy(),), daemon=True).start()

    def _trigger_ai_response(self, eye_data: dict, trigger: AlertTrigger) -> None:
        """
        Generate AI advice, speak it, and log it in structured form for frontend.
        """
        def _respond() -> None:
            self.state.ai_speaking = True
            try:
                telemetry = (
                    f"Time: {time.strftime('%H:%M')}, "
                    f"Driver active for 45 min, "
                    f"Trigger: {trigger.name}, "
                    f"Emotion: {self.state.current_emotion}, "
                    f"Eye openness: {self._safe_eye_opening_percent(eye_data)}%, "
                    f"Distracted: {eye_data.get('is_distracted', False)}, "
                    f"Head yaw: {eye_data.get('yaw_deg', 0.0):+.1f}°"
                )

                logger.info("Sending telemetry to AI brain [%s]: %s", trigger.name, telemetry)

                raw_response: str = self.brain.generate_advice(telemetry)

                try:
                    data: dict = json.loads(raw_response)
                except json.JSONDecodeError:
                    logger.error("Brain returned invalid JSON — skipping speech")
                    return

                message: str = str(data.get("message", "Stay alert.")).strip() or "Stay alert."

                self._log_structured_event(
                    trigger=trigger.name,
                    level="DANGER" if trigger in (AlertTrigger.DROWSY, AlertTrigger.DISTRACTED) else "INFO",
                    message=message,
                    eye_data=eye_data,
                    buzzer=True,
                    raw_response=raw_response,
                )

                self.voice.speak(message)
                logger.info("[AI/%s] %s", trigger.name, message)

            except Exception:
                logger.exception("AI response pipeline failed")
            finally:
                self.state.ai_speaking = False

        threading.Thread(target=_respond, daemon=True).start()

    def _speak_and_log_instant_alert(
        self,
        *,
        message: str,
        trigger: AlertTrigger,
        eye_data: dict,
    ) -> None:
        self.voice.speak(message)
        self._log_structured_event(
            trigger=trigger.name,
            level="WARNING",
            message=message,
            eye_data=eye_data,
            buzzer=True,
        )

    def _draw_hud(self, frame, eye_data: dict):
        frame = self.eye_detector.draw_overlay(frame, eye_data)
        cv2.putText(
            frame,
            f"Emotion: {self.state.current_emotion} ({self.state.current_confidence:.0f}%)",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
        )
        return frame

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> None:
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            logger.critical("Cannot open camera index %d — aborting.", CAMERA_INDEX)
            return

        self.voice.say("System online. Drive safely.")

        try:
            self._loop(cap)
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info("ADAMS pipeline stopped.")

    def _loop(self, cap: cv2.VideoCapture) -> None:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Empty frame received — camera may have disconnected.")
                break

            now = time.time()
            state = self.state

            # 1. Eye / EAR + head-pose analysis
            eye_data: dict = self.eye_detector.analyze(frame)

            # 2. Periodic emotion scan
            if now - state.last_emotion_time > EMOTION_INTERVAL:
                self._run_emotion_detection(frame)
                state.last_emotion_time = now

            # 3. Immediate voice alerts + structured logging
            voice_alert_due = (now - state.last_voice_alert) > VOICE_ALERT_COOLDOWN

            if eye_data.get("is_drowsy", False) and voice_alert_due:
                self._speak_and_log_instant_alert(
                    message="Driver! you are in a drowsy state, please wake up!",
                    trigger=AlertTrigger.VOICE_DROWSY,
                    eye_data=eye_data,
                )
                state.last_voice_alert = now

            elif eye_data.get("is_distracted", False) and voice_alert_due:
                self._speak_and_log_instant_alert(
                    message="Driver! you are distracted, please focus on the road!",
                    trigger=AlertTrigger.VOICE_DISTRACTED,
                    eye_data=eye_data,
                )
                state.last_voice_alert = now

            # 4. Track sustained-condition onset timestamps
            state.drowsy_since = (
                state.drowsy_since or now if eye_data.get("is_drowsy", False) else None
            )
            state.distracted_since = (
                state.distracted_since or now if eye_data.get("is_distracted", False) else None
            )

            # 5. Full AI response
            if not state.ai_speaking:
                drowsy_duration = (now - state.drowsy_since) if state.drowsy_since else 0.0
                distracted_duration = (now - state.distracted_since) if state.distracted_since else 0.0

                if (
                    drowsy_duration >= DROWSY_CONFIRM_SEC
                    and now - state.last_ai_time_drowsy > AI_COOLDOWN_DROWSY
                ):
                    self._trigger_ai_response(eye_data, AlertTrigger.DROWSY)
                    state.last_ai_time_drowsy = now

                elif (
                    distracted_duration >= DISTRACTION_CONFIRM_SEC
                    and now - state.last_ai_time_distracted > AI_COOLDOWN_DISTRACTED
                ):
                    self._trigger_ai_response(eye_data, AlertTrigger.DISTRACTED)
                    state.last_ai_time_distracted = now

                elif (
                    state.current_emotion in HIGH_RISK_EMOTIONS
                    and now - state.last_ai_time_emotion > AI_COOLDOWN_EMOTION
                ):
                    self._trigger_ai_response(eye_data, AlertTrigger.EMOTION)
                    state.last_ai_time_emotion = now

            # 6. Render HUD
            frame = self._draw_hud(frame, eye_data)
            cv2.imshow("ADAMS Driver Monitor", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break


if __name__ == "__main__":
    AdamsVisionPipeline().run()