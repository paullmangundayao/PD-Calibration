import RPi.GPIO as GPIO
import time
import math
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ========== GPIO Pin Assignments ==========
# Linear Rails
STEP_PIN_1 = 7
DIR_PIN_1 = 12

STEP_PIN_2 = 20
DIR_PIN_2 = 21

# Bubble Wrap Feeder
STEP_PIN_FEED = 24
DIR_PIN_FEED = 23

# Package Handling Mechanisms
SERVO_PIN = 26          # Servo for package release
STEP_PIN_FORK = 8       # Fork lift mechanism
DIR_PIN_FORK = 25

# Linear Actuator Relays
ACT1_RELAY1 = 14    
ACT1_RELAY2 = 15    
ACT2_RELAY1 = 18   
ACT2_RELAY2 = 17
ACT3_RELAY1 = 27
ACT3_RELAY2 = 22
ACT4_RELAY1 = 10
ACT4_RELAY2 = 9

# List of used actuator GPIO pins
used_pins = [
    ACT1_RELAY1, ACT1_RELAY2,
    ACT2_RELAY1, ACT2_RELAY2,
    ACT3_RELAY1, ACT3_RELAY2,
    ACT4_RELAY1, ACT4_RELAY2,
]       

# ========== Motor Parameters ==========
# Linear Rails
STEPS_PER_REV_1 = 200
LEAD_SCREW_PITCH_1_CM = 0.4
STEPS_PER_CM_1 = STEPS_PER_REV_1 / LEAD_SCREW_PITCH_1_CM

STEPS_PER_REV_2 = 200
LEAD_SCREW_PITCH_2_CM = 0.4
STEPS_PER_CM_2 = STEPS_PER_REV_2 / LEAD_SCREW_PITCH_2_CM

# Bubble Wrap Feeder
STEPS_PER_REV_FEEDER = 3200
LEAD_SCREW_PITCH_FEEDER = 10
STEPS_PER_CM_FEEDER = STEPS_PER_REV_FEEDER / LEAD_SCREW_PITCH_FEEDER

# Fork Mechanism
STEPS_PER_REV_FORK = 200
LEAD_SCREW_PITCH_FORK_CM = 0.5
STEPS_PER_CM_FORK = STEPS_PER_REV_FORK / LEAD_SCREW_PITCH_FORK_CM

# ========== Timing and Constants ==========
PULSE_WIDTH = 0.0005
STANDARD_BUBBLE_WRAP_WIDTH_CM = 25.4
SERVO_ACTIVATION_ANGLE = 55    # Degrees for package release

# ========== Actuator Control Functions ==========
def turn_off_top_actuators():
    """Turn off all actuator relays"""
    logging.info("Turning OFF all top actuators...")
    for pin in used_pins:
        GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.5)

def top_actuators_off_LEFT():
    """Deactivate left actuator"""
    logging.info("Deactivating top LEFT actuator...")
    GPIO.output(ACT2_RELAY1, GPIO.HIGH)
    GPIO.output(ACT2_RELAY2, GPIO.HIGH)

def top_actuators_pull():
    """Activate pull motion on main actuators"""
    logging.info("Pulling all top actuators...")
    # ACT1
    GPIO.output(ACT1_RELAY1, GPIO.HIGH)
    GPIO.output(ACT1_RELAY2, GPIO.LOW)
    # ACT3
    GPIO.output(ACT3_RELAY1, GPIO.HIGH)
    GPIO.output(ACT3_RELAY2, GPIO.LOW)
    # ACT4
    GPIO.output(ACT4_RELAY1, GPIO.HIGH)
    GPIO.output(ACT4_RELAY2, GPIO.LOW)

def top_actuators_push():
    """Activate push motion on main actuators"""
    logging.info("Pushing all top actuators...")
    # ACT1
    GPIO.output(ACT1_RELAY1, GPIO.LOW)
    GPIO.output(ACT1_RELAY2, GPIO.HIGH)
    # ACT3
    GPIO.output(ACT3_RELAY1, GPIO.LOW)
    GPIO.output(ACT3_RELAY2, GPIO.HIGH)
    # ACT4
    GPIO.output(ACT4_RELAY1, GPIO.LOW)
    GPIO.output(ACT4_RELAY2, GPIO.HIGH)

def top_actuators_push_LEFT():
    """Activate left push"""
    logging.info("Pushing top LEFT actuator...")
    GPIO.output(ACT2_RELAY1, GPIO.HIGH)
    GPIO.output(ACT2_RELAY2, GPIO.LOW)

