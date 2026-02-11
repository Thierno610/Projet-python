import requests
import json

BASE_URL = "http://localhost:5000"

def test_email():
    print("\n--- Test Envoi Email ---")
    dest = "dtmaissatou224@gmail.com" # Test sending to self
    try:
        response = requests.post(
            f"{BASE_URL}/api/test-email", 
            json={"email": dest}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_email()
