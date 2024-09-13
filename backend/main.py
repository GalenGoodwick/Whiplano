from fastapi import FastAPI, HTTPException, Query,Depends,Form,status
from backend import database, mint, paypal, transaction, utils
from typing import Optional
from pydantic import BaseModel,Field
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv
import os  

from backend.utils import get_current_user,create_auth_token,verify_token,User,Token,TokenData,authenticate_user,SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES
app = FastAPI()

database_client = database.DatabaseManager(
    host='localhost',
    user='root',
    password='new_password',
    database ='whiplano'
)

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:8000/callback/google"


#BASE MODELS

class NFTData(BaseModel):
    collection_name: str = Field(..., description="Name of the collection") 
    collection_description: str = Field(..., description="Description of the collection")
    collection_symbol: str = Field(..., description="Symbol of the collection")
    number: int = Field(..., description="Number of TRSs")
    uri: str = Field(..., description="URI of the NFT")
    creator_id: str = Field(..., description="ID of the creator")

class CreatePaymentData(BaseModel):
    amount : str =  Field(..., description="Amount")
    cancel_url : str = Field(..., description="URL for the user to be redirected to when the payment is cancelled. ")
    description : str = Field(...,description="Description of the payment for Paypal.")

class BlockChainTransactionData(BaseModel):
    transaction_number : str = Field(..., description = "Transaction number of the paypal transaction to be stored on the chain. ")



@app.get("/")
async def root():
    return {"message": "App is running."}

@app.post("/login", response_model=Token)
async def login(email: str = Form(...), password: str = Form(...)):
    user = authenticate_user( email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_auth_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/login/google")
def login_with_google():
    """
    Redirects the user to the Google OAuth2 authorization page for login.

    This function constructs a URL to the Google OAuth2 authorization page with the necessary parameters
    to initiate the login process. The function then returns a RedirectResponse object to redirect the user
    to the constructed URL.

    Parameters:
    None

    Returns:
    RedirectResponse: A FastAPI response object that redirects the user to the Google OAuth2 authorization page.
    """
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=openid email")


@app.get("/callback/google")
def google_callback(request: Request):
    """
    This function handles the callback from Google OAuth2 authorization.
    It exchanges the authorization code for an access token and retrieves the user's email.

    Parameters:
    request (Request): The FastAPI Request object containing the query parameters.
        - code: The authorization code obtained from Google OAuth2.

    Returns:
    dict: A dictionary containing the user's email.
        - email: The email of the authenticated user.
    """
    code = request.query_params["code"]
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    response = google_requests.post(token_url, data=payload)
    idinfo = id_token.verify_oauth2_token(response.json()["id_token"], google_requests.Request(), GOOGLE_CLIENT_ID)

    return {"email": idinfo['email']}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve the current user's information.

    This function retrieves the current user's information from the FastAPI endpoint '/users/me'.
    It uses the 'get_current_user' function as a dependency to authenticate and authorize the user.
    If the user is authenticated and authorized, the function returns the user's information.

    Parameters:
    current_user (User): The current user's information. This parameter is obtained from the 'get_current_user' function.

    Returns:
    User: The current user's information.
    """
    return current_user

@app.post("/mint")
async def mint_nft(data : NFTData):
    """
    This function is responsible for minting a new NFT using the provided data.

    Parameters:
    data (NFTData): A Pydantic model containing the necessary data for minting an NFT.
        - collection_name (str): The name of the collection.
        - collection_description (str): The description of the collection.
        - collection_symbol (str): The symbol of the collection.
        - number (int): The number of TRSs.
        - uri (str): The URI of the NFT.
        - creator_id (str): The ID of the creator.

    Returns:
    dict: A dictionary containing a success message.
        - message (str): "NFT minted successfully."

    Raises:
    HTTPException: If an error occurs during the minting process.
    """
    try:
        mint.mint_nft(data)
        return {"message": "NFT minted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/paypal/create_payment")
async def paypal_payment(data : CreatePaymentData):
    """
    This function is responsible for creating a payment on PayPal.

    Parameters:
    data (CreatePaymentData): A Pydantic model containing the necessary data for creating a payment.
        - amount (str): The amount of the payment.
        - cancel_url (str): The URL for the user to be redirected to when the payment is cancelled.
        - description (str): Description of the payment for PayPal.
        - return_url (str): The URL for the user to be redirected to after the payment is completed.

    Returns:
    dict: A dictionary containing a success message.
        - message (str): "Payment created successful."

    Raises:
    HTTPException: If an error occurs during the payment creation process.
    """
    try:
        data['return_url'] = "http://localhost:8000/paypal/execute_payment"
        e = await paypal.create_payment(data)
        print(e)
        return {"message": "Payment created successful."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/paypal/execute_payment')
async def execute_payment(
    paymentId: Optional[str] = Query(None), 
    PayerID: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):
    try:
        
        resp = await paypal.execute_payment(paymentId,PayerID)
        return resp
    except Exception as e:
       raise HTTPException(status_code=500, detail=str(e)) 

@app.get('/paypal/payout')
async def payout(data: dict):
    """
    This function is responsible for processing a payout on PayPal.

    Parameters:
    data (dict): A dictionary containing the necessary data for processing a payout.
        The dictionary should contain the following keys:
        - recipient_type: The type of recipient (e.g., email, phone, bank).
        - amount: The amount of the payout.
        - currency: The currency of the payout.
        - note: An optional note for the payout.
        - sender_item_id: An optional sender item ID for the payout.
        - receiver: The recipient's details (e.g., email, phone, bank details).

    Returns:
    dict: A dictionary containing a success message.
        - message (str): "Payout successful."

    Raises:
    HTTPException: If an error occurs during the payout process.
    """
    try:
        response = await paypal.payout(data)
        return {"message": "Payout successful.","response": response}
    except Exception as e:    
        raise HTTPException(status_code=500, detail=str(e))
   
    
@app.post('/transaction/create')
async def transaction(data: BlockChainTransactionData):
    
    return 

