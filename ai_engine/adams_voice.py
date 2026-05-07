"""
ADAMS Voice
===========
Stable Windows Voice Engine.

Uses:
- win32com SAPI
- proper COM initialization
- thread-safe queue
- reliable speech output

Version: 4.0 Stable
"""

import queue
import threading
import logging
import pythoncom
import win32com.client

logger = logging.getLogger("adams.voice")

PRIORITY_ALERT = 0
PRIORITY_NORMAL = 1


class AdamsVoice:

    def __init__(self):

        self._queue = queue.PriorityQueue()

        self._running = True

        self._thread = threading.Thread(
            target=self._worker,
            daemon=True,
            name="adams-voice",
        )

        self._thread.start()

        logger.info("AdamsVoice ready.")

        print("✅ ADAMS Voice Engine: Ready")

    # -------------------------------------------------------------

    def speak(self, text: str):

        if not text:
            return

        print(f"🗣️ ADAMS Speaking: {text}")

        self._queue.put((
            PRIORITY_NORMAL,
            text,
        ))

    def alert(self, text: str):

        if not text:
            return

        print(f"🚨 ADAMS Alert: {text}")

        self._queue.put((
            PRIORITY_ALERT,
            text,
        ))

    # -------------------------------------------------------------

    def _worker(self):

        """
        Voice thread.
        """

        try:

            # IMPORTANT FIX
            pythoncom.CoInitialize()

            speaker = win32com.client.Dispatch(
                "SAPI.SpVoice"
            )

            print("✅ Windows SAPI Voice Ready")

        except Exception as e:

            print(f"❌ Voice init failed: {e}")

            return

        while self._running:

            try:

                priority, text = self._queue.get(
                    timeout=0.5
                )

            except queue.Empty:
                continue

            try:

                print(f"🔊 SPEAKING: {text}")

                speaker.Speak(text)

                print("✅ FINISHED SPEAKING")

            except Exception as e:

                logger.error(
                    "Voice error: %s",
                    e,
                )

            finally:

                self._queue.task_done()

        pythoncom.CoUninitialize()

    # -------------------------------------------------------------

    def stop(self):

        self._running = False

        print("🛑 ADAMS Voice stopped.")