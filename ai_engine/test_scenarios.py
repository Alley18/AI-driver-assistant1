from brain import AdamsBrain  # Import the class you just made

def run_test():
    adams = AdamsBrain()
    
    # 📋 A list of things the ML team might detect
    scenarios = [
        "Driver is yawning repeatedly.",
        "Eyes have been closed for 2.5 seconds.",
        "Driver is looking down at a smartphone.",
        "Driver is perfectly alert and looking at the road.",
        "Driver is shouting and looks very angry (High Stress)."
    ]
    
    print("🚀 STARTING ADAMS AI STRESS TEST...\n")
    
    for i, situation in enumerate(scenarios, 1):
        print(f"Test #{i}: {situation}")
        advice = adams.generate_advice(situation)
        print(f"ADAMS Response: {advice}")
        print("-" * 30)

if __name__ == "__main__":
    run_test()