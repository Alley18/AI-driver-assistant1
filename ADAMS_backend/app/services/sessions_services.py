from app.db.arango_db import db
from .auth_services import get_deviceid
from .storing_services import save_session

def create_session(device_id, off_time):
    # Find the latest ON event before the OFF event time
    query_on = """
    FOR e IN event
        FILTER e.device_id == @device_id
        FILTER e.type == "ON"
        FILTER e.time <= @off_time
        SORT e.time DESC
        LIMIT 1
        RETURN { "start_time": e.time, "date": e.date }
    """
    bind_vars_on = {
        'device_id': device_id,
        'off_time': off_time
    }
    on_events = list(db.aql.execute(query_on, bind_vars=bind_vars_on))
    
    if not on_events:
        print("[Warning] No ON event found for device_id:", device_id, "before OFF time:", off_time)
        return
    
    on_event = on_events[0]
    start_time = on_event["start_time"]
    date = on_event["date"]
    
    events_query = """
    FOR e IN event
        FILTER e.device_id == @device_id
        FILTER e.time >= @start_time AND e.time <= @off_time
        FILTER e.type NOT IN ["ON", "OFF", "Eyes reopened", "Recovered from drowsiness", 
        "Recovered from distraction"]
        SORT e.time ASC
        RETURN { "time": e.time, "event": e.type }
    """
    bind_vars_events = {
        'device_id': device_id,
        'start_time': start_time,
        'off_time': off_time
    }
    event_list = list(db.aql.execute(events_query, bind_vars=bind_vars_events))
    
    session_doc = {
        "device_id": device_id,
        "date": date,
        "start": start_time,
        "end": off_time,
        "events": event_list
    }
    
    save_session(session_doc)

def get_sessions(user_id):
    device_id = get_deviceid(user_id)

    query = """
    FOR s in sessions
        FILTER s.device_id == @device_id
        RETURN s
    """

    session_list = list(db.aql.execute(query, bind_vars={'device_id': device_id}))

    return session_list
