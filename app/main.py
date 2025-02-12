from fastapi import FastAPI
import os  
import logging
ROYALTY  = 2.5
FEES = 2.5
from app.core.database import  database_client
from fastapi.middleware.cors import CORSMiddleware
# Initialize logging
from app.utils.logging_config import logging_config  # Import the configuration file
import logging.config
logging.config.dictConfig(logging_config)
logger = logging.getLogger("main")

from app.utils.utils import SERVER_URL
from app.api import admin,auth,marketplace,transactions,trs,user
app = FastAPI(
    title="Whiplano API",
    description="The API used for the IP platform Whiplano",
    version="0.1.1",
    contact={
        "name": "Dan",
        "email": "danielvincent1718@gmail.com",
    }
)
whiplano_id = '0000-0000-0000'

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
)


GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = SERVER_URL + "/callback/google"

app.include_router(auth.router,tags=["Authentication"])
app.include_router(admin.router,tags=["Admin"])
app.include_router(marketplace.router,tags=["Marketplace"])
app.include_router(transactions.router,tags=["Transactions"])
app.include_router(trs.router,tags=["TRS"])
app.include_router(user.router,tags=["User"])

@app.get("/")
async def root():
    """
    This function is the root endpoint of the application. It checks if the application is running.

    Parameters:
    None

    Returns:
    dict: A dictionary containing a success message.
        - message (str): "App is running."
    """
    logger.info("App is running.")
    return {"message": "App is running."}

@app.on_event("startup")
async def startup_event():
    await database_client.init_pool()
