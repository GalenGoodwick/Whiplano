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
    host='localhost',
    user='root',
    password='new_password',
    database ='whiplano'
)


# The wallet it is to be minted to, in this case the central wallet. 
class NFTMinter:
    def __init__(self, central_key):
        self.central_key = central_key
        self.client = Client("https://api.devnet.solana.com")
        
    def metadata_generator(self,collection_name, collection_description, symbol, image_path_uri, number):
        """
        This function generates metadata for a collection of NFTs and saves it as JSON files.

        Parameters:
        collection_name (str): The name of the collection.
        collection_description (str): The description of the collection.
        symbol (str): The symbol of the collection.
        image_path_uri (str): The URI of the image for the collection.
        number (int): The number of NFTs in the collection.

        Returns:
        str: The path to the directory where the collection's JSON files are saved.
        """
        collection_metadata = {
            "name": collection_name,
            "symbol": symbol,
            "description": collection_description,
            "image": image_path_uri,
            "attributes": [],
            "properties" : {
                "files": [{
                    "uri": image_path_uri,
                    "type": "image/png"
                }],
                "category": "image"
            }
        }
        path_beginner = './collections/'
        os.makedirs(f'{path_beginner}{collection_name}', exist_ok=True)
        with open(f'{path_beginner}{collection_name}/collection.json','w') as file:
            json.dump(collection_metadata, file, indent=4)
            print("Succesfuly created collection.json")

        metadata_template = {
            "name": collection_name,
            "symbol": symbol,
            "description": collection_description,
            "image": image_path_uri,
            "attributes": [
                {
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

    def image_duplicator(self,uri, number, collection_name):
        """
        This function duplicates an image to create multiple copies for a collection of NFTs.

        Parameters:
        uri (str): The URI of the original image.
        number (int): The number of copies to create.
        collection_name (str): The name of the collection.

        Returns:
        None
        """
        original_image = Image.open(uri)
        original_image.save(f'./collections/{collection_name}/collection.png')
        original_image.save(f'./collections/{collection_name}/0.png')
        '''for i in range(number):
            file_name = f'./collections/{collection_name}/{i}.png'
            original_image.save(file_name)'''

    def run_command(self,command):
        """
        This function executes a shell command and prints its output.

        Parameters:
        command (str): The shell command to be executed.

        Returns:
        None

        Raises:
        subprocess.CalledProcessError: If the command execution fails.
        """
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(result.stdout)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print("Error executing command:", e)
            
        
   
    def edit_config(self,collection_symbol, central_key, number):
        """
        This function edits the configuration file 'config.json' with the provided parameters.

        Parameters:
        collection_symbol (str): The symbol of the collection to be minted.
        central_key (str): The public key of the wallet to which the NFTs will be minted.
        number (int): The number of NFTs to be minted.
s
        Returns:
        None

        The function opens the 'config.json' file, reads its content, updates the 'number', 'symbol', and 'central_key' fields with the provided parameters,
        and then writes the updated content back to the file.
    """
        with open('./config.json', 'r+') as file:
            data = json.load(file)
            data['number'] = number
            data['symbol'] = collection_symbol
            data['central_key'] = central_key
            file.seek(0)
            json.dump(data, file, indent=4)
            file.truncate()

    def mint(self,number):
        """
        This function executes the 'sugar mint' command a specified number of times.
        It is used to mint a specified number of NFTs.

        Parameters:
        number (int): The number of NFTs to be minted. The function will execute the 'sugar mint' command this many times.

        Returns:
        None

        The function iterates over the range of 'number' and executes the 'sugar mint' command.
        After each minting operation, it prints a success message indicating the number of NFTs minted.
        """
        mint_command = ['sugar','mint']
        for i in range(number):
            self.run_command('sugar mint')
            print("Succesfuly minted ",i+1, " NFT's")

        return

    async def mint_nfts(self,collection_name, collection_description, collection_symbol, number, uri,creator_id): 
        """
        This function automates the process of minting NFTs on the Solana blockchain.
        It performs various tasks such as generating metadata, duplicating images, editing configuration,
        uploading to central, deploying, verifying, minting, and cleaning up.

        Parameters:
        collection_name (str): The name of the collection of NFTs.
        collection_description (str): The description of the collection.
        collection_symbol (str): The symbol of the collection.
        number (int): The number of NFTs to be minted.
        uri (str): The URI of the image to be used for the NFTs.

        Returns:
        None

        The function performs the following steps:
        1. Removes a stagnant cache file if it exists.
        2. Generates metadata for the collection and individual NFTs.
        3. Duplicates images for the collection and individual NFTs.
        4. Edits the configuration file with the provided parameters.
        5. Uploads the collection to the central wallet.
        6. Deploys the collection on the Solana blockchain.
        7. Verifies the deployed collection.
        8. Mints the specified number of NFTs.
        9. Cleans up by removing the cache file and the temporary directory for the collection.
        """
        central_key = "9QVeLdhziTQBFSTNWQxbzhwzQ"
        try:
            os.remove('./cache.json')
            print("Removed stagnant cache")
        except:
            print("No cache to remove")
        
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
            print(e)


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
