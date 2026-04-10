import pyttsx3

class AdamsVoice:
    def __init__(self):
        self.engine = pyttsx3.init()
        # Adjusting voice properties
        self.engine.setProperty('rate', 160)    # Speed of speech
        self.engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        
        # Optional: Select a different voice (0 for Male, 1 for Female usually)
        voices = self.engine.getProperty('voices')
        if len(voices) > 1:
            self.engine.setProperty('voice', voices[1].id)

    def say(self, text):
        print(f"🗣️  ADAMS Speaking: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

# Quick standalone test
if __name__ == "__main__":
    v = AdamsVoice()
    v.say("ADAMS Safety System Online. Drive safely.")