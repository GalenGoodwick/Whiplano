import subprocess
from solana.rpc.api import Client
import json
import os
from PIL import Image
import time
import shutil
from backend.database import DatabaseManager
from backend.transaction import get_token_account_address
    
'''except Exception as e:
   
    from database import DatabaseManager
    from transaction import get_token_account_address'''
    
import asyncio
 
from solders.pubkey import Pubkey
from dotenv import load_dotenv

load_dotenv()

database_password = os.getenv("DATABASE_PASSWORD")
central_key = os.getenv('CENTRAL_WALLET_PUBKEY')
database = DatabaseManager(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    password=os.getenv("DATABASE_PASSWORD"),
    database =os.getenv("DATABASE_NAME")
)
from backend.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("mint")



async def mint_nft(data):
    
    minter = NFTMinter(central_key)
    await minter.mint_nfts(
        data['collection_name'],
        data['collection_description'],
        data['collection_symbol'],
        data['number'],
        data['uri'],
        data['creator_id']
    )
    

#e = NFTMinter("9QVeLdhziTQBFSTNWQxbzhwzQYgmcH4vT8GPsWqDBQFj")
#e.mint_nfts("TestingDatbase","tiele","title",100,'./collections/assets/9.png',10)
