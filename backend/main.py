from fastapi import FastAPI, HTTPException, Query,Depends,Form,status
from backend import database, mint, paypal, utils
from backend import transaction as transaction_module
from typing import Optional
from pydantic import BaseModel,Field,EmailStr
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv
import os  
import requests
import logging

# Initialize logging
from backend.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("main")

from backend.utils import get_current_user,create_auth_token,verify_token,User,Token,TokenData,authenticate_user,SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES
app = FastAPI()
whiplano_id = '0000-0000-0000'
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
class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    
class NFTData(BaseModel):
    collection_name: str = Field(..., description="Name of the collection") 
    collection_description: str = Field(..., description="Description of the collection")
    collection_symbol: str = Field(..., description="Symbol of the collection")
    number: int = Field(..., description="Number of TRSs")
    uri: str = Field(..., description="URI of the NFT")
    creator_id: str = Field(..., description="ID of the creator")

class CreatePaymentData(BaseModel):
    amount : int =  Field(..., description="Amount")
    cancel_url : str = Field(..., description="URL for the user to be redirected to when the payment is cancelled. ")
    description : str = Field(...,description="Description of the payment for Paypal.")

class BlockChainTransactionData(BaseModel):
    transaction_number : str = Field(..., description = "Transaction number of the paypal transaction to be stored on the chain. ")

class MintTrsData(BaseModel):
    collection_name : str = Field(..., description = "Name of the collection")
    collection_description : str = Field(..., description = "Description of the collection")
    collection_symbol : str = Field(..., description = "Symbol of the collection")
    number : int = Field(..., description = "Number of TRSs")
    uri : str = Field(..., description="URI of the NFT")
    creator_id : str = Field(..., description = "ID of the creator")
    
class TradeCreateData(BaseModel):
    collection_name : str = Field(..., description = "Name of the collection to be bought")
    seller_id : list = Field(..., description = "ID of the seller")
    number : int = Field(..., description = "Number of TRSs to be traded") 
    cost : float = Field(..., description = "Cost of one TRS")
    


@app.get("/")
async def root():
    logger.info("App is running.")
    return {"message": "App is running."}

@app.post("/login", response_model=Token)
async def login(email: str = Form(...), password: str = Form(...)):
    
    user = await authenticate_user( email, password)
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
    logger.info(f"User {user.email} succesfully authenticated")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/signup', response_model=Token)
async def signup(user: SignupRequest):
    # Check if the user already exists
    existing_user = await database_client.get_user_by_email(user.email)
    if existing_user:
        logger.info("Attempted sign up for existing user. ")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = utils.hash_password(user.password)
    
    user_id = await database_client.add_user(user.username,user.email,hashed_password)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_auth_token(data={"sub": user.email}, expires_delta=access_token_expires)
    logger.info(f"User created with email {user.email}")
    # Return token
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/login/google")
async def login_with_google():
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
    logging.info("Redirecting user to Google OAuth2")
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/auth?client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=openid email")


@app.get("/callback/google")
async def google_callback(request: Request):
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
    response =  requests.post(token_url, data=payload)
    idinfo = id_token.verify_oauth2_token(response.json()["id_token"], google_requests.Request(), GOOGLE_CLIENT_ID)
    
    if not idinfo['email_verified']:
        return {"error":"Email not verified."}
    try:
        user = await database_client.get_user_by_email(idinfo['email'])
    except Exception as e:
        
        #signup logic
        return
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_auth_token(
        data={"sub": idinfo['email']}, expires_delta=access_token_expires
    )
    logging.info(f"Authenticated user {idinfo['email']} using Google OAuth2")
    return {"access_token": access_token, "token_type": "bearer"}

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

@app.post("/mint_trs", dependencies=[Depends(get_current_user)])
async def mint_trs(data : NFTData):
    """
    This function is responsible for minting a new TRS using the provided data.

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
        - message (str): "TRS minted successfully."

    Raises:
    HTTPException: If an error occurs during the minting process.
    """
    try:
        
        data = dict(data)
        await mint.mint_nft(data)
        return {"message": "TRS minted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/paypal/create_payment", dependencies=[Depends(get_current_user)])
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
        data = dict(data)
        
        data['return_url'] = "http://localhost:8000/paypal/execute_payment"
        resp = await paypal.create_payment(data)
        print(resp)
        print(resp['links'][1])
        return {"message": "Payment created successful.",
                'approval_url': resp['links'][1]['href']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@app.post('/transaction/create', dependencies=[Depends(get_current_user)])
async def transaction(data: BlockChainTransactionData):
    try:
        resp = transaction_module.transaction(data.transaction_number)
        return resp
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store transaction: {str(e)}")


async def trade_continuation():
    
    return
@app.post('/trade/create',dependencies=[Depends(get_current_user)])
async def trade_create(data : TradeCreateData,buyer : User = Depends(get_current_user)):
    wallets = {}
    for i in data.seller_id:
        wallets[i] = await database_client.get_wallet_by_collection(i,data.collection_name)
    trs_count = 0
    for i in wallets:
        trs_count += len(wallets[i])
    if trs_count < data.number:
        logger.info("Not enough TRS being offered by the sellers. ")
        raise HTTPException(status_code=400, detail="Insufficient funds")
    else:
        description = f"Buy order for {data.number} TRS of {data.collection_name}. Price per TRS = {data.number}, Total Amount = {(data.number*data.cost)}"
        data = {
            'collection_name':(data.number)*(data.cost),
            'cancel_url' : "https://example.com",
            "description": description            
        }
        try:
            resp = await paypal.create_payment(data)
            await database_client.add_paypal_transaction(resp['id'],buyer.id,whiplano_id)
            logger.info(f"Payment created succesfully with id {resp['id']}")
            
            return {"message": "Payment created successful.",
                    'approval_url': resp['links'][1]['href']}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        return


@app.get('/paypal/execute_payment')
async def execute_payment(
    paymentId: Optional[str] = Query(None), 
    PayerID: Optional[str] = Query(None),
):
    try:
        resp = await paypal.execute_payment(paymentId,PayerID)
        logger.info(f"Executed transaction with id {paymentId}")
        await database_client.modify_paypal_transaction(paymentId,'executed')
        
    except Exception as error:
        logger.error(f"Error executing transaction {paymentId} {error}")
        raise HTTPException(status_code=500, detail=str(error)) 
