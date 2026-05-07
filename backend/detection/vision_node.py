"""
ADAMS Vision Pipeline
=====================
Main orchestration module for the Advanced Driver Alertness Monitoring System.

FIXES INCLUDED
---------------
✅ Fixed voice getting stuck after first response
✅ Proper microphone pause/resume handling
✅ AI speech lock fixed
✅ Prevented overlapping TTS calls
✅ Added safer threading
✅ Better cooldown handling
✅ Fixed ears never resuming
✅ Cleaner architecture
✅ Better shutdown handling

Authors : ADAMS Team
Version : 2.3.0 (Stable)
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
# Path bootstrap
# ---------------------------------------------------------------------------

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# Silence TensorFlow logs
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from deepface import DeepFace

from backend.detection.face_mesh import EyeDetector
from ai_engine.brain import AdamsBrain
from ai_engine.adams_voice import AdamsVoice
from ai_engine.adams_ears import AdamsEars
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
# Configuration
# ---------------------------------------------------------------------------

EMOTION_INTERVAL = 5.0

AI_COOLDOWN_DROWSY = 10.0
AI_COOLDOWN_DISTRACTED = 8.0
AI_COOLDOWN_EMOTION = 15.0

DROWSY_CONFIRM_SEC = 2.0
DISTRACTION_CONFIRM_SEC = 1.5

VOICE_ALERT_COOLDOWN = 5.0

CAMERA_INDEX = 0


# ---------------------------------------------------------------------------
# Emotion Mapping
# ---------------------------------------------------------------------------

EMOTION_MAP = {
    "angry": "Angry",
    "disgust": "Angry",
    "fear": "Stressed",
    "sad": "Stressed",
    "happy": "Happy",
    "surprise": "Neutral",
    "neutral": "Neutral",
}

HIGH_RISK_EMOTIONS = frozenset({
    "Angry",
    "Stressed",
})


# ---------------------------------------------------------------------------
# Alert Types
# ---------------------------------------------------------------------------

class AlertTrigger(Enum):

    DROWSY = auto()
    DISTRACTED = auto()
    EMOTION = auto()

    VOICE_DROWSY = auto()
    VOICE_DISTRACTED = auto()


# ---------------------------------------------------------------------------
# Runtime State
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
# Main Pipeline
# ---------------------------------------------------------------------------

class AdamsVisionPipeline:

    # ---------------------------------------------------------------------
    # Constructor
    # ---------------------------------------------------------------------

    def __init__(self):

        logger.info("Initialising ADAMS Vision Pipeline...")

        self.eye_detector = EyeDetector()

        self.brain = AdamsBrain()

        self.voice = AdamsVoice()

        self.ears = AdamsEars()

        self.state = PipelineState()

        self._lock = threading.Lock()

    # ---------------------------------------------------------------------
    # Voice Safe Speak
    # ---------------------------------------------------------------------

    def _speak_safely(self, text: str):

        """
        Prevent microphone conflicts during TTS.
        """

        try:

            # Pause microphone
            self.ears.pause()

            # Speak
            self.voice.speak(text)

        except Exception as e:

            logger.error("Voice speak failed: %s", e)

        finally:

            # IMPORTANT FIX:
            # Always resume ears even if TTS crashes

            time.sleep(0.5)

            self.ears.resume()

    # ---------------------------------------------------------------------
    # Driver Speech Callback
    # ---------------------------------------------------------------------

    def _on_driver_speech(self, text: str):

        logger.info("Driver said: %s", text)

        with self._lock:

            if self.state.ai_speaking:
                return

            self.state.ai_speaking = True

        try:

            # Prevent conversation during danger alert
            if (
                time.time() - self.state.last_voice_alert
                < 3.0
            ):
                self._speak_safely(
                    "Please focus on the road right now."
                )
                return

            # Generate AI response
            reply = self.brain.chat(text)

            if not reply:
                reply = "I did not understand."

            # Speak response
            self._speak_safely(reply)

        except Exception as e:

            logger.error("Speech callback failed: %s", e)

        finally:

            with self._lock:
                self.state.ai_speaking = False

    # ---------------------------------------------------------------------
    # Utility
    # ---------------------------------------------------------------------

    def _safe_eye_opening_percent(
        self,
        eye_data: dict
    ) -> int:

        return int(
            float(
                eye_data.get("eye_opening", 0.0)
            ) * 100
        )

    # ---------------------------------------------------------------------
    # Structured Logging
    # ---------------------------------------------------------------------

    def _log_structured_event(
        self,
        trigger: str,
        level: str,
        message: str,
        eye_data: dict,
        buzzer: bool,
        raw_res: str = None,
    ):

        event = {

            "timestamp":
                time.strftime("%Y-%m-%d %H:%M:%S"),

            "trigger":
                trigger,

            "level":
                level,

            "message":
                message,

            "eye_opening":
                self._safe_eye_opening_percent(
                    eye_data
                ),

            "is_drowsy":
                bool(
                    eye_data.get(
                        "is_drowsy",
                        False
                    )
                ),

            "is_distracted":
                bool(
                    eye_data.get(
                        "is_distracted",
                        False
                    )
                ),

            "yaw_deg":
                float(
                    eye_data.get(
                        "yaw_deg",
                        0.0
                    )
                ),

            "emotion":
                self.state.current_emotion,
        }

        try:

            log_event(
                json.dumps(event),
                raw_res or json.dumps({
                    "message": message
                }),
            )

        except Exception as e:

            logger.error(
                "Logging failed: %s",
                e
            )

    # ---------------------------------------------------------------------
    # Emotion Detection
    # ---------------------------------------------------------------------

    def _run_emotion_detection(
        self,
        frame_copy
    ):

        def _detect():

            try:

                results = DeepFace.analyze(
                    frame_copy,
                    actions=["emotion"],
                    enforce_detection=False,
                    silent=True,
                )

                res = (
                    results[0]
                    if isinstance(results, list)
                    else results
                )

                label = res["dominant_emotion"]

                with self._lock:

                    self.state.current_emotion = (
                        EMOTION_MAP.get(
                            label,
                            "Neutral",
                        )
                    )

                    self.state.current_confidence = float(
                        res["emotion"][label]
                    )

            except Exception as e:

                logger.debug(
                    "Emotion detection failed: %s",
                    e,
                )

        threading.Thread(
            target=_detect,
            daemon=True,
        ).start()

    # ---------------------------------------------------------------------
    # AI Alert Response
    # ---------------------------------------------------------------------

    def _trigger_ai_response(
        self,
        eye_data: dict,
        trigger: AlertTrigger,
    ):

        def _respond():

            with self._lock:

                if self.state.ai_speaking:
                    return

                self.state.ai_speaking = True

            try:

                telemetry = (
                    f"Trigger: {trigger.name}, "
                    f"Emotion: {self.state.current_emotion}, "
                    f"EAR: {eye_data.get('ear_value')}"
                )

                raw_response = (
                    self.brain.generate_advice(
                        telemetry
                    )
                )

                data = json.loads(raw_response)

                msg = data.get(
                    "message",
                    "Please stay focused.",
                )

                self._log_structured_event(
                    trigger.name,
                    "DANGER",
                    msg,
                    eye_data,
                    True,
                    raw_response,
                )

                # IMPORTANT FIX:
                # Use safe speaker wrapper

                self._speak_safely(msg)

            except Exception as e:

                logger.error(
                    "AI response failed: %s",
                    e,
                )

            finally:

                with self._lock:
                    self.state.ai_speaking = False

        threading.Thread(
            target=_respond,
            daemon=True,
        ).start()

    # ---------------------------------------------------------------------
    # Main Loop
    # ---------------------------------------------------------------------

    def run(self):

        cap = cv2.VideoCapture(
            CAMERA_INDEX,
            cv2.CAP_DSHOW,
        )

        if not cap.isOpened():

            logger.critical(
                "Camera failed to open."
            )

            return

        # Startup speech
        self.voice.speak(
    "ADAMS online. Say Hey Adams to talk to me."
)

        # Start ears
        self.ears.start(
            callback=self._on_driver_speech
        )

        # -------------------------------------------------------------
        # Camera Loop
        # -------------------------------------------------------------

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            now = time.time()

            eye_data = self.eye_detector.analyze(
                frame
            )

            # ---------------------------------------------------------
            # Emotion Detection
            # ---------------------------------------------------------

            if (
                now - self.state.last_emotion_time
                > EMOTION_INTERVAL
            ):

                self._run_emotion_detection(
                    frame.copy()
                )

                self.state.last_emotion_time = now

            # ---------------------------------------------------------
            # Voice Alerts
            # ---------------------------------------------------------

            voice_ready = (
                now - self.state.last_voice_alert
            ) > VOICE_ALERT_COOLDOWN

            if (
                voice_ready
                and not self.state.ai_speaking
            ):

                if eye_data.get("is_drowsy"):

                    self.state.last_voice_alert = now

                    threading.Thread(
                        target=self._speak_safely,
                        args=("Wake up!",),
                        daemon=True,
                    ).start()

                elif eye_data.get("is_distracted"):

                    self.state.last_voice_alert = now

                    threading.Thread(
                        target=self._speak_safely,
                        args=("Eyes on road!",),
                        daemon=True,
                    ).start()

            # ---------------------------------------------------------
            # Drowsiness Tracking
            # ---------------------------------------------------------

            if eye_data.get("is_drowsy"):

                if not self.state.drowsy_since:
                    self.state.drowsy_since = now

            else:

                self.state.drowsy_since = None

            # ---------------------------------------------------------
            # Sustained Drowsiness AI Trigger
            # ---------------------------------------------------------

            if not self.state.ai_speaking:

                if (
                    self.state.drowsy_since
                    and (
                        now - self.state.drowsy_since
                        > DROWSY_CONFIRM_SEC
                    )
                    and (
                        now - self.state.last_ai_time_drowsy
                        > AI_COOLDOWN_DROWSY
                    )
                ):

                    self._trigger_ai_response(
                        eye_data,
                        AlertTrigger.DROWSY,
                    )

                    self.state.last_ai_time_drowsy = now

            # ---------------------------------------------------------
            # HUD Overlay
            # ---------------------------------------------------------

            display_frame = (
                self.eye_detector.draw_overlay(
                    frame,
                    eye_data,
                )
            )

            cv2.putText(
                display_frame,
                f"State: {self.state.current_emotion}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            cv2.putText(
                display_frame,
                "Say 'Hey Adams' to talk",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (200, 200, 200),
                1,
            )

            cv2.imshow(
                "ADAMS Driver Monitor",
                display_frame,
            )

            # Exit
            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), 27):
                break

        # -----------------------------------------------------------------
        # Shutdown
        # -----------------------------------------------------------------

        logger.info(
            "Shutting down ADAMS..."
        )

        self.ears.stop()

        cap.release()

        cv2.destroyAllWindows()

        logger.info(
            "ADAMS Vision Pipeline shut down cleanly."
        )


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    AdamsVisionPipeline().run()