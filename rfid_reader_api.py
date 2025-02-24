import requests
import time
import serial
from reader import Reader
from tools import interpret_lower_48_TID
import os
from dotenv import load_dotenv

load_dotenv()

# API settings
BASE_URL = "http://192.168.0.151:8080/api"
LOGIN_URL = f"{BASE_URL}/users/login"
RFID_API_URL = f"{BASE_URL}/rfid"

CREDENTIALS = {
    "username": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD")
}

HEADERS = {
    "Content-Type": "application/json",
}

token = None  # Global variable for storing the token


def get_token():
    """Request a new token and store it globally."""
    global token
    try:
        print("\n[*] Requesting new JWT token...")
        response = requests.post(LOGIN_URL, json=CREDENTIALS, headers=HEADERS, timeout=5)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("token", "")
            HEADERS["Authorization"] = f"Bearer {token}"
            print("[+] Token received successfully.")
        else:
            print(f"[!] Failed to retrieve token: {response.status_code} - {response.text}")
            token = None  # Reset token on failure
    except requests.RequestException as e:
        print(f"[!] Network error while retrieving token: {e}")
        token = None


def send_to_api(tag_uid):
    """Send RFID tag data to the API. If the token is expired, refresh it."""
    global token
    if not token:
        print("[!] No token found, requesting a new one...")
        get_token()
        if not token:
            print("[ERROR] Cannot send data: authentication failed.")
            return

    payload = {
        "rfid_tag": tag_uid,
        "cashbox_id": os.getenv("CASHBOX_ID")
    }

    try:
        print(f"\n[*] Sending data to API: {payload}")
        response = requests.post(RFID_API_URL, json=payload, headers=HEADERS, timeout=5)

        if response.status_code == 200:
            print(f"[+] Data sent successfully: {tag_uid}")
        elif response.status_code == 401:
            print("[!] Unauthorized (401) - Refreshing token and retrying...")
            get_token()  # Request a new token
            send_to_api(tag_uid)  # Retry request
        else:
            print(f"[!] API error: {response.status_code} - {response.text}")

    except requests.RequestException as e:
        print(f"[!] Network error: {e}")


def start_reader(reader):
    """Initialize RFID reader."""
    print("Initializing RFID reader...")
    reader.clear_serial_buffers()
    print("Serial buffers cleared.")

    print("Setting TX power level to 25dB...")
    reader.set_tx_power_level(25)

    print("Starting continuous reading mode...")
    reader.ser.write(b'\nR2,0,6\r')
    time.sleep(1)


def read_loop(reader):
    """Main loop for reading RFID tags."""
    print("Starting RFID reader loop...")

    while True:
        print("\nRequesting tag data...")
        reader.ser.write(b'\nR2,0,6\r')
        time.sleep(0.2)

        tag_uid = reader.read()
        print(f"[DEBUG] Raw reader output: {tag_uid}")

        if tag_uid in ["R", "NO TAG", ""]:
            print("[WARNING] Ignoring invalid response from reader.")
            reader.clear_serial_buffers()
            time.sleep(0.5)
            continue  

        print(f"[+] Tag detected: {tag_uid}")

        # Send tag to API
        send_to_api(tag_uid)


if __name__ == "__main__":
    SERIAL_PORT = "/dev/ttyUSB0"
    BAUD_RATE = 38400

    try:
        get_token()  # Get token before starting

        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        reader = Reader(ser)

        start_reader(reader)
        read_loop(reader)

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nExiting program...")