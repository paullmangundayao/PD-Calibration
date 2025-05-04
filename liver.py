import RPi.GPIO as GPIO
import time
import logging

# GPIO Pin Assignments
STEP_PIN_FORK = 27
DIR_PIN_FORK = 17
SERVO_PLACEMENT = 7

# Fork Stepper Motor Parameters
STEPS_PER_REV_FORK = 400
LEAD_SCREW_PITCH_FORK = 1
STEPS_PER_CM_FORK = STEPS_PER_REV_FORK / LEAD_SCREW_PITCH_FORK

# Logging Setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def move_fork_stepper(distance_cm, direction):
    steps_required = int(distance_cm * STEPS_PER_CM_FORK)
    GPIO.output(DIR_PIN_FORK, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    for _ in range(steps_required):
        GPIO.output(STEP_PIN_FORK, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_FORK, GPIO.LOW)
        time.sleep(0.0005)
    logging.info(f"[Fork] Moved {distance_cm} cm ({steps_required} steps) {direction}")


def emergency_stop():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
    logging.warning("🛑 EMERGENCY STOP triggered: All GPIOs have been reset.")


def deliver_product(servo):
    try:
        angle = 40
        duty = (angle / 18.0) + 2.5
        servo.ChangeDutyCycle(duty)
        logging.info("[Servo] Delivering product (rotating to 40°)")
        time.sleep(0.5)
        servo.ChangeDutyCycle(0)
        return True
    except Exception as e:
        logging.error(f"[Servo] Failed to move: {e}")
        return False


def run_delivery():
    try:
        logging.info("Starting servo and fork stepper sequence...")
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup([SERVO_PLACEMENT, STEP_PIN_FORK, DIR_PIN_FORK], GPIO.OUT)

        servo = GPIO.PWM(SERVO_PLACEMENT, 50)
        servo.start(0)

        if deliver_product(servo):
            logging.info("Servo delivery successful.")
            time.sleep(2.0)
        else:
            logging.error("Servo delivery failed.")
            return False

        move_fork_stepper(1.9, "backward")
        time.sleep(0.5)
        move_fork_stepper(1.9, "forward")

        servo.stop()
        GPIO.cleanup()
        logging.info("GPIO cleanup complete.")
        return True

    except Exception as e:
        logging.error(f"Unexpected error during delivery: {e}")
        GPIO.cleanup()
        return False
    