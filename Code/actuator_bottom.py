# Linear actuator 3 & 4 (Bottom Seal)

import RPi.GPIO as GPIO
import time

# Define GPIO pins for Actuator 1 (Top Sealer 1)
ACTUATOR3_PIN1 = 24  # GPIO24 (Pin 18)
ACTUATOR4_PIN2 = 5   # GPIO5  (Pin 29)

# Define GPIO pins for Actuator 2 (Top Sealer 2)
ACTUATOR5_PIN1 = 25  # GPIO25 (Pin 22)
ACTUATOR6_PIN2 = 6   # GPIO6  (Pin 31)

# Setup GPIO
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(ACTUATOR3_PIN1, GPIO.OUT)
GPIO.setup(ACTUATOR4_PIN2, GPIO.OUT)
GPIO.setup(ACTUATOR5_PIN1, GPIO.OUT)
GPIO.setup(ACTUATOR6_PIN2, GPIO.OUT)

# Initialize actuators to OFF state
def turn_off_actuators():
    GPIO.output(ACTUATOR3_PIN1, GPIO.HIGH)
    GPIO.output(ACTUATOR4_PIN2, GPIO.HIGH)
    GPIO.output(ACTUATOR5_PIN1, GPIO.HIGH)
    GPIO.output(ACTUATOR6_PIN2, GPIO.HIGH)

# Push Actuator 1 (Top Sealer 1)
def actuator1_push():
    GPIO.output(ACTUATOR3_PIN1, GPIO.LOW)
    GPIO.output(ACTUATOR4_PIN2, GPIO.HIGH)

# Pull Actuator 1
def actuator1_pull():
    GPIO.output(ACTUATOR3_PIN1, GPIO.HIGH)
    GPIO.output(ACTUATOR4_PIN2, GPIO.LOW)

# Push Actuator 2 (Top Sealer 2)
def actuator2_push():
    GPIO.output(ACTUATOR5_PIN1, GPIO.LOW)
    GPIO.output(ACTUATOR6_PIN2, GPIO.HIGH)

# Pull Actuator 2
def actuator2_pull():
    GPIO.output(ACTUATOR5_PIN1, GPIO.HIGH)
    GPIO.output(ACTUATOR6_PIN2, GPIO.LOW)

# Main program
try:
    print("Raspberry Pi Two Actuator Control (Top Seal)")
    print("Press Enter to start the sequence...")
    input()

    # Actuator 1 sequence
    print("Pushing Actuator 1...")
    actuator1_push()
    time.sleep(2)

    print("Actuator 1 staying pushed...")
    time.sleep(4)

    print("Returning Actuator 1 to normal...")
    actuator1_pull()
    time.sleep(1)

    # Actuator 2 sequence
    print("Pushing Actuator 2...")
    actuator2_push()
    time.sleep(2)

    print("Actuator 2 staying pushed...")
    time.sleep(4)

    print("Returning Actuator 2 to normal...")
    actuator2_pull()
    time.sleep(1)

    print("Sequence complete.")

except KeyboardInterrupt:
    print("Program interrupted.")

finally:
    turn_off_actuators()
    GPIO.cleanup()
    print("GPIO cleaned up.")
