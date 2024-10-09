import aiohttp
import asyncio
import json
from aiohttp import web
import urllib3
import os
import time
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import base64
from backend.database import DatabaseManager
import logging

# Initialize logging
from backend.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
load_dotenv()
logger = logging.getLogger("paypal")
PAYPAL_API_URL = 'https://api-m.sandbox.paypal.com/v1/payments/payment'
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
database_client =DatabaseManager(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    password=os.getenv("DATABASE_PASSWORD"),
    database =os.getenv("DATABASE_NAME")
)

def get_access_token():
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"

    headers = {
    "Accept": "application/json",
    "Accept-Language": "en_US"
    }
    payload = {
    "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=payload, auth=HTTPBasicAuth(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET))

    if response.status_code == 200:
        access_token = response.json().get('access_token')
        
        return access_token

class PayPal:
    def __init__(self):
        self.client_id = PAYPAL_CLIENT_ID
        self.client_secret = PAYPAL_CLIENT_SECRET

    async def create_payment(self,amount,return_url,cancel_url,description):
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            data = {
                "intent": "sale",
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": amount,
                        "currency": "USD"
                    },
                    "description": description
                }]
            }
            async with session.post(PAYPAL_API_URL, auth=auth, headers=headers, json=data) as response:
                response_data = await response.json()
            
                logger.info(f"Created payment with id {response_data['id']},description : {response_data['transactions'][0]['description']}")
                return response_data

    async def execute_payment(self, payment_id, payer_id):
        execute_url = f'{PAYPAL_API_URL}/{payment_id}/execute'
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            data = {
                "payer_id": payer_id
            }
            async with session.post(execute_url, auth=auth, headers=headers, json=data) as response:
                response_data = await response.json()
                #print(response_data)
                return response_data

class PayPalPayouts:
    def __init__(self):
        
        self.payout_url = 'https://api.sandbox.paypal.com/v1/payments/payouts'
    
    async def send_payout(self,access_token, sender_batch_id, recipient_email, amount, currency="USD", note="Payout"):
        payout_data = {
            "sender_batch_header": {
                "sender_batch_id": sender_batch_id,
                "email_subject": "You have a payout!",
                "email_message": "You have received a payout. Thanks for using our service!"
            },
            "items": [
                {
                    "recipient_type": "EMAIL",
                    "amount": {
                        "value": amount,
                        "currency": currency
                    },
                    "note": note,
                    "sender_item_id": sender_batch_id,
                    "receiver": recipient_email
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.payout_url, headers=headers, data=json.dumps(payout_data)) as response:
                response_data = await response.json()
                if response.status == 201:  # 201 Created
                    print("Payout successfully sent!")
                    return response_data
                else:
                    print(f"Failed to send payout: {response_data}")
                    return response_data

async def verify_transaction(transaction):
    return

async def create_payment(data):
    paypal = PayPal()
    resp =  await paypal.create_payment(data['amount'], data['return_url'], data['cancel_url'], data['description'])
    
    return resp

async def execute_payment(payment_id, payer_id):
    paypal  = PayPal()
    resp = await paypal.execute_payment(payment_id, payer_id)
    return resp 

async def payout(data):
    paypal = PayPalPayouts()
    
    access_token = get_access_token()
    response = await paypal.send_payout(
        access_token,
        sender_batch_id=data['batch_id'],
        recipient_email=data['recipient_email'],
        amount=data['amount'],
        currency=data['currency'],
        note=data['note'])
    
    logger.info(f"Payout sent to {data['recipient_email']}, amount = {data['amount']} ")
    return response

