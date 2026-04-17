import pyttsx3
import threading
import os

class AdamsVoice:
    def __init__(self):
        self.is_speaking = False
        self.lock = threading.Lock()
        self.rate = 160
        self.volume = 1.0
        print("✅ ADAMS Voice Engine: Ready")

    def _setup_engine(self):
        """Helper to initialize engine with Pi-specific stability fixes."""
        engine = pyttsx3.init()
        # Immediate fix for the 'gmw/en' ValueError on Raspberry Pi
        try:
            engine.setProperty('voice', 'english')
        except:
            pass
        
        engine.setProperty('rate', self.rate)
        engine.setProperty('volume', self.volume)
        return engine

    def _speak_worker(self, text):
        """Internal worker to handle the voice engine safely in a background thread."""
        with self.lock:
            self.is_speaking = True
            try:
                engine = self._setup_engine()
                
                # Selection logic for specific voice variants
                voices = engine.getProperty('voices')
                if len(voices) > 1:
                    # Usually voices[1] is a different gender/tone on Linux
                    engine.setProperty('voice', voices[1].id)

                engine.say(text)
                engine.runAndWait()
                engine.stop() 
            except Exception as e:
                print(f"❌ Voice Thread Error: {e}")
                # Emergency fallback to system call if the library hangs
                os.system(f'espeak "{text}" 2>/dev/null')
            finally:
                self.is_speaking = False

    def speak(self, text):
        """NON-BLOCKING: The AI vision pipeline will keep moving while ADAMS talks."""
        if not self.is_speaking:
            print(f"🗣️  ADAMS Speaking: {text}")
            threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    def say(self, text):
        """BLOCKING: Use this only for startup/critical shutdown messages."""
        print(f"📢 ADAMS Startup: {text}")
        try:
            engine = self._setup_engine()
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            # If pyttsx3 fails at startup, we use system espeak so the app still runs
            os.system(f'espeak "{text}" 2>/dev/null')