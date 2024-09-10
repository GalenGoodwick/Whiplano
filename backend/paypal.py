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
load_dotenv()

PAYPAL_API_URL = 'https://api-m.sandbox.paypal.com/v1/payments/payment'
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

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



async def handle_payout(request):
    paypal_payouts = PayPalPayouts()
    access = get_access_token()
    response = await paypal_payouts.send_payout(
        access,
        sender_batch_id='batch_id_1234',
        recipient_email='sb-pi4yd32634479@personal.example.com',
        amount='100.00'
    )
    print(response)
async def handle_execute(request):
    payment_id = request.query.get('paymentId')
    payer_id = request.query.get('PayerID')

    if payment_id and payer_id:
        paypal = PayPal()
        payment_response = await paypal.execute_payment(payment_id, payer_id)
        return web.json_response(payment_response)
    else:
        return web.Response(text="Payment ID or Payer ID missing", status=400)

async def handle_create(request):
    paypal = PayPal()
    payment_response = await paypal.create_payment()
    payment_id = payment_response.get('id')
    approval_url = next((link['href'] for link in payment_response['links'] if link['rel'] == 'approval_url'), None)
    return web.json_response({'payment_id': payment_id, 'approval_url': approval_url})

async def handle_get_kyc(request):
    user_id = request.query.get('user_id')
    
    if user_id:
        paypal_kyc = PayPal()
        kyc_response = await paypal_kyc.get_kyc_information(user_id)
        return web.json_response(kyc_response)
    else:
        return web.Response(text="User ID missing", status=400)


def payment_webapp():
  app = web.Application()
  app.router.add_get('/create', handle_create)
  app.router.add_get('/execute', handle_execute)
  #app.router.add_get('/get_kyc', handle_get_kyc)  
  app.router.add_get('/payout', handle_payout)
  return app
'''
if __name__ == "__main__":
  app = payment_webapp()  
  
  web.run_app(app, port=8080)
  '''
  
async def create_payment(data):
    paypal = PayPal()
    resp =  await paypal.create_payment(data['amount'], data['return_url'], data['cancel_url'], data['description'])
    print(resp)
    return resp

async def execute_payment(payment_id, payer_id):
    paypal  = PayPal()
    resp = await paypal.execute_payment(payment_id, payer_id)
    print(resp)
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
    print("Payout sent. ")
    return response

