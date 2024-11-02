from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List
from app.utils.utils import get_current_user
from app.core.database import database_client
from app.utils.models import User
from app.core import storage

from app.core import storage
from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("trs")

router = APIRouter()



@router.post("/create_trs_request", dependencies=[Depends(get_current_user)],tags=["TRS"], summary="Creates TRS", description="Makes a TRS Creation request, with all the given data.")
async def create_trs_request(
    current_user: User = Depends(get_current_user),
    model_name: str = Form(...),
    title: str = Form(...),
    description : str = Form(...),
    files: List[UploadFile] = File(...),
    image: UploadFile = File(...),
    number:int = Form(...)
):
    """
    This function creates a TRS creation request by uploading files to a storage service,
    and storing the request details in a database.

    Parameters:
    current_user (User): The user making the TRS creation request. This parameter is obtained from the 'get_current_user' function.
    model_name (str): The name of the model used for creating the TRS.
    metadata (Metadata): The metadata associated with the TRS creation request.
    files (List[UploadFile]): The files associated with the TRS creation request.
    number (int): The number of TRS to be minted. Currently only a placeholder. 
    Returns:
    JSONResponse: A JSON response indicating the success or failure of the TRS creation request.
        - status_code (int): The HTTP status code of the response.
        - content (dict): The content of the response. It contains a message indicating the success or failure of the request.

    Raises:
    HTTPException: If an error occurs during the TRS creation request.
    """
    if len(files) > 10:
        return JSONResponse(status_code=400, content={"message": "A maximum of 10 files can be uploaded."})
    exist = await database_client.check_collection_exists(title)
    pend_request = await database_client.get_trs_creation_requests('pending')
    confirmed_request = await database_client.get_trs_creation_requests('approved')
    all_request = pend_request + confirmed_request
    for request in all_request: 
        if request['title'] == title:
            raise HTTPException(status_code=409, detail = "There is already a TRS creation request in this Title.")
    if exist: 
        raise HTTPException(status_code=409, detail = "Collection already exists.")
    try:
        
        file_urls = []
        for file in files:
            file_url = await storage.upload_to_s3(file,f'trs_data/{title}/{file.filename}')
            file_urls.append(file_url)
        image_url = await storage.upload_to_s3(image, f'trs_data/{title}/thumbnail.png')
        file_url_header =  f'trs_data/{title}/'

        await database_client.add_trs_creation_request(model_name,title,description,current_user.email, file_url_header)

        return JSONResponse(status_code= 200, content = {"message":"Trs creation request submitted succesfully. "})
    except Exception as e:
        return HTTPException(status_code = 500, detail = str(e))
