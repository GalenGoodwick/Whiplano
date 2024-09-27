import boto3
from botocore.client import Config
import os

# Filebase S3-Compatible API endpoint and your Filebase credentials
FILEBASE_ACCESS_KEY = 'your-filebase-access-key'
FILEBASE_SECRET_KEY = 'your-filebase-secret-key'
ENDPOINT_URL = 'https://s3.filebase.com'
BUCKET_NAME = 'your-bucket-name'

# Initialize boto3 S3 resource with Filebase credentials
s3 = boto3.resource(
    's3',
    aws_access_key_id=FILEBASE_ACCESS_KEY,
    aws_secret_access_key=FILEBASE_SECRET_KEY,
    endpoint_url=ENDPOINT_URL,
    config=Config(signature_version='s3v4')
)

def upload_file(file_path, bucket_name, object_name=None):
    """Upload a file to Filebase S3 bucket."""
    try:
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        s3.Bucket(bucket_name).upload_file(file_path, object_name)
        print(f"File '{file_path}' uploaded successfully to '{bucket_name}/{object_name}'.")
    except Exception as e:
        print(f"Error uploading file: {e}")

def download_file(bucket_name, object_name, download_path):
    """Download a file from Filebase S3 bucket."""
    try:
        s3.Bucket(bucket_name).download_file(object_name, download_path)
        print(f"File '{object_name}' downloaded successfully to '{download_path}'.")
    except Exception as e:
        print(f"Error downloading file: {e}")

if __name__ == "__main__":
    # Example file paths for upload and download
    local_upload_file = "/path/to/local/upload/file.txt"
    local_download_path = "/path/to/save/downloaded/file.txt"
    object_name_in_s3 = "file.txt"  # This will be the name of the file in the bucket

    # Upload a file to the bucket
    print("Uploading file...")
    upload_file(local_upload_file, BUCKET_NAME, object_name_in_s3)

    # Download the file from the bucket
    print("Downloading file...")
    download_file(BUCKET_NAME, object_name_in_s3, local_download_path)
