from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/weekly-data')
def get_weekly_data():
    data = {"Mon": 1,
      "Tue": 2,
      "Wed": 1,
      "Thu": 3,
      "Fri": 1,
      "Sat": 1,
      "Sun": 2,}
    return jsonify(data)

@app.route('/monthly-data')
def get_monthly_data():
    data = {
      "Jan": 1,
      "Feb": 2,
      "Mar": 1,
      "Apr": 3,
      "May": 1,
      "Jun": 1,
      "Jul": 2,
      "Aug": 5,
      "Sep": 3,
      "Oct": 5,
      "Nov": 1,
      "Dec": 2,
    }
    return jsonify(data)

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

@app.route('/detailed-daily-report')
def get_detailed_daily_report():
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
  }
    }
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)