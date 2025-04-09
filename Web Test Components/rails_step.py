import RPi.GPIO as GPIO
import time
import math
from algo import AlgoOptimizer

# ========== GPIO Pin Assignments ==========
# Bubble wrap stepper (Feed Stepper) - Height
STEP_PIN = 16
DIR_PIN = 20

# Linear Rails (Dual Steppers) - Width
STEP_PIN_1 = 16  # Rail 1 Step
DIR_PIN_1 = 20   # Rail 1 Direction
# Add EN Pin - EN_PIN1 =

STEP_PIN_2 = 21  # Rail 2 Step
DIR_PIN_2 = 7    # Rail 2 Direction
# Add EN Pin - EN_PIN2 =

# ========== Stepper Motor Parameters ==========
# Bubble wrap feeder motor
STEPS_PER_REV_FEEDER = 3200
LEAD_SCREW_PITCH_FEEDER = 8  # mm/rev
STEPS_PER_MM_FEEDER = STEPS_PER_REV_FEEDER / LEAD_SCREW_PITCH_FEEDER

# Linear rail motors
STEPS_PER_REV_RAIL = 200
MICROSTEPPING_RAIL = 16
LEADSCREW_PITCH_RAIL = 2  # mm/rev
STEPS_PER_MM_RAIL = (STEPS_PER_REV_RAIL * MICROSTEPPING_RAIL) / LEADSCREW_PITCH_RAIL

# ========== GPIO Setup ==========
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup([STEP_PIN, DIR_PIN, STEP_PIN_1, DIR_PIN_1, STEP_PIN_2, DIR_PIN_2], GPIO.OUT)

# ========== Movement Functions ==========

def move_stepper(length_mm, direction):
    steps_required = int(math.ceil(length_mm * STEPS_PER_MM_FEEDER))
    GPIO.output(DIR_PIN, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    for _ in range(steps_required):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.0005)
    print(f"[Feeder] Moved {length_mm} mm ({steps_required} steps) {direction}")

def move_both_rails(distance_cm, direction="forward"):
    steps = int(distance_cm * 10 * STEPS_PER_MM_RAIL)
    dir_signal = GPIO.HIGH if direction == "forward" else GPIO.LOW
    GPIO.output(DIR_PIN_1, dir_signal)
    GPIO.output(DIR_PIN_2, dir_signal)
    for _ in range(steps):
        GPIO.output(STEP_PIN_1, GPIO.HIGH)
        GPIO.output(STEP_PIN_2, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_1, GPIO.LOW)
        GPIO.output(STEP_PIN_2, GPIO.LOW)
        time.sleep(0.0005)
    print(f"[Rails] Moved {distance_cm} cm ({steps} steps) {direction}")

# ========== Integration with VisionOptimizer ==========
try:
    print("\n[INFO] Starting Dimension Detection and Movement Sequence...")

    optimizer = VisionOptimizer()
    result = optimizer.measure_and_optimize()

    if result:
        print("\n--- Optimization Result ---")
        print(f"Object Dimensions (L, W, H): {result['object_dimensions']}")
        print(f"Optimal Dimensions: {result['optimized_dimensions']}")
        print(f"Bubble Wrap Size: {result['bubble_wrap_size']}")
        print(f"Front Image: {result['front_image_path']}")
        print(f"Side Image: {result['side_image_path']}")

        # Extract bubble wrap size
        wrap_length_mm = result['bubble_wrap_size']['length'] * 10  # Convert cm to mm
        wrap_width_cm = result['bubble_wrap_size']['width']         # Already in cm

        # Move Feed Stepper (Height)
        move_stepper(wrap_length_mm, "forward")

        # Move Linear Rails (Width)
        move_both_rails(wrap_width_cm, "forward")
        time.sleep(0.5)
        move_both_rails(wrap_width_cm, "backward")
    else:
        print("[ERROR] Measurement or optimization failed.")

except KeyboardInterrupt:
    print("\n🛑 Interrupted by user.")

finally:
    GPIO.cleanup()
    print("✅ GPIO cleaned up. Exiting...")
