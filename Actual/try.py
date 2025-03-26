import RPi.GPIO as GPIO
import time
import math

### -------------------- GPIO SETUP --------------------
GPIO.setmode(GPIO.BCM)

# -------------------- TOP SEAL ACTUATORS --------------------
ACT1_PIN1, ACT1_PIN2 = 22, 27
ACT2_PIN1, ACT2_PIN2 = 23, 17
GPIO.setup([ACT1_PIN1, ACT1_PIN2, ACT2_PIN1, ACT2_PIN2], GPIO.OUT)

# -------------------- SERVO MOTOR (Product Placement) --------------------
SERVO_PIN = 4
GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm_servo = GPIO.PWM(SERVO_PIN, 50)
pwm_servo.start(0)

# -------------------- BUBBLE WRAP FEED (Stepper 1) --------------------
STEP1_PIN, DIR1_PIN, ENA1_PIN = 16, 20, 21
GPIO.setup([STEP1_PIN, DIR1_PIN, ENA1_PIN], GPIO.OUT)

# Stepper Motor Parameters
STEPS_PER_REV = 3200
LEAD_SCREW_PITCH = 8  # mm
STEPS_PER_MM = STEPS_PER_REV / LEAD_SCREW_PITCH

# -------------------- LINEAR RAILS (Stepper 2) --------------------
# Using same pins as bubble wrap for demo, change if needed

# -------------------- CLAW SERVO & LINEAR ACTUATOR --------------------
CLAW_SERVO_PIN = 18  # Change if different
GPIO.setup(CLAW_SERVO_PIN, GPIO.OUT)
pwm_claw = GPIO.PWM(CLAW_SERVO_PIN, 50)
pwm_claw.start(0)

# -------------------- UTILITIES --------------------
def set_servo(pin, pwm, angle):
    duty = (angle / 18) + 2.5
    GPIO.output(pin, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    GPIO.output(pin, False)
    pwm.ChangeDutyCycle(0)

def move_stepper(length_mm, step_pin, dir_pin, ena_pin, direction="forward"):
    steps = int(math.ceil(length_mm * STEPS_PER_MM))
    GPIO.output(dir_pin, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    GPIO.output(ena_pin, GPIO.LOW)
    for _ in range(steps):
        GPIO.output(step_pin, GPIO.HIGH)
        time.sleep(0.0005)
        GPIO.output(step_pin, GPIO.LOW)
        time.sleep(0.0005)
    GPIO.output(ena_pin, GPIO.HIGH)

def actuator_push(pin1, pin2):
    GPIO.output(pin1, GPIO.LOW)
    GPIO.output(pin2, GPIO.HIGH)

def actuator_pull(pin1, pin2):
    GPIO.output(pin1, GPIO.HIGH)
    GPIO.output(pin2, GPIO.LOW)

def turn_off_actuators():
    GPIO.output([ACT1_PIN1, ACT1_PIN2, ACT2_PIN1, ACT2_PIN2], GPIO.HIGH)

### -------------------- MAIN SEQUENCE --------------------

try:
    input("Press Enter to start full packaging sequence...")

    # 1. INITIAL SEAL
    print("[1] Performing Initial Seal...")
    actuator_push(ACT1_PIN1, ACT1_PIN2)
    time.sleep(2)
    print("Hold seal...")
    time.sleep(3)
    actuator_pull(ACT1_PIN1, ACT1_PIN2)
    time.sleep(1)

    actuator_push(ACT2_PIN1, ACT2_PIN2)
    time.sleep(2)
    print("Hold seal...")
    time.sleep(3)
    actuator_pull(ACT2_PIN1, ACT2_PIN2)
    time.sleep(1)

    # 2. PRODUCT PLACEMENT USING SERVO
    print("[2] Placing product using servo...")
    set_servo(SERVO_PIN, pwm_servo, 85)
    time.sleep(3)
    set_servo(SERVO_PIN, pwm_servo, 0)

    # 3. DISPENSING BUBBLE WRAP
    print("[3] Dispensing bubble wrap...")
    move_stepper(100, STEP1_PIN, DIR1_PIN, ENA1_PIN, "forward")  # 100mm = 10cm as example

    # 4. POSITION LINEAR RAILS
    print("[4] Moving linear rails...")
    move_stepper(50, STEP1_PIN, DIR1_PIN, ENA1_PIN, "forward")  # 50mm

    # 5. PUSH PRODUCT WITH LINEAR ACTUATORS (SIMULATED)
    print("[5] Pushing product...")
    actuator_push(ACT1_PIN1, ACT1_PIN2)
    actuator_push(ACT2_PIN1, ACT2_PIN2)
    time.sleep(5)
    actuator_pull(ACT1_PIN1, ACT1_PIN2)
    actuator_pull(ACT2_PIN1, ACT2_PIN2)

    # 6. CLAW MECHANISM
    print("[6] Claw grabbing bubble wrap...")
    time.sleep(1.5)
    set_servo(CLAW_SERVO_PIN, pwm_claw, 85)  # Grip
    time.sleep(1)
    print("Claw pulling bubble wrap...")
    time.sleep(2)
    set_servo(CLAW_SERVO_PIN, pwm_claw, 0)  # Release

    print("✅ Full process completed.")

except KeyboardInterrupt:
    print("\nProcess interrupted.")

finally:
    turn_off_actuators()
    pwm_servo.stop()
    pwm_claw.stop()
    GPIO.cleanup()
    print("GPIO cleaned up.")
