import os
from google import genai
from dotenv import load_dotenv

# 1. Path Logic: Look for .env in the parent folder
basedir = os.path.abspath(os.path.dirname(__file__))
dotenv_path = os.path.join(basedir, "..", ".env")
load_dotenv(dotenv_path)

class AdamsBrain:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Error: GEMINI_API_KEY not found in .env file!")
            
        # Initialize the client specifically for the Gemini API
        self.client = genai.Client(api_key=api_key)
        
        # Use the high-speed 2.5 Flash model we found in your list
        self.model_id = "gemini-2.5-flash" 

    def generate_advice(self, driver_state):
        try:
            # Generate Content using the new SDK syntax
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=f"The driver is {driver_state}.",
                config={
                    "system_instruction": (
                        "You are ADAMS, a professional driving assistant. "
                        "Give short safety advice (max 8 words). "
                        "Format: [Level] Advice. Levels: INFO, WARNING, DANGER."
                    )
                }
            )
            # FIXED INDENTATION: The return must be inside the 'try' block
            return response.text
        except Exception as e:
            return f"Brain Error: {str(e)}"

if __name__ == "__main__":
    adams = AdamsBrain()
    print("--- ADAMS AI TEST ---")
    # Test a high-danger scenario
    print(adams.generate_advice("eyes closed for 3 seconds"))