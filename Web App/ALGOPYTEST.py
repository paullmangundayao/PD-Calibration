import RPi.GPIO as GPIO
import time
import numpy as np
import random
import cv2
import datetime
import logging

# Configure logging for debugging output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration and Setup ---

# GPIO pin assignments for ultrasonic sensor and servo motor.
TRIG_PIN = 23      # Trigger pin for HC-SR04
ECHO_PIN = 24      # Echo pin for HC-SR04
SERVO_PIN = 18    # PWM output pin for servo controlling the side camera

# Control constants
NEUTRAL_ANGLE = 90        # Neutral servo angle (degrees)
SCALING_FACTOR = 1.2      # Factor for converting distance error to servo angle adjustment (adjusted for 22 cm)
TARGET_DISTANCE = 19.8    

# Genetic algorithm and optimization constants
POPULATION_SIZE = 10
GENERATIONS = 50
SEALING_MARGIN = 2        # Extra margin added to object dimensions
MUTATION_RATE = 0.1

# Pixel-to-cm ratio (calibrate this based on your setup; note that the front camera is fixed at 30 cm)
PIXEL_TO_CM_RATIO_FRONT = 0.06035  # Calibration for front camera (cm per pixel) 0.0605 
PIXEL_TO_CM_RATIO_SIDE  = 0.049  # Calibration for side camera (cm per pixel) 0.04885

# --- Setup GPIO ---
logging.debug("Setting up GPIO...")
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.setup(SERVO_PIN, GPIO.OUT)
servo = GPIO.PWM(SERVO_PIN, 50)
servo.start(0)
logging.debug("GPIO setup complete.")

# --- Ultrasonic Sensor and Servo Control Functions ---

def measure_distance(timeout=0.2):
    logging.debug("Measuring distance...")
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.0002)
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    echo_start = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        if time.time() - echo_start > timeout:
            logging.error("Timeout waiting for echo to start.")
            return None
    start_time = time.time()

    echo_end = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        if time.time() - echo_end > timeout:
            logging.error("Timeout waiting for echo to end.")
            return None
    stop_time = time.time()

    elapsed_time = stop_time - start_time
    distance = (elapsed_time * 34300) / 2
    logging.debug(f"Distance measured: {distance:.2f} cm")
    return distance

def set_servo_angle(angle):
    logging.debug(f"Setting servo angle to: {angle} degrees")
    angle = max(0, min(160, angle))
    duty_cycle = angle / 18.0 + 2.5
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)
    logging.debug("Servo angle set.")

def adjust_side_camera_position(target_distance=TARGET_DISTANCE, tolerance=0.5, max_iterations=20):
    logging.debug("Adjusting side camera position...")
    current_angle = NEUTRAL_ANGLE
    set_servo_angle(current_angle)

    for i in range(max_iterations):
        distance = measure_distance()
        if distance is None:
            logging.error("Distance measurement failed. Skipping this iteration.")
            continue

        error = distance - target_distance
        logging.debug(f"[Side Cam Adjust] Iteration {i}: Distance = {distance:.2f} cm, Error = {error:.2f} cm")
        if abs(error) <= tolerance:
            logging.debug("[Side Cam Adjust] Target distance reached.")
            break
        angle_adjustment = error * SCALING_FACTOR
        new_angle = current_angle - angle_adjustment
        new_angle = max(0, min(160, new_angle))
        set_servo_angle(new_angle)
        current_angle = new_angle
        time.sleep(0.1)

# --- Computer Vision Functions ---

def detect_front_dimensions(camera):
    for attempt in range(3):
        ret, frame = camera.read()
        if ret:
            break
        logging.warning(f"Front camera read failed. Retry {attempt + 1}/3")
        time.sleep(1)
    if not ret:
        logging.error("Failed to read frame from front camera after retries.")
        return None, None, None

    alpha = 1.5
    beta = 50
    frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    frame_blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    height, width, _ = frame_blurred.shape
    roi = frame_blurred[int(height * 0.2):int(height * 0.8), int(width * 0.2):int(width * 0.8)]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    kernel = np.ones((7, 7), np.uint8)
    mask_final = cv2.morphologyEx(mask_white, cv2.MORPH_OPEN, kernel, iterations=2)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        logging.error("No contours found in front camera frame.")
        return None, None, None

    largest_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest_contour) < 5000:
        logging.error("Largest contour too small in front camera frame.")
        return None, None, None

    x, y, w, h = cv2.boundingRect(largest_contour)
    width_cm = round(w * PIXEL_TO_CM_RATIO_FRONT + 0.2, 1)
    height_cm = round(h * PIXEL_TO_CM_RATIO_FRONT - 0.2, 1)

    image_path = f'/home/team48/packaging_env/images/front_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
    cv2.imwrite(image_path, roi)

    logging.debug(f"Front dimensions: width={width_cm} cm, height={height_cm} cm. Saved: {image_path}")
    return width_cm, height_cm, image_path

