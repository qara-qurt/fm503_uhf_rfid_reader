import requests
import time
import serial
from reader import Reader
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

token = None


def get_token():
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
            token = None
    except requests.RequestException as e:
        print(f"[!] Network error while retrieving token: {e}")
        token = None


def send_to_api(tag_uid):
    global token
    if not token:
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
            get_token()
            send_to_api(tag_uid)
        else:
            print(f"[!] API error: {response.status_code} - {response.text}")

    except requests.RequestException as e:
        print(f"[!] Network error: {e}")


def start_reader(reader):
    print("Initializing RFID reader...")
    reader.clear_serial_buffers()
    print("Serial buffers cleared.")

    print("Setting TX power level to 25dB...")
    success = reader.set_tx_power_level(25)
    if not success:
        print("[!] Failed to set TX power.")
    time.sleep(0.5)


def read_loop(reader):
    print("Starting RFID reader loop...")
    detected_tags = set()

    while True:
        try:
            epc_data = reader.multi_tag_EPC_read()
            if not epc_data:
                print("[INFO] No tags detected.")
                continue

            current_tags = set()

            for entry in epc_data:
                binary_epc = entry[0]  # list of ints
                tag_uid = hex(int(reader.convert_to_raw(binary_epc), 2)).upper().replace('X', 'x')

                current_tags.add(tag_uid)

                if tag_uid not in detected_tags:
                    print(f"[+] New tag detected: {tag_uid}")
                    send_to_api(tag_uid)

            detected_tags = current_tags

        except Exception as e:
            print(f"[ERROR] Exception during reading: {e}")


if __name__ == "__main__":
    SERIAL_PORT = "/dev/ttyUSB0"
    BAUD_RATE = 38400

    try:
        get_token()

        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        reader = Reader(ser)

        start_reader(reader)
        read_loop(reader)

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nExiting program...")
