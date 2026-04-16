import cv2
import time
import json
import sys
import os
import threading

# Path fix for local imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from deepface import DeepFace
from backend.detection.face_mesh import EyeDetector
from ai_engine.brain import AdamsBrain
from ai_engine.voice_engine import AdamsVoice
from ai_engine.logger import log_event

# --- CONFIG ---
EMOTION_INTERVAL   = 4   
AI_COOLDOWN        = 8   
DROWSY_CONFIRM_SEC = 2   

EMOTION_MAP = {
    "angry": "Angry", "disgust": "Angry", "fear": "Stressed",
    "sad": "Stressed", "happy": "Happy", "surprise": "Neutral", "neutral": "Neutral"
}

class AdamsVisionPipeline:
    def __init__(self):
        print("🚀 Initializing ADAMS Vision Pipeline...")
        self.eye_detector = EyeDetector()
        self.brain         = AdamsBrain()
        self.voice         = AdamsVoice()

        self.current_emotion    = "Neutral"
        self.current_confidence = 0.0
        self.last_ai_time       = 0
        self.last_emotion_time  = 0
        self.drowsy_since       = None
        self.ai_speaking        = False
        
        self.last_voice_alert = 0
        self.alert_cooldown = 4.0 

        print("✅ All systems online. Press 'q' or ESC to quit.\n")

    def _run_emotion_detection(self, frame):
        def detect():
            try:
                result = DeepFace.analyze(img_path=frame.copy(), actions=["emotion"], 
                                         enforce_detection=False, silent=True)
                if isinstance(result, list): result = result[0]
                raw = result["dominant_emotion"]
                self.current_emotion    = EMOTION_MAP.get(raw, "Neutral")
                self.current_confidence = float(result["emotion"][raw])
            except Exception as e:
                print(f"⚠️ Emotion error: {e}")
        threading.Thread(target=detect, daemon=True).start()

    def _trigger_ai_response(self, eye_data):
        def respond():
            self.ai_speaking = True # Lock to prevent multiple AI calls
            try:
                telemetry = (f"Eye openness: {int(eye_data['eye_opening'] * 100)}%, "
                             f"Drowsy: {eye_data['is_drowsy']}, Emotion: {self.current_emotion}")
                
                raw_response = self.brain.generate_advice(telemetry)
                log_event(telemetry, raw_response)

                data = json.loads(raw_response)
                message = data.get("message", "Stay alert.")
                
                # Use the non-blocking .speak() method
                self.voice.speak(message)

                print(f"\n{'='*50}\n[AI ADVICE]: {message}\n{'='*50}\n")
            except Exception as e:
                print(f"⚠️ Brain error: {e}")
            finally:
                self.ai_speaking = False # Unlock

        threading.Thread(target=respond, daemon=True).start()

    def run(self):
        cap = cv2.VideoCapture(0)
        self.voice.say("System online. Drive safely.")

        while True:
            ret, frame = cap.read()
            if not ret: break
            now = time.time()

            # 1. Eye detection
            eye_data = self.eye_detector.analyze(frame)

            # 2. Emotion detection (background)
            if now - self.last_emotion_time > EMOTION_INTERVAL:
                self._run_emotion_detection(frame)
                self.last_emotion_time = now

            # 3. Simple Drowsiness Alert (Immediate)
            if eye_data["is_drowsy"]:
                if now - self.last_voice_alert > self.alert_cooldown:
                    self.voice.speak("Wake up!")
                    self.last_voice_alert = now
                
                if self.drowsy_since is None: self.drowsy_since = now
            else:
                self.drowsy_since = None

            # 4. Complex AI Alert (After 2 seconds of drowsiness)
            drowsy_duration = (now - self.drowsy_since) if self.drowsy_since else 0
            should_alert = (drowsy_duration >= DROWSY_CONFIRM_SEC or self.current_emotion in ["Angry", "Stressed"])

            if should_alert and not self.ai_speaking and (now - self.last_ai_time > AI_COOLDOWN):
                self._trigger_ai_response(eye_data)
                self.last_ai_time = now

            # 5. UI and Display
            frame = self.eye_detector.draw_overlay(frame, eye_data)
            cv2.putText(frame, f"Emotion: {self.current_emotion}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow("ADAMS Driver Monitor", frame)

            if cv2.waitKey(1) & 0xFF in [ord('q'), 27]: break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    AdamsVisionPipeline().run()