def detect_side_dimension(camera):
    logging.debug("Detecting side dimensions...")
    adjust_side_camera_position()

    for attempt in range(3):
        ret, frame = camera.read()
        if ret:
            break
        logging.warning(f"Side camera read failed. Retry {attempt + 1}/3")
        time.sleep(1)
    if not ret:
        logging.error("Failed to read frame from side camera after retries.")
        return None, None

    alpha = 1.5
    beta = 50
    frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    frame_blurred = cv2.GaussianBlur(frame, (5, 5), 0)

    height, width, _ = frame_blurred.shape
    roi = frame_blurred[int(height * 0.2):int(height * 0.8), int(width * 0.2):int(width * 0.8)]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    kernel = np.ones((7, 7), np.uint8)
    mask_final = cv2.morphologyEx(mask_white, cv2.MORPH_OPEN, kernel, iterations=2)
    mask_final = cv2.morphologyEx(mask_final, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask_final, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        logging.error("No contours found in side camera frame.")
        return None, None

    largest_contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest_contour) < 5000:
        logging.error("Largest contour too small in side camera frame.")
        return None, None

    x, y, w, h = cv2.boundingRect(largest_contour)
    length_cm = round(w * PIXEL_TO_CM_RATIO_SIDE - 0.4, 1)

    image_path = f'/home/team48/packaging_env/images/side_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.png'
    cv2.imwrite(image_path, roi)
    logging.debug(f"Side dimension: length={length_cm} cm. Saved: {image_path}")
    return length_cm, image_path

# --- Genetic Algorithm ---

def fitness_function(candidate, dimensions, margin):
    penalties = [max(0, c - (d + margin)) for c, d in zip(candidate, dimensions)]
    return sum(penalties)

def genetic_algorithm(dimensions, pop_size, gens, margin, mut_rate):
    population = [np.array([d + margin + random.uniform(0, 0.1) for d in dimensions]) for _ in range(pop_size)]
    for _ in range(gens):
        population.sort(key=lambda ind: fitness_function(ind, dimensions, margin))
        new_pop = []
        for _ in range(pop_size):
            p1, p2 = random.sample(population[:5], 2)
            child = (p1 + p2) / 2
            if random.random() < mut_rate:
                child += np.random.normal(0, 0.1, 3)
            new_pop.append(child)
        population = new_pop
    best = population[0]
    return {"Optimal Length": best[0], "Optimal Width": best[1], "Optimal Height": best[2]}

def calculate_2d_bubble_wrap_size(opt):
    return {
        "length": (2 * opt["Optimal Height"]) + (2 * opt["Optimal Width"]),
        "width": (2 * opt["Optimal Length"]) + (2 * opt["Optimal Width"])
    }

# --- Main Measure Function ---
def measure_and_optimize():
    logging.debug("Starting measure_and_optimize()...")
    front_cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
    side_cam = cv2.VideoCapture(2, cv2.CAP_V4L2)
    front_cam.set(cv2.CAP_PROP_EXPOSURE, 1)
    side_cam.set(cv2.CAP_PROP_EXPOSURE, 1)

    try:
        fw, fh, front_img = detect_front_dimensions(front_cam)
        if fw is None or fh is None:
            return None
        sl, side_img = detect_side_dimension(side_cam)
        if sl is None:
            return None
        dims = (sl, fw, fh)
        opt = genetic_algorithm(dims, POPULATION_SIZE, GENERATIONS, SEALING_MARGIN, MUTATION_RATE)
        wrap = calculate_2d_bubble_wrap_size(opt)
        return {
            "object_dimensions": dims,
            "optimized_dimensions": opt,
            "bubble_wrap_size": wrap,
            "front_image_path": front_img,
            "side_image_path": side_img
        }
    finally:
        if front_cam:
            front_cam.release()
            front_cam = None
        if side_cam:
            side_cam.release()
            side_cam = None
        cv2.destroyAllWindows()

if __name__ == "__main__":
    try:
        result = measure_and_optimize()
        if result:
            logging.info(f"Result: {result}")
        else:
            logging.error("No result returned.")
    except KeyboardInterrupt:
        logging.warning("Interrupted by user.")
    finally:
        servo.stop()
        GPIO.cleanup()