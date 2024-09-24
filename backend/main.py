from fastapi import FastAPI, HTTPException, Query,Depends,Form,status, Request
from backend import database, mint, paypal, utils
from backend import transaction as transaction_module
from typing import Optional
from pydantic import BaseModel,Field,EmailStr
from datetime import datetime, timedelta

from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv
import os  
import requests
import logging
import uuid

ROYALTY  = 2.5
FEES = 2.5
# Initialize logging
from backend.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("main")

from backend.utils import get_current_user,get_current_verified_user,get_current_admin,create_auth_token,verify_token,User,Token,TokenData,authenticate_user,SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES,SERVER_URL
app = FastAPI()
whiplano_id = '0000-0000-0000'

database_client = database.DatabaseManager(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    password=os.getenv("DATABASE_PASSWORD"),
    database =os.getenv("DATABASE_NAME")
)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = SERVER_URL + "/callback/google"


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
   
class TradeCreateData(BaseModel):
    collection_name : str = Field(..., description = "Name of the collection to be bought")
    seller_id : list = Field(..., description = "ID of the seller")
    number : int = Field(..., description = "Number of TRSs to be traded") 
    cost : float = Field(..., description = "Cost of one TRS")
    


@app.get("/")
async def root():
    """
    This function is the root endpoint of the application. It checks if the application is running.

    Parameters:
    None

    Returns:
    dict: A dictionary containing a success message.
        - message (str): "App is running."
    """
    logger.info("App is running.")
    return {"message": "App is running."}

@app.post("/login", response_model=Token)
async def login(email: str = Form(...), password: str = Form(...)):
    """
    Authenticates a user using their email and password.

    Parameters:
    email (str): The email of the user.
    password (str): The password of the user.

    Returns:
    dict: A dictionary containing the access token and token type.
        - access_token (str): The access token for the user.
        - token_type (str): The type of the access token (e.g., "bearer").

    Raises:
    HTTPException: If the email or password is incorrect.
    """
    user = await authenticate_user(email, password)
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
    """
    This function handles the signup process for a new user. It checks if the user already exists,
    hashes the password, adds the user to the database, and creates an access token.

    Parameters:
    user (SignupRequest): A Pydantic model containing the necessary data for signup.
        - username (str): The username of the user.
        - email (str): The email of the user.
        - password (str): The password of the user.

    Returns:
    dict: A dictionary containing the access token and token type.
        - access_token (str): The access token for the user.
        - token_type (str): The type of the access token (e.g., "bearer").

    Raises:
    HTTPException: If an error occurs during the signup process.
    """
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
    logger.info("Hashed password")
    user_id = await database_client.add_user(user.username,user.email,hashed_password)
    logger.info("Added user to the database. ")
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_auth_token(data={"sub": user.email}, expires_delta=access_token_expires)
    logger.info(f"User created with email {user.email}")
    # Return token
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/verify_user",dependencies = [Depends(get_current_user)])
async def verify_user():
    return

    

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

@app.post("/admin/add")
async def add_admin(email: str, dependencies = [Depends(get_current_admin)]) -> str:
    """
    This function adds a new admin user to the system.

    Parameters:
    email (str): The email of the admin user to be added.
    dependencies (list): A list of dependencies required for the function to execute.
        In this case, it depends on the current user being authenticated.

    Returns:
    str: A success message indicating that the admin user has been added to the system.
    """
    return await database_client.add_admin(email)

@app.post("/admin/creation_requests",dependencies = [Depends(get_current_admin)])
async def admin_creation_requests():
    
    return

@app.get("/callback/google", response_model = Token)
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
        
        return {"message":"User not registered, signing up by google hasn't been added yet."}
    
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

