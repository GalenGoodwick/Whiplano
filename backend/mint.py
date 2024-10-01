import subprocess
from solana.rpc.api import Client
import json
import os
from PIL import Image
import time
import shutil
from backend.storage import download_file
from backend.database import DatabaseManager
from backend.transaction import get_token_account_address
import dotenv
import asyncio
from solders.pubkey import Pubkey
dotenv.load_dotenv()


database_password = os.getenv("DATABASE_PASSWORD")
central_key = os.getenv('CENTRAL_WALLET_PUBKEY')
database = DatabaseManager(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    password=os.getenv("DATABASE_PASSWORD"),
    database =os.getenv("DATABASE_NAME")
)



def run_mint_script(image_path, metadata_path, name):
    try:
        # Run the JS script with Node.js
        result = subprocess.run(
            ['node', './backend/mint.js', image_path, metadata_path, name], 
            check=True, 
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        data = json.loads(output)
        mint_address = data.get('mintAddress')
        return mint_address

    except subprocess.CalledProcessError as e:
        print(f"Error running JS script: {e.stderr.decode('utf-8')}")
        return None

async def mint(title,description,number,owner_email):
    image_path = f'../collections/{title}/thumbnail'
    metadata_path = f'../collections/{title}/metadata.json'
    download_file(f'{title}/thumbnail.png', image_path)
    with open(metadata_path, 'w') as json_file:
        metadata = {
                "title": title,
                "description":description,
                "number":number,
                "owner":owner_email
                }

        json.dump(metadata,json_file)
    
    mint_address = run_mint_script(image_path,metadata_path,title)
    return mint_address
# Example usage
image_path = '../collections/assets/9.png'
metadata_path = '../collections/assets/9.json'
name = 'bunana'

mint_address, token_address = run_mint_script(image_path, metadata_path, name)

