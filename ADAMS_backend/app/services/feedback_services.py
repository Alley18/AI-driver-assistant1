import json
from datetime import datetime
from typing import Dict, Any, Optional
from app.db.arango_db import db
from app.services.auth_services import get_deviceid
from app.services.storing_services import save_feedback
from app.ai.llm_feedback import generate_driving_coach_feedback, parse_feedback_response

def generate_feedback(device_id) -> Dict[str, Any]:
    summary = fetch_latest_summary(device_id)
    trend = fetch_latest_trend(device_id)
    
    if not summary:
        return {
            "error": "No recent session summary found",
            "device_id": device_id
        }
    
    session_json = json.dumps(summary)
    trend_json = json.dumps(trend)
    
    try:
        feedback_text = generate_driving_coach_feedback(session_json, trend_json)
        print(f"Feedback text: {feedback_text}")
        print(feedback_text["feedback"])  
        print(feedback_text["recommended_action"])
        parsed_feedback = parse_feedback_response(feedback_text)
    except Exception as e:
        return {
            "error": "Failed to generate feedback",
            "details": str(e),
            "device_id": device_id,
        }

    feedback_doc = {
        "device_id": device_id,
        "feedback": parsed_feedback["feedback"],
        "recommended_action": parsed_feedback["recommended_action"],
        "timestamp": datetime.now().isoformat()
    }

    save_feedback(feedback_doc)

def fetch_latest_summary(device_id: str) -> Optional[Dict]:
    summary_query = """
    FOR s IN summary
        FILTER s.device_id == @device_id
        SORT s.timestamp DESC
        LIMIT 1
        RETURN s
    """
    cursor = db.aql.execute(summary_query, bind_vars={'device_id': device_id})
    
    return next(cursor, None)

def fetch_latest_trend(device_id: str) -> Optional[Dict]:
    trend_query = """
    FOR t IN trend
        FILTER t.device_id == @device_id
        SORT t.timestamp DESC
        LIMIT 1
        RETURN t
    """
    cursor = db.aql.execute(trend_query, bind_vars={'device_id': device_id})
    
    return next(cursor, None)

def fetch_feedback(user_id) -> Optional[Dict]:
    device_id = get_deviceid(user_id)
    
    trend_query = """
    FOR f IN feedback
        FILTER f.device_id == @device_id
        SORT f.timestamp DESC
        LIMIT 1
        RETURN {
            "feedback": f.feedback,
            "recommended_action": f.recommended_action
        }
    """
    cursor = db.aql.execute(trend_query, bind_vars={'device_id': device_id})
    
    return next(cursor, None)
