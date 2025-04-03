import RPi.GPIO as GPIO
import time
import math
import keyboard

# ----------------- GPIO CONFIG -----------------
STEP_PIN = 16
DIR_PIN = 20
EN_PIN = # Add Enable pin (OPTIONAL FOR LINEAR SLIDE RAILS)

relay1 = 22 # Horizontal
relay2 = 27 # Horizontal
relay3 = 23 # Horizontal
relay4 = 17 # Horizontal

SERVO_PIN = 4  # Product slider

# ----------------- SETUP -----------------
GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(relay1, GPIO.OUT)
GPIO.setup(relay2, GPIO.OUT)
GPIO.setup(relay3, GPIO.OUT)
GPIO.setup(relay4, GPIO.OUT)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Servo PWM setup
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

# ----------------- CONSTANTS -----------------
STEPS_PER_REV = 3200
LEAD_SCREW_PITCH = 8
STEPS_PER_MM = STEPS_PER_REV / LEAD_SCREW_PITCH
FIXED_LENGTH_MM = 10 # Fixed length depending on initial seal length

# ----------------- FUNCTION DEFINITIONS -----------------
def move_stepper(length_mm):
    steps_required = int(math.ceil(length_mm * STEPS_PER_MM))
    GPIO.output(DIR_PIN, GPIO.HIGH)  # Always forward
    for _ in range(steps_required):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.0005)

def turn_off_all_relays():
    GPIO.output(relay1, GPIO.HIGH)
    GPIO.output(relay2, GPIO.HIGH)
    GPIO.output(relay3, GPIO.HIGH)
    GPIO.output(relay4, GPIO.HIGH)

def actuators_push():
    GPIO.output(relay1, GPIO.LOW)
    GPIO.output(relay2, GPIO.HIGH)
    GPIO.output(relay3, GPIO.LOW)
    GPIO.output(relay4, GPIO.HIGH)
    time.sleep(7)
    turn_off_all_relays()

def actuators_pull():
    GPIO.output(relay1, GPIO.HIGH)
    GPIO.output(relay2, GPIO.LOW)
    GPIO.output(relay3, GPIO.HIGH)
    GPIO.output(relay4, GPIO.LOW)
    time.sleep(5)
    turn_off_all_relays()

def set_servo_angle(angle):
    duty = (angle / 18) + 2.5
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(SERVO_PIN, False)
    pwm.ChangeDutyCycle(0)

def ask_for_distance(): # Stepper roller
    while True:
        user_input = input("Enter the distance in mm for the stepper motor to move: ").strip()
        try:
            distance = float(user_input)
            if distance <= 0:
                print("Distance must be greater than 0.")
            else:
                return distance
        except ValueError:
            print("Invalid input. Please enter a valid number.")

# ----------------- MAIN -----------------
try:
    turn_off_all_relays()

    answer = input("Do you want to perform the initial seal? (yes/no): ").strip().lower()
    if answer == "yes":
        move_stepper(FIXED_LENGTH_MM)
        actuators_push()
        time.sleep(0.5)
        actuators_pull()

    print("Press 's' to continue to servo step or 'q' to quit.")

    while True:
        if keyboard.read_key() == 's':
            set_servo_angle(85)
            time.sleep(1)
            set_servo_angle(0)
            break
        elif keyboard.is_pressed('q'):
            break
        time.sleep(0.05)

    # Stepper distance input
    distance_mm = ask_for_distance()
    move_stepper(distance_mm)

except KeyboardInterrupt:
    pass

finally:
    turn_off_all_relays()
    pwm.stop()
    GPIO.cleanup()