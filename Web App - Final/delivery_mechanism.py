import RPi.GPIO as GPIO
import time
import math
import logging
from algo import AlgoOptimizer

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ========== GPIO Pin Assignments ==========
STEP_PIN_FEED = 16
DIR_PIN_FEED = 20

STEP_PIN_FORK = 8
DIR_PIN_FORK = 9

STEP_PIN_LR1 = 16
DIR_PIN_LR1 = 20
EN_PIN_LR1 = 10

STEP_PIN_LR2 = 21
DIR_PIN_LR2 = 7
EN_PIN_LR2 = 11

ACT1_PIN1, ACT1_PIN2 = 22, 27
ACT2_PIN1, ACT2_PIN2 = 23, 17
ACT3_PIN1, ACT3_PIN2 = 24, 5
ACT4_PIN1, ACT4_PIN2 = 25, 6

SERVO_PLACEMENT = 4

# ========== Stepper Motor Parameters ==========
STEPS_PER_REV_FEEDER = 3200
LEAD_SCREW_PITCH_FEEDER = 8
STEPS_PER_CM_FEEDER = STEPS_PER_REV_FEEDER / LEAD_SCREW_PITCH_FEEDER

# Fork Stepper Motor Parameters
STEPS_PER_REV_FORK = 3200
LEAD_SCREW_PITCH_FORK = 8
STEPS_PER_CM_FORK = STEPS_PER_REV_FORK / LEAD_SCREW_PITCH_FORK

STEPS_PER_REV_RAIL = 200
MICROSTEPPING_RAIL = 16
LEADSCREW_PITCH_RAIL = 2
STEPS_PER_CM_RAIL = (STEPS_PER_REV_RAIL * MICROSTEPPING_RAIL) / LEADSCREW_PITCH_RAIL

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
GPIO.output(EN_PIN_LR1, GPIO.LOW)
GPIO.output(EN_PIN_LR2, GPIO.LOW)

GPIO.setup([
    ACT1_PIN1, ACT1_PIN2,
    ACT2_PIN1, ACT2_PIN2,
    ACT3_PIN1, ACT3_PIN2,
    ACT4_PIN1, ACT4_PIN2
], GPIO.OUT)

GPIO.setup(SERVO_PLACEMENT, GPIO.OUT)
servo = GPIO.PWM(SERVO_PLACEMENT, 50)
servo.start(0)

# ========== Movement Functions ==========

def move_stepper(length_cm, direction):
    steps_required = int(math.ceil(length_cm * STEPS_PER_CM_FEEDER))
    GPIO.output(DIR_PIN_FEED, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    for _ in range(steps_required):
        GPIO.output(STEP_PIN_FEED, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_FEED, GPIO.LOW)
        time.sleep(0.0005)
    print(f"[Feeder] Moved {length_cm} cm ({steps_required} steps) {direction}")

def move_fork_stepper(manual_distance_cm, direction):
    steps_required = int(manual_distance_cm * STEPS_PER_CM_FORK)
    GPIO.output(DIR_PIN_FORK, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    for _ in range(steps_required):
        GPIO.output(STEP_PIN_FORK, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_FORK, GPIO.LOW)
        time.sleep(0.0005)
    print(f"[Fork] Moved {manual_distance_cm} cm ({steps_required} steps) {direction}")

def move_both_rails(distance_cm, direction="forward"):
    steps = int(distance_cm * STEPS_PER_CM_RAIL)
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
    try:
        angle_forward = 85
        angle_reset = 0

        duty_forward = (angle_forward / 18.0) + 2.5
        servo.ChangeDutyCycle(duty_forward)
        print("[Servo] Delivering product (rotating to 85°)")
        time.sleep(0.5)

        duty_reset = (angle_reset / 18.0) + 2.5
        servo.ChangeDutyCycle(duty_reset)
        print("[Servo] Returning to 0°")
        time.sleep(0.5)

        servo.ChangeDutyCycle(0)
        return True

    except Exception as e:
        print(f"[ERROR] Failed to move servo: {e}")
        return False

def move_actuators_forward(duration=7):
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
    GPIO.output(ACT1_PIN1, GPIO.LOW)
    GPIO.output(ACT1_PIN2, GPIO.LOW)
    GPIO.output(ACT2_PIN1, GPIO.LOW)
    GPIO.output(ACT2_PIN2, GPIO.LOW)
    GPIO.output(ACT3_PIN1, GPIO.LOW)
    GPIO.output(ACT3_PIN2, GPIO.LOW)
    GPIO.output(ACT4_PIN1, GPIO.LOW)
    GPIO.output(ACT4_PIN2, GPIO.LOW)
    print("[Actuators] All actuators stopped.")

# ========== Main Sequence ==========
try:
    print("\n[INFO] Starting Dimension Detection and Movement Sequence...")

    optimizer = AlgoOptimizer()
    result = optimizer.measure_and_optimize()

    if result:
        print("\n--- Optimized Bubble Wrap Size Result ---")
        print(f"Bubble Wrap Size: {result['bubble_wrap_size']}")

        wrap_length_cm = result['bubble_wrap_size']['length']
        wrap_width_cm = result['bubble_wrap_size']['width']

        print(f"[INFO] Wrap Length for Feeder: {wrap_length_cm} cm")
        print(f"[INFO] Wrap Width for Rails: {wrap_width_cm} cm")
        logging.debug(f"[DEBUG] Linear Rails will move: {wrap_width_cm} cm")

        if deliver_product():
            print("[INFO] Product delivered successfully.")
            time.sleep(2.0)  # Delay before fork movement
        else:
            print("[ERROR] Product delivery failed.")
            raise Exception("Aborting due to servo error.")

        # 🚶 Step-by-step execution
        move_fork_stepper(1.9, "backward")
        time.sleep(0.3)
        move_fork_stepper(1.9, "forward")
        time.sleep(1)

        move_stepper(wrap_length_cm, "forward")
        time.sleep(3)

        move_both_rails(wrap_width_cm, "forward")
        time.sleep(0.3)
        move_both_rails(wrap_width_cm, "backward")
        time.sleep(0.5)

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
