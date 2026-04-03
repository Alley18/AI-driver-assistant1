import json
from brain import AdamsBrain
from logger import log_event


def serious_test():
    adams = AdamsBrain()
    
    # Simulating a live feed of ML detections 
    live_stream = [
    "Eye openness: 90%, Gaze: Forward, Phone: NO",
    "Eye openness: 10%, Yawning: YES, Duration: 3s", # Sleepy
    "Eye openness: 85%, Gaze: Downward, Phone: YES", # Distracted
    "Heart rate: 110bpm, Shouting detected, Gaze: Erratic" # Stressed
]
    
    print("🚦 ADAMS SYSTEM ONLINE - STARTING LIVE MONITORING\n")
    
    for detection in live_stream:
        raw_response = adams.generate_advice(detection)

        log_event(detection, raw_response)
        
        try:
            # Convert the string from the AI into a real Python Dictionary
            data = json.loads(raw_response)
            
            print(f"INPUT: {detection}")
            print(f"[{data['level']}] {data['message']}")
            
            if data['buzzer_active']:
                print("🔊 !!! BUZZER TRIGGERED !!!")
            
            print("-" * 40)
        except Exception as e:
            print(f"Error parsing AI response: {raw_response}")

if __name__ == "__main__":
    serious_test()