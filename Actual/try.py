import RPi.GPIO as GPIO
import time
import math

### -------------------- GPIO SETUP --------------------
GPIO.setmode(GPIO.BCM)

# -------------------- TOP SEAL ACTUATORS --------------------
ACT1_PIN1, ACT1_PIN2 = 22, 27
ACT2_PIN1, ACT2_PIN2 = 23, 17
GPIO.setup([ACT1_PIN1, ACT1_PIN2, ACT2_PIN1, ACT2_PIN2], GPIO.OUT)

# -------------------- BOTTOM SEAL ACTUATORS --------------------
ACT3_PIN1, ACT3_PIN2 = 24, 5   # Bottom Sealer 1
ACT4_PIN1, ACT4_PIN2 = 25, 6   # Bottom Sealer 2
GPIO.setup([ACT3_PIN1, ACT3_PIN2, ACT4_PIN1, ACT4_PIN2], GPIO.OUT)

# -------------------- SERVO MOTOR (Product Placement) --------------------
SERVO_PIN = 4
GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm_servo = GPIO.PWM(SERVO_PIN, 50)
pwm_servo.start(0)

# -------------------- BUBBLE WRAP FEED (Stepper 1) --------------------
STEP1_PIN, DIR1_PIN, ENA1_PIN = 16, 20, 21
GPIO.setup([STEP1_PIN, DIR1_PIN, ENA1_PIN], GPIO.OUT)

# Stepper Motor Parameters (Bubble Wrap Feed)
STEPS_PER_REV = 3200
LEAD_SCREW_PITCH = 8  # mm
STEPS_PER_MM = STEPS_PER_REV / LEAD_SCREW_PITCH

# -------------------- LINEAR RAIL MOTORS (Stepper 2 & 3) --------------------
LINEAR1_DIR_PIN = 7
LINEAR1_STEP_PIN = 21
LINEAR1_ENA_PIN = 8

LINEAR2_DIR_PIN = 19
LINEAR2_STEP_PIN = 13
LINEAR2_ENA_PIN = 26

GPIO.setup([LINEAR1_DIR_PIN, LINEAR1_STEP_PIN, LINEAR1_ENA_PIN], GPIO.OUT)
GPIO.setup([LINEAR2_DIR_PIN, LINEAR2_STEP_PIN, LINEAR2_ENA_PIN], GPIO.OUT)

LINEAR_STEPS_PER_REV = 200
LINEAR_MICROSTEPPING = 16
LINEAR_LEADSCREW_PITCH = 2  # mm
LINEAR_STEPS_PER_MM = (LINEAR_STEPS_PER_REV * LINEAR_MICROSTEPPING) / LINEAR_LEADSCREW_PITCH

# -------------------- CLAW SERVO --------------------
CLAW_SERVO_PIN = 18
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

def move_linear_rail(step_pin, dir_pin, ena_pin, distance_cm, direction="forward"):
    steps = int(distance_cm * 10 * LINEAR_STEPS_PER_MM)
    GPIO.output(dir_pin, GPIO.HIGH if direction == "forward" else GPIO.LOW)
    GPIO.output(ena_pin, GPIO.LOW)
    print(f"Moving linear rail {distance_cm} cm ({steps} steps) {direction}")
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
    GPIO.output([
        ACT1_PIN1, ACT1_PIN2,
        ACT2_PIN1, ACT2_PIN2,
        ACT3_PIN1, ACT3_PIN2,
        ACT4_PIN1, ACT4_PIN2
    ], GPIO.HIGH)

### -------------------- MAIN SEQUENCE --------------------
try:
    input("Press Enter to start full packaging sequence...")

    print("[0] Rolling bubble wrap for initial material...")
    move_stepper(50, STEP1_PIN, DIR1_PIN, ENA1_PIN, "forward")

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

    print("[2] Placing product using servo...")
    set_servo(SERVO_PIN, pwm_servo, 85)
    time.sleep(3)
    set_servo(SERVO_PIN, pwm_servo, 0)

    print("[3] Dispensing bubble wrap...")
    move_stepper(100, STEP1_PIN, DIR1_PIN, ENA1_PIN, "forward")

    print("[4] Moving linear rail 1...")
    move_linear_rail(LINEAR1_STEP_PIN, LINEAR1_DIR_PIN, LINEAR1_ENA_PIN, 5, "forward")

    print("[4] Moving linear rail 2...")
    move_linear_rail(LINEAR2_STEP_PIN, LINEAR2_DIR_PIN, LINEAR2_ENA_PIN, 5, "forward")

    print("[5] Pushing product...")
    actuator_push(ACT1_PIN1, ACT1_PIN2)
    actuator_push(ACT2_PIN1, ACT2_PIN2)
    time.sleep(5)
    actuator_pull(ACT1_PIN1, ACT1_PIN2)
    actuator_pull(ACT2_PIN1, ACT2_PIN2)

    print("[6] Claw grabbing bubble wrap...")
    time.sleep(1.5)
    set_servo(CLAW_SERVO_PIN, pwm_claw, 85)
    time.sleep(1)
    print("Claw pulling bubble wrap...")
    time.sleep(2)
    set_servo(CLAW_SERVO_PIN, pwm_claw, 0)

    print("[7] Performing Final Seal with Bottom Sealers...")
    actuator_push(ACT3_PIN1, ACT3_PIN2)
    time.sleep(2)
    print("Bottom Sealer 1 holding...")
    time.sleep(3)
    actuator_pull(ACT3_PIN1, ACT3_PIN2)
    time.sleep(1)

    actuator_push(ACT4_PIN1, ACT4_PIN2)
    time.sleep(2)
    print("Bottom Sealer 2 holding...")
    time.sleep(3)
    actuator_pull(ACT4_PIN1, ACT4_PIN2)
    time.sleep(1)

    print("✅ Full packaging process completed.")

except KeyboardInterrupt:
    print("\n⚠️ Process interrupted by user.")

finally:
    turn_off_actuators()
    pwm_servo.stop()
    pwm_claw.stop()
    GPIO.cleanup()
    print("🧹 GPIO cleaned up.")