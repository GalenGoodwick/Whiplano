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

from backend.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("mint")
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
            ['node', '/app/backend/mint.js', image_path, metadata_path, name], 
            check=True, 
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        print("OUTPUT GIVEN",  output)
        data = json.loads(output)
        mint_address = data.get('mintAddress')
        logger.info(f"Minted NFT with mint address :{mint_address} ")
        return mint_address

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running JS script: {e.stderr}")
        return None

async def mint(title,description,number,owner_email):
    image_path = f'/tmp/collections/{title}/thumbnail'
    metadata_path = f'/tmp/collections/{title}/metadata.json'
    download_file(f'trs_data/{title}/thumbnail.png', image_path)
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

