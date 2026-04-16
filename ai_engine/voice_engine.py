import pyttsx3
import threading

class AdamsVoice:
    def __init__(self):
        self.is_speaking = False
        self.lock = threading.Lock()
        self.rate = 160
        self.volume = 1.0

    def _speak_worker(self, text):
        """Internal worker to handle the voice engine safely."""
        with self.lock:
            self.is_speaking = True
            try:
                # Initialize inside the thread for stability
                engine = pyttsx3.init()
                engine.setProperty('rate', self.rate)
                engine.setProperty('volume', self.volume)
                
                voices = engine.getProperty('voices')
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)

                engine.say(text)
                engine.runAndWait()
                engine.stop() 
            except Exception as e:
                print(f"❌ Voice Error: {e}")
            finally:
                self.is_speaking = False

    def speak(self, text):
        """NON-BLOCKING: The camera will keep moving while ADAMS talks."""
        if not self.is_speaking:
            print(f"🗣️  ADAMS Speaking: {text}")
            threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    def say(self, text):
        """BLOCKING: Use this only for startup messages."""
        try:
            temp_engine = pyttsx3.init()
            temp_engine.say(text)
            temp_engine.runAndWait()
        except:
            pass