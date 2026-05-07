import pyttsx3
import threading
import speech_recognition as sr
import os

class AdamsVoice:
    def __init__(self):
        self.is_speaking = False
        self.lock = threading.Lock()
        self.rate = 160
        self.volume = 1.0
        print("🔊 Voice Subsystem: Ready")

    def _setup_engine(self):
        """Standardizes engine init to prevent Raspberry Pi driver crashes."""
        engine = pyttsx3.init()
        try:
            # Critical Pi Fix: Force 'english' to avoid the gmw/en ValueError
            engine.setProperty('voice', 'english')
        except:
            pass
        engine.setProperty('rate', self.rate)
        engine.setProperty('volume', self.volume)
        return engine

    def _speak_worker(self, text):
        """Handles speech in a background thread so the camera doesn't freeze."""
        with self.lock:
            self.is_speaking = True
            try:
                engine = self._setup_engine()
                # Check for alternative voices if available
                voices = engine.getProperty('voices')
                if len(voices) > 1:
                    engine.setProperty('voice', voices[1].id)

                engine.say(text)
                engine.runAndWait()
                engine.stop() 
            except Exception as e:
                print(f"❌ Voice Thread Error: {e}")
                # Emergency fallback to system command
                os.system(f'espeak "{text}" 2>/dev/null &')
            finally:
                self.is_speaking = False

    def speak(self, text):
        """NON-BLOCKING: Use this for real-time alerts."""
        if not self.is_speaking:
            print(f"🗣️  ADAMS: {text}")
            threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

    def say(self, text):
        """BLOCKING: Use this for startup/init sequences."""
        print(f"📢 ADAMS: {text}")
        try:
            engine = self._setup_engine()
            engine.say(text)
            engine.runAndWait()
        except:
            os.system(f'espeak "{text}" 2>/dev/null')

class AdamsEars:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 400 
        self.recognizer.dynamic_energy_threshold = True

    def listen(self):
        """BLOCKING: Pauses camera feed to listen for driver input."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("\n🎤 [ADAMS LISTENING...]")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = self.recognizer.recognize_google(audio)
                print(f"👤 Driver: {command}")
                return command.lower()
        except Exception as e:
            print(f"🔇 Ears Error/No Speech: {e}")
            return ""