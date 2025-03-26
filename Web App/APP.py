from flask import Flask, jsonify, request, send_from_directory, render_template
import os
import ALGOPYTEST as detection  # Changed to use the modified ALGO.py module
import logging
import RPi.GPIO as GPIO
import time
import atexit

app = Flask(__name__)

# Configuring logging for better debug output
logging.basicConfig(level=logging.DEBUG)

# Path to the directory where images are stored (adjust to match your ALGO.py image save location)
IMAGE_FOLDER = '/home/team48/packaging_env/images'

# --- Servo Setup for Delivery Notification ---
SERVO_PIN = 4  # GPIO 4
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo_pwm = GPIO.PWM(SERVO_PIN, 50)
servo_pwm.start(0)

def set_servo_angle(angle):
    """Rotate the servo to the specified angle (delivery mode)."""
    duty = (angle / 18) + 2.5
    GPIO.output(SERVO_PIN, True)
    servo_pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    servo_pwm.ChangeDutyCycle(0)

@atexit.register
def cleanup_gpio():
    servo_pwm.stop()
    GPIO.cleanup()

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('DESIGN.html')

@app.route('/capture-dimensions', methods=['GET'])
def capture_dimensions():
    try:
        result = detection.measure_and_optimize()
        if result:
            front_image_url = os.path.join('/images', os.path.basename(result["front_image_path"]))

            # Trigger servo to indicate delivery action
            set_servo_angle(85)

            return jsonify({
                "measured_dimensions": {
                    "length": result["object_dimensions"][0],
                    "width": result["object_dimensions"][1],
                    "height": result["object_dimensions"][2]
                },
                "optimal_dimensions": result["optimized_dimensions"],
                "bubble_wrap_size": result["bubble_wrap_size"],
                "image_url": front_image_url,
                "delivery": True  # Flag to show alert on frontend
            })
        else:
            return jsonify({"error": "Measurement and optimization yielded no results"}), 500
    except Exception as e:
        return jsonify({"error": "Failed to capture dimensions.", "detail": str(e)}), 500

@app.route('/images/<filename>')
def images(filename):
    try:
        return send_from_directory(IMAGE_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)