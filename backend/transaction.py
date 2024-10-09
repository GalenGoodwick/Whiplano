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
import os 
import dotenv
dotenv.load_dotenv()

client = AsyncClient("https://api.devnet.solana.com")

from backend.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("transaction")

central_wallet = Pubkey.from_string(os.getenv('CENTRAL_WALLET_PUBKEY'))
central_wallet_keypair = Keypair.from_bytes(json.loads(os.getenv('CENTRAL_WALLET_KEY').encode()))


async def get_token_account_address(mint_address):
    """
    Asynchronously retrieves the token account address for a given mint address.

    Parameters:
    mint_address (Pubkey): The public key of the mint for which the token account address is to be retrieved.

    Returns:
    Pubkey: The public key of the token account associated with the given mint address.

    This function uses the Solana Python SDK to interact with the Solana blockchain. It first creates a TokenAccountOpts object with the provided mint address. Then, it calls the get_token_accounts_by_owner method of the AsyncClient to retrieve the token accounts associated with the central wallet and the specified mint. The function extracts the public key of the first token account from the response and returns it.
    """
    try:
        opts = TokenAccountOpts(mint=mint_address)
        resp = await client.get_token_accounts_by_owner(central_wallet,opts)
        resp  = resp.to_json()
        resp = json.loads(resp)

        token_account_address = resp['result']['value'][0]['pubkey']
        print(token_account_address)
        return token_account_address
    except Exception as e:
        
        print(f"Error: {e}")
class TransactionCreator:
    def __init__(self, token_account_address):
        self.token_account_address = token_account_address
        
    
    async def generate_memo(txn_number: str, seller_email: str, buyer_email: str, trs_count: int, seller_uuid: str, buyer_uuid: str) -> str:
        """
        Generates a memo string for a Solana transaction that includes a PayPal transaction number, seller and buyer information, 
        and the number of TRS. If the memo exceeds 500 bytes, the function will remove email addresses and use UUIDs.
        
        Args:
        - txn_number: PayPal transaction number.
        - seller_email: Seller's email address.
        - buyer_email: Buyer's email address.
        - trs_count: Number of TRS (items).
        - seller_uuid: UUID for the seller.
        - buyer_uuid: UUID for the buyer.
        
        Returns:
        - memo: A UTF-8 encoded string under 500 bytes.
        """
        
        # Memo template with both emails
        memo = f"txn={txn_number},buyer={buyer_email},seller={seller_email},number={trs_count},buyer_uuid={buyer_uuid},seller_uuid={seller_uuid}"
        
        # Check if the memo size is under 500 bytes when UTF-8 encoded
        if len(memo.encode('utf-8')) <= 500:
            return memo
        
        # If emails make the memo exceed 500 bytes, remove them and stick to UUIDs
        memo = f"txn={txn_number},items={trs_count},buyer_uuid={buyer_uuid},seller_uuid={seller_uuid}"
        logger.info(f"Created memo {memo}")
        return memo
          
    async def send_transaction(self,txn_number,seller_email,buyer_email,trs_count,seller_uuid,buyer_uuid):
        txn = Transaction()
        
        memo_params = MemoParams(
            program_id = MEMO_PROGRAM_ID,
            message= await self.generate_memo(txn_number,seller_email,buyer_email,trs_count,seller_uuid,buyer_uuid),
            signer = central_wallet,
        )
        memo = create_memo(memo_params)
        txn.add(memo)
        transferparams = TransferParams(
            program_id=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'),
            source = self.token_account_address,
            dest = self.token_account_address,
            owner = central_wallet,
            amount = 1,
            signers = []
        )
        txn.add(
            transfer(transferparams)
        )
        response = await client.send_transaction(txn,central_wallet_keypair)
        
        logger.info(F"Transaction hash: {response}")
    


async def transaction(data):
    
    e = TransactionCreator(data['token_account_address'])
    
    await e.send_transaction(
        data['transaction_number'],
        data['seller_email'],
        data['buyer_email'],
        data['trs_count'],
        data['seller_id'],
        data['buyer_id']
    )
    logger.log(f"Created and signed transaction for {data['transaction_number']}")
    return {"message": "Created and signed transaction successfully"}
    
 


#asyncio.run(main())

