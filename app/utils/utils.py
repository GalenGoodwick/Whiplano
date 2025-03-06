import bcrypt
from datetime import datetime, timedelta
from typing import Union
import jwt
import os
from pydantic import EmailStr, BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import uuid
from app.core.database import database_client
from app.utils.models import User, Token, TokenData
import smtplib
from email.mime.text import MIMEText

smtp_server = "smtp.gmail.com"
port = 465
email_address = "danielvincent1718@gmail.com"

SERVER_URL = "https://whiplano-1b8102db6480.herokuapp.com"

load_dotenv()  # Load environment variables
email_password = os.getenv("GOOGLE_EMAIL_PASSWORD")
database_client = database_client

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



def hash_password(password: str) -> bytes:
    """
    Hash a password using bcrypt.

    This function generates a random salt using bcrypt's gensalt function,
    and then hashes the provided password using the generated salt and bcrypt's hashpw function.
    The hashed password is returned as bytes.

    Parameters:
    password (str): The password to be hashed. This should be a string of ASCII characters.

    Returns:
    bytes: The hashed password as bytes. This can be safely stored in a database.
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Function to check if the password matches the hashed password

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify if a given password matches the hashed password.

    This function uses bcrypt to compare the hashed version of the provided password
    with the stored hashed password. It returns True if the passwords match, and False otherwise.

    Parameters:
    password (str): The password provided by the user. This should be a string of ASCII characters.
    hashed_password (bytes): The hashed password stored in the database. This should be a bytes object.

    Returns:
    bool: True if the provided password matches the hashed password, False otherwise.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_auth_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    Create a JWT (JSON Web Token) for authentication.

    This function generates a JWT token using the provided data and an optional expiration delta.
    The token is encoded with a secret key and an algorithm. If an expiration delta is provided,
    the token will expire after the specified duration. Otherwise, it will expire after a default
    duration specified by the ACCESS_TOKEN_EXPIRE_MINUTES environment variable.

    Parameters:
    data (dict): A dictionary containing the data to be included in the JWT token.
                 This data will be included in the token's payload.
    expires_delta (Union[timedelta, None], optional): The duration after which the token should expire.
                                                      If not provided, the token will expire after a default duration.
                                                      Defaults to None.

    Returns:
    str: The generated JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """
    Verify a JWT token and decode its payload.

    This function takes a JWT token as input, verifies its integrity using the provided secret key and algorithm,
    and decodes the token's payload. If the token is valid, the function returns the decoded payload as a dictionary.
    If the token is invalid or cannot be decoded, the function returns an empty dictionary.

    Parameters:
    token (str): The JWT token to be verified and decoded. This token should be a string.

    Returns:
    dict: The decoded payload of the JWT token if it is valid. An empty dictionary otherwise.
    """
    try:
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return {}



async def authenticate_user(email: str, password: str) -> Union[User, None]:
    """Authenticate a user by verifying their email and password.

    This function retrieves a user from the database based on the provided email.
    It then verifies the password by comparing it with the hashed password stored in the database.
    If the email and password match, the function returns the user object. Otherwise, it returns None.

    Parameters:
    email (str): The email of the user attempting to authenticate.
    password (str): The password provided by the user.

    Returns:
    Union[User, None]: The user object if the email and password are valid, otherwise None.
    """
    user = await database_client.get_user_by_email(email)
    
    if user and verify_password(password, user["password_hash"]):
        
        user_instance = User(email=user['email'],
                             username=user["username"],
                             verified=user["verified"],
                             artisan=user["artisan"],
                             creator=user["creator"],
                             pfp_uri=user["pfp_uri"],
                             bio=user["bio"],
                             telegram=user["telegram"],
                             twitter=user["twitter"],
                             admin=user["admin"]
                             )
        return user_instance
    return None


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Asynchronously retrieves the current user based on the provided token.

    This function verifies the token, retrieves the user from the database, and returns the user object.
    If the token is invalid, unauthorized, or the user does not exist, it raises an HTTPException.

    Parameters:
    token (str): The JWT token provided by the client. This token is used to authenticate the user.
                The default value is obtained from the `oauth2_scheme` dependency.

    Returns:
    User: The user object containing the user's ID, username, and email.

    Raises:
    HTTPException: If the token is invalid, unauthorized, or the user does not exist.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
    
    email = payload.get("sub")
    
    if email is None:
        raise credentials_exception
    user = await database_client.get_user_by_email(email)
    user_instance = User(email=user['email'],
                             username=user["username"],
                             id=user["user_id"],
                             last_login=user["last_login"],
                             verified=user["verified"],
                             role=user["role"],
                             kyc=user["kyc"],
                             artisan=user["artisan"],
                             creator=user["creator"],
                             pfp_uri=user["pfp_uri"],
                             bio=user["bio"],
                             telegram=user["telegram"],
                             twitter=user["twitter"],
                             )
    if user is None:
        raise credentials_exception
    return user_instance


async def get_current_verified_user(token: str = Depends(oauth2_scheme)):
    
    """
Asynchronously retrieves the current verified user based on the provided token.

This function verifies the token, retrieves the user from the database, and returns the user object.
If the token is invalid, unauthorized, or the user does not exist, it raises an HTTPException.
If the user is not verified, it also raises an HTTPException.

Parameters:
token (str): The JWT token provided by the client. This token is used to authenticate the user.
             The default value is obtained from the `oauth2_scheme` dependency.

Returns:
User: The user object containing the user's ID, username, and email.

Raises:
HTTPException: If the token is invalid, unauthorized, or the user does not exist.
               If the user is not verified.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    authorization_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User is not verified",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)

    if not payload:
        raise credentials_exception

    email = payload.get("sub")

    if email is None:
        raise credentials_exception
    user = await database_client.get_user_by_email(email)
    user_instance = User(email=user['email'],
                             username=user["username"],
                             id=user["user_id"],
                             last_login=user["last_login"],
                             verified=user["verified"],
                             role=user["role"],
                             kyc=user["kyc"],
                             artisan=user["artisan"],
                             creator=user["creator"],
                             pfp_uri=user["pfp_uri"],
                             bio=user["bio"],
                             telegram=user["telegram"],
                             twitter=user["twitter"],
                             )
    if user is None:

        raise credentials_exception
    elif user['status'] =='not verified':
        raise authorization_exception
    return user_instance



async def get_current_admin(token: str = Depends(oauth2_scheme)):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    authorization_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User is not an admin. ",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
    
    email = payload.get("sub")
    
    if email is None:
        raise credentials_exception
    user = await database_client.get_user_by_email(email)
    user_instance = User(email=user['email'],
                             username=user["username"],
                             id=user["user_id"],
                             last_login=user["last_login"],
                             verified=user["verified"],
                             role=user["role"],
                             kyc=user["kyc"],
                             artisan=user["artisan"],
                             creator=user["creator"],
                             pfp_uri=user["pfp_uri"],
                             bio=user["bio"],
                             telegram=user["telegram"],
                             twitter=user["twitter"],
                             )
    if user is None:
        raise credentials_exception
    elif user['role'] == 'user':
        raise authorization_exception
    return user_instance



def create_reset_token(email: str):
    expiry = datetime.utcnow() + timedelta(minutes=15)
    payload = {"sub": email, "exp": expiry}
    return jwt.encode(payload, str(SECRET_KEY), algorithm=ALGORITHM)

def verify_reset_token(token: str):
    try: 
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
        return payload[['sub']]
    except:
        None
