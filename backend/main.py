from fastapi import FastAPI, HTTPException, Query,Depends,Form,status, Request, File, UploadFile
from backend import database, paypal, utils, storage,mint
from backend import transaction as transaction_module
from typing import Optional, List
from solders.pubkey import Pubkey
from pydantic import BaseModel,Field,EmailStr
from datetime import datetime, timedelta,date
import subprocess
from fastapi.responses import RedirectResponse, JSONResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv
import os  
import requests
import logging
import uuid

import shutil

from . import mint 

ROYALTY  = 2.5
FEES = 2.5
# Initialize logging
from backend.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("main")

from backend.utils import get_current_user,get_current_verified_user,get_current_admin,create_auth_token,verify_token,User,Token,TokenData,authenticate_user,SECRET_KEY,ALGORITHM,ACCESS_TOKEN_EXPIRE_MINUTES,SERVER_URL
app = FastAPI(
    title="Whiplano API",
    description="The API used for the IP platform Whiplano",
    version="0.1.1",
    contact={
        "name": "Dan",
        "email": "danielvincent1718@gmail.com",
    }
)
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
    number : int = Field(..., description = "Number of TRSs")
    uri : str = Field(..., description="URI of the NFT")
   
class TradeCreateData(BaseModel):
    collection_name : str = Field(..., description = "Name of the collection to be bought")
    seller_id : list = Field(..., description = "ID of the seller")
    number : int = Field(..., description = "Number of TRSs to be traded") 
    cost : float = Field(..., description = "Cost of one TRS")

class KYCData(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    address: str
    identity_type: str  # 'passport' or 'national_id' or 'driver's license'
    address_proof_type : str # 'utility bill' or anything else. 

class Metadata(BaseModel):
    title: str
    description: str
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
    current_directory = os.getcwd()
    return ("Current working directory:", current_directory)
    return {"message": "App is running."}

@app.post("/login", response_model=Token,tags=["Authentication"], summary="Logs in the User", description="Used to log in users via email/password")
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
    await database_client.login_user(email=user.email)
    logger.info(f"User {user.email} succesfully authenticated")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post('/signup', response_model=Token,tags=["Authentication"], summary="Signing up of new users", description="Used to add users via email/password")
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
    await database_client.login_user(user.email)
    # Return token
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/verify_user",dependencies = [Depends(get_current_user)],tags=["Authentication"], summary="Checks if user is verified.", description="Checks if user is verified.")
async def verify_user():
    return


@app.post("/submit-kyc/", dependencies = [Depends(get_current_user)],tags=["Authentication"],summary = "Takes in all the KYC data, then verifies the user. ")
async def submit_kyc(
    current_user: User = Depends(get_current_user),
    kyc_data: KYCData = Form(...),
    identity_card: UploadFile = File(...),
    address_proof: UploadFile = File(...),
    selfie_with_id: UploadFile = File(...)

):
    """
    Submits KYC data and verifies the user.

    This function takes in KYC data, identity card, address proof, and selfie with ID as form data.
    It uploads the files to a storage service, verifies the user, and returns the submitted KYC data.

    Parameters:
    current_user (User): The current user. This parameter is obtained from the 'get_current_user' function.
    kyc_data (KYCData): The KYC data submitted by the user. This parameter is obtained from the form data.
    identity_card (UploadFile): The identity card uploaded by the user. This parameter is obtained from the form data.
    address_proof (UploadFile): The address proof uploaded by the user. This parameter is obtained from the form data.
    selfie_with_id (UploadFile): The selfie with ID uploaded by the user. This parameter is obtained from the form data.

    Returns:
    dict: A dictionary containing the message, KYC data, and URLs of the uploaded files.
    """
    identity_url = await storage.upload_to_s3(identity_card, f"identity_cards/{current_user.id}")
    utility_url = await storage.upload_to_s3(address_proof, f"address_proof/{current_user.id}")
    selfie_url = await storage.upload_to_s3(selfie_with_id, f"selfies/{current_user.id}")
    logger.info(f"Uploaded Identity, Utility, and selfie to Filebase for user {current_user.email}.")
    await database_client.verify_user(current_user.email)
    logger.info(f"User {current_user.email} has been verified. ")
    return {
        "message": "KYC information submitted successfully",
        "first_name": kyc_data.first_name,
        "last_name": kyc_data.last_name,
        "date_of_birth": kyc_data.date_of_birth,
        "address": kyc_data.address,
        "identity_type": kyc_data.identity_type,
        "identity_card_url": identity_url,
        "address_proof_type": kyc_data.address_proof_type,
        "address_proof_url": utility_url,
        "selfie_with_id_url": selfie_url
    }
    
    
@app.get("/login/google",dependencies = [Depends(get_current_user)],tags=["Authentication"], summary="Returns a url for logging in via Google Auth", description="Returns a url for logging in via Google Auth")
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

@app.post("/admin/add",tags=["Admin"], summary="Adds an admin", description="Updates a user to be an Admin. ")
async def add_admin(email: str, dependencies = [Depends(get_current_user)]) -> str:
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

@app.get("/admin/creation_requests",dependencies = [Depends(get_current_user)],tags=["Admin"], summary="For getting the TRS creation requests", description="Returns the list of TRS creation requests currently pending for admins to approve. ")
async def admin_creation_requests():
    try:
        data = await database_client.get_trs_creation_requests('pending')
        
        return data
    except Exception as e: 
        return HTTPException(status_code= 500, content= e)
    

@app.post("/admin/approve",dependencies = [Depends(get_current_user)],tags = ["Admin"],summary = "For approving TRS creation requests, and minting the TRS")
async def admin_approve(id: int):
    exist = await database_client.check_collection_exists()
    if exist: 
        raise HTTPException(status_code= 409, content = "Collection already exists.")
    
    number = 1000
    trs_creation_data = await database_client.get_trs_creation_data(id)
    trs_creation_data = trs_creation_data[0]
    mint_address = await mint.mint(trs_creation_data['title'],trs_creation_data['description'],number,trs_creation_data['creator_email'])
    token_account_address = await transaction_module.get_token_account_address(Pubkey.from_string(mint_address))
    await database_client.approve_trs_creation_request(id,trs_creation_data['creator_email'],number,mint_address,trs_creation_data['title'],token_account_address)
    return {"message":"TRS Succesfully created. "}
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
    await database_client.login_user(email=idinfo['email'])
    logging.info(f"Authenticated user {idinfo['email']} using Google OAuth2")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User, tags=["User"],summary="Returns the current user", description="Returns the current user.")
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

