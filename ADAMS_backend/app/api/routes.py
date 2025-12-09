import requests
from flask import Blueprint, request, jsonify
from ..services.auth_services import get_userid, is_userid_provided, auth_match, hash_password, is_authorized_device, get_deviceid
from ..services.storing_services import save_user, save_device
from ..services.hardware_services import store_state ,store_event
from ..services.client_services import get_today_log, get_event_count, get_driver_state, get_weekly_report, get_monthly_report, get_weekly_event, get_weekly_log
from ..services.sessions_services import get_sessions
from ..services.feedback_services import fetch_feedback

HARDWARE_IP = "172.19.23.147"
api_bp = Blueprint("api", __name__)

#----------------------------------------------------------#
#----------------------llm route---------------------------#
#----------------------------------------------------------#
@api_bp.route("/feedback", methods=["GET"])
def get_feedback():
    user_id = request.args.get("userID", None)
    result = fetch_feedback(user_id)
    return jsonify(result)

#----------------------------------------------------------#
#-------------------hardware route-------------------------#
#----------------------------------------------------------#
@api_bp.route("/on-route", methods=["GET"])
def start_session():
    try:
        resp = requests.get(f"http://{HARDWARE_IP}:8080/start", timeout=5)
        return jsonify({
            "status": "session_started",
            "status_code": resp.status_code
        }), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@api_bp.route("/off-route", methods=["GET"])
def stop_session():
    try:
        resp = requests.get(f"http://{HARDWARE_IP}:8080/stop", timeout=5)
        return jsonify({
            "status": "session_stopped",
            "status_code": resp.status_code
        }), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@api_bp.route("/kucing-event", methods=["POST"]) 
def receive_event():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    result = store_event(data) 
    return jsonify(result)

@api_bp.route("/kucing-state", methods=["POST"]) 
def receive_state():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    result = store_state(data) 
    return jsonify(result)

#----------------------------------------------------------#
#-------------------frontend route-------------------------#
#----------------------------------------------------------#

#-------------------login/signup/register-------------------------#

@api_bp.route('/login-route', methods=['POST'])
def login_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    success, error_msg, user_id, username = auth_match(username, password)
    device_id = get_deviceid(user_id)
    if not success:
        # Authentication failed
        return jsonify({"error": error_msg}), 404

    # Authentication successful
    return jsonify({"user_id": user_id, "username": username, 'device_id':device_id}), 200

@api_bp.route('/signup-route', methods=["POST"])
def store_user_lol():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
    try:
        password = data.get('password')
        hashed_pw = hash_password(password)
        
        data['password_hash'] = hashed_pw
        data.pop('password', None)

        success, msg = save_user(data)
        if not success:
            return jsonify({"error": msg}), 409

        username = data.get("username")
        user_id = get_userid(username)
        
        if not user_id:
            return jsonify({"error": "User not found after store_user"}), 404
        return jsonify({"user_id": user_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route('/register-device', methods=["POST"])
def device_user():
    data = request.get_json()
    device_id = data.get("device_id")

    if not device_id or not is_authorized_device(device_id):
        return jsonify({"error": "unauthorized or missing device_id"}), 403

    result = save_device(data)
    return jsonify(result)

    
#-------------------homepage-------------------------#

@api_bp.route('/current-events-list', methods=["GET"])
def fetch_homepage_log():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_today_log(user_id)
    return jsonify(data)

@api_bp.route('/real-time-status', methods=["GET"])
def fetch_homepage_pie():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_event_count(user_id)
    return jsonify(data)

@api_bp.route('/current-driver-status', methods=["GET"])
def fetch_homepage_state():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_driver_state(user_id)
    return jsonify(data)


#----------------week, month report-----------------------#

@api_bp.route('/thisweek', methods=["GET"])
def fetch_weekly_report():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_weekly_report(user_id)
    return jsonify(data)

@api_bp.route('/thismonth')
def fetch_monthly_report():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_monthly_report(user_id)
    return jsonify(data)


#------------------weekly activities------------------#

@api_bp.route('/weekly-activity', methods=["GET"])
def fetch_weekly_event():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_weekly_event(user_id)
    return jsonify(data)

@api_bp.route('/event-log-list', methods=["GET"])
def fetch_weekly_log_debug():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_weekly_log(user_id)
    return jsonify(data)

#------------------session------------------#

@api_bp.route('/sessions', methods=["GET"])
def fetch_all_sessions():
    user_id = request.args.get("userID", None)
    is_userid_provided(user_id)
    data = get_sessions(user_id)
    return jsonify(data)

