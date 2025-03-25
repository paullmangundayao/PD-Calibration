import RPi.GPIO as GPIO
import time

# Constants
SERVO_PIN = 4  # GPIO 4 (physical pin 7), Change depending sa setup

# Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Set PWM frequency to 50Hz (standard for servos)
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_angle(angle):
    """Rotate the servo to the specified angle."""
    duty = (angle / 18) + 2.5
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    pwm.ChangeDutyCycle(0)

try:
    print("Servo Control Program")
    print("Enter 0 for 0 degrees")
    print("Enter 1 for 85 degrees")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("Enter mode (0 or 1): ").strip()

        if user_input == '0':
            print("Setting servo to 0 degrees.")
            set_angle(0)
        elif user_input == '1':
            print("Setting servo to 85 degrees.")
            set_angle(85)
        elif user_input.lower() == 'exit':
            print("Exiting program.")
            break
        else:
            print("Invalid input. Please enter 0, 1, or 'exit'.")

except KeyboardInterrupt:
    print("\nProgram interrupted by user.")

finally:
    pwm.stop()
    GPIO.cleanup()
    print("GPIO cleanup done.")
