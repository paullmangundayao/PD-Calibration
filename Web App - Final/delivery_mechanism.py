import RPi.GPIO as GPIO
import time
import math
from algo import AlgoOptimizer

# ========== GPIO Pin Assignments ==========
# Bubble wrap stepper (Feed Stepper) - Height
STEP_PIN_FEED = 16
DIR_PIN_FEED = 20

# Fork Stepper 
STEP_PIN_FORK = 8
DIR_PIN_FORK = 9

# Linear Rails (Dual Steppers) - Width
STEP_PIN_LR1 = 16  # Rail 1 Step
DIR_PIN_LR1 = 20   # Rail 1 Direction
EN_PIN_LR1 = 10

STEP_PIN_LR2 = 21  # Rail 2 Step
DIR_PIN_LR2 = 7    # Rail 2 Direction
EN_PIN_LR2 = 11

# Linear Actuators
ACT1_PIN1, ACT1_PIN2 = 22, 27  # Horizontal
ACT2_PIN1, ACT2_PIN2 = 23, 17  # Horizontal

ACT3_PIN1, ACT3_PIN2 = 24, 5   # Vertical
ACT4_PIN1, ACT4_PIN2 = 25, 6   # Vertical

# Servo
SERVO_PLACEMENT = 4
# To be assigned - SERVO_CLAW = 

# ========== Stepper Motor Parameters ==========
STEPS_PER_REV_FEEDER = 3200
LEAD_SCREW_PITCH_FEEDER = 8  # cm/rev
STEPS_PER_MM_FEEDER = STEPS_PER_REV_FEEDER / LEAD_SCREW_PITCH_FEEDER

STEPS_PER_REV_RAIL = 200
MICROSTEPPING_RAIL = 16
LEADSCREW_PITCH_RAIL = 2  # cm/rev
STEPS_PER_MM_RAIL = (STEPS_PER_REV_RAIL * MICROSTEPPING_RAIL) / LEADSCREW_PITCH_RAIL

# ========== GPIO Setup ==========
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup([
    STEP_PIN_FEED, DIR_PIN_FEED,
    STEP_PIN_FORK, DIR_PIN_FORK,
    STEP_PIN_LR1, DIR_PIN_LR1,
    STEP_PIN_LR2, DIR_PIN_LR2
], GPIO.OUT)

GPIO.setup([EN_PIN_LR1, EN_PIN_LR2], GPIO.OUT)

GPIO.setup([
    ACT1_PIN1, ACT1_PIN2,
    ACT2_PIN1, ACT2_PIN2,
    ACT3_PIN1, ACT3_PIN2,
    ACT4_PIN1, ACT4_PIN2
], GPIO.OUT)

GPIO.setup(SERVO_PLACEMENT, GPIO.OUT)
servo = GPIO.PWM(SERVO_PLACEMENT, 50)
servo.start(0)

# ========== Helper Functions ==========

