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


client = AsyncClient("https://api.devnet.solana.com")

with open('./central_wallet.json') as file:
    secret_key = json.load(file)

central_wallet = Pubkey.from_string("9QVeLdhziTQBFSTNWQxbzhwzQYgmcH4vT8GPsWqDBQFj")
central_wallet_keypair = Keypair.from_bytes(secret_key)


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
    def __init__(self, token_account_address, transaction_details):
        self.token_account_address = token_account_address
        self.transaction_details = transaction_details
    
    async def memo_creator(self):
        text = bytes(self.transaction_details,encoding ='utf-8')
        params = MemoParams(
            program_id = MEMO_PROGRAM_ID,
            message= text,
            signer = central_wallet,
        )
        return create_memo(params)
          
    async def send_transaction(self):
        txn = Transaction()
        memo = await self.memo_creator()
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
        
        print(F"Transaction hash: {response}")
    
    async def transaction(self):
        payment_recieved = True #Wait for confirmation.
        payment_sent = True #Wait for confirmation.
        royalty_sent = True #Wait for confirmation.
        await self.send_transaction()

        transaction_number_1 = self.transaction_details['transaction_number_1']
        transaction_number_2 = self.transaction_details['transaction_number_2']
        transaction_number_3 = self.transaction_details['transaction_number_3']

        amount = self.transaction_details['amount']

            
    
        return 
    

 




async def main():
    e = TransactionCreator(Pubkey.from_string('EhKdZDMYs4PnYurXaz1fCYfkpnDxdzEZBc2SNEF8B8HS'),'hello')
    await e.create_transaction()
    await client.close()
    



#asyncio.run(main())

