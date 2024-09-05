import subprocess
from solana.rpc.api import Client
import json
import os
from PIL import Image

central_key =  "9QVeLdhziTQBFSTNWQxbzhwzQYgmcH4vT8GPsWqDBQFj" 
# The wallet it is to be minted to, in this case the central wallet. 

def metadata_generator(collection_name, collection_description, symbol, image_path_uri, number):
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
            }]
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

    for i in range(number):
        metadata = metadata_template.copy()
        metadata['name'] = collection_name + str(i)
        metadata["attributes"][0]["value"] = str(i)
        with open(f'{path_beginner}{collection_name}/{i}.json','w') as file:
            strin = json.dumps(metadata, indent=4)
            file.write(strin)

    return f'{path_beginner}{collection_name}'

def image_duplicator(uri,number,collection_name):
    original_image = Image.open(uri)
    original_image.save(f'./collections/{collection_name}/collection.png')
    
    for i in range(number):
        file_name = f'./collections/{collection_name}/{i}.png'
        original_image.save(file_name)
def image_duplicator(uri, number, collection_name):
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
    
    for i in range(number):
        file_name = f'./collections/{collection_name}/{i}.png'
        original_image.save(file_name)

def run_command(command):
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
    except subprocess.CalledProcessError as e:
        print("Error executing command:", e)
        
   
def edit_config(collection_symbol, central_key, number):
    """
    This function edits the configuration file 'config.json' with the provided parameters.

    Parameters:
    collection_symbol (str): The symbol of the collection to be minted.
    central_key (str): The public key of the wallet to which the NFTs will be minted.
    number (int): The number of NFTs to be minted.

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

def mint(number):
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
        run_command('sugar mint')
        print("Succesfuly minted ",i+1, " NFT's")

    return

def mint_nfts(collection_name, collection_description, collection_symbol, number, uri): 
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
    metadata_generator(collection_name,collection_description,collection_symbol,uri,number)
    print("Generating images")
    image_duplicator(uri,number,collection_name)
    print("Editing config")
    edit_config(collection_symbol,central_key,number)
    print("Uploading to central")
    run_command(f'sugar upload -k ./central_wallet.json ./collections/{collection_name}')
    print("Deploying")
    run_command("sugar deploy")
    print("Verifying")
    run_command("sugar verify")
    print("Minting")
    for i in range(number):
        run_command("sugar mint")
        print("Minted ", i+1, " NFT's")
    print("Cleaning up")
    os.remove('./cache.json')
    os.rmdir(f'./collections/{collection_name}')

#Example call - mint_nfts("Testing","For testing Purposes","TST",15,'./collections/assets/5.png')
