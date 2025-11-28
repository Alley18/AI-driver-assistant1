import Adafruit_ADS1x15

adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)
GAIN = 1

def read_fsr(threshold=72):
    """
    Reads the FSR sensor value.
    Returns True if hand is detected (pressure above threshold).
    """
    value = adc.read_adc(0, gain=GAIN)
    return value > threshold, value
