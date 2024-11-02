import asyncio
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from spl.token.async_client import  AsyncToken
from solders.keypair import Keypair
from solana.rpc.types import TokenAccountOpts
from solana.transaction import Transaction
from spl.token.instructions import transfer,TransferParams
from spl.memo.instructions import create_memo,MemoParams
from spl.memo.constants import MEMO_PROGRAM_ID
import json
import aiohttp
import os 
import subprocess
import dotenv
dotenv.load_dotenv()

client = AsyncClient("https://api.devnet.solana.com")


from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("dac")

central_wallet = Pubkey.from_string(os.getenv('CENTRAL_WALLET_PUBKEY'))
central_wallet_keypair = Keypair.from_bytes(json.loads(os.getenv('CENTRAL_WALLET_KEY').encode()))

def fetch_metadata_script(mint_address):
    try:
        # Run the JS script with Node.js
        result = subprocess.run(
            ['node', '/app/app/js/fetch_metadata.js', mint_address], 
            check=True, 
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        error_output = result.stderr.strip()
        
        logger.info("JS script stdout:", output)  # This will log console.log outputs
        logger.error("JS script stderr:", error_output)
        
        data = json.loads(output)
        uri = data.get('uri')
        logger.info(f"Fetched metadata of NFT with mint address: {mint_address} and uri : {uri}")
        return uri

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running JS script: {e.stderr}")
        return None

async def fetch_metadata_from_uri(url):
    async with aiohttp.ClientSession() as session:
        try:
            # Send a GET request to the specified URL
            async with session.get(url) as response:
                # Raise an error for bad responses (4xx or 5xx)
                response.raise_for_status()

                # Parse the JSON content
                metadata = await response.json()
                return metadata

        except aiohttp.ClientResponseError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
        except Exception as err:
            logger.error(f"An error occurred: {err}")

async def fetch_metadata(mint_address):
    uri = fetch_metadata_script(mint_address)
    if uri:
        metadata = await fetch_metadata_from_uri(uri)
        print(metadata)
        return metadata
    else:
        
        return None

async def get_owners(mint_address):
    met = await fetch_metadata(mint_address)
    return met['owners']

async def upload_metadata(metadata):
    metadata_json = json.dumps(metadata)
    try:
        # Run the JS script with Node.js
        result = subprocess.run(
            ['node', '/app/app/js/upload_metadata.js', metadata_json], 
            check=True, 
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        error_output = result.stderr.strip()
        
        logger.info("JS script stdout:", output)  # This will log console.log outputs
        logger.error("JS script stderr:", error_output)
        
        data = json.loads(output)
        uri = data.get('uri')
        logger.info(f"Uploaded metadata of NFT. ")
        return uri

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running JS script: {e.stderr}")
        return None

async def update_metadata_uri(mint_address,metadata_uri):
    try:
        # Run the JS script with Node.js
        result = subprocess.run(
            ['node', '/app/app/js/update_metadata.js', mint_address,metadata_uri], 
            check=True, 
            capture_output=True,
            text=True
        )
        output = result.stdout.strip()
        error_output = result.stderr.strip()
        
        logger.info("JS script stdout:", output)  # This will log console.log outputs
        logger.error("JS script stderr:", error_output)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error running JS script: {e.stderr}")
        return None

    return
async def transfer(mint_address, seller_email,buyer_email, number): 
    initial_metadata = await fetch_metadata(mint_address)
    initial_metadata['owners'][seller_email] -= number
    initial_metadata['owners'][buyer_email] += number

    metadata_uri = await upload_metadata(initial_metadata)
    await update_metadata_uri(mint_address,metadata_uri)
    logger.info(f"Transferred {number} TRS from {seller_email} to {buyer_email}, mint address :{mint_address}")
    return True


