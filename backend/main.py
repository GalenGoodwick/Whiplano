from fastapi import FastAPI, HTTPException, Query
from backend import database, mint, paypal, transaction, utils
from typing import Optional

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "App is running."}

@app.post("/mint")
async def mint_nft(data : dict):
    try:
        
        mint.mint_nft(data)
        return {"message": "NFT minted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/paypal/create_payment")
async def paypal_payment(data : dict):
    
    try:
        data['return_url'] = "http://localhost:8000/paypal/execute_payment"
        await paypal.create_payment(data)
        return {"message": "Payment successful."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/paypal/execute_payment')
async def execute_payment(
    paymentId: Optional[str] = Query(None), 
    PayerID: Optional[str] = Query(None),
    token: Optional[str] = Query(None)
):

    print(paymentId,token,PayerID)
    print("hi")
    await paypal.execute_payment(paymentId,PayerID)
    
@app.get('/paypal/payout')
async def payout(data : dict):
    try:
        e = await paypal.payout(data)
        return {"message": "Payout successful."}
    except Exception as e:
        print('e')
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post('/transaction/create')
async def transaction(data: dict):
    return 