@app.post("/create_trs_request", dependencies=[Depends(get_current_user)],tags=["TRS"], summary="Creates TRS", description="Makes a TRS Creation request, with all the given data.")
async def create_trs_request(
    current_user: User = Depends(get_current_user),
    model_name: str = Form(...),
    title: str = Form(...),
    description : str = Form(...),
    files: List[UploadFile] = File(...),
    image: UploadFile = File(...),
    number:int = Form(...)
):
    """
    This function creates a TRS creation request by uploading files to a storage service,
    and storing the request details in a database.

    Parameters:
    current_user (User): The user making the TRS creation request. This parameter is obtained from the 'get_current_user' function.
    model_name (str): The name of the model used for creating the TRS.
    metadata (Metadata): The metadata associated with the TRS creation request.
    files (List[UploadFile]): The files associated with the TRS creation request.
    number (int): The number of TRS to be minted. Currently only a placeholder. 
    Returns:
    JSONResponse: A JSON response indicating the success or failure of the TRS creation request.
        - status_code (int): The HTTP status code of the response.
        - content (dict): The content of the response. It contains a message indicating the success or failure of the request.

    Raises:
    HTTPException: If an error occurs during the TRS creation request.
    """
    if len(files) > 10:
        return JSONResponse(status_code=400, content={"message": "A maximum of 10 files can be uploaded."})
    exist = await database_client.check_collection_exists()
    pend_request = await database_client.get_trs_creation_requests('pending')
    confirmed_request = await database_client.get_trs_creation_requests('approved')
    all_request = pend_request + confirmed_request
    for request in all_request: 
        if request['name'] == title:
            raise HTTPException(status_code=409, content = "There is already a TRS creation request in this Title.")
    if exist: 
        raise HTTPException(status_code=409, content = "Collection already exists.")
    try:
        
        file_urls = []
        for file in files:
            file_url = await storage.upload_to_s3(file,f'trs_data/{title}/{file.filename}')
            file_urls.append(file_url)
        image_url = await storage.upload_to_s3(image, f'trs_data/{title}/thumbnail.png')
        file_url_header =  f'trs_data/{title}/'

        await database_client.add_trs_creation_request(model_name,title,description,current_user.email, file_url_header)

        return JSONResponse(status_code= 200, content = {"message":"Trs creation request submitted succesfully. "})
    except Exception as e:
        return HTTPException(status_code = 500, content = str(e))

