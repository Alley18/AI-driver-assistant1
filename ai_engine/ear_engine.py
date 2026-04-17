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

    def _speak_worker(self, text):
        with self.lock:
            self.is_speaking = True
            try:
                engine = pyttsx3.init()
                # PI FIX: Set voice to 'english' immediately to avoid ValueError
                engine.setProperty('voice', 'english') 
                engine.setProperty('rate', self.rate)
                engine.setProperty('volume', self.volume)
                
                engine.say(text)
                engine.runAndWait()
                engine.stop() 
            except Exception as e:
                print(f"❌ Voice Error: {e}")
                # Fallback to system call
                os.system(f'espeak "{text}" 2>/dev/null &')
            finally:
                self.is_speaking = False

    def speak(self, text):
        if not self.is_speaking:
            threading.Thread(target=self._speak_worker, args=(text,), daemon=True).start()

class AdamsEars:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = True

    def listen(self):
        try:
            with sr.Microphone() as source:
                # 1 second of silence to calibrate for background car/fan noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("\n🎤 [ADAMS LISTENING...]")
                
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                command = self.recognizer.recognize_google(audio)
                print(f"👤 Driver said: {command}")
                return command.lower()
            
        except sr.WaitTimeoutError:
            print("🔇 No speech detected.")
            return ""
        except sr.UnknownValueError:
            print("❓ Could not understand audio.")
            return ""
        except Exception as e:
            print(f"❌ Ear Error: {e}")
            return ""