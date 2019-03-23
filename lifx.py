import time

import requests
import RPi.GPIO as GPIO

token = ""
label = "Taklampa"
on = {
    "power": "on",
    "duration": 1.5,
}
off = {
    "power": "off",
    "duration": 1.5,
}


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN)  # Read output from PIR motion sensor

while True:
    i = GPIO.input(11)

    if i == 0:  # When output from motion sensor is LOW
        time.sleep(0.5)
    elif i == 1:  # When output from motion sensor is HIGH
        print("Intruder detected"), i
        # GPIO.output(3, 1)  # Turn ON LED
        offtimer = 0
        response = requests.put("https://api.lifx.com/v1/lights/label:" + label +
                                "/state", data=on, headers={"Authorization": "Bearer %s" % token, })
        time.sleep(0.5)
    while offtimer > timertemp:
        response = requests.put("https://api.lifx.com/v1/lights/label:" + label +
                                "/state", data=off, headers={"Authorization": "Bearer %s" % token, })
