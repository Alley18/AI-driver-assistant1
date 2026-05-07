"""
ADAMS Ears
==========
Speech recognition engine for the Advanced Driver Alertness Monitoring System.

Features
--------
- Continuous background listening
- Wake word detection ("Hey Adams")
- One-shot listening support
- Pause / resume microphone processing
- Windows microphone compatibility
- Background threaded execution
- Better error handling and logging

Authors : ADAMS Team
Version : 2.1.0 (Fixed & Cleaned)
"""

import time
import threading
import logging
import speech_recognition as sr


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger("adams.ears")


# ---------------------------------------------------------------------
# Wake Words
# ---------------------------------------------------------------------

WAKE_WORDS = {
    "adams",
    "hey adams",
    "adam",
    "hey adam",
}


# ---------------------------------------------------------------------
# Main Class
# ---------------------------------------------------------------------

class AdamsEars:
    """
    Speech recognition engine for ADAMS.

    Example
    -------
    ears = AdamsEars()

    def handle(text):
        print(text)

    ears.start(callback=handle)
    """

    # -----------------------------------------------------------------
    # Constructor
    # -----------------------------------------------------------------

    def __init__(
        self,
        energy_threshold: int = 300,
        dynamic_energy: bool = True,
        ambient_duration: float = 0.5,
        mic_index: int = None,
        list_microphones: bool = False,
    ) -> None:

        # Speech recognizer
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy

        # Settings
        self._ambient_duration = ambient_duration
        self._mic_index = mic_index

        # Runtime states
        self._running = False
        self._paused = False
        self._thread = None

        # Optional callback
        self.callback = None

        # Show microphones
        if list_microphones:
            self._print_microphones()

        print("✅ ADAMS Ears: Ready")

    # -----------------------------------------------------------------
    # Public Methods
    # -----------------------------------------------------------------

    def start(self, callback) -> None:
        """
        Start continuous background listening.

        Parameters
        ----------
        callback : callable
            Function that receives recognized command text.
        """

        if self._running:
            logger.warning("AdamsEars already running.")
            return

        self.callback = callback
        self._running = True

        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="adams-ears",
        )

        self._thread.start()

        logger.info("AdamsEars continuous listener started.")
        print("👂 ADAMS Ears: Listening for wake word ('Hey Adams')...")

    def stop(self) -> None:
        """Stop the listener."""

        self._running = False

        logger.info("AdamsEars listener stopped.")
        print("🛑 ADAMS Ears stopped.")

    def pause(self) -> None:
        """Pause microphone processing."""

        self._paused = True

        logger.info("Ears paused.")
        print("⏸️ ADAMS Ears paused.")

    def resume(self) -> None:
        """Resume microphone processing."""

        self._paused = False

        logger.info("Ears resumed.")
        print("▶️ ADAMS Ears resumed.")

    # -----------------------------------------------------------------
    # One-shot Listening
    # -----------------------------------------------------------------

    def listen(self) -> str:
        """
        Listen once and return transcribed text.
        """

        return self._capture(
            timeout=5,
            phrase_time_limit=8,
        )

    # Backwards compatibility
    listen_once = listen

    # -----------------------------------------------------------------
    # Background Listening Loop
    # -----------------------------------------------------------------

    def _listen_loop(self) -> None:
        """
        Main continuous listening loop.
        """

        while self._running:

            # Pause mode
            if self._paused:
                time.sleep(0.5)
                continue

            # Listen for wake word
            heard = self._capture(
                timeout=None,
                phrase_time_limit=4,
            )

            if not heard:
                continue

            # Wake word detection
            if any(word in heard for word in WAKE_WORDS):

                print("🔔 Wake word detected.")
                print("🎧 Listening for command...")

                # Capture actual command
                command = self._capture(
                    timeout=6,
                    phrase_time_limit=12,
                )

                if not command:
                    continue

                # Execute callback safely
                try:
                    if self.callback:
                        self.callback(command)

                except Exception as e:
                    logger.exception(
                        "Callback execution failed: %s",
                        e,
                    )

    # -----------------------------------------------------------------
    # Audio Capture
    # -----------------------------------------------------------------

    def _capture(
        self,
        timeout=None,
        phrase_time_limit=None,
    ) -> str:
        """
        Capture microphone input and convert speech to text.

        Returns
        -------
        str
            Recognized text in lowercase.
            Empty string on failure.
        """

        try:

            # Select microphone
            mic = (
                sr.Microphone(device_index=self._mic_index)
                if self._mic_index is not None
                else sr.Microphone()
            )

            with mic as source:

                # Reduce background noise
                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self._ambient_duration,
                )

                print("\n🎤 [ADAMS LISTENING...]")

                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            # Speech recognition
            text = self.recognizer.recognize_google(audio)

            print(f"👤 Driver said: {text}")

            return text.lower()

        except sr.WaitTimeoutError:
            return ""

        except sr.UnknownValueError:
            print("❓ Could not understand audio.")
            return ""

        except sr.RequestError as e:
            print(f"❌ Speech API error: {e}")
            logger.error("Speech API error: %s", e)
            return ""

        except Exception as e:
            print(f"❌ Ear Error: {e}")
            logger.exception("Unexpected microphone error")
            return ""

    # -----------------------------------------------------------------
    # Utility Methods
    # -----------------------------------------------------------------

    @staticmethod
    def _print_microphones() -> None:
        """
        Print available microphones.
        """

        print("\n🎙️ Available microphones:")

        try:
            microphones = sr.Microphone.list_microphone_names()

            for i, name in enumerate(microphones):
                print(f"  [{i}] {name}")

        except Exception as e:
            print(f"❌ Could not list microphones: {e}")

        print()


# ---------------------------------------------------------------------
# Quick Test
# ---------------------------------------------------------------------

if __name__ == "__main__":

    # Optional logging
    logging.basicConfig(level=logging.INFO)

    # Show microphones
    AdamsEars._print_microphones()

    # Create instance
    ears = AdamsEars(
        list_microphones=False
    )

    # Callback function
    def handle_command(text):
        print(f"\n✅ Command received: '{text}'\n")

    # Start listener
    ears.start(callback=handle_command)

    print("\nSay 'Hey Adams' followed by your command.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        ears.stop()
        print("👋 Goodbye.")