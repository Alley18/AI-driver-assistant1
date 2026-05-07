import RPi.GPIO as GPIO
import time
import threading

class AdamsHardware:
    def __init__(self, buzzer_pin=18, force_pin=24):
        self.buzzer_pin = buzzer_pin
        self.force_pin = force_pin
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup Buzzer
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        
        # Setup Force Sensor (Assuming Digital Output or using a threshold)
        GPIO.setup(self.force_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        
        print("🔌 Hardware Subsystem: Pins 18 (Buzzer) & 24 (Force) Active")

    def alert_buzzer(self, duration=0.5):
        """Beeps the buzzer in a non-blocking thread."""
        def beep():
            GPIO.output(self.buzzer_pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
        
        threading.Thread(target=beep, daemon=True).start()

    def is_hands_on_wheel(self):
        """Returns True if the force sensor detects pressure."""
        return GPIO.input(self.force_pin) == GPIO.HIGH

    def cleanup(self):
        GPIO.cleanup()