import json
import base64
from solders.pubkey import Pubkey as PublicKey
from solana.rpc.api import Client
from solana.transaction import Transaction
from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solana.system_program import SYS_PROGRAM_ID
from solana.rpc.commitment import Confirmed
from solana.rpc.core import RPCException

from solders.keypair import Keypair
from solana.rpc.api import Client
from solana.transaction import TransactionInstruction
from spl.token.constants import TOKEN_PROGRAM_ID

# Replace with your own NFT metadata program ID
METADATA_PROGRAM_ID = PublicKey("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")

# Load your wallet (Keypair)
def load_keypair_from_file(filepath: str) -> Keypair:
    with open(filepath, "r") as f:
        secret_key = json.load(f)
    return Keypair.from_secret_key(bytes(secret_key))

# Create metadata account address for NFT
def get_metadata_address(mint_pubkey: PublicKey) -> PublicKey:
    seeds = [b"metadata", bytes(METADATA_PROGRAM_ID), bytes(mint_pubkey)]
    return PublicKey.find_program_address(seeds, METADATA_PROGRAM_ID)[0]

# Update NFT metadata
def update_nft_metadata(mint_address: str, payer: Keypair, name: str, symbol: str, uri: str):
    client = Client("https://api.mainnet-beta.solana.com")
    
    mint_pubkey = PublicKey(mint_address)
    metadata_address = get_metadata_address(mint_pubkey)

    # Create instruction to update metadata
    instruction_data = {
        "name": name,
        "symbol": symbol,
        "uri": uri,
    }

    metadata_instruction = TransactionInstruction(
        keys=[
            {"pubkey": metadata_address, "is_signer": False, "is_writable": True},
            {"pubkey": payer.public_key, "is_signer": True, "is_writable": False},
            {"pubkey": mint_pubkey, "is_signer": False, "is_writable": False},
            {"pubkey": SYS_PROGRAM_ID, "is_signer": False, "is_writable": False},
        ],
        program_id=METADATA_PROGRAM_ID,
        data=json.dumps(instruction_data).encode("utf-8"),
    )

    # Send transaction
    transaction = Transaction()
    transaction.add(metadata_instruction)

    try:
        result = client.send_transaction(transaction, payer)
        print("Transaction successful:", result)
    except RPCException as e:
        print(f"Transaction failed: {str(e)}")

if __name__ == "__main__":
    # Provide your own wallet keypair path
    payer = load_keypair_from_file("path/to/your/wallet.json")
    
    # Set the mint address of the NFT you want to update
    mint_address = "YourNFTMintAddressHere"
    
    # New metadata fields
    name = "New NFT Name"
    symbol = "NEW"
    uri = "https://example.com/new_metadata.json"
    
    update_nft_metadata(mint_address, payer, name, symbol, uri)
