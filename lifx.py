import paho.mqtt.client as mqtt                 # MQTT paho library
from gpiozero import LED, Button, MotionSensor  # gpiozero library
from time import sleep                          # Sleep function
import requests                                 # Lifx HTTP requests
print("Import done")

# Lifx HTTP api token
TOKEN = ""
# Label of light to be controlled
label = "Taklampa"
# Time until ligth turns off after no motion, defined in minutes
timer = 15

# GPIO pins
onboard = LED(47, active_high=False, initial_value=True)    # Onboard LED
pir = MotionSensor(17)  # Motion sensor, physical pin: 11
b1 = Button(27)         # Button 1, physical pin: 13
b2 = Button(22)         # Button 2, physical pin: 15
b3 = Button(23)         # Button 3, physical pin: 16
b4 = Button(24)         # Button 4, physical pin: 18

# Lifx states
on = {
    "power": "on",
    "duration": 1.5,
}
off = {
    "power": "off",
    "duration": 1.5,
}

temptimer = 0       # Define countdown variable
sensor = True       # Define initial sensor state, use same as initial led state
light = True        # Define initial lifx light state


def sensorToggle():
    global sensor
    global temptimer
    global light
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
    client.publish("lifxhomeauto/status", payload=bool(sensor))
    print("Sensor is now", bool(sensor))


def motionOn():
    global light
    global temptimer
    print()
    print("Motion detected")
    temptimer = 0
    if light == False:
        lifx(on)
        light = True


def motionOff():
    global light
    global temptimer
    print("No motion, starting timer")
    temptimer = 1       # Start countdown timer as while loop


def on_message(client, userdata, msg):
    print("Topic:", msg.topic)
    print("Message:", str(msg.payload.decode("utf-8")))
    sensorToggle()


def lifx(state):
    response = requests.put("https://api.lifx.com/v1/lights/label:" + label +
                            "/state", data=state, headers={"Authorization": "Bearer %s" % TOKEN, })
    print("Light powered", state["power"] + ".", response)


print("Setting up GPIO pins")
pir.when_motion = motionOn      # Callback when motion
pir.when_no_motion = motionOff  # Callback when no motion

b1.when_pressed = sensorToggle  # Callback when button 1 pressed

print("Setting up MQTT client")
client = mqtt.Client()
client.on_message = on_message
client.connect("broker.mqttdashboard.com")
client.loop_start()
client.subscribe("lifxhomeauto/state", 2)

sleep(1)  # Wait for GPIO to initialize


print("Initializing loop")
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
                print("No motion for", timer, "minutes")

except (KeyboardInterrupt, SystemExit):
    print()
    print("KeyboardInterrupt detected, exiting...")
    client.loop_stop()
    raise
except:
    print("Exit and cleanup sucsessful")