@app.post('/trade/create',dependencies=[Depends(get_current_user)],tags=['Transactions'],summary="Creates a trade.",description="Creates a trade, adds it to the pending trades database, creates a paypal transaction")
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


@app.get('/trade/execute_payment',tags =['Transactions'],summary='Executes the trade.',description='Executes the buyer transaction, sends payouts, transafers assets, and Finalizes the trade.')
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


@app.get('/wallet/get', dependencies=[Depends(get_current_user)],tags=["User"], description="Returns a formatted wallet, as a JSON with created TRS, TRS on marketplace, and TRS with artisan rights.")
async def wallet_get(user: User = Depends(get_current_user)):
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
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        final_wallet = {}
        
        for trs in wallet['trs']:
            if trs['collection_name'] in final_wallet.keys():
                final_wallet[trs['collection_name']]['number'] +=1 
                if trs['artisan'] == 1:
                    final_wallet[trs['collection_name']]['artisan'] +=1
                elif trs['marketplace'] == 1:
                    final_wallet[trs['collection_name']]['marketplace'] +=1 
                elif trs['creator'] == user.id:
                    final_wallet[trs['collection_name']]['created'] = True
            else:
                collection_data = await database_client.get_collection_data(trs['collection_name'])
                final_wallet[trs['collection_name']] = {'number': 1, 'created': False, 'artisan': 0,'marketplace': 0,'data':collection_data}
                if trs['artisan'] == 1:
                    final_wallet[trs['collection_name']]['artisan'] +=1
                elif trs['marketplace'] == 1:
                    final_wallet[trs['collection_name']]['marketplace'] +=1 

        return final_wallet
    except Exception as e:
        logger.error(f"Error fetching wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/marketplace',tags=["Marketplace"],summary="Fetches the marketplace",description="Fetches all the martketplace entries, along with the respective data. ")
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
    try:
        trs_on_marketplace = await database_client.get_marketplace_all()
        return trs_on_marketplace
    except Exception as e:
        logger.error(f"Error fetching marketplace: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get('/marketplace/collection',tags=["Marketplace"],summary="Fetches the marketplace for one collection",description="Fetches the martketplace entries for one specific collection, along with the respective data. ")
async def marketplace_collection(collection_name: str):
    """
    Retrieves all TRS of a specific collection currently listed on the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    """
    try:
        trs_on_marketplace = await database_client.get_marketplace_collection(collection_name)
        
        return trs_on_marketplace
    except Exception as e:
        logger.error(f"Error fetching marketplace for collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/marketplace/place',dependencies=[Depends(get_current_user)],tags=["Marketplace"],summary="Adds TRS to the marketplace",description="Adds TRS to the martketplace from a users wallet.  ")
async def marketplace_add(collection_name: str, number: int,price:int, user: User = Depends(get_current_user)) -> dict:
    """
    This function adds TRS of a specific collection to the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    number (int): The number of TRS to be added to the marketplace.
    price (int): The bid price for the TRS in the marketplace.
    user (User): The user making the request. This parameter is obtained from the 'get_current_user' function.

    Returns:
    dict: A dictionary containing a success message if the TRS are added to the marketplace successfully.
        - message (str): "TRS added to marketplace successfully."
    """
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        
        for i in wallet['trs']: 
            logger.debug(i)
            if i['collection_name'] == collection_name and i['marketplace'] == 0 and i['artisan'] == 0:
                req_wallet.append(i)

        if len(req_wallet) >= number:   
            values = []
            values2 = []
            for i in req_wallet[:number]:
                price = 1000
                values.append((i['trs_id'],collection_name, user.id,price))
                values2.append((i['trs_id'],))
            await database_client.add_trs_to_marketplace(user.id,values,values2,i['collection_name'])

            return {"message": "TRS added to marketplace successfully."}
        else:
            return {"message": F"Insufficient TRS of {collection_name} in wallet."}
    except Exception as e:
        logger.error("Error in adding trs to marketplace", e)
        raise HTTPException(status_code = 500, detail = e)

@app.post('/marketplace/remove',dependencies=[Depends(get_current_user)],tags=["Marketplace"],summary="Removes TRS from the marketplace",description="Removes TRS from the martketplace from a users wallet.  ")
async def marketplace_remove(collection_name: str, number: int, user: User = Depends(get_current_user)) -> dict:
    """
    This function removes TRS of a specific collection from the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    number (int): The number of TRS to be removed from the marketplace.
    user (User): The user making the request. This parameter is obtained from the 'get_current_user' function.

    Returns:
    dict: A dictionary containing a success message if the TRS are removed from the marketplace successfully.
        - message (str): "TRS removed from marketplace successfully."
    If there are not enough TRS in the user's wallet for the specified collection, the function returns:
        - message (str): "Insufficient TRS of {collection_name} in wallet."
    """
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        for i in wallet['trs']: 
            if i['collection_name'] == collection_name and i['marketplace'] == 1 and i['artisan'] == 0:
                req_wallet.append(i)

        if len(req_wallet) >= number:
            values = []
            for i in req_wallet[:number]:
                values.append((i['trs_id'],))
            await database_client.remove_trs_from_marketplace(values,user.id)

            return {"message": "TRS removed from marketplace successfully."}
        else:
            return {"message": F"Insufficient TRS of {collection_name} in wallet."}
    except Exception as e:
        logger.error("Error in removing trs from marketplace", e)
        raise HTTPException(status_code = 500, detail = e)


@app.post('/artisan/activate',dependencies=[Depends(get_current_user)],tags=["User"],summary="Activates artisan rights for a user's TRS",description="Activates artisan rights for a user's TRS")
async def artisan_activate(collection_name: str, number: int, user: User = Depends(get_current_user)) -> dict:
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        for i in wallet['trs']: 
            logger.debug(i)
            if i['collection_name'] == collection_name and i['marketplace'] == 0 and i['artisan'] == 0:
                req_wallet.append(i)

        if len(req_wallet) >= number:
            values = []
            for i in req_wallet[:number]:
                values.append((i['trs_id'],))
            await database_client.activate_artisan_trs(values, user.id)

            return {"message": "TRS added to marketplace successfully."}
        else:
            return {"message": F"Insufficient TRS of {collection_name} in wallet."}
    except Exception as e:
        logger.error("Error in activating artisan rights on trs. ", e)
        raise HTTPException(status_code = 500, detail = e)
    


@app.post('/artisan/deactivate',dependencies=[Depends(get_current_user)],tags=["User"],summary="Deactivates artisan rights for a user's TRS",description="Deactivates artisan rights for a user's TRS")
async def artisan_deactivate(collection_name: str, number: int, user: User = Depends(get_current_user)) -> dict:
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        for i in wallet['trs']: 
            if i['collection_name'] == collection_name and i['marketplace'] == 0 and i['artisan'] == 1:
                req_wallet.append(i)
        if len(req_wallet) >= number:
            values = []
            for i in req_wallet[:number]:
                values.append(i['trs_id'])
            await database_client.deactivate_artisan_trs(values, user.id)

            return {"message": "TRS added to marketplace successfully."}
        else:
            return {"message": F"Insufficient TRS of {collection_name} in wallet."}
        
    except Exception as e:
        logger.error("Error in deactivating artisan rights for trs. ", e)
        raise HTTPException(status_code = 500, detail = e)
    
