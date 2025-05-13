from flask import Flask, jsonify, request, send_from_directory, render_template
from initial_seal import InitialSealController
from flask import session 
from delivery_mechanism import run_delivery
from emergency_stop import emergency_stop as hardware_emergency_stop
import os
import algot as detection
import logging
import traceback

app = Flask(__name__)
app.secret_key = '1234'

# Logging configuration
logging.basicConfig(level=logging.DEBUG)

# Directory where images are stored
IMAGE_FOLDER = '/home/team48/packaging_env/images'

from flask import redirect, url_for

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'team35' and password == 'team35':
            session['authenticated'] = True  # Set session flag
            return render_template('index.html')
        else:
            error = "Invalid username or password."
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/capture-dimensions', methods=['GET'])
def capture_dimensions():
    try:
        # Store result in session instead of just returning
        session['measurement_data'] = detection.measure_and_optimize()
        
        if session['measurement_data']:
            result = session['measurement_data']
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
            return jsonify({"error": "Measurement failed"}), 500
            
    except Exception as e:
        logging.error(f"Capture error: {str(e)}")
        return jsonify({"error": "Measurement failed"}), 500

@app.route('/deliver-product', methods=['POST'])
def deliver_product():
    try:
        if 'measurement_data' not in session:
            return jsonify({"error": "Capture dimensions first"}), 400
            
        wrap_width = session['measurement_data']['bubble_wrap_size']['width']
        wrap_length = session['measurement_data']['bubble_wrap_size']['length']

        # Call with both width and length
        success = run_delivery(wrap_width, wrap_length)
        
        if success:
            return jsonify({"status": "success"})
        return jsonify({"status": "error"}), 500
            
    except Exception as e:
        logging.error(f"Delivery error: {str(e)}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/initial-feed', methods=['POST'])
def initial_feed():
    controller = None
    try:
        if not session.get('authenticated'):
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        controller = InitialSealController()
        controller.perform_feeding()  # Only does the feeding
        return jsonify({"status": "success", "message": "Bubble wrap feeding completed"})

    except Exception as e:
        logging.error(f"Feeding error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if controller:
            controller.cleanup()

@app.route('/initial-seal-actuate', methods=['POST'])
def initial_seal_actuate():
    controller = None
    try:

        app.logger.info("Initializing sealing controller...")
        controller = InitialSealController()
        app.logger.info("Performing sealing operation...")
        controller.perform_sealing()
        return jsonify({"status": "success", "message": "Actuator sealing completed"})

    except Exception as e:
        logging.error(f"Sealing error: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if controller:
            controller.cleanup()
        
@app.route('/emergency-stop', methods=['POST'])
def emergency_stop():
    try:
        hardware_emergency_stop()
        return jsonify({
            "status": "success",
            "message": "Emergency stop activated. All hardware stopped."
        })
    except Exception as e:
        logging.error(f"Emergency stop error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Emergency stop failed",
            "detail": str(e)
        }), 500

@app.route('/images/<filename>')
def images(filename):
    try:
        return send_from_directory(IMAGE_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404
@app.route('/images', methods=['GET'])
def list_images():
    try:
        files = os.listdir(IMAGE_FOLDER)
        images = [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        return jsonify({"images": images})
    except Exception as e:
        return jsonify({"error": "Failed to list images", "detail": str(e)}), 500
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
