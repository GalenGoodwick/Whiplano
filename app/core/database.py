import asyncmy
import asyncio
import uuid
from fastapi import FastAPI, HTTPException
from datetime import datetime
from app.core import storage
import os 
import dotenv
dotenv.load_dotenv()

import logging.config
from app.utils.logging_config import logging_config 
logging.config.dictConfig(logging_config)
logger = logging.getLogger("database")

class DatabaseManager:
    def __init__(self, host=None, user=None, password=None, database=None):
        self.pool = None
        
    async def init_pool(self):
        """Initialize the database connection pool."""
        self.pool = await asyncmy.create_pool(
            host=os.getenv("DATABASE_HOST"),
            user=os.getenv("DATABASE_USERNAME"),
            password=os.getenv("DATABASE_PASSWORD"),
            database=os.getenv("DATABASE_NAME"),
            minsize=1,
            maxsize=10
        )

        
    async def get_connection(self):
        """
        Acquires a connection from the pool with retry logic.

        Returns:
        - Connection object
        """
        retries = 3
        for attempt in range(retries):
            try:
                # Use async with to acquire a connection
                async with self.pool.acquire() as connection:
                    return connection
            except Exception as e:
                logger.error(f"Error acquiring connection (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:  # Not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise HTTPException(status_code=500, detail="Database connection error. Please try again later.")
        
    async def login_user(self, user_id=None, email=None):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    if user_id is not None:
                        query = "UPDATE users set last_login = %s where user_id = %s"
                        cursor.execute(query, (datetime.now(), user_id))
                        connection.commit()
                        logger.info(f"Last login updated for user {user_id}")
                    else:
                        query = "UPDATE users set last_login = %s where email = %s"
                        cursor.execute(query, (datetime.now(), email))
                        connection.commit()
                        logger.info(f"Last login updated for user {email}")
                except:
                    logger.error("Failed to update last_login for user. ")
                
    async def add_user(self, username, email, password_hash):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    user_id = str(uuid.uuid4())
                    query = "INSERT INTO users (user_id,username, email, password_hash) VALUES (%s, %s, %s,%s)"
                    values = (user_id,username, email, password_hash)
                    cursor.execute(query, values)
                    connection.commit()
                    logger.info(f"User {username} with id {user_id} added successfully")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def get_user(self, user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    query = "SELECT * FROM users WHERE user_id = %s"
                    cursor.execute(query, (user_id,))
                    result = cursor.fetchone()
                    return result
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    
    
    async def get_user_by_email(self, email):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    query = "SELECT * FROM users WHERE email = %s"
                    cursor.execute(query, (email,))
                    result = cursor.fetchone()
                    try:
                        logger.info(f"Fetched user {result['email']}")
                    except:
                        logger.info(f"No such user. ")
                    return result
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def update_user(self, user_id, username=None, email=None, password_hash=None):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
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
                    cursor.execute(query, tuple(values))
                    connection.commit()
                    logger.info("User updated successfully")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def delete_user(self, user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "DELETE FROM users WHERE user_id = %s"
                    cursor.execute(query, (user_id,))
                    connection.commit()
                    logger.info(f"User {user_id} deleted successfully")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def add_asset(self, values):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = f"INSERT INTO trs (user_id,trs_id,collection_name,creator) VALUES (%s, %s,%s,%s)"

                    cursor.executemany(query, values)
                    connection.commit()
                    logger.info(f"Tokens added succesfully. ")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
        
    async def get_owner(self, trs_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "SELECT user_id FROM trs WHERE trs_id = %s"
                    cursor.execute(query, (trs_id,))
                    result = cursor.fetchone()
                    return result
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def add_transaction(self, buyer_transaction_number, trs_id, buyer_id, seller_id, amount, number):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    transaction_number = str(uuid.uuid4())
                    query = f"INSERT INTO transactions (buyer_transaction_number,transaction_number,trs_id,buyer_id,seller_id,amount,number) VALUES (%s,%s, %s,%s,%s,%s)"
                    values = (buyer_transaction_number,transaction_number, trs_id, buyer_id, seller_id, amount, number)
                    cursor.execute(query, values)
                    connection.commit()
                    logger.info(f"Transaction {transaction_number} and buyer transaction number {buyer_transaction_number} added successfully")
                    
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def modify_transaction(self, transaction_number,status):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = f"UPDATE transactions set status = %s  where transaction_number = %s "
                    values = (status,transaction_number)
                    cursor.execute(query, values)
                    connection.commit()
                    logger.info(f"Transaction {transaction_number} modified successfully to {status}")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def transfer_asset(self, user_id, trs_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = f"UPDATE trs SET user_id = %s WHERE trs_id = %s"

                    cursor.execute(query, (user_id, trs_id))
                    logger.info(f"Transferred TRS {trs_id} to {user_id}.")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    

            
    async def add_trs(self,number, mint_address, collection_name, token_account_address,creator_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    batch_values = []
                    trs_id_values = []
                    for i in range(number):
                        trs_id = uuid.uuid4().int
                        batch_values.append((str(trs_id), collection_name, str(mint_address), str(token_account_address),str(creator_id)))
                        trs_id_values.append((creator_id,trs_id,collection_name,creator_id))
                    query = f"INSERT INTO collections (trs_id, collection_name, mint_address, token_account_address,creator_id) VALUES (%s, %s, %s, %s,%s)"
                    cursor.executemany(query,batch_values)
                    connection.commit()
                    await self.add_asset(trs_id_values)       
                    logger.info(f"Added {number} tokens of collection name {collection_name} to {creator_id}.")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def add_paypal_transaction(self, transaction_number, buyer_id, seller_id, amount):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = f"INSERT INTO paypal_transactions (transaction_id, buyer_id, seller_id, amount) VALUES (%s,%s,%s,%s)"
                    values = (str(transaction_number), str(buyer_id), str(seller_id), amount)

                    cursor.execute(query, values)
                    logger.info(f"Added PayPal transaction with transaction number {transaction_number}")
                except Exception as e:
                    logger.error(f"Error adding paypal transaction: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            
    async def modify_paypal_transaction(self,transaction_id,status):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try: 
                    
                    query = f"UPDATE paypal_transactions SET status = %s WHERE transaction_id = %s"
                    values = (str(status),str(transaction_id))
                    logger.info(f"Updated paypal transaction {transaction_id} to {status} ")
                except Exception as e:
                    logger.error(f"Error updating paypal transaction : {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def get_wallet(self, user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        
                        query = "SELECT trs_id,collection_name FROM trs WHERE user_id = %s"
                        cursor.execute(query, (user_id,))
                        result = cursor.fetchall()
                        logger.info(f"Returned wallet of user {user_id}")
                        return result
                    except Exception as e:
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
    
    async def get_collection_data(self,name):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "SELECT * FROM collection_data WHERE name = %s"
                    cursor.execute(query, (name,))
                    result = cursor.fetchall()
                    return result
                except Exception as e:

                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def get_approved_transactions(self,buyer_transaction_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "SELECT * FROM transactions WHERE buyer_id = %s AND status = %s"
                    cursor.execute(query, (buyer_transaction_id, "initiated"))
                    result = cursor.fetchall()
                    logger.info(f"Retrieved approved transactions for buyer {buyer_transaction_id}")
                    return result
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
        
    
    
    async def approve_initiated_transactions(self,buyer_transaction_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "UPDATE transacations SET status = 'approved' where buyer_id = %s AND status = 'initiated'"
                    cursor.execute(query, (buyer_transaction_id, ))
                    result = cursor.fetchall()
                    logger.info(f"Approved initiated transactions for buyer {buyer_transaction_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))


    
    async def finish_approved_transactions(self,buyer_transaction_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "UPDATE transacations SET status = 'finished' where buyer_id = %s AND status = 'initiated'"
                    cursor.execute(query, (buyer_transaction_id, ))
                    result = cursor.fetchall()
                    logger.info(f"Finished approved transactions for buyer {buyer_transaction_id}")
                    return True
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    
    async def get_wallet_by_collection(self,user_id,collection_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                if not await self.get_user(user_id):
                    logger.error(f"User not found {user_id}")
                    return None
                else:
                    try:
                        
                        query = "SELECT trs_id, collection_name FROM trs WHERE user_id = %s AND collection_name = %s"
                        cursor.execute(query, (user_id, collection_id))
                        result = cursor.fetchall()
                        logger.info(f"Selected wallet by collection {collection_id}, from {user_id}")
                        return result
                    except Exception as e:
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
            
    async def get_mint_address(self,collection_name):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
        
                try:
                    
                    query = "SELECT mint_address FROM collections WHERE collection_name = %s"
                    cursor.execute(query, (collection_name,))
                    result = cursor.fetchall()
                    logger.info(f"Retrieved Mint Address by collection {collection_name}")
                    return result
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                
    
    
    async def get_creator(self,collection_name):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "SELECT creator_id FROM collections WHERE collection_name = %s LIMIT 1"

                    cursor.execute(query, (collection_name,))
                    result = cursor.fetchall()
                    logger.info(f"Retrieved Creator id of collection {collection_name}")
                    return result['creator_id']
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
        
    async def get_wallet_formatted(self,user_id):

        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        
                        query = "SELECT trs_id,collection_name,creator,artisan,marketplace FROM trs WHERE user_id = %s"
                        cursor.execute(query, (user_id,))
                        result = cursor.fetchall()

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
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
    async def add_trs_to_marketplace(self,user_id,values,values2, collection_name):

        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
        
                try: 
                    
                    query = "INSERT INTO marketplace (trs_id,collection_name,order_type,buyer_seller_id,bid_price) VALUES (%s,%s,%s,%s,%s)"

                    cursor.executemany(query, values)
                    connection.commit()
                    query = "UPDATE trs set marketplace = 1 WHERE trs_id = %s"
                    
                    cursor.executemany(query,values2)
                    connection.commit()
                    logger.info(f"Added {len(values)} trs of collection {collection_name} to the Marketplace")
                    return {'message':f"Added trs {len(values)} of collection {collection_name} to the Marketplace"}


                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    async def remove_trs_from_marketplace(self, values,user_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        
                        query = "DELETE FROM marketplace where trs_id = %s"

                        cursor.executemany(query, values)
                        connection.commit()
                        query = "UPDATE trs set marketplace = 0 WHERE trs_id = %s"
                        cursor.executemany(query,values)
                        connection.commit()
                        logger.info(f"Removed trs from the Marketplace")
                        return {'message':f"Removed trs from the Marketplace"}


                    except Exception as e:
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))


    async def get_marketplace_all(self):

        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
        
                try:
                    
                    query = "SELECT  collection_name, bid_price, COUNT(*) AS number_of_trs from  marketplace GROUP BY collection_name,bid_price "

                    cursor.execute(query)
                    results = cursor.fetchall()
                    for collection in results: 
                        data = await self.get_collection_data(collection['collection_name'])
                        collection['collection_data'] = data
                        
                    logger.info(f"Entire Marketplace fetched successfully. ")
                    return results


                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    async def get_marketplace_collection(self, collection_name: str):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
        
                try:
                    
                    query = "SELECT  collection_name, bid_price, COUNT(*) AS number_of_trs from  marketplace WHERE collection_name = %s GROUP BY collection_name,bid_price "

                    cursor.execute(query, (collection_name,))
                    results = cursor.fetchall()

                    logger.info(f"Marketplace for collection {collection_name} fetched successfully. ")
                    return results

                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                

    async def add_admin(self, email: str) -> None:
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "UPDATE users set role = 'admin' WHERE email = %s"

                    cursor.execute(query, (email,))
                    connection.commit()

                    logger.info(f"User {email} added to the admin list. ")

                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    
    async def verify_user(self, email: str) -> None:
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "UPDATE users set status = 'verified' WHERE email = %s"

                    cursor.execute(query, (email,))
                    connection.commit()

                    logger.info(f"User {email} has been verified. ")

                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    
    async def activate_artisan_trs(self,values, user_id):

        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        

                        query = "UPDATE trs set artisan = 1 WHERE trs_id = %s"
                        cursor.executemany(query,values)
                        connection.commit()
                        logger.info(f"Activated TRS rights for {user_id}")
                        return {'message':f"Activated TRS rights for {user_id}"}


                    except Exception as e:
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))

    
    async def deactivate_artisan_trs(self,values, user_id):

        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                if not await self.get_user(user_id):
                    logger.info(f"User not found {user_id}")
                    return None
                else:
                    try: 
                        

                        query = "UPDATE trs set artisan = 0 WHERE trs_id = %s"
                        cursor.executemany(query,values)
                        connection.commit()
                        logger.info(f"Deactivated artisan rights for TRS {user_id}")
                        return {'message':f"Deactivated artisan rights for TRS {user_id}"}


                    except Exception as e:
                        logger.error(f"Error: {e}")
                        raise HTTPException(status_code=400, detail=str(e))
            
    async def check_collection_exists(self,name):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:       
                    query = "SELECT  * from  collection_data where name = %s"
                    cursor.execute(query, (name,))
                    results = cursor.fetchall()
                    if len(results) == 0:
                        logger.info(f"Collection {name} does not exist. ")
                        return False
                    else:
                        logger.info(f"Collection {name} does not exist. ")
                        return True
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def add_trs_creation_request(self,model_name,title,description,creator_email, file_url_header):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    query = "INSERT INTO trs_creation_requests (model_name, title, description, creator_email, file_url_header) VALUES (%s, %s, %s,%s,%s)"
                    values = (model_name,title, description, creator_email, file_url_header)
                    cursor.execute(query, values)
                    connection.commit()
                    logger.info(f"New TRS request submitted from {creator_email} with title {title}.")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def get_trs_creation_requests(self,status):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "SELECT * FROM trs_creation_requests WHERE status = %s"
                    cursor.execute(query, (status,))
                    result = cursor.fetchall()
                    return result
                except Exception as e:
                    
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    
    
    async def get_trs_creation_data(self,id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    query = "SELECT * FROM trs_creation_requests WHERE id = %s"
                    cursor.execute(query, (id,))
                    result = cursor.fetchall()
                    return result
                except Exception as e:
                    
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
    async def add_collection_data(self,name,creator,description,number,url_header):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try:
                    
                    user_id = str(uuid.uuid4())
                    cid = storage.get_file_cid(f'{url_header}thumbnail.png')
                    image_uri = 'https://ipfs.filebase.io/ipfs/' + str(cid)
                    query = "INSERT INTO collection_data (name,creator, description, number, image_uri) VALUES (%s, %s, %s,%s,%s)"
                    
                    values = (name,creator,description,number,image_uri)
                    cursor.execute(query, values)
                    connection.commit()
                    logger.info(f"Collection data has been added for {name} . ")
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
                    
            
    async def approve_trs_creation_request(self,id,creator_email,number,mint_address,collection_name,token_account_address):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try: 
                    q1 = "select * from trs_creation_requests where id = %s"
                    query = "UPDATE trs_creation_requests set status = 'approved' WHERE id = %s"
                    cursor.execute(query,(id,))
                    logger.info(f"Approved TRS creation request {id}")
                    creation_data = await self.get_trs_creation_data(id)
                    logger.info(creation_data)
                    creation_data = creation_data[0]
                    await self.add_collection_data(creation_data['title'],creator_email,creation_data['description'],number,creation_data['file_url_header'])
                    creator_id = await self.get_user_by_email(creator_email)
                    creator_id = creator_id['user_id']
                    await self.add_trs(number,mint_address,collection_name,token_account_address,creator_id)
                    logger.info(f"Finalized TRS Creation request. {id} from {creator_email}")
                    connection.commit()
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

                
    async def trade_create(self,trade_id, cost, number, collection_name,buyer_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try: 
                    
                    marketplace_query = """
                    SELECT trs_id, bid_price 
                    FROM marketplace 
                    WHERE collection_name = %s AND bid_price = %s
                    """
                    cursor.execute(marketplace_query, (collection_name, cost))
                    marketplace_trs = cursor.fetchall()

                    if len(marketplace_trs) < number:
                        raise ValueError(f"Not enough trs available. Required: {number}, Found: {len(marketplace_trs)}")

                    # Step 2: Get trs data from trs table with in_trade = 0
                    trs_ids = [trs['trs_id'] for trs in marketplace_trs]
                    trs_query = """
                    SELECT trs_id, user_id 
                    FROM trs 
                    WHERE trs_id IN (%s) AND in_trade = 0
                    """ % ','.join(['%s'] * len(trs_ids))
                    
                    cursor.execute(trs_query, trs_ids)
                    available_trs = cursor.fetchall()
                    if len(available_trs) < number:
                        raise ValueError(f"Not enough trs available in trs table. Required: {number}, Found: {len(available_trs)}")

                    selected_trs = available_trs[:number]
                    update_trs_query = """
                    UPDATE trs 
                    SET in_trade = 1 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * number)
                    cursor.execute(update_trs_query, [trs['trs_id'] for trs in selected_trs])
                    logger.info("Updated trs status to in_trade")
                    trade_insert_query = """
                    INSERT INTO trades (trade_id, buyer_id, seller_id, trs_id, status) 
                    VALUES (%s, %s, %s, %s, 'initiated')
                    """
                    trade_values = [(trade_id, buyer_id, trs['user_id'], trs['trs_id']) for trs in selected_trs]
                    cursor.executemany(trade_insert_query, trade_values)
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
                    cursor.executemany(transaction_insert_query, transaction_values)
                    
                    # Commit changes to the database
                    connection.commit()
                    logger.info(f"Transaction for collection {collection_name} and buyer {buyer_id} processed successfully.")

                    connection.commit()
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))


    async def execute_trade(self, trade_id):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try: 
                    
                            
                    # Step 1: Fetch all trs for the given trade_id and store trs_ids
                    fetch_trs_query = """
                    SELECT trs_id 
                    FROM trades 
                    WHERE trade_id = %s
                    """
                    cursor.execute(fetch_trs_query, (trade_id,))
                    trs_ids = [trs['trs_id'] for trs in cursor.fetchall()]
                    logger.info(f"Fetched TRS ID's for trade {trade_id}.")
                    # Step 2: Update trades status to 'finished'
                    update_trades_query = """
                    UPDATE trades 
                    SET status = 'completed' 
                    WHERE trade_id = %s
                    """
                    cursor.execute(update_trades_query, (trade_id,))
                    logger.info(f"Updated trade_status to finished for trade {trade_id}.")
                    # Step 3: Fetch all transactions corresponding to this trade and change status to 'approved'
                    fetch_transactions_query = """
                    SELECT transaction_number, buyer_id, seller_id, number, cost, collection_name 
                    FROM transactions 
                    WHERE buyer_transaction_id = %s
                    """
                    cursor.execute(fetch_transactions_query, (trade_id,))
                    transactions = cursor.fetchall()
                    buyer_id = transactions[0]['buyer_id']
                    buyer_user = await self.get_user(buyer_id)
                    
                    update_transactions_status_query = """
                    UPDATE transactions 
                    SET status = 'approved' 
                    WHERE buyer_transaction_id IN (%s)
                    """ % ','.join(['%s'] * len(transactions))
                    transaction_ids = [transaction['transaction_number'] for transaction in transactions]
                    cursor.execute(update_transactions_status_query, transaction_ids)
                    logger.info(f"Approved the transactions for trade {trade_id} ")
                    # Step 4: Change ownership of the trs (trs_id) to buyer_id from seller_id
                    update_ownership_query = """
                    UPDATE trs 
                    SET user_id = %s 
                    WHERE trs_id = %s AND user_id = %s
                    """
                    ownership_updates = [(transaction['buyer_id'], trs_id, transaction['seller_id']) 
                                        for trs_id in trs_ids for transaction in transactions]
                    cursor.executemany(update_ownership_query, ownership_updates)
                    logger.info(f"Changed the owner for trade {trade_id}")
                    # Step 5: Change transaction status to 'finished'
                    update_transactions_finished_query = """
                    UPDATE transactions 
                    SET status = 'finished' 
                    WHERE buyer_transaction_id IN (%s)
                    """ % ','.join(['%s'] * len(transactions))
                    cursor.execute(update_transactions_finished_query, transaction_ids)
                    logger.info(f"Finished the transactions for trade {trade_id}")
                    # Step 6: Set in_trade = 0 for all involved trs
                    update_in_trade_query = """
                    UPDATE trs 
                    SET in_trade = 0 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * len(trs_ids))
                    cursor.execute(update_in_trade_query, trs_ids)
                    remove_marketplace_query = """
                    UPDATE trs 
                    SET marketplace = 0 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * len(trs_ids))
                    cursor.execute(remove_marketplace_query, trs_ids)
                    logger.info(f"Set in_trade to zero for trade {trade_id}")
                    
                    delete_marketplace_query = """
                    DELETE FROM marketplace 
                    WHERE trs_id IN (%s)
                    """ % ','.join(['%s'] * len(trs_ids))
                    cursor.execute(delete_marketplace_query, trs_ids)
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
                    connection.commit()
                    logger.info(f"Executed trade {trade_id}")
                    return response_list
                except Exception as e:
                    connection.rollback()
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

    async def get_token_account_address(self, collection_name):
        async with await self.get_connection() as connection:
            async with connection.cursor(dictionary=True) as cursor:
                try: 
                    
                    query = "select * from collections where collection_name = %s"
                    cursor.execute(query,(collection_name,))
                    logger.info(f"Fetched token account address of collection : {collection_name}")
                    result = cursor.fetchall()
                    token_account_address = result[0]["token_account_address"]
                    mint_address = result[0]['mint_address']
                    return token_account_address,mint_address
                    
                except Exception as e:
                    logger.error(f"Error: {e}")
                    raise HTTPException(status_code=400, detail=str(e))

database_client =DatabaseManager(
    host=os.getenv("DATABASE_HOST"),
    user=os.getenv("DATABASE_USERNAME"),
    password=os.getenv("DATABASE_PASSWORD"),
    database =os.getenv("DATABASE_NAME")
)
asyncio.run(database_client.init_pool())