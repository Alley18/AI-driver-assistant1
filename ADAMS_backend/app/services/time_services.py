import datetime
from datetime import datetime, timedelta

#-----------------------------------------------
#done
#-----------------------------------------------
def preprocess_timestamp(data: dict):
    if "timestamp" in data:
        try:
            dt = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            data["date"] = dt.date().isoformat()
            data["time"] = dt.time().isoformat(timespec='minutes') #minutes
            data["day"] = dt.strftime("%A")
        except ValueError:
            print("[Warning] Invalid timestamp format:", data["timestamp"])
    return data

def return_today():
    return datetime.today()

def return_from_monday():
    today = return_today()
    weekday = today.weekday()
    last_monday = today - timedelta(days=weekday)
    return last_monday

