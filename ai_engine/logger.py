import json
import csv
from datetime import datetime
import os

def log_event(detection, ai_response_json):
    log_file = "logs/driving_history.csv"
    
    # Create logs folder if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    try:
        data = json.loads(ai_response_json)
        
        # Prepare the data row
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": detection,
            "level": data.get("level"),
            "message": data.get("message"),
            "buzzer": data.get("buzzer_active")
        }
        
        # Write to CSV
        file_exists = os.path.isfile(log_file)
        with open(log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
            
    except Exception as e:
        print(f"Logging Error: {e}")