@app.post("/mint_trs", dependencies=[Depends(get_current_verified_user)])
async def mint_trs(data : MintTrsData,user:User = Depends(get_current_user)):
    """
    This function is responsible for minting a new TRS using the provided data.

    Parameters:
    data (MintTrsData): A Pydantic model containing the necessary data for minting an NFT.
        - collection_name (str): The name of the collection.
        - collection_description (str): The description of the collection.
        - collection_symbol (str): The symbol of the collection.
        - number (int): The number of TRSs.
        - uri (str): The URI of the NFT.
        
    Returns:
    dict: A dictionary containing a success message.
        - message (str): "TRS minted successfully."

    Raises:
    HTTPException: If an error occurs during the minting process.
    """
    try:
        
        data = dict(data)
        data['creator_id'] = user
    
        await mint.mint_nft(data)
        return {"message": "TRS minted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post('/trade/create',dependencies=[Depends(get_current_verified_user)])
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
        data_transac = {
            'collection_name':(data.number)*(data.cost),
            'cancel_url' : "https://example.com",
            "description": description,
            "return_url": SERVER_URL + "/trade/execute_payment"   
        }
        try:
            resp = await paypal.create_payment(data_transac)
            await database_client.add_paypal_transaction(resp['id'],buyer.id,whiplano_id)
            logger.info(f"Payment created succesfully with id {resp['id']}")
            buyer_transaction_number = resp['id']
            required_transactions = {}
            required_number = data.number
            for seller_id in data.seller_id:
                if len(wallets[seller_id]) >= required_number:
                    required_transactions[seller_id] = wallets[seller_id][0:required_number-1]
                else:
                    required_transactions[seller_id] = wallets[seller_id]
                    required_number -= len(wallets[seller_id])
            
            for seller_id in required_transactions:
                await database_client.add_transaction(buyer_transaction_number,data.collection_name,buyer.id,seller_id,data.cost,len(required_transactions['seller_id']))
                    
                    

            return {"message": "Payment created successful.",
                    'approval_url': resp['links'][1]['href']}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        
        return


@app.get('/trade/execute_payment')
async def execute_payment(
    paymentId: Optional[str] = Query(None), 
    PayerID: Optional[str] = Query(None),
):
    """
    This function executes a PayPal payment with the given payment ID and Payer ID.
    It retrieves the payment details, modifies the payment status in the database,
    approves initiated transactions, retrieves approved transactions, and processes
    the transactions by executing payouts, updating the transaction records, and
    transferring assets between users.

    Parameters:
    paymentId (str, optional): The ID of the PayPal payment.
    PayerID (str, optional): The ID of the PayPal Payer.

    Returns:
    dict: A dictionary containing a success message if the payment is executed successfully.
        - message (str): "Completed Trade with buyer transaction number {paymentId}"

    Raises:
    HTTPException: If an error occurs during the payment execution.
    """
    try:
        resp = await paypal.execute_payment(paymentId,PayerID)
        logger.info(f"Executed payment with id {paymentId}")
        await database_client.modify_paypal_transaction(paymentId,'executed')

        initiate = await database_client.approve_initiated_transactions(paymentId)
        if initiate:
            logger.info(f"Approved initiated transactions with buyer payment id {paymentId}")
        else:
            raise HTTPException(status_code=500,detail="Failed to approve transaction. ")

        transactions = await database_client.get_approved_transactions(paymentId)

        batch_id = str(uuid.uuid4)
        for transaction in transactions:
            seller_email = await database_client.get_user(transaction['seller_id'])
            seller_email = seller_email['email']
            buyer_email = await database_client.get_user(transaction['buyer_id'])
            buyer_email = buyer_email['email']
            creator_email = await database_client.get_creator(transaction['collection_id'])
            creator_email = await database_client.get_user(creator_email)
            creator_email = creator_email['email']
            payout_info = {
                    "batch_id":batch_id,
                    "recipient_email":seller_email,
                    "amount":(transaction['cost']*transaction['number']) * ( 100 - ROYALTY + FEES) / 100,
                    "currency":"USD",
                    "note": f"Payment to {seller_email} for TRS of collection {transaction['collection_name']}. "
                }
            await paypal.payout(payout_info)
            royalty_payout_info = payout_info = {
                    "batch_id":batch_id,
                    "recipient_email":seller_email,
                    "amount":(transaction['cost']*transaction['number']) * (ROYALTY) / 100,
                    "currency":"USD",
                    "note": f"Royalty for {creator_email} for trade of TRS of collection {transaction['collection_name']}. "
                }
            data = {
                "transaction_number":transaction['transaction_number'],
                "buyer_id": transaction['buyer_id'],
                "seller_id": transaction['seller_id'],
                "seller_email": seller_email,
                "buyer_email":buyer_email,
                "trs_count": transaction['number']
            }
            await transaction_module.transaction(data)

            seller_wallet  = await database_client.get_wallet_by_collection(transaction['seller_id'],transaction['collection_name'])

            req_trs = seller_wallet[0:transaction['number']-1]

            for trs in req_trs: 
                database_client.transfer_asset(transaction['buyer_id'],trs['trs_id'])


        finalize = await database_client.finish_approved_transactions(paymentId)
        logger.info(f"Completed Trade with buyer transaction number {paymentId}")
        return {"message": f"Completed Trade with buyer transaction number {paymentId}"}



    except Exception as error:
        logger.error(f"Error executing transaction {paymentId} {error}")
        raise HTTPException(status_code=500, detail=str(error))


@app.get('/wallet/get', dependencies=[Depends(get_current_user)], description="Returns a formatted wallet, as a JSON with created TRS, TRS on marketplace, and TRS with artisan rights.")
async def trade_create(user: User = Depends(get_current_user)):
    """
    This function retrieves and formats the wallet of the current user. The wallet includes
    the created TRS, TRS on the marketplace, and TRS with artisan rights.

    Parameters:
    user (User): The current user. This parameter is obtained from the 'get_current_user' function.

    Returns:
    dict: A dictionary representing the formatted wallet. The dictionary contains the following keys:
        - created_trs: A list of TRS created by the user.
        - trs_on_marketplace: A list of TRS on the marketplace.
        - trs_with_artisan_rights: A list of TRS with artisan rights.
    """
    
    wallet = await database_client.get_wallet_formatted(user.id)
    return wallet



@app.get('/marketplace')
async def marketplace():
    """
    Retrieves all TRS currently listed on the marketplace.

    Returns:
    list: A list of dictionaries, where each dictionary represents a TRS on the marketplace.
          Each dictionary contains the following keys:
          - trs_id: The unique identifier of the TRS.
          - collection_name: The name of the collection to which the TRS belongs.
          - owner_id: The unique identifier of the owner of the TRS.
          - price: The price of the TRS on the marketplace.

    """
    trs_on_marketplace = await database_client.get_marketplace_all()
    return trs_on_marketplace

@app.get('/marketplace/collection')
async def marketplace_collection(collection_name: str):
    """
    Retrieves all TRS of a specific collection currently listed on the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    """
    trs_on_marketplace = await database_client.get_marketplace_collection(collection_name)
    return trs_on_marketplace

@app.post('/marketplace/place',dependencies=[Depends(get_current_verified_user)])
async def marketplace_add(collection_name: str, number: int, user: User = Depends(get_current_user)) -> dict:
    """
    This function adds TRS of a specific collection to the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    number (int): The number of TRS to be added to the marketplace.
    user (User): The user making the request. This parameter is obtained from the 'get_current_user' function.

    Returns:
    dict: A dictionary containing a success message if the TRS are added to the marketplace successfully.
        - message (str): "TRS added to marketplace successfully."
    """
    wallet = await database_client.get_wallet_formatted(user.id)
    req_wallet = []
    for i in wallet: 
        if i['collection_name'] == collection_name and i['marketplace'] == 0 and i['artisan'] == 0:
            req_wallet.append(i)

    if len(req_wallet) >= number:
        for i in req_wallet:
            price = 1000
            await database_client.add_trs_to_marketplace(i['trs_id'],collection_name, user.id,price)

        return {"message": "TRS added to marketplace successfully."}
    else:
        return {"message": F"Insufficient TRS of {collection_name} in wallet."}

    return





