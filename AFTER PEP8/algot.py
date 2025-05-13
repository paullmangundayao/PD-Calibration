import RPi.GPIO as GPIO
import time
import numpy as np
import random
import cv2
import datetime
import logging

# Configure logging for debugging output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Configuration and Setup ---

# GPIO pin assignments for ultrasonic sensor and servo motor.
TRIG_PIN = 13      # Trigger pin for HC-SR04
ECHO_PIN = 6       # Echo pin for HC-SR04
SERVO_PIN = 19     # PWM output pin for servo controlling the side camera

# Control constants
NEUTRAL_ANGLE = 90         # Neutral servo angle (degrees)
SCALING_FACTOR = 1.2       # Factor for converting distance error to servo angle
TARGET_DISTANCE = 15       # Target distance in cm

# Genetic algorithm and optimization constants
POPULATION_SIZE = 10
GENERATIONS = 50
SEALING_MARGIN = 0.5       # Extra margin added to object dimensions
MUTATION_RATE = 0.1

# Pixel-to-cm ratios (calibrated values)
PIXEL_TO_CM_RATIO_FRONT = 0.06035  # Front camera calibration
PIXEL_TO_CM_RATIO_SIDE = 0.03895   # Side camera calibration


# --- Setup GPIO ---
logging.debug("Setting up GPIO...")
GPIO.setmode(GPIO.BCM)          # Initialize the GPIO mode to BCM
GPIO.setwarnings(False)         # Disable warnings if reinitializing GPIO
GPIO.setup(TRIG_PIN, GPIO.OUT)  # Set trigger pin as output
GPIO.setup(ECHO_PIN, GPIO.IN)   # Set echo pin as input

logging.debug("GPIO setup complete.")


# --- Ultrasonic Sensor and Servo Control Functions ---

def measure_distance(timeout=0.2):
    """Measure distance using HC-SR04 ultrasonic sensor.
    
    Triggers the sensor and returns measured distance in centimeters.
    Includes timeout to avoid infinite loops if no echo is received.
    """
    logging.debug("Measuring distance...")

    # Ensure GPIO is set up
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)

    GPIO.output(TRIG_PIN, False)
    time.sleep(0.0002)  # 200 microseconds delay

    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)  # 10 microseconds pulse
    GPIO.output(TRIG_PIN, False)

    start_time = time.time()
    stop_time = time.time()

    # Wait for echo to start with timeout
    echo_start = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
        if time.time() - echo_start > timeout:
            logging.error("Timeout waiting for echo to start.")
            return None

    # Wait for echo to end with timeout
    echo_end = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()
        if time.time() - echo_end > timeout:
            logging.error("Timeout waiting for echo to end.")
            return None

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2  # cm
    logging.debug(f"Distance measured: {distance:.2f} cm")

    return distance


def set_servo_angle(angle):
    """Set servo to specified angle (0 to 160 degrees).
    
    Creates fresh PWM instance for each movement.
    """
    logging.debug(f"Setting servo angle to: {angle} degrees")
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(SERVO_PIN, GPIO.OUT)

        servo = GPIO.PWM(SERVO_PIN, 50)
        servo.start(0)

        angle = max(0, min(160, angle))  # Clamp angle
        duty_cycle = angle / 18.0 + 2.5
        servo.ChangeDutyCycle(duty_cycle)
        time.sleep(0.5)
        servo.ChangeDutyCycle(0)

        servo.stop()
        del servo
        GPIO.cleanup(SERVO_PIN)  # Only clean up used pin
        logging.debug("Servo angle set and cleaned.")
    except Exception as e:
        logging.error(f"[Servo ERROR] {e}")
        GPIO.cleanup(SERVO_PIN)


def adjust_side_camera_position(
        target_distance=TARGET_DISTANCE,
        tolerance=0.5,
        max_iterations=20
):
    """Adjust side camera position using servo and ultrasonic sensor."""
    logging.debug("Adjusting side camera position...")
    current_angle = NEUTRAL_ANGLE
    set_servo_angle(current_angle)

    for i in range(max_iterations):
        distance = measure_distance()
        if distance is None:
            logging.error("Distance measurement failed. Skipping iteration.")
            continue

        error = distance - target_distance
        logging.debug(
            f"[Side Cam Adjust] Iter {i}: "
            f"Distance = {distance:.2f} cm, "
            f"Error = {error:.2f} cm"
        )
        if abs(error) <= tolerance:
            logging.debug("[Side Cam Adjust] Target distance reached.")
            break

        angle_adjustment = error * SCALING_FACTOR
        new_angle = current_angle - angle_adjustment
        new_angle = max(0, min(160, new_angle))  # Constrain angle
        set_servo_angle(new_angle)
        current_angle = new_angle
        time.sleep(0.1)


# --- Computer Vision Functions for Camera Detection ---

