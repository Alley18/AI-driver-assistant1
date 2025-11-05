from app.services.time_services import return_today, return_from_monday
from app.db.arango_db import db

def get_today_log_debug():
    today = return_today().strftime('%Y-%m-%d')
    print(f"========== DEBUG get_today_log ==========")
    print(f"Today's date: {today}")
    
    # Do we have ANY events at all?
    count_query = "RETURN LENGTH(event)"
    count_result = list(db.aql.execute(count_query))
    print(f"Total events in collection: {count_result}")
    
    # What do the timestamps look like?
    sample_query = "FOR e IN event LIMIT 3 RETURN {timestamp: e.timestamp, type: e.type}"
    sample_result = list(db.aql.execute(sample_query))
    print(f"Sample events: {sample_result}")
    
    # What dates do we actually have?
    date_query = """
    FOR e IN event
        LET dateStr = DATE_FORMAT(e.timestamp, "%Y-%m-%d")
        COLLECT date = dateStr WITH COUNT INTO count
        RETURN {date, count}
    """
    date_result = list(db.aql.execute(date_query))
    print(f"Dates in database: {date_result}")
    
    # Your actual query
    query = """
    FOR e IN event
        FILTER DATE_FORMAT(e.timestamp, "%Y-%m-%d") == @today
        SORT e.timestamp ASC
        RETURN {
            "time": DATE_FORMAT(e.timestamp, "%H:%M"),
            "type": e.type
        }
    """
    
    cursor = db.aql.execute(query, bind_vars={'today': today})
    result = list(cursor)
    print(f"Filtered result count: {len(result)}")
    print(f"Filtered result: {result}")
    print(f"==========================================")
    
    return result

def get_weekly_log_debug():
    today = return_today()
    last_monday = return_from_monday()
    today_str = today.strftime('%Y-%m-%d')
    monday_str = last_monday.strftime('%Y-%m-%d')

    query = """
    FOR e IN event
        FILTER e.date >= @monday AND e.date <= @today
        FILTER e.type != null
        RETURN {day: e.day, time: e.time, type: e.type}
    """
    cursor = db.aql.execute(query, bind_vars={'monday': monday_str, 'today': today_str})
    events = list(cursor)

    # Group events by day
    result = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": []
    }

    for event in events:
        day = event.get("day")
        time = event.get("time")
        event_type = event.get("type")
        
        if day and time and event_type and day in result:
            result[day].append({
                "time": time,
                "type": event_type
            })

    # Sort events by time within each day
    for day in result:
        result[day].sort(key=lambda x: x["time"])

    return result

def get_weekly_event_debug():
    today = return_today()
    last_monday = return_from_monday()
    today_str = today.strftime('%Y-%m-%d')
    monday_str = last_monday.strftime('%Y-%m-%d')
    
    print(f"========== DEBUG get_weekly_event ==========")
    print(f"Today: {today}")
    print(f"Last Monday: {last_monday}")
    print(f"Date range: {monday_str} to {today_str}")

    query = """
    FOR e IN event
        LET day = e.day
        FILTER e.date >= @monday AND e.date <= @today
        COLLECT day = day, type = e.type WITH COUNT INTO freq
        RETURN {day, type, freq}
    """

    cursor = db.aql.execute(query, bind_vars={'monday': monday_str, 'today': today_str})
    raw_result = list(cursor)
    
    print(f"Total grouped results: {len(raw_result)}")
    print(f"Raw query result: {raw_result}")

    result = {}
    processed_count = 0
    
    for item in raw_result:
        day = item['day'] if item['day'] else 'Other'
        type_ = item['type'] if item['type'] else 'Other'
        freq = item['freq']
        
        print(f"Processing: day={day}, type={type_}, freq={freq}")
        
        # If day not yet in result, initialize
        if day not in result:
            result[day] = {}
            print(f"  -> Initialized day: {day}")
        
        # Store the count per type
        result[day][type_] = freq
        processed_count += 1
        print(f"  -> Added to {day}: {type_} = {freq}")

    print(f"\n--- Summary ---")
    print(f"Processed: {processed_count}")
    print(f"Unique days: {len(result)}")
    print(f"\nFinal result structure:")
    for day, types in result.items():
        print(f"  {day}: {types}")
    print(f"==========================================\n")

    return result

