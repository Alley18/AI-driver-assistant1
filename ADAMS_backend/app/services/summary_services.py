from ..ai.trend_analysis import analyze_driver_trends
from ..db.arango_db import db
from .storing_services import save_trend
from datetime import datetime

def create_summary(device_id, off_time):
    # Find the latest ON event before the OFF event time (off_time is ISO timestamp string)
    query_on = """
    FOR e IN event
        FILTER e.device_id == @device_id
        FILTER e.type == "ON"
        FILTER e.timestamp <= @off_time
        SORT e.timestamp DESC
        LIMIT 1
        RETURN { "start_time": e.timestamp, "date": e.date }
    """
    bind_vars_on = {
        'device_id': device_id,
        'off_time': off_time
    }
    on_events = list(db.aql.execute(query_on, bind_vars=bind_vars_on))
    if not on_events:
        print("[Warning] No ON event found before OFF timestamp for device:", device_id)
        return

    on_event = on_events[0]
    start_time = on_event["start_time"]

    event_query = """
    FOR e IN event
        FILTER e.device_id == @device_id
        FILTER e.timestamp >= @start_time AND e.timestamp <= @off_time
        FILTER e.type NOT IN ["ON", "OFF"]
        RETURN {
            "timestamp": e.timestamp,
            "ear": e.ear,
            "mar": e.mar,
            "perclos": e.perclos,
            "pitch": e.pitch,
            "yaw": e.yaw,
            "roll": e.roll,
            "type": e.type
        }
    """
    event_data = list(db.aql.execute(event_query, bind_vars={
        'device_id': device_id,
        'start_time': start_time,
        'off_time': off_time
    }))

    event_count_query = """
    FOR e IN event
        FILTER e.device_id == @device_id
        FILTER e.timestamp >= @start_time AND e.timestamp <= @off_time
        FILTER e.type NOT IN ["ON", "OFF", "Eyes reopened", "Recovered from drowsiness", "Recovered from distraction"]
        RETURN {
            "timestamp": e.timestamp
        }
    """
    event_count = list(db.aql.execute(event_count_query, bind_vars={
        'device_id': device_id,
        'start_time': start_time,
        'off_time': off_time
    }))

    #event count
    yawn_count = sum(1 for e in event_data if e.get("type") == "Yawn")
    eyes_closed_count = sum(1 for e in event_data if e.get("type") == "Eyes closed for too long")
    distraction_count = sum(1 for e in event_data if e.get("type") == "Distraction")
    drowsiness_count = sum(1 for e in event_data if e.get("type") == "Drowsiness")

    #total duration in seconds
    duration_query = """
    LET typePairs = [
        { start: "Eyes closed for too long", end: "Eyes reopened", category: "Eyes closed for too long" },
        { start: "Drowsiness", end: "Recovered from drowsiness", category: "Drowsiness" },
        { start: "Distraction", end: "Recovered from distraction", category: "Distraction" }
        ]

    FOR p IN typePairs
        FOR e IN event
            FILTER e.type == p.start
            FILTER e.device_id == @device_id
            FILTER e.timestamp >= @start_time AND e.timestamp <= @off_time
            LET recovery = FIRST(
                FOR r IN event
                    FILTER r.type == p.end
                    FILTER r.device_id == @device_id
                    FILTER r.timestamp > e.timestamp
                    SORT r.timestamp ASC
                    LIMIT 1
                    RETURN r
            )
            FILTER recovery != null
            LET durationMs = DATE_DIFF(
                e.timestamp,
                recovery.timestamp,
                "millisecond"
            )
            COLLECT category = p.category INTO group
            LET totalDurationMs = SUM(group[*].durationMs)
            RETURN {
                category,
                totalDurationSeconds: totalDurationMs / 1000
            }
    """

    duration_data = list(db.aql.execute(duration_query, bind_vars={
        'device_id': device_id,
        'start_time': start_time,
        'off_time': off_time
    }))


    duration_seconds_map = {item["category"]: item["totalDurationSeconds"] for item in duration_data}

    eyes_close_duration = duration_seconds_map.get("Eyes closed for too long", 0)
    drowsy_duration = duration_seconds_map.get("Drowsiness", 0)
    distracted_duration = duration_seconds_map.get("Distraction", 0)

    # Calculate duration in minutes
    dt_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    dt_end = datetime.fromisoformat(off_time.replace("Z", "+00:00"))
    duration_min = round((dt_end - dt_start).total_seconds() / 60, 2)

    summary_doc = {
        "device_id": device_id,
        "start_time": start_time,
        "end_time": off_time,
        "duration_min": duration_min,
        "total_events": len(event_count),

        "event_counts": {
            "yawn_detected": yawn_count,
            "eyes_closed_too_long": eyes_closed_count,
            "distraction_detected": distraction_count,
            "drowsiness_detected": drowsiness_count
        },

        #total duration in seconds
        "episode_durations": {
            "total_eyes_closed_seconds": eyes_close_duration,  
            "total_drowsy_seconds": drowsy_duration,
            "total_distracted_seconds": distracted_duration
        },
    }

    try:
        db.collection("summary").insert(summary_doc)
        print("[DB] Summary saved for device:", device_id)
    except Exception as e:
        print("[Error] Could not save summary:", e)

def fetch_summary_trend(device_id):

    query = """
    FOR s IN summary
    FILTER s.device_id == @device_id
    return s
    """

    summary = list(db.aql.execute(query, bind_vars={'device_id': device_id}))

    return summary

def store_trends_summary(device_id):
    user_summary_list = fetch_summary_trend(device_id)
    trends = analyze_driver_trends(user_summary_list)

    trends["device_id"] = device_id
    trends["timestamp"] = datetime.now().isoformat()
    
    save_trend(trends)
    return {"status": "processed"}
