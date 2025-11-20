from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# mock user db
users = {
    "adams": "u001"
}

# Mock data by user
mock_data = {
    "u001": {
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
    user_id = request.args.get("userID", None)
    
    # If no username provided
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Check if user exists in mock_data
    if user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[user_id]["event_log_list"])

@app.route('/weekly-activity')
def get_weekly_activity():
    user_id = request.args.get("userID", None)
    
    # If no username provided
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Check if user exists in mock_data
    if user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[user_id]["weekly_activity"])

@app.route('/real-time-status')
def get_real_time_status():
    user_id = request.args.get("userID", None)
    
    # If no username provided
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Check if user exists in mock_data
    if user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[user_id]["real_time_status"])

@app.route('/current-events-list')
def get_current_events_list():
    user_id = request.args.get("userID", None)
    
    # If no username provided
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Check if user exists in mock_data
    if user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[user_id]["current_events_list"])

@app.route('/thisweek')
def get_this_week():
    user_id = request.args.get("userID")
    category = request.args.get("category") 
    
    if not user_id or user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404
    
    # category could be used for special filtering if needed
    return jsonify(mock_data[user_id]["this_week"])

@app.route('/thismonth')
def get_this_month():
    user_id = request.args.get("userID")
    category = request.args.get("category")
    
    if not user_id or user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404
    
    # category could be used for special filtering if needed
    return jsonify(mock_data[user_id]["this_month"])

@app.route('/current-driver-status')
def get_driver_status():
    user_id = request.args.get("userID", None)
    
    # If no username provided
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    # Check if user exists in mock_data
    if user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404
    
    # Return user-specific data
    return jsonify(mock_data[user_id]["current_driver_status"])

@app.route('/get-data', methods=['POST'])
def get_data():
    data = request.get_json()
    user_id = data.get('userID')

    if user_id not in mock_data:
        return jsonify({"error": "User ID not found"}), 404

    return jsonify(mock_data[user_id])

# ------ receive username, send user id ------ #
@app.route('/get_user_id', methods=['POST'])
def get_user_id():
    data = request.get_json()
    username = data.get("username")

    if not username:
        return jsonify({"error": "Username missing"}), 400

    # Return existing ID or create a new one dynamically
    if username not in users:
        users[username] = f"u{len(users) + 1:03}"

    return jsonify({"user_id": users[username]})




