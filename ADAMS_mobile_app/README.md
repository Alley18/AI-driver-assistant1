# ADAMS Mobile Application
The ADAMS app converts raw alertness data collected from the hardware and backend into meaningful insights that help users understand their driving patterns. With AI-driven analysis and clean visualizations such as charts, summaries, and event logs, the app provides a comprehensive view of driver behavior and safety trends.

## Features
- **Real-time Status**
The main page that shows the driver's real-time status along with a quick overview of recent activity. It includes the driver's current state, a ring chart of event types, and a timestamped event log. 
  
- **Reports: Weekly and Monthly Charts**
The Reports page provides an overview of weekly and monthly event trends, with an easy toggle between report periods. A bar chart visualizes how events occur over time.

- **Reports: Trend Analysis**
The Trend Analysis feature uses an LLM to review the driver’s recent behavior, identify patterns, and generate clear feedback with recommended actions for safer driving.

- **Weekly Activity**
The Weekly Activity page offers a day-by-day breakdown of the current week, letting users scroll through past data. It features a ring chart of event types and a timestamped event log.

- **Session Logs**
The Session Logs page allows drivers to view all of their past driving sessions.

- **Device Connection**
The 'Link to you hardware' page handles device pairing, allowing users to register their ADAMS hardware using its unique ID so the app can authenticate and access the their data.

## Tech Stack
- **Framework:** Flutter
- **Backend:** Flask
- **Database:** Hive, ArangoDB
