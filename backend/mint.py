import subprocess
from solana.rpc.api import Client
import json
import os
from PIL import Image
import time
import shutil
from backend.database import DatabaseManager
from backend.transaction import get_token_account_address
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
'''

def metadata_generator(self,collection_name, collection_description, symbol, image_path_uri, number):


    metadata_template = {
        "name": ,
        "symbol": symbol,
        "description": collection_description,
        "image": image_path_uri,
        "attributes": [
            {g
                "trait_type":"Number",
                "value": None
            }
        ],
        "properties" : {
            "files": [{
                "uri": image_path_uri,
                "type": "image/png"
            }]
        }
    }

    for i in range(1):
        metadata = metadata_template.copy()
        metadata['name'] = collection_name + str(i)
        metadata["attributes"][0]["value"] = str(i)
        with open(f'{path_beginner}{collection_name}/{i}.json','w') as file:
            strin = json.dumps(metadata, indent=4)
            file.write(strin)

    return f'{path_beginner}{collection_name}'


'''
async def mint_nft(data):
    ''''
    await minter.mint_nfts(
        data['collection_name'],
        data['collection_description'],
        data['uri'],
        data['Additional Data']
    )
    
    
    await database.add_trs(number,mint_addresses[0],collection_name,token_account_address,creator_id)
    central_key = "9QVeLdhziTQBFSTNWQxbzhwzQ"

    
    print("Generating metadata")
    
    self.metadata_generator(collection_name,collection_description,collection_symbol,uri,1)
    print("Generating images")
    self.image_duplicator(uri,1,collection_name)
    print("Editing config")
    self.edit_config(collection_symbol,central_key,1)
    print("Uploading to central")
    
    self.run_command(f'sugar upload -k ./central_wallet.json ./collections/{collection_name}')
    print("Deploying")
    self.run_command("sugar deploy")
    print("Verifying")
    self.run_command("sugar verify")
    print("Minting")
    mint_addresses = []

    e = self.run_command("sugar mint")
    mint_split = e.split()
    
    for l in mint_split:
        if l == 'Mint:':
            mint_address = mint_split[mint_split.index(l)+1]
            mint_address = Pubkey.from_string(mint_address)
            mint_addresses.append(mint_address)
            break
    
    print(mint_address)
    print("Minted the NFT")
    time.sleep(5)

    token_account_address = await (get_token_account_address(mint_addresses[0]))
    print("Token account address: ",token_account_address)
    print(type(token_account_address))
    await database.add_trs(number,mint_addresses[0],collection_name,token_account_address,creator_id)
    
    
    print("Cleaning up")
    try:
        os.remove('./cache.json')
        shutil.rmtree(f'./collections/{collection_name}')
    except Exception as e:
        print(e)'''

    return
#e = NFTMinter("9QVeLdhziTQBFSTNWQxbzhwzQYgmcH4vT8GPsWqDBQFj")
#e.mint_nfts("TestingDatbase","tiele","title",100,'./collections/assets/9.png',10)