def detect_front_dimensions(camera):
    """Detect object dimensions from front camera."""
    ret, frame = camera.read()
    if not ret:
        logging.error("Failed to read frame from front camera.")
        return None, None, None

    # Increase contrast and brightness
    alpha = 1.5  # Contrast control (1.0-3.0)
    beta = 50    # Brightness control (0-100)
    frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    # Apply Gaussian blur
    frame_blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    # Crop to central region
    height, width, _ = frame_blurred.shape
    x1, y1 = int(width * 0.2), int(height * 0.2)
    x2, y2 = int(width * 0.8), int(height * 0.8)
    roi = frame_blurred[y1:y2, x1:x2]

    # Convert ROI to grayscale
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Threshold to isolate white box
    _, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Apply morphological operations
    kernel = np.ones((7, 7), np.uint8)
    mask_final = cv2.morphologyEx(mask_white, cv2.MORPH_OPEN, kernel, iterations=2)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, iterations=2)

    # Find contours
    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        logging.error("No contours found in front camera frame.")
        return None, None, None

    largest_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest_contour) < 5000:
        logging.error("Largest contour too small in front camera frame.")
        return None, None, None

    # Draw bounding box
    x, y, w, h = cv2.boundingRect(largest_contour)
    cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Convert to centimeters
    width_cm = w * PIXEL_TO_CM_RATIO_FRONT + 0.2
    height_cm = h * PIXEL_TO_CM_RATIO_FRONT - 0.2

    # Round to one decimal place
    width_cm = round(width_cm, 1)
    height_cm = round(height_cm, 1)

    image_path = (
        f'/home/team48/packaging_env/images/'
        f'front_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
    )
    cv2.imwrite(image_path, roi)

    logging.debug(
        f"Front dimensions detected: "
        f"width={width_cm} cm, height={height_cm} cm. "
        f"Image saved to {image_path}"
    )

    return width_cm - 0.4, height_cm + 0.3, image_path


def detect_side_dimension(camera):
    """Detect object dimension from side camera."""
    logging.debug("Detecting side dimensions...")
    
    # Adjust camera position first
    adjust_side_camera_position(
        target_distance=TARGET_DISTANCE,
        tolerance=0.5,
        max_iterations=20
    )
    
    for attempt in range(3):  # Retry up to 3 times
        ret, frame = camera.read()
        if not ret:
            logging.error("Failed to read frame from side camera.")
            continue

        alpha = 1.5  # Contrast control
        beta = 50    # Brightness control
        frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
        frame_blurred = cv2.GaussianBlur(frame, (5, 5), 0)

        height, width, _ = frame_blurred.shape
        x1, y1 = int(width * 0.2), int(height * 0.2)
        x2, y2 = int(width * 0.8), int(height * 0.8)
        roi = frame_blurred[y1:y2, x1:x2]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        kernel = np.ones((7, 7), np.uint8)
        mask_final = cv2.morphologyEx(mask_white, cv2.MORPH_OPEN, kernel, iterations=2)
        mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            logging.error("No contours found in side camera frame. Retrying...")
            time.sleep(1)
            continue

        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) < 5000:
            logging.error("Largest contour too small. Retrying...")
            time.sleep(1)
            continue

        x, y, w, h = cv2.boundingRect(largest_contour)
        cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 2)

        length_cm = w * PIXEL_TO_CM_RATIO_SIDE - 0.4
        length_cm = round(length_cm, 1)

        image_path = (
            f'/home/team48/packaging_env/images/'
            f'side_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
        )
        cv2.imwrite(image_path, roi)

        logging.debug(
            f"Side dimension detected: length={length_cm} cm. "
            f"Image saved to {image_path}"
        )
        return length_cm + 0.1, image_path

    logging.error("Failed to detect side dimensions after multiple attempts.")
    return None, None


# --- Genetic Algorithm and Related Functions ---

def fitness_function(candidate_solution, object_dimensions, sealing_margin):
    """Calculate fitness score for genetic algorithm candidate."""
    candidate_length, candidate_width, candidate_height = candidate_solution
    min_length = object_dimensions[0] + sealing_margin
    min_width = object_dimensions[1] + sealing_margin
    min_height = object_dimensions[2] + sealing_margin

    length_penalty = max(0, candidate_length - min_length)
    width_penalty = max(0, candidate_width - min_width)
    height_penalty = max(0, candidate_height - min_height)
    total_penalty = length_penalty + width_penalty + height_penalty
    logging.debug(
        f"Fitness function: "
        f"candidate={candidate_solution}, "
        f"penalty={total_penalty}"
    )
    return total_penalty


