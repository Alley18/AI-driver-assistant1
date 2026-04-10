import os
import json
from groq import Groq
from dotenv import load_dotenv

# --- INITIALIZATION LOGIC ---
# This part MUST run before the class is used to ensure keys are loaded
basedir = os.path.abspath(os.path.dirname(__file__))
# Check both the current folder and the parent folder for .env
dotenv_paths = [
    os.path.join(basedir, ".env"),
    os.path.join(basedir, "..", ".env")
]

for path in dotenv_paths:
    if os.path.exists(path):
        load_dotenv(path)
        break

class AdamsBrain:
    def __init__(self):
        # Fetch key from environment
        api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("❌ ERROR: GROQ_API_KEY not found! Ensure it is in your .env file.")
            
        self.client = Groq(api_key=api_key)
        # Llama 3.1 8B is the best balance of speed and logic for safety tasks
        self.model = "llama-3.1-8b-instant" 

    def generate_advice(self, driver_state):
        """
        Processes driver telemetry and returns safety instructions in JSON.
        """
        # Quick validation for empty inputs
        if not driver_state or len(driver_state) < 3:
            return json.dumps({
                "level": "INFO",
                "message": "Scanning environment...",
                "buzzer_active": False,
                "suggested_route": "FASTEST"
            })

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system", 
                        "content": (
                            "You are the ADAMS Safety Controller (Advanced Driver Alertness Monitoring System). "
                            "Analyze telemetry and return JSON. "
                            "1. If SLEEPY/EYES CLOSED: level='DANGER', buzzer_active=true, route='REST_STOP'. "
                            "2. If ANGRY/STRESSED/DISTRACTED: level='WARNING', buzzer_active=false, route='SCENIC'. "
                            "3. If NEUTRAL/HAPPY: level='INFO', buzzer_active=false, route='FASTEST'. "
                            "Format exactly: {'level': str, 'message': str(max 8 words), 'buzzer_active': bool, 'suggested_route': str}"
                        )
                    },
                    {"role": "user", "content": f"Telemetry Data: {driver_state}"}
                ],
                model=self.model,
                response_format={"type": "json_object"} # Groq forces valid JSON output
            )
            
            # Extract and return the JSON string
            return chat_completion.choices[0].message.content

        except Exception as e:
            print(f"⚠️ Groq API Error: {e}")
            # Reliable fail-safe response
            return json.dumps({
                "level": "ERROR", 
                "message": "Safety AI Offline", 
                "buzzer_active": False,
                "suggested_route": "FASTEST"
            })

    def filter_notifications(self, driver_level, notification_text):
        """
        Focus Mode: Blocks phone alerts if driver is in a high-risk state.
        """
        if driver_level in ["DANGER", "WARNING"]:
            return "[BLOCKED] High-risk state: Focus on the road."
        return f"[ALLOWED] {notification_text}"

if __name__ == "__main__":
    # Quick internal test
    adams = AdamsBrain()
    print("Testing Brain with local data...")
    print(adams.generate_advice("eyes closed, duration 2s"))