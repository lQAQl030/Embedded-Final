from flask import Flask
# import RPi.GPIO as GPIO
from imu import ICM20948

# Setup
imu = ICM20948()
# LED_PIN = 17  # BCM numbering (change to match your wiring)
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(LED_PIN, GPIO.OUT)

# Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return 'Raspberry Pi GPIO Server is running!'

@app.route('/slash')
def slash_power():
    return imu.slash_power()

# @app.route('/led/on')
# def led_on():
#     GPIO.output(LED_PIN, GPIO.HIGH)
#     return '✅ LED turned ON'

# @app.route('/led/off')
# def led_off():
#     GPIO.output(LED_PIN, GPIO.LOW)
#     return '✅ LED turned OFF'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
