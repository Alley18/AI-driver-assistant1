from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🧠 Mock data by user
mock_data = {
    "adams": {
        "event_log_list": {
            "Monday": [
                {"time": "10:00", "type": "Distracted"},
                {"time": "10:01", "type": "Drowsy"},
                {"time": "10:23", "type": "Distracted"}
            ],
            "Tuesday": [
                {"time": "09:45", "type": "Loose grip"},
                {"time": "10:10", "type": "Distracted"}
            ],
            "Wednesday": [
                {"time": "13:50", "type": "Loose grip"},
                {"time": "21:15", "type": "Distracted"}
            ],
        },
        "weekly_activity": {
            "Monday": {"Distracted": 5, "Drowsy": 3, "Loose grip": 2, "Other": 1},
            "Tuesday": {"Distracted": 2, "Drowsy": 4, "Loose grip": 1, "Other": 0},
            "Wednesday": {"Distracted": 1, "Drowsy": 2, "Loose grip": 3, "Other": 2},
            "Thursday": {"Distracted": 1, "Drowsy": 2, "Loose grip": 3, "Other": 2},
            "Friday": {"Distracted": 1, "Drowsy": 2, "Loose grip": 3, "Eyes closed for too long": 2}
        },
        "real_time_status": {"Distracted": 1, "Drowsy": 2, "Loose grip": 3},
        "current_events_list": [
            {"time": "10:00", "type": "Distracted"},
            {"time": "10:01", "type": "Drowsy"},
            {"time": "10:23", "type": "Distracted"},
            {"time": "13:50", "type": "Loose grip"},
            {"time": "21:15", "type": "Distracted"}
        ],
        "this_week": {"Mon": 1, "Tue": 1, "Wed": 1},
        "this_month": {
            "01/11": 3, "02/11": 5, "03/11": 2, "04/11": 7, "05/11": 1
        },
        "current_driver_status": {"driver_state": "distracted"}
    }
}

@app.route('/event-log-list')
def get_event_log_list():
    username = request.args.get("username", None)
    
    # If no username provided
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    # Check if user exists in mock_data
    if username not in mock_data:
        return jsonify({"error": "User not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[username]["event_log_list"])

@app.route('/weekly-activity')
def get_weekly_activity():
    username = request.args.get("username", None)
    
    # If no username provided
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    # Check if user exists in mock_data
    if username not in mock_data:
        return jsonify({"error": "User not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[username]["weekly_activity"])

@app.route('/real-time-status')
def get_real_time_status():
    username = request.args.get("username", None)
    
    # If no username provided
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    # Check if user exists in mock_data
    if username not in mock_data:
        return jsonify({"error": "User not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[username]["real_time_status"])

@app.route('/current-events-list')
def get_current_events_list():
    username = request.args.get("username", None)
    
    # If no username provided
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    # Check if user exists in mock_data
    if username not in mock_data:
        return jsonify({"error": "User not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[username]["current_events_list"])

@app.route('/thisweek')
def get_this_week():
    username = request.args.get("username")
    category = request.args.get("category")  # optional, if needed
    
    if not username or username not in mock_data:
        return jsonify({"error": "User not found"}), 404
    
    # category could be used for special filtering if needed
    return jsonify(mock_data[username]["this_week"])

@app.route('/thismonth')
def get_this_month():
    username = request.args.get("username")
    category = request.args.get("category")  # optional, if needed
    
    if not username or username not in mock_data:
        return jsonify({"error": "User not found"}), 404
    
    # category could be used for special filtering if needed
    return jsonify(mock_data[username]["this_month"])

@app.route('/current-driver-status')
def get_driver_status():
    username = request.args.get("username", None)
    
    # If no username provided
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    # Check if user exists in mock_data
    if username not in mock_data:
        return jsonify({"error": "User not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[username]["current_driver_status"])

@app.route('/get-data', methods=['POST'])
def get_data():
    data = request.get_json()
    username = data.get('username')

    if username not in mock_data:
        return jsonify({"error": "User not found"}), 404

    return jsonify(mock_data[username])

