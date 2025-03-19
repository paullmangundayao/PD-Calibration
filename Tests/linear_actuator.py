# Test for actuator

import RPi.GPIO as GPIO
import time

# Define GPIO pins for Actuator 1
ACTUATOR1_PIN1 = 22  # GPIO22 (Pin 15)
ACTUATOR1_PIN2 = 27  # GPIO27 (Pin 13)

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(ACTUATOR1_PIN1, GPIO.OUT)
GPIO.setup(ACTUATOR1_PIN2, GPIO.OUT)

# Ensure the actuator is OFF initially
def turn_off_actuator():
    GPIO.output(ACTUATOR1_PIN1, GPIO.HIGH)
    GPIO.output(ACTUATOR1_PIN2, GPIO.HIGH)

# Move actuator forward (push)
def actuator_push():
    GPIO.output(ACTUATOR1_PIN1, GPIO.LOW)   # Extend actuator
    GPIO.output(ACTUATOR1_PIN2, GPIO.HIGH)

# Move actuator backward (pull)
def actuator_pull():
    GPIO.output(ACTUATOR1_PIN1, GPIO.HIGH)  # Retract actuator
    GPIO.output(ACTUATOR1_PIN2, GPIO.LOW)

# Function to run actuator movement for a specified duration
def run_actuator(action, duration):
    action()  # Call the function (push/pull)
    time.sleep(duration)  # Keep the actuator in position
    turn_off_actuator()  # Stop movement

# Main program
try:
    print("Raspberry Pi Actuator Control")
    print("Commands: [p] Push, [pl] Pull, [q] Quit")

    while True:
        command = input("Enter command: ").strip().lower()

        if command == "p":
            print("Pushing Actuator 1 for 5 seconds...")
            run_actuator(actuator_push, 5)

        elif command == "pl":
            print("Pulling Actuator 1 for 5 seconds...")
            run_actuator(actuator_pull, 5)

        elif command == "q":
            print("Exiting program...")
            break  # Exit the loop

        else:
            print("Invalid command. Use 'p' to push, 'pl' to pull, 'q' to quit.")

except KeyboardInterrupt:
    print("\nProgram interrupted by user.")

finally:
    turn_off_actuator()
    GPIO.cleanup()
    print("GPIO cleaned up.")