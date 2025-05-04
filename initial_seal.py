import RPi.GPIO as GPIO
import time
import math

class InitialSealController:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)

        # Actuator pins (Top Sealer 1 & 2)
        self.ACT1_PIN1, self.ACT1_PIN2 = 22, 27
        self.ACT2_PIN1, self.ACT2_PIN2 = 14, 17

        # Stepper motor pins for bubble wrap feed
        self.STEP1_PIN, self.DIR1_PIN = 13, 19
        self.STEPS_PER_REV = 3200
        self.LEAD_SCREW_PITCH = 8  # mm
        self.STEPS_PER_MM = self.STEPS_PER_REV / self.LEAD_SCREW_PITCH

        self._setup_gpio()

    def _setup_gpio(self):
        GPIO.setup([
            self.ACT1_PIN1, self.ACT1_PIN2,
            self.ACT2_PIN1, self.ACT2_PIN2,
            self.STEP1_PIN, self.DIR1_PIN
        ], GPIO.OUT)

    def move_stepper(self, length_mm):
        """Feed bubble wrap forward by specific length in mm."""
        steps = int(math.ceil(length_mm * self.STEPS_PER_MM))
        GPIO.output(self.DIR1_PIN, GPIO.HIGH)
        for _ in range(steps):
            GPIO.output(self.STEP1_PIN, GPIO.HIGH)
            time.sleep(0.0005)
            GPIO.output(self.STEP1_PIN, GPIO.LOW)
            time.sleep(0.0005)
        print(f"[Stepper] Moved {length_mm} mm ({steps} steps)")

    def actuate_push(self):
        """Extend both actuators."""
        GPIO.output(self.ACT1_PIN1, GPIO.HIGH)
        GPIO.output(self.ACT1_PIN2, GPIO.LOW)
        GPIO.output(self.ACT2_PIN1, GPIO.HIGH)
        GPIO.output(self.ACT2_PIN2, GPIO.LOW)
        print("[Actuators] Extended")

    def actuate_pull(self):
        """Retract both actuators."""
        GPIO.output(self.ACT1_PIN1, GPIO.LOW)
        GPIO.output(self.ACT1_PIN2, GPIO.HIGH)
        GPIO.output(self.ACT2_PIN1, GPIO.LOW)
        GPIO.output(self.ACT2_PIN2, GPIO.HIGH)
        print("[Actuators] Retracted")

    def feed_wrap(self, length_mm=500):
        """Feeds wrap, waits, and activates sealing actuators."""
        print("[Sequence] Feeding bubble wrap...")
        self.move_stepper(length_mm)

        print("[Sequence] Waiting before sealing...")
        time.sleep(5)

        print("[Sequence] Pushing actuators...")
        self.actuate_push()

        time.sleep(2)

        print("[Sequence] Pulling actuators...")
        self.actuate_pull()

    def cleanup(self):
        GPIO.cleanup()
