import requests

token = ""

headers = {
    "Authorization": "Bearer %s" % token,
}

payload = {
    "power": "on",
    "duration": 1.5,
}

motion = 1

if motion == 1:
    response = requests.put('https://api.lifx.com/v1/lights/label:Taklampa/state', data=payload, headers=headers)
