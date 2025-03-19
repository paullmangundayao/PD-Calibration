# Linear actuator 1 & 2 (Top seal)

import RPi.GPIO as GPIO
import time

# Define GPIO pins for Actuator 1
ACTUATOR1_PIN1 = 22  # GPIO22 (Pin 15)
ACTUATOR1_PIN2 = 27  # GPIO27 (Pin 13)

# Define GPIO pins for Actuator 2
ACTUATOR2_PIN1 = 23  # GPIO23 (Pin 16)
ACTUATOR2_PIN2 = 17  # GPIO17 (Pin 11)

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(ACTUATOR1_PIN1, GPIO.OUT)
GPIO.setup(ACTUATOR1_PIN2, GPIO.OUT)
GPIO.setup(ACTUATOR2_PIN1, GPIO.OUT)
GPIO.setup(ACTUATOR2_PIN2, GPIO.OUT)

# Initialize actuators to OFF state
def turn_off_actuators():
    GPIO.output(ACTUATOR1_PIN1, GPIO.HIGH)
    GPIO.output(ACTUATOR1_PIN2, GPIO.HIGH)
    GPIO.output(ACTUATOR2_PIN1, GPIO.HIGH)
    GPIO.output(ACTUATOR2_PIN2, GPIO.HIGH)

# Push Actuator 1
def actuator1_push():
    GPIO.output(ACTUATOR1_PIN1, GPIO.LOW)   # Turn Pin 1 ON
    GPIO.output(ACTUATOR1_PIN2, GPIO.HIGH)  # Turn Pin 2 OFF

# Pull Actuator 1
def actuator1_pull():
    GPIO.output(ACTUATOR1_PIN1, GPIO.HIGH)  # Turn Pin 1 OFF
    GPIO.output(ACTUATOR1_PIN2, GPIO.LOW)   # Turn Pin 2 ON

# Push Actuator 2
def actuator2_push():
    GPIO.output(ACTUATOR2_PIN1, GPIO.LOW)   # Turn Pin 1 ON
    GPIO.output(ACTUATOR2_PIN2, GPIO.HIGH)  # Turn Pin 2 OFF

# Pull Actuator 2
def actuator2_pull():
    GPIO.output(ACTUATOR2_PIN1, GPIO.HIGH)  # Turn Pin 1 OFF
    GPIO.output(ACTUATOR2_PIN2, GPIO.LOW)   # Turn Pin 2 ON

# Main program
try:
    print("Raspberry Pi Two Actuator Control")
    print("Press any key to start the sequence...")
    input()  # Wait for user input

    # Push Actuator 1 for 2 seconds
    print("Pushing Actuator 1...")
    actuator1_push()
    time.sleep(2)

    # Stay in pushed state for 4 seconds
    print("Actuator 1 staying pushed...")
    time.sleep(4)

    # Return Actuator 1 to normal (pull)
    print("Returning Actuator 1 to normal...")
    actuator1_pull()
    time.sleep(1)  # Small delay for stability

    # Push Actuator 2 for 2 seconds
    print("Pushing Actuator 2...")
    actuator2_push()
    time.sleep(2)

    # Stay in pushed state for 4 seconds
    print("Actuator 2 staying pushed...")
    time.sleep(4)

    # Return Actuator 2 to normal (pull)
    print("Returning Actuator 2 to normal...")
    actuator2_pull()
    time.sleep(1)  # Small delay for stability

    print("Sequence complete.")

except KeyboardInterrupt:
    print("Program interrupted")

finally:
    # Clean up GPIO on exit
    turn_off_actuators()
    GPIO.cleanup()
    print("GPIO cleaned up")