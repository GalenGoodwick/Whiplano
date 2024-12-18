

from fastapi import APIRouter, Depends, HTTPException

from app.utils.utils import get_current_user
from app.core.database import database_client
from app.utils.models import User


from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("user")


router = APIRouter()

@router.get("/users/me", response_model=User, tags=["User"],summary="Returns the current user", description="Returns the current user.")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retrieve the current user's information.

    This function retrieves the current user's information from the FastAPI endpoint '/users/me'.
    It uses the 'get_current_user' function as a dependency to authenticate and authorize the user.
    If the user is authenticated and authorized, the function returns the user's information.

    Parameters:
    current_user (User): The current user's information. This parameter is obtained from the 'get_current_user' function.

    Returns:
    User: The current user's information.
    """
    
    return current_user


@router.get('/wallet/get', dependencies=[Depends(get_current_user)],tags=["User"], description="Returns a formatted wallet, as a JSON with created TRS, TRS on marketplace, and TRS with artisan rights.")
async def wallet_get(user: User = Depends(get_current_user)):
    """
    This function retrieves and formats the wallet of the current user. The wallet includes
    the created TRS, TRS on the marketplace, and TRS with artisan rights.

    Parameters:
    user (User): The current user. This parameter is obtained from the 'get_current_user' function.

    Returns:
    dict: A dictionary representing the formatted wallet. The dictionary contains the following keys:
        - created_trs: A list of TRS created by the user.
        - trs_on_marketplace: A list of TRS on the marketplace.
        - trs_with_artisan_rights: A list of TRS with artisan rights.
    """
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        final_wallet = {}
        
        for trs in wallet['trs']:
            if trs['collection_name'] in final_wallet.keys():
                final_wallet[trs['collection_name']]['number'] +=1 
                if trs['artisan'] == 1:
                    final_wallet[trs['collection_name']]['artisan'] +=1
                elif trs['marketplace'] == 1:
                    final_wallet[trs['collection_name']]['marketplace'] +=1 
                elif trs['creator'] == user.id:
                    final_wallet[trs['collection_name']]['created'] = True
            else:
                collection_data = await database_client.get_collection_data(trs['collection_name'])
                final_wallet[trs['collection_name']] = {'number': 1, 'created': False, 'artisan': 0,'marketplace': 0,'data':collection_data}
                if trs['artisan'] == 1:
                    final_wallet[trs['collection_name']]['artisan'] +=1
                elif trs['marketplace'] == 1:
                    final_wallet[trs['collection_name']]['marketplace'] +=1 

        return final_wallet
    except Exception as e:
        logger.error(f"Error fetching wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/artisan/activate',dependencies=[Depends(get_current_user)],tags=["User"],summary="Activates artisan rights for a user's TRS",description="Activates artisan rights for a user's TRS")
async def artisan_activate(collection_name: str, number: int, user: User = Depends(get_current_user)) -> dict:
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        for i in wallet['trs']: 
            logger.debug(i)
            if i['collection_name'] == collection_name and i['marketplace'] == 0 and i['artisan'] == 0:
                req_wallet.append(i)

        if len(req_wallet) >= number:
            values = []
            for i in req_wallet[:number]:
                values.append((i['trs_id'],))
            await database_client.activate_artisan_trs(values, user.id)

            return {"message": "Artisan rights activated. "}
        else:
            return {"message": F"Insufficient TRS of {collection_name} in wallet."}
    except Exception as e:
        logger.error("Error in activating artisan rights on trs. ", e)
        raise HTTPException(status_code = 500, detail = e)
    


@router.post('/artisan/deactivate',dependencies=[Depends(get_current_user)],tags=["User"],summary="Deactivates artisan rights for a user's TRS",description="Deactivates artisan rights for a user's TRS")
async def artisan_deactivate(collection_name: str, number: int, user: User = Depends(get_current_user)) -> dict:
    try:
        wallet = await database_client.get_wallet_formatted(user.id)
        req_wallet = []
        for i in wallet['trs']: 
            if i['collection_name'] == collection_name and i['marketplace'] == 0 and i['artisan'] == 1:
                req_wallet.append(i)
        if len(req_wallet) >= number:
            values = []
            for i in req_wallet[:number]:
                values.append((i['trs_id'],))
            await database_client.deactivate_artisan_trs(values, user.id)

            return {"message": f"Artisan rights deactivated for the trs {collection_name}"}
        else:
            return {"message": f"Insufficient TRS of {collection_name} in wallet."}
        
    except Exception as e:
        logger.error("Error in deactivating artisan rights for trs. ", e)
        raise HTTPException(status_code = 500, detail = e)
    
