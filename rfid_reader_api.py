import requests
import time
import serial
from reader import Reader
from tools import interpret_lower_48_TID  # Import function

# API settings
API_URL = "http://your-api.com/rfid"  # Replace with actual API endpoint
HEADERS = {"Content-Type": "application/json"}

def send_to_api(tag_uid, manufacturer, model, xtid, security, file_open, serial_number):
    """Send RFID data to API"""
    payload = {
        "rfid_tag": tag_uid,
        "manufacturer": manufacturer,
        "model": model,
        "xtid": xtid,
        "security": security,
        "file_open": file_open,
        "serial_number": serial_number
    }
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            print(f"[+] Data sent successfully: {tag_uid}")
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

    # Set TX power level (default GUI: 25dB)
    print("Setting TX power level...")
    reader.set_tx_power_level(25)  # Activate reader

    # Start scanning (same as GUI)
    print("Starting continuous reading mode...")
    reader.ser.write(b'\nR2,0,6\r')  # Command to start reading
    time.sleep(1)  # Wait before reading

def read_loop(reader):
    """Continuously read RFID tags and send data to API"""
    print("Starting RFID reader loop...")

    while True:
        print("Requesting tag data...")
        reader.ser.write(b'\nR2,0,6\r')  # Send read command
        time.sleep(0.5)

        tag_uid = reader.read()  # Read RFID tag UID
        if tag_uid:
            print(f"Tag detected: {tag_uid}")

            # Read TID bank
            tid_data = reader.read_TID_bank(raw=True)
            if tid_data:
                decoded_tid = reader.hex_str_to_bin_list(tid_data)
                interpreted_tid = interpret_lower_48_TID(decoded_tid)

                manufacturer = interpreted_tid[4] or "Unknown"
                model = interpreted_tid[5] or "Unknown"
                xtid = interpreted_tid[1]
                security = interpreted_tid[2]
                file_open = interpreted_tid[3]
                serial_number = reader.extract_38_Bit_serial_number(decoded_tid)

                # Send data to API
                send_to_api(tag_uid, manufacturer, model, xtid, security, file_open, serial_number)
        else:
            print("No tag detected.")
        time.sleep(1)

if __name__ == "__main__":
    SERIAL_PORT = "/dev/ttyUSB0"  # Change if needed
    BAUD_RATE = 38400  # Serial port speed

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        reader = Reader(ser)

        start_reader(reader)  # Initialize reader (same as GUI)

        read_loop(reader)  # Start reading loop

    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except KeyboardInterrupt:
        print("\nExiting program...")
