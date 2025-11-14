import os
import requests

# Replace with your actual keys or use Streamlit secrets
API_KEY = os.getenv("APCA_API_KEY_ID", "your_key_here")
API_SECRET = os.getenv("APCA_API_SECRET_KEY", "your_secret_here")
BASE_URL = "https://paper-api.alpaca.markets"

def test_account():
    url = f"{BASE_URL}/v2/account"
    headers = {
        "APCA-API-KEY-ID": API_KEY,
        "APCA-API-SECRET-KEY": API_SECRET
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        print("✅ Alpaca keys are valid.")
        print("Account info:", r.json())
    else:
        print("❌ Alpaca key test failed.")
        print("Status:", r.status_code)
        print("Response:", r.text)

if __name__ == "__main__":
    test_account()