def top_actuators_pull_LEFT():
    """Activate left pull"""
    logging.info("Pulling top LEFT actuator...")
    GPIO.output(ACT2_RELAY1, GPIO.LOW)
    GPIO.output(ACT2_RELAY2, GPIO.HIGH)

def run_top_actuators_parallel(main_func, left_func, main_duration, left_duration):
    """Control parallel actuator operation"""
    logging.info(f"Running actuators: main({main_duration}s), left({left_duration}s)")
    
    main_func()
    left_func()
    time.sleep(min(main_duration, left_duration))

    if left_duration < main_duration:
        top_actuators_off_LEFT()
        time.sleep(main_duration - left_duration)
    elif left_duration > main_duration:
        turn_off_top_actuators()
        time.sleep(left_duration - main_duration)

    turn_off_top_actuators()
    logging.info("Parallel actuation complete")

# ========== Motor Control Functions ==========
def set_servo_angle(angle):
    """Control servo motor position (0-180 degrees)"""
    try:
        duty_cycle = (angle / 18) + 2  # Convert angle to duty cycle
        pwm = GPIO.PWM(SERVO_PIN, 50)  # 50 Hz PWM
        pwm.start(duty_cycle)
        time.sleep(0.5)  # Allow movement time
        pwm.stop()
        logging.info(f"Servo moved to {angle}°")
        return True
    except Exception as e:
        logging.error(f"Servo error: {str(e)}")
        return False

def move_fork(distance_cm, direction):
    """Control fork stepper motor"""
    try:
        steps = int(math.ceil(distance_cm * STEPS_PER_CM_FORK))
        GPIO.output(DIR_PIN_FORK, GPIO.HIGH if direction == 'backward' else GPIO.LOW)
        
        logging.info(f"Fork moving {distance_cm}cm {direction}")
        
        for _ in range(steps):
            GPIO.output(STEP_PIN_FORK, GPIO.HIGH)
            time.sleep(PULSE_WIDTH)
            GPIO.output(STEP_PIN_FORK, GPIO.LOW)
            time.sleep(PULSE_WIDTH)
            
        return True
    except Exception as e:
        logging.error(f"Fork error: {str(e)}")
        return False

def move_rail_1(distance_cm, direction):
    """Control first linear actuator"""
    try:
        steps = int(math.ceil(distance_cm * STEPS_PER_CM_1))
        GPIO.output(DIR_PIN_1, GPIO.HIGH if direction == 'backward' else GPIO.LOW)
        
        logging.info(f"Rail 1 moving {distance_cm}cm {direction}")
        
        for _ in range(steps):
            GPIO.output(STEP_PIN_1, GPIO.HIGH)
            time.sleep(PULSE_WIDTH)
            GPIO.output(STEP_PIN_1, GPIO.LOW)
            time.sleep(PULSE_WIDTH)
            
        return True
    except Exception as e:
        logging.error(f"Rail 1 error: {str(e)}")
        return False

def move_both_rails(distance_1, direction_1, distance_2, direction_2):
    """Move both rails simultaneously"""
    try:
        steps_1 = int(math.ceil(distance_1 * STEPS_PER_CM_1))
        steps_2 = int(math.ceil(distance_2 * STEPS_PER_CM_2))
        max_steps = max(steps_1, steps_2)

        GPIO.output(DIR_PIN_1, GPIO.HIGH if direction_1 == 'backward' else GPIO.LOW)
        GPIO.output(DIR_PIN_2, GPIO.HIGH if direction_2 == 'backward' else GPIO.LOW)

        logging.info(f"Moving rails:\nRail 1: {distance_1}cm {direction_1}\nRail 2: {distance_2}cm {direction_2}")

        for i in range(max_steps):
            if i < steps_1:
                GPIO.output(STEP_PIN_1, GPIO.HIGH)
            if i < steps_2:
                GPIO.output(STEP_PIN_2, GPIO.HIGH)
            
            time.sleep(PULSE_WIDTH)
            GPIO.output(STEP_PIN_1, GPIO.LOW)
            GPIO.output(STEP_PIN_2, GPIO.LOW)
            time.sleep(PULSE_WIDTH)

        return True
    except Exception as e:
        logging.error(f"Rail movement error: {str(e)}")
        return False

def move_feeder(length_cm, direction):
    """Dispense bubble wrap"""
    try:
        steps = int(math.ceil(length_cm * STEPS_PER_CM_FEEDER))
        GPIO.output(DIR_PIN_FEED, GPIO.HIGH if direction == 'backward' else GPIO.LOW)
        
        logging.info(f"Feeding {length_cm}cm of wrap {direction}")
        
        for _ in range(steps):
            GPIO.output(STEP_PIN_FEED, GPIO.HIGH)
            time.sleep(PULSE_WIDTH)
            GPIO.output(STEP_PIN_FEED, GPIO.LOW)
            time.sleep(PULSE_WIDTH)
            
        return True
    except Exception as e:
        logging.error(f"Feeder error: {str(e)}")
        return False

