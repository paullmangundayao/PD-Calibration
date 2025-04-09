import RPi.GPIO as GPIO
import time

# Constants
SERVO_PIN = 4  # GPIO 4

def deliver_product():
    """Rotate the servo to 85 degrees (delivery action), then turn off and cleanup."""
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        pwm = GPIO.PWM(SERVO_PIN, 50)  # 50Hz for standard servo
        pwm.start(0)

        angle = 85
        duty = (angle / 18) + 2.5
        GPIO.output(SERVO_PIN, True)
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.5)

        pwm.ChangeDutyCycle(0)
        pwm.stop()
        GPIO.cleanup()

        return True
    except Exception as e:
        print(f"[ERROR] Failed to move servo: {e}")
        GPIO.cleanup()
        return False