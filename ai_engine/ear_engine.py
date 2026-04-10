import speech_recognition as sr

class AdamsEars:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Helps prevent the AI from being triggered by engine hum
        self.recognizer.energy_threshold = 300 
        self.recognizer.dynamic_energy_threshold = True

    def listen(self):
        with sr.Microphone() as source:
            # Adjust for 1 second to handle background noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("\n🎤 [ADAMS LISTENING...]")
            
            try:
                # listen(source, timeout, phrase_time_limit)
                # timeout=5: wait 5s for driver to start talking
                # phrase_time_limit=5: stop listening after 5s of talking
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                command = self.recognizer.recognize_google(audio)
                print(f"👤 Driver said: {command}")
                return command
            
            except sr.WaitTimeoutError:
                print("🔇 No speech detected.")
                return ""
            except sr.UnknownValueError:
                print("❓ Could not understand audio.")
                return ""
            except Exception as e:
                print(f"❌ Ear Error: {e}")
                return ""