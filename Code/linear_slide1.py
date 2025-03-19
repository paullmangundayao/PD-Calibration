import RPi.GPIO as GPIO
import time

# Define GPIO Pins
DIR_PIN = 20    # Direction Pin
STEP_PIN = 16   # Step Pin
ENABLE_PIN = 21 # Enable Pin (Optional, can be omitted)

# Stepper Motor Parameters
STEPS_PER_REV = 200  # Adjust based on your motor (Typical NEMA 17 = 200 steps/rev)
MICROSTEPPING = 16   # Adjust based on TB6600 settings (Full Step = 1, 1/2 Step = 2, 1/4 Step = 4, etc.)
LEADSCREW_PITCH = 2  # Lead screw pitch in mm (e.g., 2mm pitch means 1 rotation = 2mm travel)
STEPS_PER_MM = (STEPS_PER_REV * MICROSTEPPING) / LEADSCREW_PITCH

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(ENABLE_PIN, GPIO.OUT)

# Function to move stepper motor
def move_distance(distance_cm, direction="forward"):
    steps = int(distance_cm * 10 * STEPS_PER_MM)  # Convert cm to mm and calculate steps
    
    # Set direction
    if direction == "forward":
        GPIO.output(DIR_PIN, GPIO.HIGH)
    else:
        GPIO.output(DIR_PIN, GPIO.LOW)

    print(f"Moving {distance_cm} cm ({steps} steps) {'forward' if direction == 'forward' else 'backward'}")
    
    # Enable Motor
    GPIO.output(ENABLE_PIN, GPIO.LOW)
    
    # Move motor
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.0005)  # Step delay (adjust based on speed requirements)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.0005)

    # Disable Motor
    GPIO.output(ENABLE_PIN, GPIO.HIGH)

try:
    while True:
        distance = float(input("Enter distance in cm (negative for reverse): "))
        direction = "forward" if distance >= 0 else "backward"
        move_distance(abs(distance), direction)
        
except KeyboardInterrupt:
    print("\nStopping and cleaning up GPIO...")
    GPIO.cleanup()
