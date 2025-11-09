# ADAMS
a.k.a Advanced Driver Alertness Monitoring System 

ADAMS is a real-time driver safety system that detects fatigue (closed eyes), distraction, and loose steering-wheel grip using computer vision and embedded sensors. ADAMS triggers instant feedback through integrated hardware components such as a buzzer, vibration motor, and force sensor if such events is found.

### Department Team
- sduphy  [ Electrical Engineer / Leader ]
- monedxy [ Hardware Engineer ]
- melju   [ Front End Developer ]
- neku    [ Back End Developer ]
- soob    [ AI/ML Engineer ]

### Overview

Road accidents are often caused by driver fatigue, distraction, and loss of steering control. ADAMS aims to reduce these risks by continuously monitoring the driver’s behavior and providing immediate alerts. ADAMS is designed to be low-cost, portable, and adaptable for research and automotive integration.

The system combines:
- Computer vision (real-time eye and head tracking)
- Steering-wheel force sensing
- Physical alerts
- An interactive UI dashboard for data visualization

PS; 
The logic can run on PC, laptop, or small single-board computers,
Works with USB webcams or onboard cameras,
Configurable detection thresholds

### Features 

Driver Monitoring
- Eye closure detection (fatigue)
- Yawning detection
- Distraction/Head pose detection (detects if driver is looking away from road)
- Force sensor to measure grip strength (detects loose or absent grip)
- Data logging
- Buzzer alarm
- Vibration motor feedback

Mobile Dashboard
- Displays all event logs in real time
- Shows timestamps and event type
- Allows history review

### Preview
*insert ss*

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
- DjangoDB
- apa lagi

### System Architecture
*cam -> logic -> dashboard + hardwares* zz

### License
ADAMS™

