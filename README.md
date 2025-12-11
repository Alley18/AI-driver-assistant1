# ADAMS — Advanced Driver Alertness Monitoring System

ADAMS is a real-time driver safety system that detects fatigue (closed eyes), distraction, and loose steering-wheel grip using computer vision and embedded sensors. ADAMS triggers instant feedback through integrated hardware components such as a buzzer, vibration motor, and force sensor if such events is found.

<img width="826" height="1169" alt="a4" src="https://github.com/user-attachments/assets/8cee0c7e-4677-400b-87f6-62b69a1a68ed" />


## 🚗 Overview

ADAMS (Advanced Driver Alertness Monitoring System) is a real-time driver-monitoring solution designed to improve road safety by detecting fatigue, distraction, and unsafe grip behavior.
It combines computer vision, embedded sensors, and instant feedback mechanisms to alert drivers before an accident occurs.

The system provides:
- Real-time eye closure and face-orientation detection
- Grip-strength monitoring using a force sensor
- Immediate alerts via vibration motor and buzzer
- A mobile dashboard (Flutter) that displays all events with timestamps
- Backend database for storing and reviewing driver behavior data

## 🎯 Features 

Real-Time Driver Monitoring
- 👁️ Eye Closure Detection (fatigue)
- 😮 Yawning Detection
- 👤 Head Pose / Distraction Detection
- ✋ Grip Strength Monitoring using force sensor (FSR-402)
- 📈 Event Logging with Timestamps
- 🔊 Buzzer Alerts
- 🔆 Vibration Motor Feedback

Mobile Dashboard (Flutter)
- Live event display (fatigue, distraction, grip loss)
- Timestamped logs
- History review
- Post-Drive AI Insights (future-ready)
  - Behavior patterns
  - Recommendation Insight

## 📸 Preview
<img width="942" height="1178" alt="IMG_3323" src="https://github.com/user-attachments/assets/b135822a-3671-4682-b5ec-3cd1876c6988" />

<img width="1674" height="1256" alt="IMG_2884" src="https://github.com/user-attachments/assets/5e15bea0-0113-4541-81a8-4c4c2f371ed5" />


## 🧱 System Architecture
<img width="603" height="597" alt="SystemArchitecture" src="https://github.com/user-attachments/assets/dfc9cbb4-7d07-4c82-af6e-f8d38f3c5d3a" />


### Hardware Components
- ~~Pi Cam 2~~ USB Webcam	- Captures driver’s face for CV processing
- Force Sensor (FSR-402) - Measures steering-wheel grip
- 3V Coin Vibration Motor - Physical alert for distraction/fatigue
- Buzzer - Audible alarm
- Raspberry Pi 4 - Interfaces sensors with main system
- Steering-Wheel Toy - Holds sensors + wiring
- Other parts (wirings, resistors, transistors, adc module, etc...)

### Software
- OpenCV
- MediaPipe
- Flutter
- Flask
- ArangoDB

## 📊 Results

- ✅ Successfully detects fatigue, distraction, and loose grip in real time
- ✅ Minimal latency (<150ms avg) between detection and alert
- ✅ Flutter dashboard logs all events with timestamps
- ✅ Hardware prototype is compact and functional
- ✅ High detection accuracy in controlled environments


### 🧑‍🤝‍🧑 Department Team
- sduphy  [ Electrical Engineer / Leader ]
- monedxy [ Hardware Engineer ]
- melju   [ Front End Developer ]
- neku    [ Back End Developer ]
- soob    [ AI/ML Engineer ]


### License
ADAMS™ @ Sejong

