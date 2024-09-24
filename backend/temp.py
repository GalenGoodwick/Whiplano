from fastapi import FastAPI, HTTPException
import dotenv
dotenv.load_dotenv()
app = FastAPI()
import os 

import httpx

async def get_paypal_access_token(client_id: str, client_secret: str) -> str:
    url = "https://api.paypal.com/v1/oauth2/token"
    print("HMm")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
        )
        response.raise_for_status()
        print(response.json())
        return response.json()["access_token"]

async def check_paypal_verification_status(access_token: str, user_email: str) -> dict:
    url = f"https://api.paypal.com/v1/customer/partners/{user_email}/verification-status"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


@app.get("/verify-paypal/{user_email}")
async def verify_paypal(user_email: str):
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")
    
    try:
        access_token = await get_paypal_access_token(client_id, client_secret)
        print("got access token ")
        verification_status = await check_paypal_verification_status(access_token, user_email)
        return verification_status
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
