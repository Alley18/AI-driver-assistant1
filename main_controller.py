import time
from ai_engine.brain import AdamsBrain  # Your AI logic
from ml.stream_data import get_live_telemetry  # The bridge we just merged
from ai_engine.voice_engine import AdamsVoice  # Your TTS engine

def run_adams_system():
    # Initialize your engines
    brain = AdamsBrain()
    voice = AdamsVoice()
    
    print("🚀 ADAMS System Active...")

    while True:
        # 1. Grab the latest data from the ML/Vision layer
        telemetry = get_live_telemetry()
        
        # 2. Check if the situation is serious (Logic layer)
        # If eyes are closed or emotion is highly stressed
        if telemetry["eye_opening"] < 0.2 or telemetry["emotion"] in ["sad", "angry"]:
            
            print(f"⚠️ Risk Detected: {telemetry['emotion']}")
            
            # 3. Ask the AI Brain for a specific safety intervention
            advice = brain.generate_advice(telemetry)
            
            # 4. Speak the advice to the driver
            voice.speak(advice)
            
        # Wait a bit so we don't spam the API
        time.sleep(3)

if __name__ == "__main__":
    try:
        run_adams_system()
    except KeyboardInterrupt:
        print("Stopping ADAMS...")