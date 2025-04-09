from flask import Flask, jsonify, request, send_from_directory, render_template
# from initial_seal import InitialSealController
# from delivery_mechanism import run_delivery
import os
import algo as detection
import logging
import traceback

app = Flask(__name__)

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

        if username == 'admin' and password == '1234':
            return render_template('index.html')  
        else:
            error = "Invalid username or password."
            return render_template('login.html', error=error)

    return render_template('login.html')

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
        success = run_delivery()
        if success:
            return jsonify({
                "status": "success",
                "message": "Product packed successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to activate packaging mechanism"
            }), 500
    except Exception as e:
        logging.error(f"Delivery error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Delivery failed",
            "detail": str(e)
        }), 500

@app.route('/initial-seal', methods=['POST'])
def initial_seal():
    try:
        controller = InitialSealController()
        controller.perform_initial_seal()
        controller.cleanup()
        return jsonify({
            "status": "success",
            "message": "Initial sealing completed successfully"
        })
    except Exception as e:
        logging.error(f"Initial sealing error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Initial sealing failed",
            "detail": str(e)
        }), 500

@app.route('/images/<filename>')
def images(filename):
    try:
        return send_from_directory(IMAGE_FOLDER, filename)
    except FileNotFoundError:
        return jsonify({"error": "Image not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
