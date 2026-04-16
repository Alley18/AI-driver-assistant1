import os
import json
from groq import Groq
from dotenv import load_dotenv

# --- INITIALIZATION LOGIC ---
# This part MUST run before the class is used to ensure keys are loaded
basedir = os.path.abspath(os.path.dirname(__file__))

# Check both the current folder AND the parent folder for .env
# brain.py lives in ai_engine/, so ".." correctly points to project root
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
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "❌ GROQ_API_KEY not found! "
                "Make sure your .env file exists in the project root."
            )

        self.client = Groq(api_key=api_key)

        # llama-3.3-70b-versatile: fast, stable, and great for structured JSON output
        self.model = "llama-3.3-70b-versatile"

    def generate_advice(self, driver_state):
        """
        Accepts driver telemetry (string or dict) and returns a safety
        instruction as a JSON string with keys:
          - level          : "INFO" | "WARNING" | "DANGER" | "ERROR"
          - message        : short spoken alert (max 8 words)
          - buzzer_active  : bool
          - suggested_route: "FASTEST" | "SCENIC" | "REST_STOP"
        """
        # --- Input validation ---
        if not driver_state:
            return self._default_response("INFO", "Scanning environment...", False, "FASTEST")

        # Accept both dict and string inputs
        if isinstance(driver_state, dict):
            driver_state = json.dumps(driver_state)

        if len(driver_state) < 3:
            return self._default_response("INFO", "Scanning environment...", False, "FASTEST")

        # --- Call Groq API ---
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are the ADAMS Safety Controller (Advanced Driver Alertness Monitoring System). "
                            "Analyze the driver telemetry data and return a JSON safety instruction. "
                            "Follow these rules strictly:\n"
                            "1. If driver is SLEEPY, DROWSY, or EYES CLOSED: "
                            "   level='DANGER', buzzer_active=true, suggested_route='REST_STOP'.\n"
                            "2. If driver is ANGRY, STRESSED, FEARFUL, or DISTRACTED: "
                            "   level='WARNING', buzzer_active=false, suggested_route='SCENIC'.\n"
                            "3. If driver is NEUTRAL, HAPPY, or CALM: "
                            "   level='INFO', buzzer_active=false, suggested_route='FASTEST'.\n"
                            "Return ONLY valid JSON with exactly these keys: "
                            "\"level\" (string), \"message\" (string, max 8 words, natural spoken language), "
                            "\"buzzer_active\" (boolean), \"suggested_route\" (string)."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Driver Telemetry: {driver_state}"
                    }
                ],
                model=self.model,
                response_format={"type": "json_object"},  # Forces valid JSON from Groq
                temperature=0.3,   # Low temperature = more consistent, predictable responses
                max_tokens=150     # The response is small — no need for more
            )

            result = chat_completion.choices[0].message.content

            # Validate the returned JSON has all expected keys
            parsed = json.loads(result)
            required_keys = {"level", "message", "buzzer_active", "suggested_route"}
            if not required_keys.issubset(parsed.keys()):
                print(f"⚠️ Brain returned incomplete JSON: {parsed}")
                return self._default_response("WARNING", "Check driver status now.", False, "FASTEST")

            return result

        except Exception as e:
            print(f"⚠️ Groq API Error: {e}")
            return self._default_response("ERROR", "Safety AI offline.", False, "FASTEST")

    def filter_notifications(self, driver_level, notification_text):
        """
        Focus Mode: Silences incoming phone notifications when driver
        is in a high-risk state so they stay focused on the road.
        """
        if driver_level in ["DANGER", "WARNING"]:
            return "[BLOCKED] High-risk state: Focus on the road."
        return f"[ALLOWED] {notification_text}"

    def _default_response(self, level, message, buzzer_active, suggested_route):
        """Helper to return a consistent fallback JSON string."""
        return json.dumps({
            "level": level,
            "message": message,
            "buzzer_active": buzzer_active,
            "suggested_route": suggested_route
        })


# --- Quick standalone test ---
if __name__ == "__main__":
    adams = AdamsBrain()
    print("🧠 Testing ADAMS Brain...\n")

    test_cases = [
        "Eye openness: 5%, Drowsy: True, Emotion: Tired, Confidence: 92%",
        "Eye openness: 85%, Drowsy: False, Emotion: Angry, Confidence: 78%",
        "Eye openness: 95%, Drowsy: False, Emotion: Happy, Confidence: 88%",
    ]

    for case in test_cases:
        print(f"INPUT : {case}")
        response = adams.generate_advice(case)
        data = json.loads(response)
        print(f"OUTPUT: [{data['level']}] {data['message']} | Buzzer: {data['buzzer_active']} | Route: {data['suggested_route']}")
        print("-" * 60)