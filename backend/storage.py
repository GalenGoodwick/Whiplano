import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from datetime import date
import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv
import asyncio
import io 
#from backend.logging_config import logging_config  # Import the configuration file
import logging.config
#logging.config.dictConfig(logging_config)
logger = logging.getLogger("storage")

load_dotenv()

# Filebase S3-Compatible API endpoint and your Filebase credentials
FILEBASE_ACCESS_KEY = os.getenv("FILEBASE_ACCESS_KEY")
FILEBASE_SECRET_KEY = os.getenv("FILEBASE_SECRET")
ENDPOINT_URL = os.getenv("FILEBASE_ENDPOINT")
BUCKET_NAME = os.getenv("FILEBASE_BUCKET")

# Initialize boto3 S3 resource with Filebase credentials
s3 = boto3.resource(
    's3',
    aws_access_key_id=FILEBASE_ACCESS_KEY,
    aws_secret_access_key=FILEBASE_SECRET_KEY,
    endpoint_url=ENDPOINT_URL,
    config=Config(signature_version='s3v4')
)
s3_client = boto3.client(
    's3',
    aws_access_key_id=FILEBASE_ACCESS_KEY,
    aws_secret_access_key=FILEBASE_SECRET_KEY,
    endpoint_url=ENDPOINT_URL,
    config=Config(signature_version='s3v4')
)

def upload_file(file_path, object_name=None):
    """Upload a file to Filebase S3 bucket."""
    try:
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        s3.Bucket().upload_file(file_path, object_name)
        print(f"File '{file_path}' uploaded successfully to '{BUCKET_NAME}/{object_name}'.")
    except Exception as e:
        print(f"Error uploading file: {e}")

async def upload_to_s3(file: UploadFile, object_name: str):
    try:
        # Upload the file object to S3 bucket
        s3.Bucket(BUCKET_NAME).upload_fileobj(file.file, object_name)
        # Generate the file URL after uploading
        file_url = f"{ENDPOINT_URL}/{BUCKET_NAME}/{object_name}"

        return file_url
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {e}")

def download_file(object_name, download_path):
    """Download a file from Filebase S3 bucket."""
    try:
        # Ensure the directory exists
        directory = os.path.dirname(download_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory '{directory}' created.")

        # Download the file
        s3.Bucket(BUCKET_NAME).download_file(object_name, download_path)
        logger.info(f"File '{object_name}' downloaded successfully to '{download_path}'.")
    
    except Exception as e:
        logger.info(f"Error downloading file: {e}")

async def test():
    with open('./collections/assets/3.png', 'rb') as file:
        # Create a fake UploadFile object
        upload_file = UploadFile(filename='lol.png', file=file)
        # Call the upload function
        file_url = await upload_to_s3(upload_file, 'lol.png')
        logger.info(f"File uploaded successfully: {file_url}")
        return file_url
#asyncio.run(test())


def get_file_cid( object_name):
    try:
        # Retrieve object metadata
        response = s3_client.head_object(Bucket=BUCKET_NAME, Key=object_name)
        
        # Extract the CID from metadata
        metadata = response.get('Metadata', {})
        metadata = metadata.json()
        cid = metadata['json']
        
        if cid:
            logger.info(f"CID for '{object_name}' is: {cid}")
            return cid
        else:
            logger.info(f"No CID found in metadata for '{object_name}'.")
            return None
    except Exception as e:
        print(f"Error retrieving CID: {e}")
        return None
