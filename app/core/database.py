import asyncmy
import asyncio
import uuid
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from app.core import storage
import os 
import dotenv
import random
from datetime import datetime
dotenv.load_dotenv()

import logging.config
from app.utils.logging_config import logging_config 
logging.config.dictConfig(logging_config)
logger = logging.getLogger("database")

class DatabaseManager:
    def __init__(self):
        self.pool = None
        logger.info("Database Instance Created Successfully. ")
    async def init_pool(self):
        """Initialize the database connection pool."""
        self.pool = await asyncmy.create_pool(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME"),
            minsize=5,
            maxsize=10, 
            echo=True
        )
        logger.info("Initialized Connection Pool successfully. ")
    async def get_connection(self):
        """
        Acquires a connection from the pool with retry logic.

        Returns:
        - Connection object
        """ 
        retries = 5
        for attempt in range(retries):
            try:
                # Check if the pool is initialized
                if self.pool is None:
                    logger.error("Connection pool is not initialized!")
                    raise HTTPException(status_code=500, detail="Connection pool is not initialized.")
                
                return await self.pool.acquire()

            except Exception as e:
                logger.error(f"Error acquiring connection (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:  # Not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("Failed to acquire connection after retries.")
                    raise HTTPException(status_code=500, detail="Database connection error. Please try again later.")
    
    async def login_user(self, user_id=None, email=None):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    if user_id is not None:
                        query = "UPDATE users set last_login = %s where user_id = %s"
                        await cursor.execute(query, (datetime.now(), user_id))
                        await connection.commit()
                        logger.info(f"Last login updated for user {user_id}")
                    else:
                        query = "UPDATE users set last_login = %s where email = %s"
                        await cursor.execute(query, (datetime.now(), email))
                        await connection.commit()
                        logger.info(f"Last login updated for user {email}")
                except:
                    logger.error("Failed to update last_login for user. ")
                
    async def add_user(self,email, password_hash):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    user_id = str(uuid.uuid4())
                    query = "INSERT INTO users (user_id, email, password_hash) VALUES (%s, %s, %s)"
                    values = (user_id, email, password_hash)
                    await cursor.execute(query, values)

                    await connection.commit()
                    logger.info(f"User {email} with id {user_id} added successfully")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def get_user(self, user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    query = "SELECT * FROM users WHERE user_id = %s"
                    await cursor.execute(query, (user_id,))
                    result = await cursor.fetchone()
                    if result:
                        columns = [column[0] for column in cursor.description]
                        user = dict(zip(columns, result))
                        return user
                    else:
                        return None
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    
    async def get_user_by_email(self, email):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    query = "SELECT * FROM users WHERE email = %s"
                    await cursor.execute(query, (email,))
                    result = await cursor.fetchone()
                    if result:
                        columns = [column[0] for column in cursor.description]
                        user = dict(zip(columns, result))
                        try:
                            logger.info(f"Fetched user {user['email']}")
                            return user
                        except:
                            logger.info(f"No such user. ")
                            return None
                    
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def update_user(self, user_id, username=None, email=None, password_hash=None):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    updates = []
                    values = []
                    if username:
                        updates.append("username = %s")
                        values.append(username)
                    if email:
                        updates.append("email = %s")
                        values.append(email)
                    if password_hash:
                        updates.append("password_hash = %s")
                        values.append(password_hash)
                    if not updates:
                        logger.warn("No updates provided")
                        return
                    query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
                    values.append(user_id)
                    await cursor.execute(query, tuple(values))
                    await connection.commit()
                    logger.info(f"User {user_id} updated successfully")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def delete_user(self, user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "DELETE FROM users WHERE user_id = %s"
                    await cursor.execute(query, (user_id,))
                    await connection.commit()
                    logger.info(f"User {user_id} deleted successfully")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def add_asset(self, values):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = f"INSERT INTO trs (user_id,trs_id,collection_name,creator) VALUES (%s, %s,%s,%s)"

                    await cursor.executemany(query, values)
                    await connection.commit()
                    logger.info(f"Tokens added succesfully. ")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
        
    async def get_owner(self, trs_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "SELECT user_id FROM trs WHERE trs_id = %s"
                    await cursor.execute(query, (trs_id,))
                    result1 = await cursor.fetchone()
                    if result1:
                        columns = [column[0] for column in cursor.description]
                        result = dict(zip(columns, result))
                        return result
                    else:
                        return None
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def add_transaction(self, buyer_transaction_number, trs_id, buyer_id, seller_id, amount, number):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    transaction_number = str(uuid.uuid4())
                    query = f"INSERT INTO transactions (buyer_transaction_number,transaction_number,trs_id,buyer_id,seller_id,amount,number) VALUES (%s,%s, %s,%s,%s,%s)"
                    values = (buyer_transaction_number,transaction_number, trs_id, buyer_id, seller_id, amount, number)
                    await cursor.execute(query, values)
                    await connection.commit()
                    logger.info(f"Transaction {transaction_number} and buyer transaction number {buyer_transaction_number} added successfully")
                    
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def modify_transaction(self, transaction_number,status):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = f"UPDATE transactions set status = %s  where transaction_number = %s "
                    values = (status,transaction_number)
                    await cursor.execute(query, values)
                    await connection.commit()
                    logger.info(f"Transaction {transaction_number} modified successfully to {status}")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def transfer_asset(self, user_id, trs_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = f"UPDATE trs SET user_id = %s WHERE trs_id = %s"

                    await cursor.execute(query, (user_id, trs_id))
                    logger.info(f"Transferred TRS {trs_id} to {user_id}.")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    

            
    async def add_trs(self,number, mint_address, collection_name, token_account_address,creator_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    batch_values = []
                    trs_id_values = []
                    for i in range(number):
                        trs_id = uuid.uuid4().int
                        batch_values.append((str(trs_id), collection_name, str(mint_address), str(token_account_address),str(creator_id)))
                        trs_id_values.append((creator_id,trs_id,collection_name,creator_id))
                    query = f"INSERT INTO collections (trs_id, collection_name, mint_address, token_account_address,creator_id) VALUES (%s, %s, %s, %s,%s)"
                    await cursor.executemany(query,batch_values)
                    await connection.commit()
                    await self.add_asset(trs_id_values)       
                    logger.info(f"Added {number} tokens of collection name {collection_name} to {creator_id}.")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def add_paypal_transaction(self, transaction_number, buyer_id, seller_id, amount):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = f"INSERT INTO paypal_transactions (transaction_id, buyer_id, seller_id, amount) VALUES (%s,%s,%s,%s)"
                    values = (str(transaction_number), str(buyer_id), str(seller_id), amount)

                    await cursor.execute(query, values)
                    await connection.commit()
                    logger.info(f"Added PayPal transaction with transaction number {transaction_number}")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error adding paypal transaction: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def modify_paypal_transaction(self,transaction_id,status): 
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try: 
                    
                    query = f"UPDATE paypal_transactions SET status = %s WHERE transaction_id = %s"
                    values = (str(status),str(transaction_id))
                    await cursor.execute(query, values)
                    await connection.commit()
                    logger.info(f"Updated paypal transaction {transaction_id} to {status} ")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error updating paypal transaction : {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def get_wallet(self, user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        
                        query = "SELECT trs_id,collection_name FROM trs WHERE user_id = %s"
                        await cursor.execute(query, (user_id,))
                        result1 = await cursor.fetchall()
                        columns = [column[0] for column in cursor.description]
                        result = [dict(zip(columns, row)) for row in result1]
                        logger.info(f"Returned wallet of user {user_id}")
                        return result
                    except Exception as e:
                        await connection.rollback()
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
    
    async def get_collection_data(self,name):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "SELECT * FROM collection_data WHERE name = %s"
                    await cursor.execute(query, (name,))
                    result1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    result = [dict(zip(columns, row)) for row in result1]
                    return result
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def get_approved_transactions(self,buyer_transaction_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "SELECT * FROM transactions WHERE buyer_id = %s AND status = %s"
                    await cursor.execute(query, (buyer_transaction_id, "initiated"))
                    result1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    result = [dict(zip(columns, row)) for row in result1]
                    logger.info(f"Retrieved approved transactions for buyer {buyer_transaction_id}")
                    return result
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
        
    
    
    async def approve_initiated_transactions(self,buyer_transaction_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "UPDATE transacations SET status = 'approved' where buyer_id = %s AND status = 'initiated'"
                    await cursor.execute(query, (buyer_transaction_id, ))
                    result = await cursor.fetchall()
                    logger.info(f"Approved initiated transactions for buyer {buyer_transaction_id}")
                    await connection.commit()
                    return True
                    
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))


    
    async def finish_approved_transactions(self,buyer_transaction_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "UPDATE transacations SET status = 'finished' where buyer_id = %s AND status = 'initiated'"
                    await cursor.execute(query, (buyer_transaction_id, ))
                    
                    logger.info(f"Finished approved transactions for buyer {buyer_transaction_id}")
                    await connection.commit()
                    return True
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    
    async def get_wallet_by_collection(self,user_id,collection_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                if not await self.get_user(user_id):
                    logger.error(f"User not found {user_id}")
                    return None
                else:
                    try:
                        
                        query = "SELECT trs_id, collection_name FROM trs WHERE user_id = %s AND collection_name = %s"
                        await cursor.execute(query, (user_id, collection_id))
                        result1 = await cursor.fetchall()
                        columns = [column[0] for column in cursor.description]
                        result = [dict(zip(columns, row)) for row in result1]
                        logger.info(f"Selected wallet by collection {collection_id}, from {user_id}")
                        return result
                    except Exception as e:
                        await connection.rollback()
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
            
    async def get_mint_address(self,collection_name):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
        
                try:
                    
                    query = "SELECT mint_address FROM collections WHERE collection_name = %s"
                    await cursor.execute(query, (collection_name,))
                    result1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    result = [dict(zip(columns, row)) for row in result1]
                    logger.info(f"Retrieved Mint Address by collection {collection_name}")
                    return result
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                
    
    
    async def get_creator(self,collection_name):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "SELECT creator_id FROM collections WHERE collection_name = %s LIMIT 1"

                    await cursor.execute(query, (collection_name,))
                    result1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    result = [dict(zip(columns, row)) for row in result1]
                    logger.info(f"Retrieved Creator id of collection {collection_name}")
                    return result['creator_id']
                
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
        
    async def get_wallet_formatted(self,user_id):

        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        
                        query = "SELECT trs_id,collection_name,creator,artisan,marketplace FROM trs WHERE user_id = %s"
                        await cursor.execute(query, (user_id,))
                        result1 = await cursor.fetchall()
                        columns = [column[0] for column in cursor.description]
                        result = [dict(zip(columns, row)) for row in result1]
                        created_trs = []
                        artisan_trs = []
                        marketplace_trs = []
                        none_trs = []
                        for i in result: 
                            if i['creator'] == user_id:
                                created_trs.append(i)
                            if i['marketplace'] == 1:
                                marketplace_trs.append(i)
                            elif i['artisan'] == 1:
                                artisan_trs.append(i)

                            none_trs.append(i)


                        logger.info(f"Returning formatted wallet for user {user_id} ")
                        return {
                            "created_trs": created_trs,
                            "artisan_trs":artisan_trs,
                            "marketplace_trs":marketplace_trs,
                            "trs": none_trs
                        }
                    except Exception as e:
                        await connection.rollback()
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
    async def add_trs_to_marketplace(self,user_id,values,values2, collection_name):

        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
        
                try: 
                    
                    query = "INSERT INTO marketplace (trs_id,collection_name,order_type,buyer_seller_id,bid_price) VALUES (%s,%s,%s,%s,%s)"

                    await cursor.executemany(query, values)
                    
                    query = "UPDATE trs set marketplace = 1 WHERE trs_id = %s"
                    
                    await cursor.executemany(query,values2)
                    await connection.commit()
                    logger.info(f"Added {len(values)} trs of collection {collection_name} to the Marketplace")
                    return {'message':f"Added trs {len(values)} of collection {collection_name} to the Marketplace"}


                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    async def remove_trs_from_marketplace(self, values,user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        
                        query = "DELETE FROM marketplace where trs_id = %s"

                        await cursor.executemany(query, values)
                        
                        query = "UPDATE trs set marketplace = 0 WHERE trs_id = %s"
                        await cursor.executemany(query,values)
                        await connection.commit()
                        logger.info(f"Removed trs from the Marketplace")
                        return {'message':f"Removed trs from the Marketplace"}


                    except Exception as e:
                        await connection.rollback()
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))


    async def get_marketplace_all(self):

        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
        
                try:
                    
                    query = "SELECT  collection_name, bid_price, COUNT(*) AS number_of_trs from  marketplace GROUP BY collection_name,bid_price "

                    await cursor.execute(query)
                    result1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    results = [dict(zip(columns, row)) for row in result1]
                    for collection in results: 
                        data = await self.get_collection_data(collection['collection_name'])
                        collection['collection_data'] = data
                        
                    logger.info(f"Entire Marketplace fetched successfully. ")
                    return results


                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    async def get_marketplace_collection(self, collection_name: str):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
        
                try:
                    
                    query = "SELECT  collection_name, bid_price, COUNT(*) AS number_of_trs from  marketplace WHERE collection_name = %s GROUP BY collection_name,bid_price "

                    await cursor.execute(query, (collection_name,))
                    result = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    results = [dict(zip(columns, row)) for row in result]
                    logger.info(f"Marketplace for collection {collection_name} fetched successfully. ")
                    return results
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                

    async def add_admin(self, email: str) -> None:
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "UPDATE users set role = 'admin' WHERE email = %s"

                    await cursor.execute(query, (email,))
                    await connection.commit()

                    logger.info(f"User {email} added to the admin list. ")

                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    
    async def verify_user(self, email: str) -> None:
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "UPDATE users set verified = 1 WHERE email = %s"

                    await cursor.execute(query, (email,))
                    await connection.commit()

                    logger.info(f"User {email} has been verified. ")

                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    
    async def activate_artisan_trs(self,values, user_id):

        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        query = "UPDATE trs set artisan = 1 WHERE trs_id = %s"
                        await cursor.executemany(query,values)
                        await connection.commit()
                        logger.info(f"Activated TRS rights for {user_id}")
                        return {'message':f"Activated TRS rights for {user_id}"}


                    except Exception as e:
                        await connection.rollback()
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))

    
    async def deactivate_artisan_trs(self,values, user_id):

        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        query = "UPDATE trs set artisan = 0 WHERE trs_id = %s"
                        await cursor.executemany(query,values)
                        await connection.commit()
                        logger.info(f"Deactivated artisan rights for TRS {user_id}")
                        return {'message':f"Deactivated artisan rights for TRS {user_id}"}


                    except Exception as e:
                        await connection.rollback()
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
            
    async def check_collection_exists(self,name):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:       
                    query = "SELECT  * from  collection_data where name = %s"
                    await cursor.execute(query, (name,))
                    result1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    results = [dict(zip(columns, row)) for row in result1]
                    if len(results) == 0:
                        logger.info(f"Collection {name} does not exist. ")
                        return False
                    else:
                        logger.info(f"Collection {name} does not exist. ")
                        return True
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                
    async def add_trs_creation_request(self,model_name,title,description,creator_email, file_url_header):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    query = "INSERT INTO trs_creation_requests (model_name, title, description, creator_email, file_url_header) VALUES (%s, %s, %s,%s,%s)"
                    values = (model_name,title, description, creator_email, file_url_header)
                    await cursor.execute(query, values)
                    await connection.commit()
                    logger.info(f"New TRS request submitted from {creator_email} with title {title}.")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def get_trs_creation_requests(self,status):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "SELECT * FROM trs_creation_requests WHERE status = %s"
                    await cursor.execute(query, (status,))
                    result1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    results = [dict(zip(columns, row)) for row in result1]
                    return results
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    
    
    async def get_trs_creation_data(self,id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "SELECT * FROM trs_creation_requests WHERE id = %s"
                    await cursor.execute(query, (id,))
                    results1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    results = [dict(zip(columns, row)) for row in results1]
                    return results
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                
    async def add_collection_data(self,name,creator,description,number,url_header):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    user_id = str(uuid.uuid4())
                    cid = storage.get_file_cid(f'{url_header}thumbnail.png')
                    image_uri = 'https://ipfs.filebase.io/ipfs/' + str(cid)
                    query = "INSERT INTO collection_data (name,creator, description, number, image_uri) VALUES (%s, %s, %s,%s,%s)"
                    
                    values = (name,creator,description,number,image_uri)
                    await cursor.execute(query, values)
                    await connection.commit()
                    logger.info(f"Collection data has been added for {name} . ")
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                    
            
    async def approve_trs_creation_request(self,id,creator_email,number,mint_address,collection_name,token_account_address):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try: 
                    q1 = "select * from trs_creation_requests where id = %s"
                    query = "UPDATE trs_creation_requests set status = 'approved' WHERE id = %s"
                    await cursor.execute(query,(id,))
                    logger.info(f"Approved TRS creation request {id}")
                    creation_data = await self.get_trs_creation_data(id)
                    logger.info(creation_data)
                    creation_data = creation_data[0]
                    await self.add_collection_data(creation_data['title'],creator_email,creation_data['description'],number,creation_data['file_url_header'])
                    creator_id = await self.get_user_by_email(creator_email)
                    creator_id = creator_id['user_id']
                    await self.add_trs(number,mint_address,collection_name,token_account_address,creator_id)
                    logger.info(f"Finalized TRS Creation request. {id} from {creator_email}")
                    await connection.commit()
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    async def trade_create(self,trade_id, cost, number, collection_name,buyer_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try: 
                    
                    marketplace_query = """
                    SELECT trs_id, bid_price 
                    FROM marketplace 
                    WHERE collection_name = %s AND bid_price = %s
                    """
                    await cursor.execute(marketplace_query, (collection_name, cost))
                    marketplace_trs1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    marketplace_trs = [dict(zip(columns, row)) for row in marketplace_trs1]
                    if len(marketplace_trs) < number:
                        raise ValueError(f"Not enough trs available. Required: {number}, Found: {len(marketplace_trs)}")

                    # Step 2: Get trs data from trs table with in_trade = 0
                    trs_ids = [trs['trs_id'] for trs in marketplace_trs]
                    trs_query = """
                    SELECT trs_id, user_id 
                    FROM trs 
                    WHERE trs_id IN (%s) AND in_trade = 0
                    """ % ','.join(['%s'] * len(trs_ids))
                    
                    await cursor.execute(trs_query, trs_ids)
                    available_trs1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    available_trs = [dict(zip(columns, row)) for row in available_trs1]
                    
                    if len(available_trs) < number:
                        raise ValueError(f"Not enough trs available in trs table. Required: {number}, Found: {len(available_trs)}")

                    selected_trs = available_trs[:number]
                    update_trs_query = """
                    UPDATE trs 
                    SET in_trade = 1 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * number)
                    await cursor.execute(update_trs_query, [trs['trs_id'] for trs in selected_trs])
                    
                    logger.info("Updated trs status to in_trade")
                    trade_insert_query = """
                    INSERT INTO trades (trade_id, buyer_id, seller_id, trs_id, status) 
                    VALUES (%s, %s, %s, %s, 'initiated')
                    """
                    trade_values = [(trade_id, buyer_id, trs['user_id'], trs['trs_id']) for trs in selected_trs]
                    await cursor.executemany(trade_insert_query, trade_values)
                    logger.info(f"Added trades for {collection_name}")

                    # Step 5: Insert into transactions table for each seller
                    sellers = {}
                    for trs in selected_trs:
                        seller_id = trs['user_id']
                        if seller_id not in sellers:
                            sellers[seller_id] = 0
                        sellers[seller_id] += 1

                    transaction_insert_query = f"""
                    INSERT INTO transactions (transaction_number, collection_name, buyer_id, seller_id, cost, number, status,buyer_transaction_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, 'initiated','{trade_id}')
                    """
                    transaction_values = [
                        (str(uuid.uuid4()), collection_name, buyer_id, seller_id, cost, sellers[seller_id])
                        for seller_id in sellers
                    ]
                    await cursor.executemany(transaction_insert_query, transaction_values)
                    
                    # Commit changes to the database
                    await connection.commit()
                    logger.info(f"Transaction for collection {collection_name} and buyer {buyer_id} processed successfully.")

                    
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))


    async def execute_trade(self, trade_id):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:                  
                    # Step 1: Fetch all trs for the given trade_id and store trs_ids
                    fetch_trs_query = """
                    SELECT trs_id 
                    FROM trades 
                    WHERE trade_id = %s
                    """
                    await cursor.execute(fetch_trs_query, (trade_id,))
                    
                    trs_ids1 = [trs['trs_id'] for trs in await cursor.fetchall()]
                    columns = [column[0] for column in cursor.description]
                    trs_ids = [dict(zip(columns, row)) for row in trs_ids1]
                    logger.info(f"Fetched TRS ID's for trade {trade_id}.")
                    # Step 2: Update trades status to 'finished'
                    update_trades_query = """
                    UPDATE trades 
                    SET status = 'completed' 
                    WHERE trade_id = %s
                    """
                    await cursor.execute(update_trades_query, (trade_id,))
                    logger.info(f"Updated trade_status to finished for trade {trade_id}.")
                    # Step 3: Fetch all transactions corresponding to this trade and change status to 'approved'
                    fetch_transactions_query = """
                    SELECT transaction_number, buyer_id, seller_id, number, cost, collection_name 
                    FROM transactions 
                    WHERE buyer_transaction_id = %s
                    """
                    await cursor.execute(fetch_transactions_query, (trade_id,))
                    transactions1 = await cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    transactions = [dict(zip(columns, row)) for row in transactions1]
                    buyer_id = transactions[0]['buyer_id']
                    buyer_user = await self.get_user(buyer_id)
                    
                    update_transactions_status_query = """
                    UPDATE transactions 
                    SET status = 'approved' 
                    WHERE buyer_transaction_id IN (%s)
                    """ % ','.join(['%s'] * len(transactions))
                    transaction_ids = [transaction['transaction_number'] for transaction in transactions]
                    await cursor.execute(update_transactions_status_query, transaction_ids)
                    logger.info(f"Approved the transactions for trade {trade_id} ")
                    # Step 4: Change ownership of the trs (trs_id) to buyer_id from seller_id
                    update_ownership_query = """
                    UPDATE trs 
                    SET user_id = %s 
                    WHERE trs_id = %s AND user_id = %s
                    """
                    ownership_updates = [(transaction['buyer_id'], trs_id, transaction['seller_id']) 
                                        for trs_id in trs_ids for transaction in transactions]
                    await cursor.executemany(update_ownership_query, ownership_updates)
                    logger.info(f"Changed the owner for trade {trade_id}")
                    # Step 5: Change transaction status to 'finished'
                    update_transactions_finished_query = """
                    UPDATE transactions 
                    SET status = 'finished' 
                    WHERE buyer_transaction_id IN (%s)
                    """ % ','.join(['%s'] * len(transactions))
                    await cursor.execute(update_transactions_finished_query, transaction_ids)
                    logger.info(f"Finished the transactions for trade {trade_id}")
                    # Step 6: Set in_trade = 0 for all involved trs
                    update_in_trade_query = """
                    UPDATE trs 
                    SET in_trade = 0 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * len(trs_ids))
                    await cursor.execute(update_in_trade_query, trs_ids)
                    remove_marketplace_query = """
                    UPDATE trs 
                    SET marketplace = 0 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * len(trs_ids))
                    await cursor.execute(remove_marketplace_query, trs_ids)
                    logger.info(f"Set in_trade to zero for trade {trade_id}")
                    
                    delete_marketplace_query = """
                    DELETE FROM marketplace 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * len(trs_ids))
                    await cursor.execute(delete_marketplace_query, trs_ids)
                    logger.info(f"Removed from marketplace for trade {trade_id}")
                    # Step 7: Create the response list
                    response_list = []
                    for transaction in transactions:
                        seller_user = await self.get_user(transaction['seller_id'])
                        collection_data = await self.get_collection_data(transaction['collection_name'])
                        collection_data = collection_data[0]
                        response_list.append({
                            'seller_id': transaction['seller_id'],
                            'seller_email':seller_user['email'],
                            'number': transaction['number'],
                            'cost': transaction['cost'],
                            'collection_name': transaction['collection_name'],
                            'buyer_id':buyer_id,
                            'buyer_email':buyer_user['email'],
                            'creator_email':collection_data['creator']
                        })

                    # Commit all changes to the database
                    await connection.commit()
                    logger.info(f"Executed trade {trade_id}")
                    return response_list
                except Exception as e:
                    connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))




    async def store_otp(self,email:str,expires : datetime,otp: str):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    
                    query = "SELECT COUNT(*) FROM email_otps WHERE email = %s"
                    await cursor.execute(query,(email,))
                    result = await cursor.fetchone()
                    expires_at_str = expires.strftime('%Y-%m-%d %H:%M:%S')

                    #Checks if there's already an OTP, if there is, it updates it. Else it creates a new one. 
                    logger.debug(result)
                    if result[0] > 0:  
                        
                        update_query = """
                            UPDATE email_otps 
                            SET otp = %s, expires_at = %s 
                            WHERE email = %s
                        """
                        await cursor.execute(update_query, (otp, expires_at_str, email))
                    else:
                        
                        insert_query = """
                            INSERT INTO email_otps (email, otp, expires_at) 
                            VALUES (%s, %s, %s)
                        """
                        await cursor.execute(insert_query, (email, otp, expires_at_str))

                    await connection.commit()
                    logger.info(f"OTP for user {email} stored succesfully. ")
                    return {"message": "OTP stored successfully"}
                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    

    async def retrieve_otp(self, email: str):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:
                    query = """
                        SELECT otp, expires_at 
                        FROM email_otps 
                        WHERE email = %s
                    """
                    await cursor.execute(query, (email,))
                    result = await cursor.fetchone()

                    if not result:
                        logger.info(f"No OTP found for {email}")
                        return None
                        

                    otp, expires_at = result
                    current_time = datetime.utcnow()

                    if current_time > expires_at:
                        logger.info(f"OTP expired for {email}")
                        return 0
                        
                    return {"otp": otp, "expires_at": expires_at}

                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error retrieving OTP for {email}: {e}")
                    raise HTTPException(status_code=500, detail="Error retrieving OTP")
    
    async def store_user_details(self,email:str, first_name: str, last_name: str, username: str, bio: str, twitter: str, telegram: str, profile_pic_uri: str):
        async with await self.get_connection() as connection:
            async with connection.cursor() as cursor:
                try:

                    check_user_query = "SELECT email FROM users WHERE email = %s"
                    await cursor.execute(check_user_query, (email,))
                    user_data = await cursor.fetchone()

                    if not user_data:
                        logger.info(f"User {email} does not exist.")
                        raise HTTPException(status_code=404, detail="User not found")

                    
                    check_username_query = "SELECT email FROM users WHERE username = %s AND email != %s"
                    await cursor.execute(check_username_query, (username, email))
                    existing_user = await cursor.fetchone()

                    if existing_user:
                        logger.info(f"Username '{username}' is already taken.")
                        raise HTTPException(status_code=400, detail="Username is already taken")

                    # Update user profile details
                    update_query = """
                        UPDATE users 
                        SET username = %s, bio = %s, twitter = %s, telegram = %s, pfp_uri = %s, first_name = %s, last_name = %s
                        WHERE email = %s
                    """
                    await cursor.execute(update_query, (username, bio, twitter, telegram, profile_pic_uri,first_name,last_name))
                    await connection.commit()
                    
                    logger.info(f"User {email} profile updated successfully.")
                    return {"message": "User details updated successfully"}

                except Exception as e:
                    await connection.rollback()
                    logger.error(f"Error storing user details for {email}: {e}")
                    raise HTTPException(status_code=500, detail="Error storing user details")
                


database_client = DatabaseManager() 