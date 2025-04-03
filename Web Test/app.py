from flask import Flask, jsonify, request, send_from_directory, render_template
import os
import testalgo as detection
import logging
import traceback

app = Flask(__name__)

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

# Directory where images are stored
IMAGE_FOLDER = '/home/team48/packaging_env/images'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture-dimensions', methods=['GET'])
def capture_dimensions():
    try:
        result = detection.measure_and_optimize()
        if result:
            front_image_url = os.path.join('/images', os.path.basename(result["front_image_path"]))
            return jsonify({
                "measured_dimensions": {
                    "length": result["object_dimensions"][0],
                    "width": result["object_dimensions"][1],
                    "height": result["object_dimensions"][2]
                },
                "optimal_dimensions": result["optimized_dimensions"],
                "bubble_wrap_size": result["bubble_wrap_size"],
                "image_url": front_image_url,
                "delivery": True
            })
        else:
            return jsonify({"error": "Measurement and optimization yielded no results"}), 500
    except Exception as e:
        logging.error("Capture error: %s", str(e))
        logging.error(traceback.format_exc())
        return jsonify({"error": "Failed to capture dimensions.", "detail": str(e)}), 500

@app.route('/deliver-product', methods=['POST'])
def deliver_product():
    try:
        import RPi.GPIO as GPIO
        import time

        SERVO_PIN = 4
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(SERVO_PIN, GPIO.OUT)

        pwm = GPIO.PWM(SERVO_PIN, 50)
        pwm.start(0)

        angle = 85
        duty = (angle / 18) + 2.5
        GPIO.output(SERVO_PIN, True)
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        GPIO.output(SERVO_PIN, False)
        pwm.ChangeDutyCycle(0)

        pwm.stop()
        GPIO.cleanup()

        return jsonify({"status": "Servo moved to delivery position."})
    except Exception as e:
        return jsonify({"error": "Failed to activate servo", "detail": str(e)}), 500

@app.route('/images/<filename>')
def images(filename):
    try:
        return send_from_directory(IMAGE_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