# ========== Main Delivery Sequence ==========
def run_delivery(optimal_width_cm, optimal_length_cm):
    """Execute full delivery sequence with actuator integration"""
    try:
        # Validate inputs
        if not isinstance(optimal_width_cm, (int, float)) or not isinstance(optimal_length_cm, (int, float)):
            raise ValueError("Invalid dimensions")
        
        required_expansion = STANDARD_BUBBLE_WRAP_WIDTH_CM - optimal_width_cm
        if required_expansion < 0:
            raise ValueError(f"Width {optimal_width_cm}cm exceeds standard {STANDARD_BUBBLE_WRAP_WIDTH_CM}cm")
        half_expansion = required_expansion

        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        all_pins = [
            STEP_PIN_1, DIR_PIN_1, STEP_PIN_2, DIR_PIN_2,
            STEP_PIN_FEED, DIR_PIN_FEED, SERVO_PIN,
            STEP_PIN_FORK, DIR_PIN_FORK
        ] + used_pins
        
        GPIO.setup(all_pins, GPIO.OUT)
        
        # Initialize relays to safe state
        for pin in used_pins:
            GPIO.output(pin, GPIO.HIGH)

        # Existing package handling sequence
        logging.info("-- INITIATING PACKAGE HANDLING --")
        if not set_servo_angle(SERVO_ACTIVATION_ANGLE):
            logging.warning("Primary servo activation failed, attempting recovery sequence...")
            for angle in [50, 55, 25, 10, 0]:
                if not set_servo_angle(angle):
                    logging.error(f"Failed to move servo to {angle}° in recovery sequence")
                time.sleep(0.3)
            raise RuntimeError("Package release failed after recovery attempts")
            
        # Modified fork movement sequence
        time.sleep(3)
        if not move_fork(0.4, 'forward'):
            raise RuntimeError("Fork extension failed")
        time.sleep(1)
        if not move_fork(0.4, 'backward'):
            raise RuntimeError("Fork retraction failed")

        if not move_fork(0.8, 'forward'):
            raise RuntimeError("Fork extension failed")
        time.sleep(1)
        if not move_fork(0.8, 'backward'):
            raise RuntimeError("Fork retraction failed")
            
        if not move_fork(1.9, 'forward'):
            raise RuntimeError("Fork extension failed")
        time.sleep(0.3)
        if not move_fork(1.9, 'backward'):
            raise RuntimeError("Fork retraction failed")

        # Material feeding
        time.sleep(5)
        logging.info("-- MATERIAL FEEDING PHASE --")
        if not move_feeder(optimal_length_cm, "forward"):
            raise RuntimeError("Wrap feeding failed")
            
        # Slide rail forward
        logging.info("-- WIDTH ADJUSTMENT PHASE --")
        if not move_both_rails(half_expansion, 'forward', half_expansion, 'forward'):
            raise RuntimeError("Rail adjustment failed")

        # New actuator sequence
        logging.info("-- LINEAR ACTUATOR OPERATION --")
        run_top_actuators_parallel(top_actuators_push, top_actuators_push_LEFT, 1, 0.8)
        time.sleep(4)
        run_top_actuators_parallel(top_actuators_pull, top_actuators_pull_LEFT, 0.5, 0.2)
        time.sleep(0.5)
        run_top_actuators_parallel(top_actuators_push, top_actuators_push_LEFT, 0.5, 0.2)
        time.sleep(4)
        run_top_actuators_parallel(top_actuators_pull, top_actuators_pull_LEFT, 0.5, 0.2)
        time.sleep(0.5)
        run_top_actuators_parallel(top_actuators_push, top_actuators_push_LEFT, 0.5, 0.2)
        time.sleep(4)
        run_top_actuators_parallel(top_actuators_pull, top_actuators_pull_LEFT, 2, 0.8)
        time.sleep(2)

        # Slide rail backward
        logging.info("-- WIDTH ADJUSTMENT PHASE --")
        if not move_both_rails(half_expansion, 'backward', half_expansion, 'backward'):
            raise RuntimeError("Rail adjustment failed")

        logging.info("COMPLETE: Full delivery sequence successful")
        return True
        
    except Exception as e:
        logging.error(f"DELIVERY FAILURE: {str(e)}")
        return False
    finally:
        GPIO.cleanup()
        logging.info("System cleanup completed")