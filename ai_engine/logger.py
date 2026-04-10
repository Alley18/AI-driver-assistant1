import json
import csv
from datetime import datetime
import os

def log_event(detection, ai_response_json):
    log_dir = "logs"
    log_file = os.path.join(log_dir, "driving_history.csv")
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    try:
        data = json.loads(ai_response_json)
        
        row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "input": detection,
            "level": data.get("level"),
            "message": data.get("message"),
            "buzzer": data.get("buzzer_active"),
            "suggested_route": data.get("suggested_route", "N/A")
        }
        
        file_exists = os.path.isfile(log_file)
        with open(log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
            
    except Exception as e:
        print(f"Logging Error: {e}")