import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)  # BCM for GPIO numbering
GPIO.setup(17, GPIO.OUT)  # Make pin 17 (which is hooked up to the BRC pin) an output

while True:
    # Pulse the BRC pin at a low duty cycle to keep Roomba awake.
    GPIO.output(17, False)
    sleep(1)
    GPIO.output(17, True)
    sleep(30)

