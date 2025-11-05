from app.db.arango_db import db
from app.services.time_services import return_today, return_from_monday

#-----------------------------------------------
#home
#-----------------------------------------------

#/current-events-list 
def get_today_log():
    today = return_today().strftime('%Y-%m-%d')

    query = """
    FOR e IN event
        LET eventDate = SUBSTRING(e.timestamp, 0, 10)
        FILTER eventDate == @today
        SORT e.timestamp ASC
        RETURN {
            "time": SUBSTRING(e.timestamp, 11, 5),
            "type": e.type
        }
    """
    
    cursor = db.aql.execute(query, bind_vars={'today': today})
    result = list(cursor)
    return result

#/real-time-status
def get_event_count():
    today = return_today().strftime('%Y-%m-%d')

    query = """
    FOR e IN event
        LET eventDate = SUBSTRING(e.timestamp, 0, 10)
        FILTER eventDate == @today
        COLLECT type = e.type WITH COUNT INTO freq
        RETURN { type: type, freq: freq }
    """

    cursor = db.aql.execute(query, bind_vars={'today': today})

    result = {}
    for item in cursor:
        key = item.get('type') or 'Other'
        result[key] = item.get('freq', 0)

    return result

#/current-driver-status
def get_driver_state():
    query = """
    FOR s IN state
        SORT s.timestamp DESC
        LIMIT 1
        RETURN s.driver_state
    """
    cursor = db.aql.execute(query)
    state = next(cursor, None)
    return {"driver_state": state}


#-----------------------------------------------
#report
#-----------------------------------------------

#/thisweek
def get_weekly_report():
    day_map = {
        "Monday": "Mon",
        "Tuesday": "Tue",
        "Wednesday": "Wed",
        "Thursday": "Thu",
        "Friday": "Fri",
        "Saturday": "Sat",
        "Sunday": "Sun"
    }

    weekdays = list(day_map.keys())
    today_index = return_today().weekday()
    valid_days = weekdays[:today_index + 1]

    query = """
    FOR e IN event
        FILTER e.day IN @valid_days
        COLLECT day = e.day WITH COUNT INTO freq
        RETURN { day, freq }
    """
    cursor = db.aql.execute(query, bind_vars={'valid_days': valid_days})

    result = {}
    for item in cursor:
        short_day = day_map.get(item['day'], item['day'])
        result[short_day] = item['freq']

    return result

#/thismonth
def get_monthly_report():
    today = return_today()
    month_start = today.replace(day=1)

    today_str = today.strftime('%Y-%m-%d')
    month_start_str = month_start.strftime('%Y-%m-%d')

    query = """
    FOR e IN event
        FILTER e.date >= @month_start AND e.date <= @today
        LET dateStr = CONCAT(SUBSTRING(e.date, 8, 2), "/", SUBSTRING(e.date, 5, 2))
        COLLECT date_str = dateStr WITH COUNT INTO freq
        RETURN { date_str, freq }
    """
    cursor = db.aql.execute(query, bind_vars={'month_start': month_start_str, 'today': today_str})

    result = {}
    for item in cursor:
        result[item['date_str']] = item['freq']

    return result

#-----------------------------------------------
#weekly activities
#-----------------------------------------------

#/event-log-list
def get_weekly_log():
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

#/weekly-activity
def get_weekly_event():
    today = return_today()
    last_monday = return_from_monday()
    today_str = today.strftime('%Y-%m-%d')
    monday_str = last_monday.strftime('%Y-%m-%d')

    query = """
    FOR e IN event
        FILTER e.date >= @monday AND e.date <= @today
        FILTER e.type != null
        COLLECT day = e.day, type = e.type WITH COUNT INTO freq
        RETURN {day, type, freq}
    """

    cursor = db.aql.execute(query, bind_vars={'monday': monday_str, 'today': today_str})
    raw_result = list(cursor)

    # Initialize all weekdays
    result = {
        "Monday": {},
        "Tuesday": {},
        "Wednesday": {},
        "Thursday": {},
        "Friday": {},
        "Saturday": {},
        "Sunday": {}
    }
    
    for item in raw_result:
        day = item.get('day')
        type_ = item.get('type', 'Other')
        freq = item.get('freq', 0)
        
        if day and day in result:
            result[day][type_] = freq

    return result

