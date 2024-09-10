import requests
from requests.auth import HTTPBasicAuth
import os 
from dotenv  import load_dotenv
load_dotenv()
# PayPal client credentials from PayPal Developer Dashboard
client_id = os.getenv("PAYPAL_CLIENT_ID")
client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
# PayPal API endpoint for access token (Sandbox or Live)
 
# Request headers and payload
headers = {
    "Accept": "application/json",
    "Accept-Language": "en_US"
}
payload = {
    "grant_type": "client_credentials"
}

# Send POST request to get the access token
response = requests.post(url, headers=headers, data=payload, auth=HTTPBasicAuth(client_id, client_secret))

# Check if the request was successful
if response.status_code == 200:
    access_token = response.json().get("access_token")
    print("Access Token:", access_token)
else:
    print(f"Failed to get access token: {response.status_code}, {response.text}")


