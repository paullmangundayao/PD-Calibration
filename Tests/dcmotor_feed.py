import RPi.GPIO as GPIO
import time
import math

# GPIO Pin Definitions
STEP_PIN = 16   # PUL+ (Step Pulse)
DIR_PIN = 20    # DIR+ (Direction)
ENA_PIN = 21    # ENA+ (Enable - Optional)

# Motor Parameters
STEPS_PER_REV = 3200  # 1.8° NEMA17 with 1/16 microstepping
LEAD_SCREW_PITCH = 8  # Distance moved per full revolution (mm)

# Calculate Steps per mm
STEPS_PER_MM = STEPS_PER_REV / LEAD_SCREW_PITCH  # e.g., 3200 / 8 = 400 steps per mm

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(ENA_PIN, GPIO.OUT)  # Optional enable pin

# Enable Stepper Driver (LOW = Enabled)
GPIO.output(ENA_PIN, GPIO.LOW)

def move_stepper(length_mm, direction):
    """
    Moves the stepper motor a given length in mm.
    :param length_mm: The length to move in mm.
    :param direction: 'forward' or 'backward'.
    """
    # Convert mm to steps
    steps_required = int(math.ceil(length_mm * STEPS_PER_MM))  # Round up for accuracy

    # Set Direction
    if direction == "forward":
        GPIO.output(DIR_PIN, GPIO.HIGH)
    elif direction == "backward":
        GPIO.output(DIR_PIN, GPIO.LOW)
    else:
        print("Invalid direction! Use 'forward' or 'backward'.")
        return

    # Move the Stepper Motor
    for _ in range(steps_required):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.0005)  # Adjust pulse width (500µs)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.0005)

    print(f"Moved {length_mm} mm ({steps_required} steps).")

# Main Program Loop
try:
    print("Stepper Motor Control - Enter Length in mm ('exit' to quit)")

    while True:
        user_input = input("Enter length (mm) and direction (f/b), e.g., '50 f': ").strip().lower()

        if user_input == "exit":
            print("Exiting...")
            break

        # Split input (expecting 'length direction' format)
        try:
            length, direction = user_input.split()
            length = float(length)

            if direction in ["f", "b"]:
                move_stepper(length, "forward" if direction == "f" else "backward")
            else:
                print("Invalid direction! Use 'f' for forward, 'b' for backward.")

        except ValueError:
            print("Invalid input! Format: <length> <direction> (e.g., '50 f')")

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
    GPIO.output(ENA_PIN, GPIO.HIGH)  # Disable motor on exit
    GPIO.cleanup()
    print("GPIO cleaned up. Exiting.")
