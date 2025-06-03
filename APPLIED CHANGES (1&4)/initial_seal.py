import RPi.GPIO as GPIO
import time
import math  # Ensure math module is imported

# === CONFIG SECTION ===
GPIO.setmode(GPIO.BCM)  # Use GPIO.BOARD if you're using physical pin numbers

# Relay GPIO Pin Assignments (Modify based on your wiring)
ACT1_RELAY1 = 14    # PUSH
ACT1_RELAY2 = 15    # PULL

ACT2_RELAY1 = 18    # TOP LEFT actuator
ACT2_RELAY2 = 17

ACT3_RELAY1 = 27
ACT3_RELAY2 = 22

ACT4_RELAY1 = 10
ACT4_RELAY2 = 9

STEP1_PIN = 24
DIR1_PIN = 23

STEPS_PER_REV = 3200
LEAD_SCREW_PITCH = 8  # mm
STEPS_PER_MM = STEPS_PER_REV / LEAD_SCREW_PITCH

# List of used GPIO pins
used_pins = [
    ACT1_RELAY1, ACT1_RELAY2,
    ACT2_RELAY1, ACT2_RELAY2,
    ACT3_RELAY1, ACT3_RELAY2,
    ACT4_RELAY1, ACT4_RELAY2,
    STEP1_PIN, DIR1_PIN
]

# === SETUP ===
try:
    for pin in used_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)  # Default state: OFF (relay deactivated)
except Exception as e:
    print(f"[ERROR] GPIO Setup failed: {e}")
    GPIO.cleanup()
    exit()

# === ACTUATOR FUNCTIONS ===

def move_stepper(length_mm):
    """Feed bubble wrap forward by specific length in mm."""
    steps = int(math.ceil(length_mm * STEPS_PER_MM))
    GPIO.output(DIR1_PIN, GPIO.LOW)  # Set motor direction (forward)
    
    for _ in range(steps):
        GPIO.output(STEP1_PIN, GPIO.HIGH)  # Activate stepper motor pin
        time.sleep(0.0005)  # Wait for step delay
        GPIO.output(STEP1_PIN, GPIO.LOW)  # Deactivate stepper motor pin
        time.sleep(0.0005)  # Wait for step delay

    print(f"[Stepper] Moved {length_mm} mm ({steps} steps)")

def turn_off_top_actuators():
    print("[INFO] Turning OFF all top actuators...")
    for pin in used_pins:
        GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.5)

def top_actuators_off_LEFT():
    print("[INFO] Deactivating top LEFT actuator...")
    GPIO.output(ACT2_RELAY1, GPIO.HIGH)
    GPIO.output(ACT2_RELAY2, GPIO.HIGH)

def top_actuators_pull():
    print("[INFO] Pushing top right actuators...")
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
    print("[INFO] Pulling top right actuators...")
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
    print("[INFO] Pushing top LEFT actuator...")
    GPIO.output(ACT2_RELAY1, GPIO.HIGH)
    GPIO.output(ACT2_RELAY2, GPIO.LOW)
    

def top_actuators_pull_LEFT():
    print("[INFO] Pulling top LEFT actuator...")
    GPIO.output(ACT2_RELAY1, GPIO.LOW)
    GPIO.output(ACT2_RELAY2, GPIO.HIGH)
    
    

# === PARALLEL ACTUATION WITH SEPARATE DURATIONS ===

def run_top_actuators_parallel(right_func, left_func, right_duration, left_duration):
    print(f"[INFO] Running actuators in parallel: right({right_duration}s), left({left_duration}s)")
    
    # Activate both actuator groups
    right_func()
    left_func()

    # Wait for the shorter duration first
    time.sleep(min(right_duration, left_duration))

    # Turn off whichever finished first
    if left_duration < right_duration:
        top_actuators_off_LEFT()
        time.sleep(right_duration - left_duration)
    elif left_duration > right_duration:
        turn_off_top_actuators()
        time.sleep(left_duration - right_duration)

    # Turn off the rest
    turn_off_top_actuators()
    print("[INFO] Parallel actuation complete.\n")
    
class InitialSealController:
    def __init__(self):
        try:
            # First cleanup any existing configurations
            GPIO.cleanup()
            
            # Explicitly set pin numbering mode FIRST
            GPIO.setmode(GPIO.BCM)
            
            # Verify mode was set
            if GPIO.getmode() != GPIO.BCM:
                raise RuntimeError("Failed to set BCM pin numbering mode")
                
            # Then configure pins
            for pin in used_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)
                
        except Exception as e:
            GPIO.cleanup()
            raise RuntimeError(f"GPIO initialization failed: {str(e)}")

    def perform_feeding(self):
        """Handle only the feeding mechanism"""
        move_stepper(40)  # Example feeding command

    def perform_sealing(self):
        """Handle only the actuator sealing"""
        try:
            # Double-check mode before operations
            if GPIO.getmode() != GPIO.BCM:
                self.__init__()  # Re-initialize if needed
            time.sleep(1)
            run_top_actuators_parallel(
                right_func=top_actuators_push,
                left_func=top_actuators_push_LEFT,
                right_duration=1,
                left_duration=0.7
            )
            time.sleep(4)
            run_top_actuators_parallel(
                right_func=top_actuators_pull,
                left_func=top_actuators_pull_LEFT,
                right_duration=0.5,
                left_duration=0.2
            )
            time.sleep(0.5)
            run_top_actuators_parallel(
                right_func=top_actuators_push,
                left_func=top_actuators_push_LEFT,
                right_duration=0.5,
                left_duration=0.2
            )
            time.sleep(4)
            run_top_actuators_parallel(
                right_func=top_actuators_pull,
                left_func=top_actuators_pull_LEFT,
                right_duration=0.5,
                left_duration=0.2
            )
            time.sleep(0.5)
            run_top_actuators_parallel(
                right_func=top_actuators_push,
                left_func=top_actuators_push_LEFT,
                right_duration=0.5,
                left_duration=0.2
            )
            time.sleep(4)
            run_top_actuators_parallel(
                right_func=top_actuators_pull,
                left_func=top_actuators_pull_LEFT,
                right_duration=2,
                left_duration=0.7
            )
        except Exception as e:
            print(f"[ERROR] Sealing failed: {e}")
            raise

    def cleanup(self):
        GPIO.cleanup()
