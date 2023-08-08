import time
import requests
import RPi.GPIO as GPIO

import dht11

def init():
    GPIO.setmode(GPIO.BCM)
    global dht11_inst

    dht11_inst = dht11.DHT11(pin=21)  # read data using pin 21

def read_temp_humidity():

    global dht11_inst

    ret = [-100, -100]

    result = dht11_inst.read()

    if result.is_valid():
        print("Temperature: %-3.1f C" % result.temperature)
        print("Humidity: %-3.1f %%" % result.humidity)

        ret[0] = result.temperature
        ret[1] = result.humidity

    return ret

def data_upload(temp,humidity):
    API_KEY = 'WI07W335WKLRGCY9'
    data = {
        'field1': temp,
        'field2': humidity,
        'key': API_KEY
    }
    response = requests.post('https://api.thingspeak.com/update', data=data)
    print(response.text)  # This will print the entry ID if successful, or '0' if there was an error.

if __name__ == "__main__":
    init()
    while True:
        read_temp_humidity()
        time.sleep(10*60)