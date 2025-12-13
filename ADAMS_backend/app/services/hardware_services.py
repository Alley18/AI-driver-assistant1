from app.services.storing_services import save_state, save_event
from app.services.sessions_services import create_session
from app.services.summary_services import create_summary, store_trends_summary
from app.services.feedback_services import generate_feedback
from datetime import datetime


#----------------------------------------------------------#
#-------------------hardware ingest------------------------#
#----------------------------------------------------------#

#/kucing-state
def store_state(payload: dict):
    state_data = payload.get("state")
    save_state(state_data)
    return {"status": "processed"}

#/kucing-event
def store_event(payload: dict):
    result_data = payload.get("event")
    save_event(result_data)
    
    if result_data.get("type") == "OFF":
        device_id = result_data.get("device_id")
        timestamp_str = result_data.get("timestamp")
        off_time = None
        if timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            off_time = dt.time().isoformat(timespec='minutes')
        if device_id and off_time:
            create_session(device_id, off_time)
            create_summary(device_id, timestamp_str)
            store_trends_summary(device_id)
            generate_feedback(device_id)
    
    return {"status": "processed"}
