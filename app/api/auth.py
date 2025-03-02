
import requests
from google.auth.transport import requests as google_requests
import random
from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile, status,Request , BackgroundTasks
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta
from app.utils.utils import hash_password, get_current_user, create_auth_token,authenticate_user
from app.utils.utils import ACCESS_TOKEN_EXPIRE_MINUTES,SERVER_URL
from app.core.database import database_client
from app.utils.models import SignupRequest, KYCData,User,Token
from datetime import timedelta
import os
from google.oauth2 import id_token
from app.core import storage
from starlette.responses import JSONResponse
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr, BaseModel
from typing import List
import random
from dotenv import load_dotenv
load_dotenv()  


GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = SERVER_URL + "/callback/google"  

from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("authentication")

router = APIRouter()

email_conf = conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("GOOGLE_MAIL_ID"),
    MAIL_PASSWORD = os.getenv("GOOGLE_EMAIL_PASSWORD"),
    MAIL_FROM = os.getenv("GOOGLE_MAIL_ID"),
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="Whiplano",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)


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
    return {"access_token": access_token, "token_type": "bearer", "info":{user.model_dump()}}



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
    user_id = await database_client.add_user(user.email,hashed_password)
    logger.info("Added user to the database. ")
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_auth_token(data={"sub": user.email}, expires_delta=access_token_expires)
    logger.info(f"User created with email {user.email}")
    await database_client.login_user(user.email)
    # Return token
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/send_otp",dependencies = [Depends(get_current_user)],tags=["Authentication"], summary="Sends an OTP to the email. ", description="Sends an OTP to the email. ")
async def send_otp(current_user: User = Depends(get_current_user)):
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=5)  # OTP expires in 5 minutes
    email = current_user.email
    html = f"""
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            padding: 20px;
        }}
        .container {{
            max-width: 500px;
            margin: auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: left;
        }}
        .otp {{
            font-size: 24px;
            font-weight: bold;
            color: #2d89ef;
            margin: 10px 0;
        }}
        .footer {{
            margin-top: 20px;
            font-size: 14px;
            color: #555;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Email Verification Code</h2>
        <p>Hello,</p>
        <p>Your One-Time Password (OTP) for email verification on <strong>Whiplano</strong> is:</p>
        <p class="otp">{otp}</p>
        <p>This OTP is valid for <strong>5 minutes</strong>. Please do not share it with anyone.</p>
        <p>If you did not request this, please ignore this email.</p>
        <p class="footer">Thank you,<br>Whiplano Team</p>
    </div>
    <br><br><br> 
</body>
</html>
"""
    message = MessageSchema(
        subject="Your One-Time Password (OTP) for Email Verification",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    await database_client.store_otp(current_user.email,expires_at, otp)
    await fm.send_message(message)
@router.post("/recieve_otp",dependencies= [Depends(get_current_user)],tags=["Authentication"],summary="Allows the user to check their otp",description="Recieves an otp from the user, checks it with the one stored in the database, if yes verifies the user")
async def recieve_otp(entered_otp:int, current_user: User = Depends(get_current_user),):
    try:

        otp = await database_client.fetch_otp(current_user.email)
        if (otp == None) or (otp == 0):
            return "No valid OTP found."
        else: 
            if otp == entered_otp:
                await database_client.verify_user(current_user.email)
                logger.info(f"Verified user {current_user.email} ")
    except Exception as e:
        logger.errror(f"Error verifying user {e}")
        raise HTTPException(status_code=400, detail=str(e))
    return

    
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
