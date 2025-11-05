from flask import Blueprint, request, jsonify
from app.services.ingest_services import store_event, store_state
from app.services.frontend_services import get_today_log, get_event_count, get_driver_state, get_weekly_report, get_monthly_report, get_weekly_event, get_weekly_log
from app.services.debug import get_today_log_debug, get_weekly_log_debug, get_weekly_event_debug

api_bp = Blueprint("api", __name__)

#----------------------------------------------------------#
#-------------------hardware route-------------------------#
#----------------------------------------------------------#

@api_bp.route("/kucing-event", methods=["POST"]) 
def receive_event():
    data = request.json
    result = store_event(data) 
    return jsonify(result)

@api_bp.route("/kucing-state", methods=["POST"]) 
def receive_state():
    data = request.json
    result = store_state(data) 
    return jsonify(result)

#----------------------------------------------------------#
#-------------------frontend route-------------------------#
#----------------------------------------------------------#

#-------------------login/signup-------------------------#

@api_bp.route('/login_route', methods=["POST"])
def match_user():
    pass

@api_bp.route('/login_route', methods=["POST"])
def store_user_lol():
    pass

#-------------------homepage-------------------------#

@api_bp.route('/current-events-list', methods=["GET"])
def fetch_homepage_log():
    data = get_today_log()
    return jsonify(data)

@api_bp.route('/real-time-status', methods=["GET"])
def fetch_homepage_pie():
    data = get_event_count()
    return jsonify(data)

@api_bp.route('/current-driver-status', methods=["GET"])
def fetch_homepage_state():
    data = get_driver_state()
    return jsonify(data)


#----------------week, month report-----------------------#

@api_bp.route('/thisweek', methods=["GET"])
def fetch_weekly_report():
    data = get_weekly_report()
    return jsonify(data)

@api_bp.route('/thismonth')
def fetch_monthly_report():
    data = get_monthly_report()
    return jsonify(data)


#------------------weekly activities------------------#

@api_bp.route('/weekly-activity', methods=["GET"])
def fetch_weekly_event():
    data = get_weekly_event()
    return jsonify(data)

@api_bp.route('/event-log-list', methods=["GET"])
def fetch_weekly_log_debug():
    data = get_weekly_log()
    return jsonify(data)

'''
session (nanti)
'''