def genetic_algorithm(
        object_dimensions,
        population_size,
        generations,
        sealing_margin,
        mutation_rate
):
    """Optimize packaging dimensions using genetic algorithm."""
    logging.debug("Starting genetic algorithm...")
    population = [
        np.array([
            object_dimensions[0] + sealing_margin + random.uniform(0, 0.1),
            object_dimensions[1] + sealing_margin + random.uniform(0, 0.1),
            object_dimensions[2] + sealing_margin + random.uniform(0, 0.1)
        ])
        for _ in range(population_size)
    ]
    best_solution = population[0]
    
    for generation in range(generations):
        population.sort(
            key=lambda individual: fitness_function(
                individual,
                object_dimensions,
                sealing_margin
            )
        )
        best_solution = population[0]
        logging.debug(f"Generation {generation}: Best solution = {best_solution}")
        new_population = []
        
        while len(new_population) < population_size:
            parent1, parent2 = random.sample(population[:5], 2)
            child = (parent1 + parent2) / 2  # Simple crossover
            if random.random() < mutation_rate:
                child += np.random.normal(0, 0.1, 3)  # Mutation
                logging.debug("Mutation applied to child.")
            new_population.append(child)
        
        population = new_population

    logging.debug("Genetic algorithm complete.")
    return {
        "Optimal Length": best_solution[0],
        "Optimal Width": best_solution[1],
        "Optimal Height": best_solution[2]
    }


def calculate_2d_bubble_wrap_size(optimal_dimensions):
    """Calculate required bubble wrap size from optimized dimensions."""
    optimal_length = optimal_dimensions["Optimal Length"]
    optimal_width = optimal_dimensions["Optimal Width"]
    optimal_height = optimal_dimensions["Optimal Height"]
    
    bubble_wrap_length = (optimal_height) + (optimal_width)
    bubble_wrap_width = (optimal_length) + (optimal_width)
    logging.debug(
        f"Calculated bubble wrap size: "
        f"length={bubble_wrap_length}, "
        f"width={bubble_wrap_width}"
    )
    return {"length": bubble_wrap_length, "width": bubble_wrap_width}


# --- Main Measure and Optimize Function ---

def measure_and_optimize():
    """Main function to measure dimensions and optimize packaging."""
    logging.debug("Starting measure_and_optimize()...")
    # Initialize cameras with V4L2 backend
    front_camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
    side_camera = cv2.VideoCapture(2, cv2.CAP_V4L2)

    # Increase exposure for dim environments
    front_camera.set(cv2.CAP_PROP_EXPOSURE, 1)
    side_camera.set(cv2.CAP_PROP_EXPOSURE, 1)

    try:
        logging.debug("Capturing front dimensions...")
        front_width, front_height, front_image = detect_front_dimensions(front_camera)
        if front_width is None or front_height is None:
            logging.error("Front camera failed to detect dimensions.")
            return None

        logging.debug("Adjusting side camera position...")
        adjust_side_camera_position(target_distance=TARGET_DISTANCE, tolerance=0.5)

        logging.debug("Capturing side dimension...")
        side_length, side_image = detect_side_dimension(side_camera)
        if side_length is None:
            logging.error("Side camera failed to detect dimension.")
            return None

        object_dimensions = (side_length, front_width, front_height)
        logging.debug(f"Measured object dimensions (L, W, H): {object_dimensions}")

        logging.debug("Running genetic algorithm for optimization...")
        optimized_dimensions = genetic_algorithm(
            object_dimensions,
            POPULATION_SIZE,
            GENERATIONS,
            SEALING_MARGIN,
            MUTATION_RATE
        )
        logging.debug(f"Optimized dimensions: {optimized_dimensions}")

        logging.debug("Calculating bubble wrap size...")
        bubble_wrap = calculate_2d_bubble_wrap_size(optimized_dimensions)
        logging.debug(f"Calculated bubble wrap size: {bubble_wrap}")

        return {
            "object_dimensions": object_dimensions,
            "optimized_dimensions": optimized_dimensions,
            "bubble_wrap_size": bubble_wrap,
            "front_image_path": front_image,
            "side_image_path": side_image
        }
    finally:
        logging.debug("Releasing cameras...")
        front_camera.release()
        side_camera.release()


# --- Test Code ---
def test_measure_and_optimize():
    """Test function for measure_and_optimize."""
    logging.debug("Starting test for measure_and_optimize()...")
    result = measure_and_optimize()
    if result:
        logging.info("\n--- Measurement and Optimization Result ---")
        logging.info(f"Object Dimensions (L, W, H): {result['object_dimensions']}")
        logging.info(f"Optimal Dimensions: {result['optimized_dimensions']}")
        logging.info(f"Bubble Wrap Size: {result['bubble_wrap_size']}")
        logging.info(f"Front Image Path: {result['front_image_path']}")
        logging.info(f"Side Image Path: {result['side_image_path']}")
    else:
        logging.error("Test failed: No results returned.")


if __name__ == "__main__":
    try:
        test_measure_and_optimize()
    except KeyboardInterrupt:
        logging.error("Test interrupted by user.")
    finally:
        logging.debug("Cleaning up GPIO...")
        GPIO.cleanup()