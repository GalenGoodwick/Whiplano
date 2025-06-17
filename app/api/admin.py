from fastapi import APIRouter, Depends, HTTPException
from app.utils.utils import get_current_user
from app.core.database import database_client
from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("admin")

router = APIRouter()


@router.post("/admin/add",tags=["Admin"], summary="Adds an admin", description="Updates a user to be an Admin. ")
async def add_admin(email: str, dependencies = [Depends(get_current_user)]) -> str:
    """
    This function adds a new admin user to the system.

    Parameters:
    email (str): The email of the admin user to be added.
    dependencies (list): A list of dependencies required for the function to execute.
        In this case, it depends on the current user being authenticated.

    Returns:
    str: A success message indicating that the admin user has been added to the system.
    """
    return await database_client.add_admin(email)

@router.get("/admin/creation_requests",dependencies = [Depends(get_current_user)],tags=["Admin"], summary="For getting the TRS creation requests", description="Returns the list of TRS creation requests currently pending for admins to approve. ")
async def admin_creation_requests():
    try:
        data = await database_client.get_trs_creation_requests('pending')
        logger.debug(data)
        return data
    except Exception as e: 
        return HTTPException(status_code= 500, content= e)
    

@router.post("/admin/approve",dependencies = [Depends(get_current_user)],tags = ["Admin"],summary = "For approving TRS creation requests, and minting the TRS")
async def admin_approve(id: int):

    try:
        number = 1000
        trs_creation_data = await database_client.get_trs_creation_data(id)
        logger.debug(trs_creation_data)
        trs_creation_data = trs_creation_data[0]
        exist = await database_client.check_collection_exists(trs_creation_data['title'])
        if exist: 
            raise HTTPException(status_code= 409, detail = "Collection already exists.")   
        #mint_address = await mint.mint(trs_creation_data['title'],trs_creation_data['description'],number,trs_creation_data['creator_email'])
        #token_account_address = await transaction_module.get_token_account_address(Pubkey.from_string(mint_address))
        await database_client.approve_trs_creation_request(id,trs_creation_data['creator_email'],number,"e",trs_creation_data['title'],"e")
        return {"message":"TRS Succesfully created. "}
    except Exception as e: 
        logger.error(f"Error {e}")
        raise HTTPException(status_code = 500,detail=e)
