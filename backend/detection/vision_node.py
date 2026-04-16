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
from dataclasses import dataclass, field
from typing import Optional

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
EMOTION_INTERVAL: float = 4.0        # seconds between background emotion scans
AI_COOLDOWN_DROWSY: float = 8.0      # minimum gap between AI responses for drowsiness
AI_COOLDOWN_DISTRACTED: float = 6.0  # minimum gap between AI responses for distraction
AI_COOLDOWN_EMOTION: float = 10.0    # minimum gap between AI responses for high-risk emotion
DROWSY_CONFIRM_SEC: float = 2.0      # sustained drowsiness before AI fires
DISTRACTION_CONFIRM_SEC: float = 1.5 # sustained distraction before AI fires
VOICE_ALERT_COOLDOWN: float = 4.0    # minimum gap between simple voice alerts
CAMERA_INDEX: int = 0                # default webcam

# Maps DeepFace emotion labels → ADAMS driver-state categories
EMOTION_MAP: dict[str, str] = {
    "angry":    "Angry",
    "disgust":  "Angry",
    "fear":     "Stressed",
    "sad":      "Stressed",
    "happy":    "Happy",
    "surprise": "Neutral",
    "neutral":  "Neutral",
}

HIGH_RISK_EMOTIONS: frozenset[str] = frozenset({"Angry", "Stressed"})

from enum import Enum, auto

class AlertTrigger(Enum):
    """Identifies what caused a full AI response to fire."""
    DROWSY      = auto()
    DISTRACTED  = auto()
    EMOTION     = auto()


# ---------------------------------------------------------------------------
# Shared pipeline state (threadsafe via primitive assignments / GIL)
# ---------------------------------------------------------------------------
@dataclass
class PipelineState:
    """Encapsulates mutable runtime state for the pipeline."""
    current_emotion: str = "Neutral"
    current_confidence: float = 0.0
    last_emotion_time: float = 0.0
    last_voice_alert: float = 0.0
    # Per-trigger last-fired timestamps (separate cooldowns per condition)
    last_ai_time_drowsy: float = 0.0
    last_ai_time_distracted: float = 0.0
    last_ai_time_emotion: float = 0.0
    # Onset timestamps (None = condition not currently active)
    drowsy_since: Optional[float] = None
    distracted_since: Optional[float] = None
    ai_speaking: bool = False


