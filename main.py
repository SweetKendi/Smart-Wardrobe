import RPi.GPIO as GPIO
import dht11
import time
import tkinter as tk
from tkinter import messagebox
from mfrc522 import SimpleMFRC522
import requests
import random

GPIO.setwarnings(False)
reader = SimpleMFRC522()

# Light-wear and Transitional Outfit Inventories
lightwear_inventory = []
layered_inventory = []
#details for Telegram bot
bot_token = '6584510597:AAHe3yzXCntJJbuyjFrihapke83QtXl_LLc'
chat_id = '5284112161'
clothing_type_var = None
outfit_entry = None



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

def send_telegram_message(bot_token, chat_id, message):
    base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")

# Function to fetch weather data
def fetch_weather():
    # Replace with your API key and channel ID
    api_key = "<YOUR_API_KEY>"
    channel_id = "<CHANNEL_ID>"
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={api_key}&results=2"

    try:
        response = requests.get(url)
        data = response.json()

        if "feeds" in data and len(data["feeds"]) > 0:
            feed = data["feeds"][0]
            temperature = float(feed.get("field1"))
            humidity = float(feed.get("field2"))
            weather_label.config(text=f"Temperature: {temperature}°C, Humidity: {humidity}%")
            recommend_outfit(temperature, humidity)
        else:
            weather_label.config(text="Weather data not available")
    except requests.RequestException:
        weather_label.config(text="Failed to fetch weather data")


# Function to recommend outfit based on temperature and humidity
def recommend_outfit(temperature, humidity):
    # Fetch the weather data first
    fetch_weather()

    if temperature > 25 and humidity > 60:
        if layered_inventory:
            recommended_outfit = random.choice(layered_inventory)
            outfit_label.config(text=f"Recommended layered Outfit: {recommended_outfit}")
        else:
            outfit_label.config(text="No layered outfit available in inventory")
            recommended_outfit = None
    else:
        if lightwear_inventory:
            recommended_outfit = random.choice(lightwear_inventory)
            outfit_label.config(text=f"Recommended Light-wear Outfit: {recommended_outfit}")
        else:
            outfit_label.config(text="No Light-wear outfit available in inventory")
            recommended_outfit = None

    # Send the recommended outfit via Telegram
    if recommended_outfit:
        send_telegram_message(bot_token, chat_id, recommended_outfit)

    return recommended_outfit


def clear_database():
    resp = input("Enter y to clear the database: ")
    if resp == 'y':
        with open("authlist.txt", "w") as f:
            f.write("")
        print("Database cleared.")


def write_clothing_details(id):
    outfit = input("Enter outfit: ")
    clothing_type = input("Enter type (lightwear/layered): ")
    with open("clothing_details.txt", "a+") as f:
        f.write(f"{id}:{outfit}:{clothing_type}\n")

    # Add the outfit to the appropriate list based on the type
    if clothing_type == 'lightwear':
        lightwear_inventory.append(outfit)
        print(f"New outfit '{outfit}' added to lightwear inventory!")
    elif clothing_type == 'layered':
        layered_inventory.append(outfit)
        print(f"New outfit '{outfit}' added to layered inventory!")


def register_card():
    global clothing_type_var, outfit_entry  # Declare the variables as global within the function

    id = reader.read_id()
    id = str(id)

    with open("authlist.txt", "r") as f:
        auth = f.read()
    if id not in auth:
        with open("authlist.txt", "a+") as f:
            f.write(id + '\n')
        pos = auth.count('\n')
        messagebox.showinfo("Card Registered", f"New card with UID {id} detected; registered as entry #{pos}")

        # Get data from the GUI input fields
        outfit = outfit_entry.get()
        clothing_type = clothing_type_var.get()  # This will only return "lightwear" or "layered"

        write_clothing_details(id, outfit, clothing_type)


def check_details():
    id = reader.read_id()
    id = str(id)

    with open("authlist.txt", "r") as f:
        auth = f.read()
    if id in auth:
        number = auth.split('\n')
        pos = number.index(id)
        messagebox.showinfo("Card Found", f"Card with UID {id} found in database entry #{pos}; access granted")
        with open("clothing_details.txt", "r") as f:
            details = f.read().splitlines()
        clothing_info = None
        for line in details:
            if line.startswith(id + ":"):
                fields = line.split(":")
                outfit = fields[1]
                clothing_type = fields[2]
                clothing_info = f"Outfit: {outfit}\nType: {clothing_type}"
                break
        if clothing_info:
            messagebox.showinfo("Clothing Details", clothing_info)
        else:
            messagebox.showinfo("Clothing Details", "No clothing details available.")
    else:
        messagebox.showinfo("Card Not Found", f"Card with UID {id} not found in database; access denied")

def main():
    root = tk.Tk()
    root.title("Smart Wardrobe with RFID")

    # Main Frame
    main_frame = tk.Frame(root, bg="#e0e0e0", padx=20, pady=20)
    main_frame.pack(padx=15, pady=15)

    title_label = tk.Label(main_frame, text="Smart Wardrobe with RFID", font=("Helvetica", 20, "bold"), bg="#e0e0e0")
    title_label.pack(pady=20)

    # Input fields frame
    input_frame = tk.Frame(main_frame, bg="#e0e0e0")
    input_frame.pack(pady=20)

    # Outfit Entry
    outfit_label = tk.Label(input_frame, text="Enter Outfit:", font=("Helvetica", 14), bg="#e0e0e0")
    outfit_label.grid(row=0, column=0, padx=10, pady=10)
    outfit_entry = tk.Entry(input_frame, font=("Helvetica", 12))
    outfit_entry.grid(row=0, column=1, padx=10, pady=10)

    # Clothing Type Dropdown
    clothing_type_label = tk.Label(input_frame, text="Choose Clothing Type:", font=("Helvetica", 14), bg="#e0e0e0")
    clothing_type_label.grid(row=1, column=0, padx=10, pady=10)
    clothing_type_var = tk.StringVar(root)
    clothing_type_var.set("lightwear")
    clothing_type_dropdown = tk.OptionMenu(input_frame, clothing_type_var, "lightwear", "layered")
    clothing_type_dropdown.grid(row=1, column=1, padx=10, pady=10)

    # Buttons
    register_button = tk.Button(main_frame, text="Register Card", command=register_card, font=("Helvetica", 14), bg="#4CAF50", fg="white", width=15)
    register_button.pack(pady=10)

    check_button = tk.Button(main_frame, text="Check Details", command=check_details, font=("Helvetica", 14), bg="#2196F3", fg="white", width=15)
    check_button.pack(pady=10)

    fetch_button = tk.Button(main_frame, text="Fetch Weather", command=fetch_weather, font=("Helvetica", 14), bg="#FFC107", width=15)
    fetch_button.pack(pady=10)

    recommend_button = tk.Button(main_frame, text="Recommend Outfit", command=recommend_outfit, font=("Helvetica", 14), bg="#9C27B0", fg="white", width=15)
    recommend_button.pack(pady=10)

    weather_label = tk.Label(main_frame, text="Weather: ", font=("Helvetica", 12), bg="#e0e0e0")
    weather_label.pack(pady=10)

    outfit_label = tk.Label(main_frame, text="Recommended Outfit: ", font=("Helvetica", 12), bg="#e0e0e0")
    outfit_label.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()