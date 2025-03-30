import RPi.GPIO as GPIO
import time
import math

# GPIO Pin Definitions
STEP_PIN = 16   # PUL+ (Step Pulse)
DIR_PIN = 20    # DIR+ (Direction)

# Motor Parameters
STEPS_PER_REV = 3200  # 1.8° NEMA17 with 1/16 microstepping
LEAD_SCREW_PITCH = 8  # Distance moved per full revolution (mm)

# Calculate Steps per mm
STEPS_PER_MM = STEPS_PER_REV / LEAD_SCREW_PITCH  # e.g., 3200 / 8 = 400 steps per mm

# Set fixed movement parameters
FIXED_LENGTH_MM = 10       # mm
FIXED_DIRECTION = "forward"  # 'forward' or 'backward'

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)

def move_stepper(length_mm, direction):
    steps_required = int(math.ceil(length_mm * STEPS_PER_MM))

    GPIO.output(DIR_PIN, GPIO.HIGH if direction == "forward" else GPIO.LOW)

    for _ in range(steps_required):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.0005)

    print(f"Moved {length_mm} mm ({steps_required} steps).")

# Main Program Loop
try:
    print("Stepper Motor Ready - Press Enter to move fixed length")

    while True:
        input("Press Enter to move stepper...")
        move_stepper(FIXED_LENGTH_MM, FIXED_DIRECTION)

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up. Exiting.")
