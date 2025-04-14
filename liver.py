import RPi.GPIO as GPIO
import time
import logging

# ========== GPIO Pin Assignments ==========
STEP_PIN_FORK = 27
DIR_PIN_FORK = 17
SERVO_PLACEMENT = 7  # BCM pin number for the servo motor

# ========== Fork Stepper Motor Parameters ==========
STEPS_PER_REV_FORK = 400
LEAD_SCREW_PITCH_FORK = 1
STEPS_PER_CM_FORK = STEPS_PER_REV_FORK / LEAD_SCREW_PITCH_FORK

# ========== Logging Setup ==========
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def emergency_stop():
    # Stop all outputs safely
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()  # This releases all GPIO pins
    print("🛑 EMERGENCY STOP triggered: All GPIOs have been reset.")


def move_fork_stepper(distance_cm, direction):
    steps_required = int(distance_cm * STEPS_PER_CM_FORK)
    GPIO.output(DIR_PIN_FORK, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    for _ in range(steps_required):
        GPIO.output(STEP_PIN_FORK, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_FORK, GPIO.LOW)
        time.sleep(0.0005)
    print(f"[Fork] Moved {distance_cm} cm ({steps_required} steps) {direction}")

def emergency_stop():
    # Stop all outputs safely
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()  # This releases all GPIO pins
    print("🛑 EMERGENCY STOP triggered: All GPIOs have been reset.")


def deliver_product(servo):
    try:
        angle = 40  # Adjusted angle for your use case
        duty = (angle / 18.0) + 2.5
        servo.ChangeDutyCycle(duty)
        print("[Servo] Delivering product (rotating to 50°)")
        time.sleep(0.5)
        servo.ChangeDutyCycle(0)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to move servo: {e}")
        return False

def run_delivery():
    try:
        print("\n[INFO] Running Servo and Fork Stepper Sequence...")

        # GPIO Setup
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([SERVO_PLACEMENT, STEP_PIN_FORK, DIR_PIN_FORK], GPIO.OUT)

        # Initialize Servo
        servo = GPIO.PWM(SERVO_PLACEMENT, 50)
        servo.start(0)

        # Deliver the product using the servo
        if deliver_product(servo):
            print("[INFO] Servo delivery successful.")
            time.sleep(2.0)
        else:
            print("[ERROR] Servo delivery failed.")
            return False

        # Move Fork Backward and Forward
        move_fork_stepper(1.9, "backward")
        time.sleep(0.5)
        move_fork_stepper(1.9, "forward")

        # Cleanup
        servo.stop()
        del servo
        GPIO.cleanup()
        print("✅ GPIO cleaned up.")
        return True

    except Exception as e:
        print(f"[ERROR] Unexpected error during delivery: {e}")
        GPIO.cleanup()
        return False
        


# You can test it by calling:
# run_delivery()
