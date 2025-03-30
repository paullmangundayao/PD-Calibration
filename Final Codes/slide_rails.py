# No Enable Pin

import RPi.GPIO as GPIO
import time

# GPIO Pin Assignments for Two Linear Rails
STEP_PIN_1 = 16  # Linear Rail 1 Step
DIR_PIN_1 = 20   # Linear Rail 1 Direction

STEP_PIN_2 = 21  # Linear Rail 2 Step
DIR_PIN_2 = 7    # Linear Rail 2 Direction

# Stepper Motor Parameters
STEPS_PER_REV = 200
MICROSTEPPING = 16
LEADSCREW_PITCH = 2  # mm per revolution
STEPS_PER_MM = (STEPS_PER_REV * MICROSTEPPING) / LEADSCREW_PITCH

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_PIN_1, GPIO.OUT)
GPIO.setup(DIR_PIN_1, GPIO.OUT)
GPIO.setup(STEP_PIN_2, GPIO.OUT)
GPIO.setup(DIR_PIN_2, GPIO.OUT)

def move_both_rails(distance_cm, direction="forward"):
    steps = int(distance_cm * 10 * STEPS_PER_MM)

    # Set directions for both rails
    dir_signal = GPIO.HIGH if direction == "forward" else GPIO.LOW
    GPIO.output(DIR_PIN_1, dir_signal)
    GPIO.output(DIR_PIN_2, dir_signal)

    print(f"Moving both rails {distance_cm} cm ({steps} steps) {direction}")

    for _ in range(steps):
        GPIO.output(STEP_PIN_1, GPIO.HIGH)
        GPIO.output(STEP_PIN_2, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN_1, GPIO.LOW)
        GPIO.output(STEP_PIN_2, GPIO.LOW)
        time.sleep(0.0005)

try:
    while True:
        distance = float(input("Enter distance in cm: "))
        if distance <= 0:
            print("Please enter a positive distance.")
            continue

        move_both_rails(distance, "forward")
        time.sleep(0.5)
        move_both_rails(distance, "backward")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopping and cleaning up GPIO...")
    GPIO.cleanup()