def move_stepper(length_mm, direction):
    steps_required = int(math.ceil(length_mm * STEPS_PER_MM_FEEDER))
    GPIO.output(DIR_PIN_FEED, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    for _ in range(steps_required):
        GPIO.output(STEP_PIN_FEED, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_FEED, GPIO.LOW)
        time.sleep(0.0005)
    print(f"[Feeder] Moved {length_mm} mm ({steps_required} steps) {direction}")

def move_both_rails(distance_cm, direction="forward"):
    steps = int(distance_cm * 10 * STEPS_PER_MM_RAIL)
    dir_signal = GPIO.HIGH if direction == "forward" else GPIO.LOW
    GPIO.output(DIR_PIN_LR1, dir_signal)
    GPIO.output(DIR_PIN_LR2, dir_signal)
    for _ in range(steps):
        GPIO.output(STEP_PIN_LR1, GPIO.HIGH)
        GPIO.output(STEP_PIN_LR2, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_LR1, GPIO.LOW)
        GPIO.output(STEP_PIN_LR2, GPIO.LOW)
        time.sleep(0.0005)
    print(f"[Rails] Moved {distance_cm} cm ({steps} steps) {direction}")

def deliver_product():
    """Rotate the servo to 85° to deliver product before feeding wrap."""
    try:
        angle = 85
        duty = (angle / 18.0) + 2.5
        servo.ChangeDutyCycle(duty)
        print("[Servo] Delivering product (rotating to 85°)")
        time.sleep(0.5)
        servo.ChangeDutyCycle(0)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to move servo: {e}")
        return False

def move_actuators_forward(duration=7):
    """Moves all actuators forward (HIGH on PIN1, LOW on PIN2)"""
    GPIO.output(ACT1_PIN1, GPIO.HIGH)
    GPIO.output(ACT1_PIN2, GPIO.LOW)
    GPIO.output(ACT2_PIN1, GPIO.HIGH)
    GPIO.output(ACT2_PIN2, GPIO.LOW)
    GPIO.output(ACT3_PIN1, GPIO.HIGH)
    GPIO.output(ACT3_PIN2, GPIO.LOW)
    GPIO.output(ACT4_PIN1, GPIO.HIGH)
    GPIO.output(ACT4_PIN2, GPIO.LOW)
    print(f"[Actuators] Moving forward for {duration} seconds...")
    time.sleep(duration)
    stop_all_actuators()

def move_actuators_backward(duration=3):
    """Moves all actuators backward (LOW on PIN1, HIGH on PIN2)"""
    GPIO.output(ACT1_PIN1, GPIO.LOW)
    GPIO.output(ACT1_PIN2, GPIO.HIGH)
    GPIO.output(ACT2_PIN1, GPIO.LOW)
    GPIO.output(ACT2_PIN2, GPIO.HIGH)
    GPIO.output(ACT3_PIN1, GPIO.LOW)
    GPIO.output(ACT3_PIN2, GPIO.HIGH)
    GPIO.output(ACT4_PIN1, GPIO.LOW)
    GPIO.output(ACT4_PIN2, GPIO.HIGH)
    print(f"[Actuators] Moving backward for {duration} seconds...")
    time.sleep(duration)
    stop_all_actuators()

def stop_all_actuators():
    """Stops all actuators (sets both pins LOW)"""
    GPIO.output(ACT1_PIN1, GPIO.LOW)
    GPIO.output(ACT1_PIN2, GPIO.LOW)
    GPIO.output(ACT2_PIN1, GPIO.LOW)
    GPIO.output(ACT2_PIN2, GPIO.LOW)
    GPIO.output(ACT3_PIN1, GPIO.LOW)
    GPIO.output(ACT3_PIN2, GPIO.LOW)
    GPIO.output(ACT4_PIN1, GPIO.LOW)
    GPIO.output(ACT4_PIN2, GPIO.LOW)
    print("[Actuators] All actuators stopped.")

# ========== Integration with VisionOptimizer ==========
try:
    print("\n[INFO] Starting Dimension Detection and Movement Sequence...")

    optimizer = AlgoOptimizer()
    result = optimizer.measure_and_optimize()

    if result:
        print("\n--- Optimized Bubble Wrap Size Result ---")
        print(f"Bubble Wrap Size: {result['bubble_wrap_size']}")

        wrap_length_mm = result['bubble_wrap_size']['length'] * 10
        wrap_width_cm = result['bubble_wrap_size']['width']

        # Deliver the product using the servo before feeding wrap
        if deliver_product():
            print("[INFO] Product delivered successfully.")
        else:
            print("[ERROR] Product delivery failed.")
            raise Exception("Aborting due to servo error.")
        
        # Move Feed Stepper (Height)
        move_stepper(wrap_length_mm, "forward")

        # Move Linear Rails (Width)
        move_both_rails(wrap_width_cm, "forward")
        time.sleep(0.5)
        move_both_rails(wrap_width_cm, "backward")

        # Move all actuators forward and then backward
        move_actuators_forward(7)
        move_actuators_backward(3)

    else:
        print("[ERROR] Measurement or optimization failed.")

except KeyboardInterrupt:
    print("\n🛑 Interrupted by user.")

finally:
    servo.stop()
    GPIO.cleanup()
    print("✅ GPIO cleaned up. Exiting...")