# ---------------------------------------------------------------------------
# Main pipeline class
# ---------------------------------------------------------------------------
class AdamsVisionPipeline:
    """
    Real-time driver monitoring pipeline.

    Responsibilities
    ----------------
    1. Capture frames from the webcam.
    2. Run eye/EAR + head-pose analysis on every frame (blocking, fast).
    3. Run DeepFace emotion analysis on a background thread (slow).
    4. Trigger an immediate voice alert for drowsiness ("Wake up!") or
       distraction ("Eyes on the road!") as soon as either is detected.
    5. Trigger a full AI-generated safety response after sustained drowsiness,
       sustained distraction, or a high-risk emotional state — each with its
       own independent cooldown.
    6. Render a HUD overlay and display the annotated frame.
    """

    def __init__(self) -> None:
        logger.info("Initialising ADAMS Vision Pipeline …")

        self.eye_detector = EyeDetector()
        self.brain = AdamsBrain()
        self.voice = AdamsVoice()
        self.state = PipelineState()

        logger.info("All subsystems online. Press 'q' or ESC to quit.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_emotion_detection(self, frame) -> None:
        """
        Spawn a daemon thread to run DeepFace emotion analysis.
        Results are written back to ``self.state`` without blocking the
        main capture loop.
        """
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
        Build a telemetry string from current sensor readings, send it to
        AdamsBrain, log the exchange, and speak the AI-generated advice —
        all on a daemon thread so the capture loop stays unblocked.

        Parameters
        ----------
        eye_data : dict
            Latest output from ``EyeDetector.analyze()``.
        trigger : AlertTrigger
            Which condition caused this response to fire (used for logging).
        """
        def _respond() -> None:
            self.state.ai_speaking = True
            try:
                telemetry = (
                    f"Time: {time.strftime('%H:%M')}, "
                    f"Driver active for 45 min, "
                    f"Trigger: {trigger.name}, "
                    f"Emotion: {self.state.current_emotion}, "
                    f"Eye openness: {int(eye_data['eye_opening'] * 100)}%, "
                    f"Distracted: {eye_data.get('is_distracted', False)}, "
                    f"Head yaw: {eye_data.get('yaw_deg', 0.0):+.1f}°"
                )
                logger.info("Sending telemetry to AI brain [%s]: %s", trigger.name, telemetry)

                raw_response: str = self.brain.generate_advice(telemetry)
                log_event(telemetry, raw_response)

                data: dict = json.loads(raw_response)
                message: str = data.get("message", "Stay alert.")

                self.voice.speak(message)
                logger.info("[AI/%s] %s", trigger.name, message)
            except json.JSONDecodeError:
                logger.error("Brain returned invalid JSON — skipping speech")
            except Exception:
                logger.exception("AI response pipeline failed")
            finally:
                self.state.ai_speaking = False

        threading.Thread(target=_respond, daemon=True).start()

    def _draw_hud(self, frame, eye_data: dict) -> None:
        """Delegate overlay rendering to EyeDetector, then add emotion text."""
        frame = self.eye_detector.draw_overlay(frame, eye_data)
        cv2.putText(
            frame,
            f"Emotion: {self.state.current_emotion}  "
            f"({self.state.current_confidence:.0f}%)",
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
        """Open the webcam and run the pipeline until the user quits."""
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
        """Inner capture loop — extracted for testability."""
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Empty frame received — camera may have disconnected.")
                break

            now = time.time()
            state = self.state

            # 1. Eye / EAR + head-pose analysis (synchronous, <5 ms)
            eye_data: dict = self.eye_detector.analyze(frame)

            # 2. Periodic emotion scan (async background thread)
            if now - state.last_emotion_time > EMOTION_INTERVAL:
                self._run_emotion_detection(frame)
                state.last_emotion_time = now

            # ------------------------------------------------------------------
            # 3. Immediate voice alerts (fire as soon as condition appears)
            # ------------------------------------------------------------------
            voice_alert_due = (now - state.last_voice_alert) > VOICE_ALERT_COOLDOWN

            if eye_data["is_drowsy"] and voice_alert_due:
                self.voice.speak("Wake up!")
                state.last_voice_alert = now

            elif eye_data.get("is_distracted") and voice_alert_due:
                self.voice.speak("Eyes on the road!")
                state.last_voice_alert = now

            # ------------------------------------------------------------------
            # 4. Track sustained-condition onset timestamps
            # ------------------------------------------------------------------
            state.drowsy_since = (
                state.drowsy_since or now if eye_data["is_drowsy"] else None
            )
            state.distracted_since = (
                state.distracted_since or now if eye_data.get("is_distracted") else None
            )

            # ------------------------------------------------------------------
            # 5. Full AI response — checked independently per trigger type
            # ------------------------------------------------------------------
            if not state.ai_speaking:
                drowsy_duration     = (now - state.drowsy_since)     if state.drowsy_since     else 0.0
                distracted_duration = (now - state.distracted_since) if state.distracted_since else 0.0

                if (drowsy_duration >= DROWSY_CONFIRM_SEC
                        and now - state.last_ai_time_drowsy > AI_COOLDOWN_DROWSY):
                    self._trigger_ai_response(eye_data, AlertTrigger.DROWSY)
                    state.last_ai_time_drowsy = now

                elif (distracted_duration >= DISTRACTION_CONFIRM_SEC
                        and now - state.last_ai_time_distracted > AI_COOLDOWN_DISTRACTED):
                    self._trigger_ai_response(eye_data, AlertTrigger.DISTRACTED)
                    state.last_ai_time_distracted = now

                elif (state.current_emotion in HIGH_RISK_EMOTIONS
                        and now - state.last_ai_time_emotion > AI_COOLDOWN_EMOTION):
                    self._trigger_ai_response(eye_data, AlertTrigger.EMOTION)
                    state.last_ai_time_emotion = now

            # 6. Render HUD
            frame = self._draw_hud(frame, eye_data)
            cv2.imshow("ADAMS Driver Monitor", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # 'q' or ESC
                break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    AdamsVisionPipeline().run()