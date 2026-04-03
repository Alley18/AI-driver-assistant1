import os
import json  # <--- CRITICAL: Added this
from google import genai
from dotenv import load_dotenv

# 1. Path Logic: Look for .env (Adjust ".." if your .env is in the same folder)
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, "..", ".env") 
load_dotenv(dotenv_path)

class AdamsBrain:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Error: GEMINI_API_KEY not found in .env file!")
            
        # Initialize the client
        self.client = genai.Client(api_key=api_key)
        
        # Use the high-speed 2.5 Flash model
        self.model_id = "gemini-2.0-flash" # Note: Official name is 2.0 Flash

    def generate_advice(self, driver_state):
        # 1. Validation: Don't call API for empty or "noise" data
        if not driver_state or len(driver_state) < 3:
            return json.dumps({
                "level": "INFO",
                "message": "Scanning environment...",
                "buzzer_active": False
            })

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"Driver Telemetry: {driver_state}",
                config={
                    "response_mime_type": "application/json",
                    "system_instruction": (
                        "You are the ADAMS Safety Controller. "
                        "Analyze telemetry and return JSON: "
                        "{'level': 'INFO'|'WARNING'|'DANGER', "
                        "'message': str(max 8 words), "
                        "'buzzer_active': bool}"
                    )
                }
            )
            
            # 2. Safety Check: Validate JSON before returning
            result = response.text
            json.loads(result) # If this fails, it jumps to 'except'
            return result

        except Exception as e:
            # 3. Fail-Safe: Default response if API is down or JSON is malformed
            return json.dumps({
                "level": "ERROR",
                "message": "AI System Offline",
                "buzzer_active": False
            })

    def filter_notifications(self, driver_level, notification_text):
        """
        Focus Mode Logic: Blocks distracting alerts during high-risk states.
        """
        if driver_level in ["DANGER", "WARNING"]:
            return f"[BLOCKED] Focus on the road. Notification suppressed."
        return f"[ALLOWED] {notification_text}"

if __name__ == "__main__":
    adams = AdamsBrain()
    print("--- ADAMS AI TEST ---")
    
    # Test 1: Critical Event
    result = adams.generate_advice("eyes closed for 3 seconds")
    print(f"Advice JSON: {result}")
    
    # Test 2: Focus Mode during Danger
    print(f"Focus Mode Test: {adams.filter_notifications('DANGER', 'Meeting Invite')}")