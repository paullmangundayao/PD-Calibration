import RPi.GPIO as GPIO
import time
import logging
from algot import measure_and_optimize

# GPIO Pin Assignments
# Original Fork Stepper
STEP_PIN_FORK = 27
DIR_PIN_FORK = 17
SERVO_PLACEMENT = 7

# New Bubble Wrap Stepper (ENA pin removed)
STEP_PIN_WRAP = 22    # PUL+
DIR_PIN_WRAP = 23     # DIR+

# Stepper Parameters
STEPS_PER_REV_WRAP = 3200       # Microstepping (1/16)
LEAD_SCREW_PITCH_WRAP = 0.8     # cm/rev (8mm lead screw)
STEPS_PER_CM_WRAP = STEPS_PER_REV_WRAP / LEAD_SCREW_PITCH_WRAP  # 4000 steps/cm

# Fork Stepper Parameters
STEPS_PER_REV_FORK = 400
LEAD_SCREW_PITCH_FORK = 1       # cm/rev
STEPS_PER_CM_FORK = STEPS_PER_REV_FORK / LEAD_SCREW_PITCH_FORK  # 400 steps/cm

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup([STEP_PIN_FORK, DIR_PIN_FORK, STEP_PIN_WRAP, DIR_PIN_WRAP], GPIO.OUT)

def move_stepper(length_cm, direction, motor_type="wrap"):
    """
    Move stepper motor in centimeters
    :param length_cm: Movement length in cm
    :param direction: 'forward' or 'backward'
    :param motor_type: 'wrap' or 'fork'
    """
    if motor_type == "wrap":
        steps = int(length_cm * STEPS_PER_CM_WRAP)
        step_pin, dir_pin = STEP_PIN_WRAP, DIR_PIN_WRAP
    else:  # fork motor
        steps = int(length_cm * STEPS_PER_CM_FORK)
        step_pin, dir_pin = STEP_PIN_FORK, DIR_PIN_FORK
    
    GPIO.output(dir_pin, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    
    for _ in range(steps):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(0.0005) 
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(0.0005)
    
    logging.info(f"[{motor_type.upper()}] Moved {length_cm}cm ({steps} steps) {direction}")

def cut_bubble_wrap():
    """Cut bubble wrap using algo.py's cm dimensions"""
    try:
        result = measure_and_optimize()
        if not result:
            raise ValueError("Optimization failed")
        
        length_cm = result["bubble_wrap_size"]["length"]
        move_stepper(length_cm, "forward", "wrap")
        time.sleep(0.2)
        return True
    except Exception as e:
        logging.error(f"Cutting failed: {str(e)}")
        return False

def run_delivery():
    """Full delivery sequence with bubble wrap cutting"""
    try:
        setup_gpio()
        
        if not cut_bubble_wrap():
            raise RuntimeError("Bubble wrap preparation failed")

        # Original delivery sequence
        servo = GPIO.PWM(SERVO_PLACEMENT, 50)
        servo.start(0)
        servo.ChangeDutyCycle((40 / 18) + 2.5)  # 40°
        time.sleep(0.5)
        servo.ChangeDutyCycle(0)

        # Fork movements
        move_stepper(1.9, "backward", "fork")
        time.sleep(0.2)
        move_stepper(1.9, "forward", "fork")

        return True
    finally:
        GPIO.cleanup()

def emergency_stop():
    GPIO.cleanup()
    logging.warning("🛑 EMERGENCY STOP: All motors disabled")