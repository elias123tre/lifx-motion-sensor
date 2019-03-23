import logging  # Logging library
import subprocess  # Library to send shell commands from python
from os import remove  # Remove file function
from time import sleep  # Sleep function

import paho.mqtt.client as mqtt  # MQTT paho library
import requests  # Lifx HTTP requests
from gpiozero import LED, Button, MotionSensor  # gpiozero library
from lifxlan import LifxLAN  # Lifx Lan requests

print("Import done")

remove("lifx.log")
print("Log file cleared")

console_logging_format = "%(levelname)s: %(funcName)s @ %(lineno)d - %(name)s: %(message)s"
file_logging_format = "%(levelname)s: %(asctime)s: %(name)s: %(message)s"
# Console logging
logging.basicConfig(level=logging.DEBUG, format=console_logging_format)
logger = logging.getLogger()
# Create a file handler for output file
handler = logging.FileHandler("lifx.log")
formatter = logging.Formatter(file_logging_format)
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.info("This is saved to the log")

# Rclone to publish lifx.py to google drive
subprocess.run(
    'rclone sync "lifx.py" "drive:Filer/RaspberryPi" -P', shell=True)

# Lifx lan environment and number of devices
lan = LifxLAN(1)
# Label of light to be controlled
label = "Taklampa"
# Get light(s) (add more by adding a list [])
bulb = lan.get_device_by_name(label)
logging.info("Light found: " + bulb.get_label())
# Lifx HTTP api token, deprecated
TOKEN = "c6df528836417f584c1eeff650329a767ed7bd6bcd4a7adc02766bf74fcbc2eb"
# Time until light turns off after no motion, defined in minutes
timer = 15

# GPIO pins
onboard = LED(47, active_high=False, initial_value=True)    # Onboard LED
pir = MotionSensor(17)  # Motion sensor, physical pin: 11
b1 = Button(27)         # Button 1, physical pin: 13
b2 = Button(22)         # Button 2, physical pin: 15
b3 = Button(23)         # Button 3, physical pin: 16
b4 = Button(24)         # Button 4, physical pin: 18

# Lifx states in brightness
on = 65535
off = 0

temptimer = 0       # Define countdown variable
sensor = True       # Define initial sensor state, use same as initial led state
if bulb.get_power() == on:
    light = True        # Define initial lifx light state
else:
    light = False       # Define initial lifx light state
logging.debug("Sensor: " + str(sensor) + " Light: " + str(light))


def sensorToggle():
    global sensor
    global temptimer
    global light
    print("Before publish")
    if sensor == False:      # When toggeling if already true
        onboard.on()                    # Turn on onboard LED
        lifx(on)
        light = True
        if pir.motion_detected:
            temptimer = 0
        elif not pir.motion_detected:
            temptimer = 1
        sensor ^= 1                     # Toggle sensor variable
        pir.when_motion = motionOn      # Enable PIR callbacks
        pir.when_no_motion = motionOff  # Enable PIR callbacks
    elif sensor == True:     # When toggeling if already false
        onboard.off()                   # Turn off onboard LED
        lifx(off)
        light = False
        temptimer = 0
        sensor ^= 1                     # Toggle sensor variable
        pir.when_motion = None          # Disable PIR callbacks
        pir.when_no_motion = None       # Disable PIR callbacks
    # Publish sensor state
    client.publish("lifxhomeauto/sensor", payload=bool(sensor))
    logging.debug("Sensor state: " + str(bool(sensor)))


def motionOn():
    global light
    global temptimer
    print()
    logging.debug("Motion detected")
    temptimer = 0
    if light == False:
        lifx(on)
        light = True


def motionOff():
    global light
    global temptimer
    logging.debug("No motion, starting timer")
    temptimer = 1       # Start countdown timer as while loop


def on_message(client, userdata, msg):
    if str(msg.topic) == "lifxhomeauto/toggle":
        sensorToggle()

    logging.debug("Topic: " + str(msg.topic))
    logging.debug("Message: " + str(msg.payload.decode("utf-8")))


def on_disconnect(client, userdata, rc):
    logging.warning("MQTT Disconnected")
    logging.debug(client.error_string(rc))
    logging.debug("Reconnecting")
    client.reconnect()


# def on_log(client, obj, level, string):
#     print(string)


# def on_log(client, userdata, level, buf):
#     if "PING" in buf:
#         print


def lifx(state):
    bulb.set_power(state, True)
    logging.debug("Light brightness: " + str(state))


logging.info("Setting up GPIO pins")
pir.when_motion = motionOn      # Callback when motion
pir.when_no_motion = motionOff  # Callback when no motion

b1.when_pressed = sensorToggle  # Callback when button 1 pressed

logging.info("Setting up MQTT client")
client = mqtt.Client()
client.enable_logger()
client.on_message = on_message
client.on_disconnect = on_disconnect
# client.on_log = on_log
client.connect("iot.eclipse.org")
client.loop_start()
client.subscribe("lifxhomeauto/toggle", 2)
# client.subscribe("lifxhomeauto/state", 0)

sleep(1)  # Wait for GPIO to initialize


logging.info("Initializing loop")
try:
    while True:
        while temptimer > 0:
            temptimer += 1
            sleep(1)
            print(temptimer, end="\r")
            if temptimer > timer * 60:
                temptimer = 0
                lifx(off)
                light = False
                logging.debug("No motion for " + str(timer) + " minutes")

except (KeyboardInterrupt, SystemExit):
    print()
    print("KeyboardInterrupt detected, exiting...")
    client.loop_stop()
    raise
except Exception:
    logger.exception("Error has occurred")
