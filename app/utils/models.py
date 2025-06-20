
from pydantic import BaseModel,Field,EmailStr
from datetime import datetime, timedelta,date
from typing import Optional

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    
class NFTData(BaseModel):
    collection_name: str = Field(..., description="Name of the collection") 
    collection_description: str = Field(..., description="Description of the collection")
    collection_symbol: str = Field(..., description="Symbol of the collection")
    number: int = Field(..., description="Number of TRSs")
    uri: str = Field(..., description="URI of the NFT")
    creator_id: str = Field(..., description="ID of the creator")

class CreatePaymentData(BaseModel):
    amount : int =  Field(..., description="Amount")
    cancel_url : str = Field(..., description="URL for the user to be redirected to when the payment is cancelled. ")
    description : str = Field(...,description="Description of the payment for Paypal.")

class BlockChainTransactionData(BaseModel):
    transaction_number : str = Field(..., description = "Transaction number of the paypal transaction to be stored on the chain. ")

class MintTrsData(BaseModel):
    collection_name : str = Field(..., description = "Name of the collection")
    collection_description : str = Field(..., description = "Description of the collection")
    number : int = Field(..., description = "Number of TRSs")
    uri : str = Field(..., description="URI of the NFT")
   
class TradeCreateData(BaseModel):
    collection_name : str = Field(..., description = "Name of the collection to be bought")
    number : int = Field(..., description = "Number of TRSs to be traded") 
    cost : float = Field(..., description = "Cost of one TRS")

class KYCData(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    address: str
    identity_type: str  # 'passport' or 'national_id' or 'driver's license'
    address_proof_type : str # 'utility bill' or anything else. 

class Metadata(BaseModel):
    title: str
    description: str

class User(BaseModel):
    username: Optional[str] = None
    email: str
    id: str
    bio: Optional[str] = None
    telegram: Optional[str] = None
    pfp_uri: Optional[str] = None
    twitter: Optional[str] = None
    artisan: bool
    creator: bool
    admin: bool
    verified: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class LoginToken(BaseModel):
    access_token: str
    token_type: str
    info : dict

class Token(BaseModel):
    access_token: str
    token_type: str    
class SignupToken(BaseModel):
    access_token: str
    token_type: str
    is_verified:bool
    has_onboarded:bool
class TokenData(BaseModel):
    username: str