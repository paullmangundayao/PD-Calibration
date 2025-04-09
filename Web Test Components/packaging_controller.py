import RPi.GPIO as GPIO
import time
import math

class PackagingController:
    def __init__(self):
        # Initialize all GPIO pins
        GPIO.setmode(GPIO.BCM)
        
        # Actuator pins
        self.ACT1_PIN1, self.ACT1_PIN2 = 22, 27
        self.ACT2_PIN1, self.ACT2_PIN2 = 23, 17
        self.ACT3_PIN1, self.ACT3_PIN2 = 24, 5
        self.ACT4_PIN1, self.ACT4_PIN2 = 25, 6
        
        # Stepper motor pins
        self.STEP1_PIN, self.DIR1_PIN, self.ENA1_PIN = 16, 20, 21
        
        # Linear rail pins
        self.LINEAR1_DIR_PIN = 7
        self.LINEAR1_STEP_PIN = 21
        self.LINEAR1_ENA_PIN = 8
        self.LINEAR2_DIR_PIN = 19
        self.LINEAR2_STEP_PIN = 13
        self.LINEAR2_ENA_PIN = 26
        
        # Servo pins
        self.SERVO_PIN = 4
        self.CLAW_SERVO_PIN = 18
        
        # Motor parameters
        self.STEPS_PER_REV = 3200
        self.LEAD_SCREW_PITCH = 8  # mm
        self.STEPS_PER_MM = self.STEPS_PER_REV / self.LEAD_SCREW_PITCH
        self.LINEAR_STEPS_PER_MM = (200 * 16) / 2  # 200 steps/rev, 16 microsteps, 2mm pitch
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Initialize all GPIO pins"""
        GPIO.setup([
            self.ACT1_PIN1, self.ACT1_PIN2,
            self.ACT2_PIN1, self.ACT2_PIN2,
            self.ACT3_PIN1, self.ACT3_PIN2,
            self.ACT4_PIN1, self.ACT4_PIN2,
            self.STEP1_PIN, self.DIR1_PIN, self.ENA1_PIN,
            self.LINEAR1_DIR_PIN, self.LINEAR1_STEP_PIN, self.LINEAR1_ENA_PIN,
            self.LINEAR2_DIR_PIN, self.LINEAR2_STEP_PIN, self.LINEAR2_ENA_PIN
        ], GPIO.OUT)
        
        # Initialize servos
        self.pwm_servo = GPIO.PWM(self.SERVO_PIN, 50)
        self.pwm_servo.start(0)
        self.pwm_claw = GPIO.PWM(self.CLAW_SERVO_PIN, 50)
        self.pwm_claw.start(0)
    
    def set_servo_angle(self, pin, pwm, angle):
        """Set servo to specific angle (0-180)"""
        duty = (angle / 18) + 2.5
        GPIO.output(pin, True)
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)
        GPIO.output(pin, False)
        pwm.ChangeDutyCycle(0)
    
    def move_stepper(self, length_mm, direction="forward"):
        """Move bubble wrap feed stepper"""
        steps = int(math.ceil(length_mm * self.STEPS_PER_MM))
        GPIO.output(self.DIR1_PIN, GPIO.HIGH if direction == "forward" else GPIO.LOW)
        GPIO.output(self.ENA1_PIN, GPIO.LOW)
        for _ in range(steps):
            GPIO.output(self.STEP1_PIN, GPIO.HIGH)
            time.sleep(0.0005)
            GPIO.output(self.STEP1_PIN, GPIO.LOW)
            time.sleep(0.0005)
        GPIO.output(self.ENA1_PIN, GPIO.HIGH)
    
    def move_linear_rail(self, rail_num, distance_cm, direction="forward"):
        """Move specified linear rail (1 or 2)"""
        if rail_num == 1:
            step_pin = self.LINEAR1_STEP_PIN
            dir_pin = self.LINEAR1_DIR_PIN
            ena_pin = self.LINEAR1_ENA_PIN
        else:
            step_pin = self.LINEAR2_STEP_PIN
            dir_pin = self.LINEAR2_DIR_PIN
            ena_pin = self.LINEAR2_ENA_PIN
            
        steps = int(distance_cm * 10 * self.LINEAR_STEPS_PER_MM)
        GPIO.output(dir_pin, GPIO.HIGH if direction == "forward" else GPIO.LOW)
        GPIO.output(ena_pin, GPIO.LOW)
        for _ in range(steps):
            GPIO.output(step_pin, GPIO.HIGH)
            time.sleep(0.0005)
            GPIO.output(step_pin, GPIO.LOW)
            time.sleep(0.0005)
        GPIO.output(ena_pin, GPIO.HIGH)
    
    def actuator_action(self, actuator_num, action):
        """Control actuators (1-4) with push/pull action"""
        pins = {
            1: (self.ACT1_PIN1, self.ACT1_PIN2),
            2: (self.ACT2_PIN1, self.ACT2_PIN2),
            3: (self.ACT3_PIN1, self.ACT3_PIN2),
            4: (self.ACT4_PIN1, self.ACT4_PIN2)
        }
        pin1, pin2 = pins[actuator_num]
        
        if action == "push":
            GPIO.output(pin1, GPIO.LOW)
            GPIO.output(pin2, GPIO.HIGH)
        else:
            GPIO.output(pin1, GPIO.HIGH)
            GPIO.output(pin2, GPIO.LOW)
    
    def full_packaging_sequence(self):
        """Execute complete packaging sequence"""
        try:
            print("[0] Rolling bubble wrap...")
            self.move_stepper(50, "forward")
            
            print("[1] Performing Initial Seal...")
            for actuator in [1, 2]:
                self.actuator_action(actuator, "push")
                time.sleep(2)
                print(f"Hold seal {actuator}...")
                time.sleep(3)
                self.actuator_action(actuator, "pull")
                time.sleep(1)
            
            print("[2] Placing product...")
            self.set_servo_angle(self.SERVO_PIN, self.pwm_servo, 85)
            time.sleep(3)
            self.set_servo_angle(self.SERVO_PIN, self.pwm_servo, 0)
            
            print("[3] Dispensing bubble wrap...")
            self.move_stepper(100, "forward")
            
            print("[4] Moving linear rails...")
            for rail in [1, 2]:
                self.move_linear_rail(rail, 5, "forward")
            
            print("[5] Pushing product...")
            for actuator in [1, 2]:
                self.actuator_action(actuator, "push")
            time.sleep(5)
            for actuator in [1, 2]:
                self.actuator_action(actuator, "pull")
            
            print("[6] Claw operation...")
            time.sleep(1.5)
            self.set_servo_angle(self.CLAW_SERVO_PIN, self.pwm_claw, 85)
            time.sleep(1)
            print("Claw pulling...")
            time.sleep(2)
            self.set_servo_angle(self.CLAW_SERVO_PIN, self.pwm_claw, 0)
            
            print("[7] Final Seal...")
            for actuator in [3, 4]:
                self.actuator_action(actuator, "push")
                time.sleep(2)
                print(f"Bottom Sealer {actuator-2} holding...")
                time.sleep(3)
                self.actuator_action(actuator, "pull")
                time.sleep(1)
            
            print("✅ Packaging complete!")
            
        except Exception as e:
            print(f"Error during packaging: {str(e)}")
            raise
    
    def cleanup(self):
        """Clean up all GPIO resources"""
        self.pwm_servo.stop()
        self.pwm_claw.stop()
        GPIO.cleanup()