import RPi.GPIO as GPIO
import time
import logging

# Configure logging for debugging output
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ServoCamera:
    def __init__(self):
        # GPIO pin assignments
        self.TRIG_PIN = 23      # Trigger pin for HC-SR04
        self.ECHO_PIN = 24      # Echo pin for HC-SR04
        self.SERVO_PIN = 18     # PWM output pin for servo
        self.NEUTRAL_ANGLE = 90 # Neutral servo angle (degrees)
        self.SCALING_FACTOR = 1.2 # Distance error to angle adjustment factor
        self.TARGET_DISTANCE = 19.8
        
        self._setup_gpio()
        
    def _setup_gpio(self):
        """Initialize GPIO pins and PWM for servo"""
        logging.debug("Setting up GPIO...")
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.TRIG_PIN, GPIO.OUT)
        GPIO.setup(self.ECHO_PIN, GPIO.IN)
        GPIO.setup(self.SERVO_PIN, GPIO.OUT)
        
        # Initialize servo PWM at 50Hz
        self.servo = GPIO.PWM(self.SERVO_PIN, 50)
        self.servo.start(0)
        logging.debug("GPIO setup complete.")
    
    def measure_distance(self, timeout=0.2):
        """
        Measures distance using ultrasonic sensor
        Returns distance in cm or None if measurement fails
        """
        logging.debug("Measuring distance...")
        GPIO.output(self.TRIG_PIN, False)
        time.sleep(0.0002)

        GPIO.output(self.TRIG_PIN, True)
        time.sleep(0.00001)
        GPIO.output(self.TRIG_PIN, False)

        start_time = time.time()
        stop_time = time.time()

        # Wait for echo start
        echo_start = time.time()
        while GPIO.input(self.ECHO_PIN) == 0:
            start_time = time.time()
            if time.time() - echo_start > timeout:
                logging.error("Timeout waiting for echo start.")
                return None

        # Wait for echo end
        echo_end = time.time()
        while GPIO.input(self.ECHO_PIN) == 1:
            stop_time = time.time()
            if time.time() - echo_end > timeout:
                logging.error("Timeout waiting for echo end.")
                return None

        elapsed_time = stop_time - start_time
        distance = (elapsed_time * 34300) / 2
        logging.debug(f"Distance measured: {distance:.2f} cm")
        return distance
    
    def set_servo_angle(self, angle):
        """Sets servo to specified angle (0-180 degrees)"""
        logging.debug(f"Setting servo angle to: {angle} degrees")
        angle = max(0, min(160, angle))
        duty_cycle = angle / 18.0 + 2.5
        self.servo.ChangeDutyCycle(duty_cycle)
        time.sleep(0.5)
        self.servo.ChangeDutyCycle(0)
        logging.debug("Servo angle set.")
    
    def adjust_side_camera_position(self, target_distance=None, tolerance=0.5, max_iterations=20):
        """
        Adjusts side camera position using ultrasonic feedback
        Uses class TARGET_DISTANCE if none provided
        """
        if target_distance is None:
            target_distance = self.TARGET_DISTANCE
            
        logging.debug("Adjusting side camera position...")
        current_angle = self.NEUTRAL_ANGLE
        self.set_servo_angle(current_angle)

        for i in range(max_iterations):
            distance = self.measure_distance()
            if distance is None:
                logging.error("Distance measurement failed. Skipping iteration.")
                continue

            error = distance - target_distance
            logging.debug(f"[Side Cam Adjust] Iter {i}: Dist={distance:.2f}cm, Error={error:.2f}cm")
            
            if abs(error) <= tolerance:
                logging.debug("[Side Cam Adjust] Target distance reached.")
                break
                
            angle_adjustment = error * self.SCALING_FACTOR
            new_angle = current_angle - angle_adjustment
            new_angle = max(0, min(160, new_angle))
            self.set_servo_angle(new_angle)
            current_angle = new_angle
            time.sleep(0.1)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        logging.debug("Cleaning up hardware...")
        self.servo.stop()
        GPIO.cleanup()