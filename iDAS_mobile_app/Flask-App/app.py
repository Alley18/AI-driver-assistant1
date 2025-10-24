import random
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/event-log-list')
def get_event_log_list():
    data = {
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
    }
    return jsonify(data)

@app.route('/weekly-activity')
def get_weekly_activity():
    data = {
        "Monday": {
    "Distracted": 5,
    "Drowsy": 3,
    "Loose grip": 2,
    "Other": 1
  },
  "Tuesday": {
    "Distracted": 2,
    "Drowsy": 4,
    "Loose grip": 1,
    "Other": 0
  },
  "Wednesday": {
    "Distracted": 1,
    "Drowsy": 2,
    "Loose grip": 3,
    "Other": 2
  },
  "Thursday": {
    "Distracted": 1,
    "Drowsy": 2,
    "Loose grip": 3,
    "Other": 2
  },
  "Friday": {
    "Distracted": 1,
    "Drowsy": 2,
    "Loose grip": 3,
    "Other": 2
  }
    }
    return jsonify(data)

@app.route('/real-time-status')
def get_real_time_status():
    data = {
    "Distracted": 1,
    "Drowsy": 2,
    "Loose grip": 3,
    "Other": 2
    }
    return jsonify(data)

@app.route('/current-events-list')
def get_current_events_list():
    data = [
        {"time": "10:00", "type": "Distracted"},
        {"time": "10:01", "type": "Drowsy"},
        {"time": "10:23", "type": "Distracted"},
        {"time": "13:50", "type": "Loose grip"},
        {"time": "21:15", "type": "Distracted"}
    ]
    return jsonify(data)

@app.route('/thisweek')
def get_last_7_days():
    data = {"Mon": 1,
      "Tue": 2,
      "Wed": 1,
      "Thu": 3,
      "Fri": 1}
    return jsonify(data)

@app.route('/thismonth')
def get_last_30_days():
    data = {
  "01/10": 3,
  "02/10": 5,
  "03/10": 2,
  "04/10": 7,
  "05/10": 1,
  "06/10": 4,
  "07/10": 6,
  "08/10": 2,
  "09/10": 5,
  "10/10": 3,
  "11/10": 4,
  "12/10": 7,
  "13/10": 1,
  "14/10": 5,
  "15/10": 2,
  "16/10": 3,
  "17/10": 6,
  "18/10": 4,
  "19/10": 2,
  "20/10": 5,
  "21/10": 3,
  "22/10": 4,
  "23/10": 7,
  "24/10": 1
}
    return jsonify(data)


@app.route('/current-driver-status')
def get_driver_status():
    data = {
        "status" : "Mildly Fatigued"
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)