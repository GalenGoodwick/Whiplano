from fastapi import APIRouter, Depends, HTTPException,Query
from typing import Optional
from app.utils.utils import get_current_user
from app.utils.utils import SERVER_URL
from app.core.database import database_client
from app.utils.models import User,TradeCreateData
from app.fintech import paypal
import uuid
from decimal import Decimal
from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("transactions")

router = APIRouter()


whiplano_id = '0000-0000-0000'
ROYALTY  = 2.5
FEES = 2.5

@router.post('/trade/create',dependencies=[Depends(get_current_user)],tags=['Transactions'],summary="Creates a trade.",description="Creates a trade, adds it to the pending trades database, creates a paypal transaction")
async def trade_create(data : TradeCreateData,buyer : User = Depends(get_current_user)):

    mrktplace_collection = await database_client.get_marketplace_collection(data.collection_name)
    number_of_trs = 0
    for i in mrktplace_collection:
        if i['collection_name'] == data.collection_name and i['bid_price']  == data.cost:
            number_of_trs = i['number_of_trs']
    if number_of_trs < data.number:
        logger.info("Not enough TRS being offered by the sellers at the given price. ")
        raise HTTPException(status_code=400, detail="Not enough TRS being offered by the sellers at the given price. ")
    else: 
        try:
            description = f"Buy order for {data.number} TRS of {data.collection_name}. Price per TRS = {data.number}, Total Amount = {(data.number*data.cost)}"
            data_transac = {
                'collection_name':data.collection_name,
                'cancel_url' : "https://example.com",
                "description": description,
                "return_url": SERVER_URL + "/trade/execute_payment",
                'amount' :   (data.number)*(data.cost)
            }
            try:
                resp = await paypal.create_payment(data_transac)
                
                amount = data.number*data.cost
                await database_client.add_paypal_transaction(resp['id'],buyer.id,whiplano_id,amount)
                logger.info(f"Payment created succesfully with id {resp['id']}")
                trade_create_data = await database_client.trade_create(resp['id'], data.cost,data.number,data.collection_name,buyer.id)

                        

                return {"message": "Payment created successfully.",
                        'approval_url': resp['links'][1]['href']}
                
            except Exception as e:
                raise HTTPException(status_code=501, detail=str(e))
            


        except HTTPException as e:
            logger.error(e)
            raise e
        except Exception as e: 
            logger.error(e)
            raise HTTPException(status_code = 500, detail=e)
        
        
        


@router.get('/trade/execute_payment',tags =['Transactions'],summary='Executes the trade.',description='Executes the buyer transaction, sends payouts, transafers assets, and Finalizes the trade.')
async def execute_payment(
    paymentId: Optional[str] = Query(None), 
    PayerID: Optional[str] = Query(None),
):
    """
    This function executes a PayPal payment with the given payment ID and Payer ID.
    It retrieves the payment details, modifies the payment status in the database,
    approves initiated transactions, retrieves approved transactions, and processes
    the transactions by executing payouts, updating the transaction records, and
    transferring assets between users.

    Parameters:
    paymentId (str, optional): The ID of the PayPal payment.
    PayerID (str, optional): The ID of the PayPal Payer.

    Returns:
    dict: A dictionary containing a success message if the payment is executed successfully.
        - message (str): "Completed Trade with buyer transaction number {paymentId}"

    Raises:
    HTTPException: If an error occurs during the payment execution.
    """
    try:
        resp = await paypal.execute_payment(paymentId,PayerID)
        logger.info(f"Executed payment with id {paymentId}")
        await database_client.modify_paypal_transaction(paymentId,'executed')
        batch_id = str(uuid.uuid4)
        seller_data = await database_client.execute_trade(paymentId)
        logger.info(f"Trade executed with id {paymentId}")
        token_account_address = None
        for seller in seller_data:
            amount = Decimal(seller['cost']) * Decimal(seller['number'])
            amount1 = amount * (Decimal(100-ROYALTY+FEES)/Decimal(100))
            amount2 = amount * (Decimal(ROYALTY)/Decimal(100))
            payout_info = {
                    "batch_id":batch_id,
                    "recipient_email":seller['seller_email'],
                    "amount":str(amount1),
                    "currency":"USD",
                    "note": f"Payment to {seller['seller_email']} for TRS of collection {seller['collection_name']}. "
                }
            await paypal.payout(payout_info)
            logger.info(f"Paypal payout sent to {seller['seller_email']}. ")
            royalty_payout_info = payout_info = {
                    "batch_id":batch_id,
                    "recipient_email":seller['seller_email'],
                    "amount":str(amount2),
                    "currency":"USD",
                    "note": f"Royalty for {seller['creator_email']} for trade of TRS of collection {seller['collection_name']}. "
                }
            if not token_account_address:
                token_account_address = 1
            else: 
                token_account_address,mint_address = await database_client.get_token_account_address(seller['collection_name'])
            data = {
                "transaction_number":paymentId,
                "buyer_id": seller['buyer_id'],
                "seller_id": seller['seller_id'],
                "seller_email": seller['seller_email'],
                "buyer_email":seller['buyer_email'],
                "trs_count": seller['number'],
                'token_account_address':token_account_address,
                'mint_address':mint_address
            }
            #await dac.transfer(mint_address, seller['seller_email'],seller['buyer_email'],seller['number'])
            #await transaction_module.transaction(data)
            logger.info(f"Sent transaction to complete trade {paymentId}")
            
        logger.info(f"Completed Trade with buyer transaction number {paymentId}")
        return {"message": f"Completed Trade with buyer transaction number {paymentId}"}



    except Exception as error:
        logger.error(f"Error executing transaction {paymentId} {error}")
        raise HTTPException(status_code=500, detail=str(error))



