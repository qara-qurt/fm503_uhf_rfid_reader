import requests
import time
import serial
from reader import Reader
from tools import interpret_lower_48_TID

# API settings
API_URL = "http://192.168.0.151:8080/api/rfid"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJyb2xlcyI6WyJST0xFX0FETUlOIl0sInVzZXJuYW1lIjoiZGlhcyIsInN1YiI6ImRpYXMiLCJpYXQiOjE3Mzk4MDAxNTAsImV4cCI6MTczOTg0MzM1MH0.w6uz2psWIISUasMterihPu_m8pCTJWo-InRrA88mAtk"
}

def send_to_api(tag_uid, manufacturer, model, xtid, security, file_open, serial_number):
    """Send RFID data to API"""

    # Ensure file_open is a proper boolean (True/False)
    if isinstance(file_open, str):
        file_open = file_open.lower() in ["true", "1"]  # Converts "true" -> True, "false" -> False

    payload = {
        "rfid_tag": tag_uid,
        "manufacturer": manufacturer,
        "model": model,
        "xtid": xtid,
        "security": security,
        "file_open": file_open,  # ? Now always boolean
        "serial_number": serial_number
    }

    try:
        print(f"\n[*] Sending data to API: {payload}")
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)

        if response.status_code == 200:
            print(f"[+] Data sent successfully: {tag_uid}")
        elif response.status_code == 401:
            print("[!] API error: Unauthorized (401) - Check JWT Token")
        else:
            print(f"[!] API error: {response.status_code} - {response.text}")

    except requests.RequestException as e:
        print(f"[!] Network error: {e}")

def start_reader(reader):
    """Initialize RFID reader (same as GUI)"""
    print("Initializing RFID reader...")

    # Reset serial buffers
    reader.clear_serial_buffers()
    print("Serial buffers cleared.")

    # Set TX power level (default: 8dB)
    print("Setting TX power level to 8dB...")
    reader.set_tx_power_level(8)

    # Start scanning
    print("Starting continuous reading mode...")
    reader.ser.write(b'\nR2,0,6\r')  
    time.sleep(1)

def read_loop(reader):
    """Continuously read RFID tags and send data to API"""
    print("Starting RFID reader loop...")

    while True:
        print("\nRequesting tag data...")
        reader.ser.write(b'\nR2,0,6\r')  
        time.sleep(0.2)

        tag_uid = reader.read()
        print(f"[DEBUG] Raw reader output: {tag_uid}")

        # Ignore invalid responses
        if tag_uid in ["R", "NO TAG", ""]:
            print("[WARNING] Ignoring invalid response from reader.")
            reader.clear_serial_buffers()
            time.sleep(0.5)
            continue  

        print(f"[+] Tag detected: {tag_uid}")

        # Read TID bank
        tid_data = reader.read_TID_bank(raw=True)
        if tid_data:
            decoded_tid = reader.hex_str_to_bin_list(tid_data)
            print(f"[DEBUG] Decoded TID Data: {decoded_tid}")

            # Ensure the TID data has at least 7 elements
            while len(decoded_tid) < 7:
                decoded_tid.append("Unknown")

            interpreted_tid = interpret_lower_48_TID(decoded_tid)

            manufacturer = interpreted_tid[4] or "Unknown"
            model = interpreted_tid[5] or "Unknown"
            xtid = interpreted_tid[1]
            security = interpreted_tid[2]
            file_open = interpreted_tid[3]
            serial_number = reader.extract_38_Bit_serial_number(decoded_tid)

            # Send data to API
            send_to_api(tag_uid, manufacturer, model, xtid, security, file_open, serial_number)

        time.sleep(1)

if __name__ == "__main__":
    SERIAL_PORT = "/dev/ttyUSB0"
    BAUD_RATE = 38400

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        reader = Reader(ser)

        start_reader(reader)
        read_loop(reader)

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nExiting program...")
