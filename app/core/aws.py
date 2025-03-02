from fastapi import FastAPI, File, UploadFile, HTTPException
import boto3
import os
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

import mimetypes

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY") 
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME") 
AWS_REGION = os.getenv("AWS_REGION") 


s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)


async def upload_to_aws(file: UploadFile):
    """Uploads a file to AWS S3 and ensures it displays correctly in the browser."""
    try:
        
        content_type, _ = mimetypes.guess_type(file.filename)
        if content_type is None:
            content_type = "application/octet-stream"  
        s3.upload_fileobj(
            file.file,
            AWS_BUCKET_NAME,
            file.filename,
            ExtraArgs={"ContentType": content_type}  
        )
        file_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file.filename}"
        return file_url

    except NoCredentialsError:
        raise HTTPException(status_code=500, detail="AWS credentials not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)):
    """FastAPI endpoint to upload a file and return the S3 file URL."""
    file_url = await upload_to_s3(file)
    return {"message": "File uploaded successfully", "file_url": file_url}