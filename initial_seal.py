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

    def feed_wrap(self, length_mm=50):
        """Wrapper method to feed bubble wrap before sealing."""
        try:
            print(f"[0] Rolling bubble wrap for {length_mm}mm...")
            self.move_stepper(length_mm)
            print(f"✅ Feeding complete.")
        except Exception as e:
            print(f"Error during bubble wrap feed: {str(e)}")
            raise

    def actuator_action(self, actuator_num, action):
        pins = {
            1: (self.ACT1_PIN1, self.ACT1_PIN2),
            2: (self.ACT2_PIN1, self.ACT2_PIN2)
        }
        pin1, pin2 = pins[actuator_num]
        if action == "push":
            GPIO.output(pin1, GPIO.LOW)
            GPIO.output(pin2, GPIO.HIGH)
        else:
            GPIO.output(pin1, GPIO.HIGH)
            GPIO.output(pin2, GPIO.LOW)

    def perform_initial_seal(self):
        """Run the actuator sealing process after bubble wrap is fed."""
        try:
            print("[1] Activating top seal actuators...")
            for actuator in [1, 2]:
                self.actuator_action(actuator, "push")
                time.sleep(4)
                print(f"Sealing with Actuator {actuator}...")
                time.sleep(3)
                self.actuator_action(actuator, "pull")
                time.sleep(3)

            print("✅ Initial sealing complete!")
        except Exception as e:
            print(f"Error during initial sealing: {str(e)}")
            raise

    def cleanup(self):
        """Safely reset all GPIO pins."""
        GPIO.cleanup()
        print("GPIO cleanup done.")
