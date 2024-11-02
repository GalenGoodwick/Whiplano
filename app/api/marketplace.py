from fastapi import APIRouter, Depends, HTTPException

from app.utils.utils import get_current_user
from app.core.database import database_client
from app.utils.models import User

from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("marketplace")

router = APIRouter()


@router.get('/marketplace',tags=["Marketplace"],summary="Fetches the marketplace",description="Fetches all the martketplace entries, along with the respective data. ")
async def marketplace():
    """
    Retrieves all TRS currently listed on the marketplace.

    Returns:
    list: A list of dictionaries, where each dictionary represents a TRS on the marketplace.
          Each dictionary contains the following keys:
          - trs_id: The unique identifier of the TRS.
          - collection_name: The name of the collection to which the TRS belongs.
          - owner_id: The unique identifier of the owner of the TRS.
          - price: The price of the TRS on the marketplace.

    """
    try:
        trs_on_marketplace = await database_client.get_marketplace_all()
        return trs_on_marketplace
    except Exception as e:
        logger.error(f"Error fetching marketplace: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get('/marketplace/collection',tags=["Marketplace"],summary="Fetches the marketplace for one collection",description="Fetches the martketplace entries for one specific collection, along with the respective data. ")
async def marketplace_collection(collection_name: str):
    """
    Retrieves all TRS of a specific collection currently listed on the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    """
    try:
        trs_on_marketplace = await database_client.get_marketplace_collection(collection_name)
        
        return trs_on_marketplace
    except Exception as e:
        logger.error(f"Error fetching marketplace for collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/marketplace/place',dependencies=[Depends(get_current_user)],tags=["Marketplace"],summary="Adds TRS to the marketplace",description="Adds TRS to the martketplace from a users wallet.  ")
async def marketplace_add(collection_name: str, number: int,price:int, user: User = Depends(get_current_user)) -> dict:
    """
    This function adds TRS of a specific collection to the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    number (int): The number of TRS to be added to the marketplace.
    price (int): The bid price for the TRS in the marketplace.
    user (User): The user making the request. This parameter is obtained from the 'get_current_user' function.

    Returns:
    dict: A dictionary containing a success message if the TRS are added to the marketplace successfully.
        - message (str): "TRS added to marketplace successfully."
    """
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        
        for i in wallet['trs']: 
            
            if i['collection_name'] == collection_name and i['marketplace'] == 0 and i['artisan'] == 0:
                req_wallet.append(i)

        if len(req_wallet) >= number:   
            values = []
            values2 = []
            for i in req_wallet[:number]:
        
                values.append((i['trs_id'],collection_name,'sell', user.id,price))
                values2.append((i['trs_id'],))
            await database_client.add_trs_to_marketplace(user.id,values,values2,i['collection_name'])

            return {"message": "TRS added to marketplace successfully."}
        else:
            return {"message": F"Insufficient TRS of {collection_name} in wallet."}
    except Exception as e:
        logger.error("Error in adding trs to marketplace", e)
        raise HTTPException(status_code = 500, detail = e)

@router.post('/marketplace/remove',dependencies=[Depends(get_current_user)],tags=["Marketplace"],summary="Removes TRS from the marketplace",description="Removes TRS from the martketplace from a users wallet.  ")
async def marketplace_remove(collection_name: str, number: int, user: User = Depends(get_current_user)) -> dict:
    """
    This function removes TRS of a specific collection from the marketplace.

    Parameters:
    collection_name (str): The name of the collection.
    number (int): The number of TRS to be removed from the marketplace.
    user (User): The user making the request. This parameter is obtained from the 'get_current_user' function.

    Returns:
    dict: A dictionary containing a success message if the TRS are removed from the marketplace successfully.
        - message (str): "TRS removed from marketplace successfully."
    If there are not enough TRS in the user's wallet for the specified collection, the function returns:
        - message (str): "Insufficient TRS of {collection_name} in wallet."
    """
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        for i in wallet['trs']: 
            if i['collection_name'] == collection_name and i['marketplace'] == 1 and i['artisan'] == 0:
                req_wallet.append(i)

        if len(req_wallet) >= number:
            values = []
            for i in req_wallet[:number]:
                values.append((i['trs_id'],))
            await database_client.remove_trs_from_marketplace(values,user.id)

            return {"message": "TRS removed from marketplace successfully."}
        else:
            return {"message": F"Insufficient TRS of {collection_name} in wallet."}
    except Exception as e:
        logger.error("Error in removing trs from marketplace", e)
        raise HTTPException(status_code = 500, detail = e)


