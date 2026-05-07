"""
ADAMS Vision Pipeline
=====================
Main orchestration module for the Advanced Driver Alertness Monitoring System.
Coordinates real-time eye tracking, emotion analysis, and AI-driven safety alerts.

DeepFace has been replaced with FER (Facial Expression Recognition) which uses
OpenCV only — eliminating the TensorFlow / protobuf conflict with mediapipe.

Authors : ADAMS Team
Version : 3.0.0
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
from enum import Enum, auto

# ---------------------------------------------------------------------------
# Path bootstrap — ensures sibling packages are importable when run directly
# ---------------------------------------------------------------------------
ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------------------------
# Lazy-import FER so a missing optional dep gives a clear error message
# ---------------------------------------------------------------------------
try:
    from fer import FER as _FER
    _fer_available = True
except ImportError:
    _FER = None
    _fer_available = False

from backend.hardware_control import AdamsHardware
from backend.detection.face_mesh import EyeDetector
from ai_engine.brain import AdamsBrain
from ai_engine.voice_engine import AdamsVoice
from ai_engine.logger import log_event

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt = "%H:%M:%S",
)
logger = logging.getLogger("adams.pipeline")

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
EMOTION_INTERVAL:           float = 4.0    # seconds between emotion scans
AI_COOLDOWN_DROWSY:         float = 8.0
AI_COOLDOWN_DISTRACTED:     float = 6.0
AI_COOLDOWN_EMOTION:        float = 10.0
DROWSY_CONFIRM_SEC:         float = 2.0
DISTRACTION_CONFIRM_SEC:    float = 1.5
VOICE_ALERT_COOLDOWN:       float = 4.0
CAMERA_INDEX:               int   = 0

# Display colours (BGR)
_GREEN  = (0,   220,  80)
_YELLOW = (0,   200, 240)
_RED    = (40,   40, 220)
_WHITE  = (240, 240, 240)
_GREY   = (140, 140, 140)

# Maps FER / DeepFace emotion labels → ADAMS driver-state categories
EMOTION_MAP: dict[str, str] = {
    "angry":   "Angry",
    "disgust": "Angry",
    "fear":    "Stressed",
    "sad":     "Stressed",
    "happy":   "Happy",
    "surprise":"Neutral",
    "neutral": "Neutral",
}

# Colour per ADAMS emotion category (BGR)
EMOTION_COLOUR: dict[str, tuple] = {
    "Angry":   _RED,
    "Stressed":_YELLOW,
    "Happy":   _GREEN,
    "Neutral": _WHITE,
}

HIGH_RISK_EMOTIONS: frozenset[str] = frozenset({"Angry", "Stressed"})


# ---------------------------------------------------------------------------
# Alert trigger enum
# ---------------------------------------------------------------------------
class AlertTrigger(Enum):
    DROWSY              = auto()
    DISTRACTED          = auto()
    EMOTION             = auto()
    VOICE_DROWSY        = auto()
    VOICE_DISTRACTED    = auto()


# ---------------------------------------------------------------------------
# Shared pipeline state
# ---------------------------------------------------------------------------
@dataclass
class PipelineState:
    current_emotion:        str   = "Neutral"
    current_confidence:     float = 0.0

    last_emotion_time:      float = 0.0
    last_voice_alert:       float = 0.0

    last_ai_time_drowsy:    float = 0.0
    last_ai_time_distracted:float = 0.0
    last_ai_time_emotion:   float = 0.0

    drowsy_since:           Optional[float] = None
    distracted_since:       Optional[float] = None

    ai_speaking:            bool  = False

    # Rolling FPS measurement
    _frame_times:           list  = field(default_factory=list)

    def record_frame(self, t: float) -> None:
        self._frame_times.append(t)
        if len(self._frame_times) > 30:
            self._frame_times.pop(0)

    @property
    def fps(self) -> float:
        if len(self._frame_times) < 2:
            return 0.0
        span = self._frame_times[-1] - self._frame_times[0]
        return (len(self._frame_times) - 1) / span if span > 0 else 0.0


# ---------------------------------------------------------------------------
# Main pipeline class
# ---------------------------------------------------------------------------
class AdamsVisionPipeline:
    """
    Real-time driver monitoring pipeline.

    Subsystems
    ----------
    - EyeDetector   : mediapipe face-mesh based drowsiness & gaze tracking
    - FER           : lightweight OpenCV-based facial emotion recognition
    - AdamsBrain    : Groq LLM safety advice generator
    - AdamsVoice    : text-to-speech alert delivery
    - AdamsHardware : buzzer / force-sensor interface
    """

    def __init__(self) -> None:
        logger.info("Initialising ADAMS Vision Pipeline …")

        self.hardware = AdamsHardware()

        self.eye_detector = EyeDetector()

        if _fer_available:
            self.emotion_detector = _FER(mtcnn=False)
            logger.info("FER emotion detector ready.")
        else:
            self.emotion_detector = None
            logger.warning(
                "FER not installed — emotion detection disabled. "
                "Run: pip install fer"
            )

        self.brain  = AdamsBrain()
        self.voice  = AdamsVoice()
        self.state  = PipelineState()

        logger.info("All subsystems online. Press 'q' or ESC to quit.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_eye_opening_percent(self, eye_data: dict) -> int:
        try:
            return int(float(eye_data.get("eye_opening", 0.0)) * 100)
        except Exception:
            return 0

    def _build_structured_event(
        self,
        *,
        trigger:  str,
        level:    str,
        message:  str,
        eye_data: dict,
        buzzer:   bool,
    ) -> dict:
        return {
            "timestamp":         time.strftime("%Y-%m-%d %H:%M:%S"),
            "trigger":           trigger,
            "input":             str(eye_data.get("input", "")),
            "level":             level,
            "message":           message,
            "spoken_text":       message,
            "buzzer":            buzzer,
            "driver_state":      trigger,
            "emotion":           self.state.current_emotion,
            "emotion_confidence":round(self.state.current_confidence, 2),
            "eye_opening":       self._safe_eye_opening_percent(eye_data),
            "is_drowsy":         bool(eye_data.get("is_drowsy",     False)),
            "is_distracted":     bool(eye_data.get("is_distracted", False)),
            "yaw_deg":           float(eye_data.get("yaw_deg",       0.0)),
        }

    def _log_structured_event(
        self,
        *,
        trigger:      str,
        level:        str,
        message:      str,
        eye_data:     dict,
        buzzer:       bool,
        raw_response: Optional[str] = None,
    ) -> None:
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
                raw_response if raw_response is not None
                else json.dumps({"message": message}, ensure_ascii=False),
            )
        except Exception:
            logger.exception("Failed to log structured event")

    # ------------------------------------------------------------------
    # Emotion detection (FER — OpenCV only, no TF conflict)
    # ------------------------------------------------------------------

    def _run_emotion_detection(self, frame) -> None:
        """
        Runs FER in a daemon thread so it never blocks the main loop.
        FER uses a small MTCNN-free Haar/DNN cascade — fast on RPi.
        """
        if self.emotion_detector is None:
            return

        def _detect(snapshot) -> None:
            try:
                results = self.emotion_detector.detect_emotions(snapshot)

                if not results:
                    # No face found — keep previous emotion
                    return

                # Use the face with the largest bounding box
                best = max(
                    results,
                    key=lambda r: r["box"][2] * r["box"][3]
                )
                emotions: dict[str, float] = best["emotions"]

                raw_label: str = max(emotions, key=emotions.get)

                self.state.current_emotion    = EMOTION_MAP.get(
                    raw_label, "Neutral"
                )
                # FER returns 0.0–1.0; convert to percentage
                self.state.current_confidence = emotions[raw_label] * 100.0

                logger.debug(
                    "Emotion → %s (%.1f%%)",
                    self.state.current_emotion,
                    self.state.current_confidence,
                )

            except Exception:
                logger.exception("Emotion detection failed")

        threading.Thread(
            target=_detect,
            args=(frame.copy(),),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    # AI response
    # ------------------------------------------------------------------

    def _trigger_ai_response(
        self,
        eye_data: dict,
        trigger:  AlertTrigger,
    ) -> None:
        """Generate AI advice, speak it, and log it in structured form."""

        def _respond() -> None:
            self.state.ai_speaking = True
            try:
                telemetry = (
                    f"Time: {time.strftime('%H:%M')}, "
                    f"Trigger: {trigger.name}, "
                    f"Emotion: {self.state.current_emotion} "
                    f"({self.state.current_confidence:.0f}%), "
                    f"Eye openness: "
                    f"{self._safe_eye_opening_percent(eye_data)}%, "
                    f"Drowsy: {eye_data.get('is_drowsy', False)}, "
                    f"Distracted: {eye_data.get('is_distracted', False)}, "
                    f"Head yaw: {eye_data.get('yaw_deg', 0.0):+.1f}°"
                )

                logger.info(
                    "Sending telemetry to AI brain [%s]: %s",
                    trigger.name, telemetry,
                )

                raw_response: str = self.brain.generate_advice(telemetry)

                try:
                    data: dict = json.loads(raw_response)
                except json.JSONDecodeError:
                    logger.error("Brain returned invalid JSON")
                    return

                message: str = (
                    str(data.get("message", "Stay alert.")).strip()
                    or "Stay alert."
                )

                self._log_structured_event(
                    trigger=trigger.name,
                    level=(
                        "DANGER"
                        if trigger in (
                            AlertTrigger.DROWSY,
                            AlertTrigger.DISTRACTED,
                        )
                        else "INFO"
                    ),
                    message=message,
                    eye_data=eye_data,
                    buzzer=bool(data.get("buzzer_active", False)),
                    raw_response=raw_response,
                )

                # Activate physical buzzer if AI recommends it
                if data.get("buzzer_active", False):
                    self.hardware.alert_buzzer(duration=0.5)

                self.voice.speak(message)
                logger.info("[AI/%s] %s", trigger.name, message)

            except Exception:
                logger.exception("AI response pipeline failed")
            finally:
                self.state.ai_speaking = False

        threading.Thread(target=_respond, daemon=True).start()

    # ------------------------------------------------------------------
    # Instant alert (no AI, immediate voice + buzzer)
    # ------------------------------------------------------------------

    def _speak_and_log_instant_alert(
        self,
        message: str,
        trigger: AlertTrigger,
        eye_data: dict,
    ) -> None:
        self.hardware.alert_buzzer(duration=1.0)
        self.voice.speak(message)
        self._log_structured_event(
            trigger=trigger.name,
            level="DANGER",
            message=message,
            eye_data=eye_data,
            buzzer=True,
        )

    # ------------------------------------------------------------------
    # HUD rendering
    # ------------------------------------------------------------------

    def _draw_hud(self, frame, eye_data: dict) -> None:
        """Overlay eye-tracking landmarks and dashboard info."""
        frame = self.eye_detector.draw_overlay(frame, eye_data)

        h, w = frame.shape[:2]
        now  = self.state

        # ── Emotion badge ──────────────────────────────────────────────
        emotion_colour = EMOTION_COLOUR.get(
            now.current_emotion, _WHITE
        )
        emotion_text = (
            f"{now.current_emotion}  "
            f"{now.current_confidence:.0f}%"
        )
        cv2.putText(
            frame, emotion_text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65,
            emotion_colour, 2, cv2.LINE_AA,
        )

        # ── Drowsy indicator ───────────────────────────────────────────
        if eye_data.get("is_drowsy", False):
            cv2.putText(
                frame, "⚠  DROWSY",
                (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                _RED, 2, cv2.LINE_AA,
            )

        # ── Distracted indicator ───────────────────────────────────────
        if eye_data.get("is_distracted", False):
            cv2.putText(
                frame, "⚠  DISTRACTED",
                (20, 115),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                _YELLOW, 2, cv2.LINE_AA,
            )

        # ── FPS counter (top-right) ────────────────────────────────────
        fps_text = f"FPS: {now.fps:.1f}"
        (tw, _), _ = cv2.getTextSize(
            fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
        )
        cv2.putText(
            frame, fps_text,
            (w - tw - 15, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            _GREY, 1, cv2.LINE_AA,
        )

        # ── AI-speaking indicator ──────────────────────────────────────
        if now.ai_speaking:
            cv2.putText(
                frame, "AI ●",
                (w - 80, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                _GREEN, 1, cv2.LINE_AA,
            )

        return frame

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Open the camera and start the main loop."""
        cap = cv2.VideoCapture(CAMERA_INDEX)

        if not cap.isOpened():
            logger.critical(
                "Cannot open camera index %d", CAMERA_INDEX
            )
            return

        # Prefer 640 × 480 @ 30 fps for RPi performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS,           30)

        self.voice.say("System online. Drive safely.")

        try:
            self._loop(cap)
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info("ADAMS pipeline stopped.")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _loop(self, cap: cv2.VideoCapture) -> None:  # noqa: C901
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Empty frame received — camera disconnected?")
                break

            now   = time.time()
            state = self.state
            state.record_frame(now)

            # ── 1. Eye / gaze analysis ─────────────────────────────────
            eye_data: dict = self.eye_detector.analyze(frame)

            # ── 2. Force / hands-on-wheel sensor ──────────────────────
            hands_on_wheel = self.hardware.is_hands_on_wheel()

            if (
                not hands_on_wheel
                and eye_data.get("is_distracted", False)
            ):
                self._speak_and_log_instant_alert(
                    message=(
                        "CRITICAL: hands off wheel and eyes off road!"
                    ),
                    trigger=AlertTrigger.VOICE_DISTRACTED,
                    eye_data=eye_data,
                )

            # ── 3. Periodic emotion detection ─────────────────────────
            if now - state.last_emotion_time > EMOTION_INTERVAL:
                self._run_emotion_detection(frame)
                state.last_emotion_time = now

            # ── 4. Instant voice alerts (no AI round-trip) ────────────
            voice_alert_due = (
                now - state.last_voice_alert
            ) > VOICE_ALERT_COOLDOWN

            if eye_data.get("is_drowsy", False) and voice_alert_due:
                self._speak_and_log_instant_alert(
                    message=(
                        "Driver, you are drowsy — please wake up!"
                    ),
                    trigger=AlertTrigger.VOICE_DROWSY,
                    eye_data=eye_data,
                )
                state.last_voice_alert = now

            elif eye_data.get("is_distracted", False) and voice_alert_due:
                self._speak_and_log_instant_alert(
                    message=(
                        "Driver, you are distracted — focus on the road!"
                    ),
                    trigger=AlertTrigger.VOICE_DISTRACTED,
                    eye_data=eye_data,
                )
                state.last_voice_alert = now

            # ── 5. Track sustained-state durations ────────────────────
            state.drowsy_since = (
                state.drowsy_since or now
                if eye_data.get("is_drowsy", False)
                else None
            )
            state.distracted_since = (
                state.distracted_since or now
                if eye_data.get("is_distracted", False)
                else None
            )

            # ── 6. AI deep-analysis responses ─────────────────────────
            if not state.ai_speaking:

                drowsy_duration = (
                    (now - state.drowsy_since)
                    if state.drowsy_since else 0.0
                )
                distracted_duration = (
                    (now - state.distracted_since)
                    if state.distracted_since else 0.0
                )

                if (
                    drowsy_duration >= DROWSY_CONFIRM_SEC
                    and (now - state.last_ai_time_drowsy) > AI_COOLDOWN_DROWSY
                ):
                    self._trigger_ai_response(eye_data, AlertTrigger.DROWSY)
                    state.last_ai_time_drowsy = now

                elif (
                    distracted_duration >= DISTRACTION_CONFIRM_SEC
                    and (now - state.last_ai_time_distracted)
                    > AI_COOLDOWN_DISTRACTED
                ):
                    self._trigger_ai_response(
                        eye_data, AlertTrigger.DISTRACTED
                    )
                    state.last_ai_time_distracted = now

                elif (
                    state.current_emotion in HIGH_RISK_EMOTIONS
                    and (now - state.last_ai_time_emotion)
                    > AI_COOLDOWN_EMOTION
                ):
                    self._trigger_ai_response(
                        eye_data, AlertTrigger.EMOTION
                    )
                    state.last_ai_time_emotion = now

            # ── 7. Render HUD ──────────────────────────────────────────
            frame = self._draw_hud(frame, eye_data)
            cv2.imshow("ADAMS Driver Monitor", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):   # 'q' or ESC
                break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    AdamsVisionPipeline().run()