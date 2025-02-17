import requests

# API endpoint (ensure it's correctly structured)
API_URL = "http://192.168.0.151:8080/api/rfid"  

# Headers (including authorization)
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJyb2xlcyI6WyJST0xFX0FETUlOIl0sInVzZXJuYW1lIjoiZGlhcyIsInN1YiI6ImRpYXMiLCJpYXQiOjE3Mzk4MDAxNTAsImV4cCI6MTczOTg0MzM1MH0.w6uz2psWIISUasMterihPu_m8pCTJWo-InRrA88mAtk"
}

# ? Fixed JSON field names to match Java DTO
payload = {
    "rfidTag": "RE28069152000600A4EA21076",  # ? Matches Java field name
    "manufacturer": "Impinj",
    "model": "Monza R6",
    "xtid": "True",
    "security": "False",
    "fileOpen": False,  # ? Changed from string to boolean
    "serialNumber": "123456789"
}

try:
    print(f"Sending POST request to {API_URL} ...")
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=5)

    # Print response details
    print(f"Status Code: {response.status_code}")
    print("Response Body:", response.text)

except requests.exceptions.RequestException as e:
    print(f"[!] API request failed: {e}")
