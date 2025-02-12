
import requests
from google.auth.transport import requests as google_requests

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, status,Request
from fastapi.responses import RedirectResponse

from app.utils.utils import hash_password, get_current_user, create_auth_token,authenticate_user
from app.utils.utils import ACCESS_TOKEN_EXPIRE_MINUTES,SERVER_URL
from app.core.database import database_client
from app.utils.models import SignupRequest, KYCData,User,Token
from datetime import timedelta
import os
from google.oauth2 import id_token
from app.core import storage
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = SERVER_URL + "/callback/google"  

from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("authentication")

router = APIRouter()


@router.post("/login", response_model=Token,tags=["Authentication"], summary="Logs in the User", description="Used to log in users via email/password")
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



@router.post('/signup', response_model=Token,tags=["Authentication"], summary="Signing up of new users", description="Used to add users via email/password")
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
    hashed_password = hash_password(user.password)
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

@router.post("/verify_user",dependencies = [Depends(get_current_user)],tags=["Authentication"], summary="Checks if user is verified.", description="Checks if user is verified.")
async def verify_user():
    return


@router.post("/submit-kyc/", dependencies = [Depends(get_current_user)],tags=["Authentication"],summary = "Takes in all the KYC data, then verifies the user. ")
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
    
    
@router.get("/login/google",tags=["Authentication"], summary="Returns a url for logging in via Google Auth", description="Returns a url for logging in via Google Auth")
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


@router.get("/callback/google", response_model = Token)
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
