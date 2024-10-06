import mysql.connector
from mysql.connector import Error
import uuid
from backend.logging_config import logging_config  # Import the configuration file
import logging.config
from fastapi import FastAPI, HTTPException
from datetime import datetime
from backend import storage
logging.config.dictConfig(logging_config)
logger = logging.getLogger("database")

class DatabaseManager:
    def __init__(self, host, user, password, database):
        """
        Initializes a new instance of the DatabaseManager class.

        Parameters:
        - host (str): The host address of the MySQL database.
        - user (str): The username for connecting to the MySQL database.
        - password (str): The password for connecting to the MySQL database.
        - database (str): The name of the MySQL database.

        Returns:
        - None

        Raises:
        - HTTPException: If there is an error connecting to the MySQL database.
        """
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )

            if self.connection.is_connected():
                logger.info("Successfully connected to the database")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            self.connection = None

            
    async def login_user(self, user_id=None, email=None):
        """
        Updates the last login timestamp for a user in the database.

        Parameters:
        - user_id (int): The unique identifier of the user. If both user_id and email are provided, user_id will be used.
        - email (str): The email address of the user. If both user_id and email are provided, user_id will be used.

        Returns:
        - None

        Raises:
        - None

        """
        if not self.connection:
            logger.critical("No database connection")
            return None
        try:
            if user_id is not None:
                cursor = self.connection.cursor()
                query = "UPDATE users set last_login = %s where user_id = %s"
                cursor.execute(query, (datetime.now(), user_id))
                self.connection.commit()
                logger.info(f"Last login updated for user {user_id}")
            else:
                cursor = self.connection.cursor()
                query = "UPDATE users set last_login = %s where email = %s"
                cursor.execute(query, (datetime.now(), email))
                self.connection.commit()
                logger.info(f"Last login updated for user {email}")
        except:
            logger.error("Failed to update last_login for user. ")
        finally:
            cursor.close()
            
            

                
    async def add_user(self, username, email, password_hash):
        """
        Adds a new user to the database.

        This function establishes a connection to the database, checks if the connection is available,
        and then inserts a new user record into the 'users' table. If the connection is not available,
        it prints a message indicating the lack of a database connection.

        Parameters:
        - username (str): The username of the new user.
        - email (str): The email address of the new user.
        - password_hash (str): The hashed password of the new user.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            user_id = str(uuid.uuid4())
            
            query = "INSERT INTO users (user_id,username, email, password_hash) VALUES (%s, %s, %s,%s)"
            
            values = (user_id,username, email, password_hash)
            cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"User {username} with id {user_id} added successfully")
            
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
             
        finally:
            cursor.close()

    async def get_user(self, user_id):
        """
        Retrieves a user's details from the database based on the provided user ID.

        Parameters:
        - user_id (int): The unique identifier of the user.

        Returns:
        - dict: A dictionary containing the user's details if the user exists in the database.
                 If the user does not exist or there is an error, returns None.
        """
        if not self.connection:
            logger.critical("No database connection")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
        finally:
            cursor.close()
    
    
    async def get_user_by_email(self, email):
        """
        Retrieves a user's details from the database based on the provided email address.

        Parameters:
        - email (str): The email address of the user.

        Returns:
        - dict: A dictionary containing the user's details if the user exists in the database.
                 If the user does not exist or there is an error, returns None.
        """
        if not self.connection:
            logger.critical("No Database Connection")
            return
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE email = %s"
            
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            try:
                logger.info(f"Fetched user {result['email']}")
            except:
                logger.info(f"No such user. ")
            return result
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
        finally:
            cursor.close()
            
    async def update_user(self, user_id, username=None, email=None, password_hash=None):
        """
        Updates a user's details in the database.

        This function connects to the database, checks if a connection is available, and then updates the user's details
        in the 'users' table based on the provided user ID. If any of the optional parameters (username, email, password_hash)
        are provided, their corresponding fields in the database will be updated. If no updates are provided, the function
        prints a message indicating that no updates were made.

        Parameters:
        - user_id (int): The unique identifier of the user.
        - username (str, optional): The new username for the user. If not provided, the username remains unchanged.
        - email (str, optional): The new email address for the user. If not provided, the email remains unchanged.
        - password_hash (str, optional): The new hashed password for the user. If not provided, the password remains unchanged.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            return
        try:
            cursor = self.connection.cursor()
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
            self.connection.commit()
            logger.info("User updated successfully")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cursor.close()

    async def delete_user(self, user_id):
        """
        Deletes a user from the database based on the provided user ID.

        This function first checks if a database connection is available. If not, it prints a message indicating the lack of a
        database connection and returns early. If a connection is available, it attempts to delete the user from the 'users'
        table using the provided user ID. If the deletion is successful, it prints a success message. If an error occurs during
        the deletion process, it prints the error message. In both cases, the function ensures that the database cursor is
        closed.

        Parameters:
        - user_id (int): The unique identifier of the user to be deleted.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            self.connection.commit()
            logger.info(f"User {user_id} deleted successfully")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cursor.close()

    async def add_asset(self, values):
        """
        Adds a new asset (token) to the user's wallet in the database.

        This function checks if a database connection is available. If not, it prints a message indicating the lack of a
        database connection and returns early. If a connection is available, it attempts to insert a new asset record into
        the 'trs' table. The 'wallet_id' is set to the same value as 'user_id'.

        Parameters:
        - user_id (int): The unique identifier of the user who owns the asset.
        - trs_id (str): The unique identifier of the asset (token).
        - collection_id (str): The identifier of the collection to which the asset belongs.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO trs (user_id,trs_id,collection_name,creator) VALUES (%s, %s,%s,%s)"

            cursor.executemany(query, values)
            self.connection.commit()
            logger.info(f"Tokens added succesfully. ")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
    async def get_owner(self, trs_id):
        """
        Retrieves the owner of a specific asset (token) from the database.

        This function connects to the database, checks if a connection is available, and then retrieves the owner's user ID
        from the 'trs' table based on the provided asset (token) ID. If the connection is not available, it prints a message
        indicating the lack of a database connection.

        Parameters:
        - trs_id (str): The unique identifier of the asset (token).

        Returns:
        - dict: A dictionary containing the owner's user ID if the asset exists in the database.
                 If the asset does not exist or there is an error, returns None.
        """
        if not self.connection:
            logger.critical("No database connection")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT user_id FROM trs WHERE trs_id = %s"
            cursor.execute(query, (trs_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
    
    async def add_transaction(self, buyer_transaction_number, trs_id, buyer_id, seller_id, amount, number):
        """
        Adds a new transaction record to the database.

        This function connects to the database, checks if a connection is available, and then inserts a new transaction record
        into the 'transactions' table. If the connection is not available, it prints a message indicating the lack of a
        database connection.

        Parameters:
        - transaction_number (str): The unique identifier of the transaction.
        - trs_id (str): The unique identifier of the asset (token) involved in the transaction.
        - buyer_id (int): The unique identifier of the buyer.
        - seller_id (int): The unique identifier of the seller.
        - amount (float): The amount of the transaction.
        - number (int): The quantity of assets (tokens) involved in the transaction.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical('No Database Connection')
        try:
            cursor = self.connection.cursor()
            transaction_number = str(uuid.uuid4())
            query = f"INSERT INTO transactions (buyer_transaction_number,transaction_number,trs_id,buyer_id,seller_id,amount,number) VALUES (%s,%s, %s,%s,%s,%s)"
            values = (buyer_transaction_number,transaction_number, trs_id, buyer_id, seller_id, amount, number)
            cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"Transaction {transaction_number} and buyer transaction number {buyer_transaction_number} added successfully")
            
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    async def modify_transaction(self, transaction_number,status):
        """
    Modifies a transaction record in the database.

    Parameters:
    - transaction_number (str): The unique identifier of the transaction.
    - status (str): The new status of the transaction.

    Returns:
    - None

    Raises:
    - HTTPException: If there is an error updating the transaction record.
        """
        if not self.connection:
            logger.critical('No Database Connection')
        try:
            cursor = self.connection.cursor()
            query = f"UPDATE transactions set status = %s  where transaction_number = %s "
            values = (status,transaction_number)
            cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"Transaction {transaction_number} modified successfully to {status}")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    async def transfer_asset(self, user_id, trs_id):
        """
        Transfers an asset (token) from the current owner to a new user in the database.

        This function connects to the database, checks if a connection is available, and then updates the 'user_id' field
        in the 'trs' table to the new user's ID. The function also prints a success message if the transfer is successful,
        or an error message if an error occurs.

        Parameters:
        - user_id (int): The unique identifier of the new owner of the asset.
        - trs_id (str): The unique identifier of the asset (token) to be transferred.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
        try:
            cursor = self.connection.cursor()
            query = f"UPDATE trs SET user_id = %s WHERE trs_id = %s"

            cursor.execute(query, (user_id, trs_id))
            logger.info(f"Transferred TRS {trs_id} to {user_id}.")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    
    async def close_connection(self):
        """
        Closes the database connection if it is currently open.

        This function checks if a database connection is available and if it is connected.
        If both conditions are met, it closes the connection and prints a success message.

        Parameters:
        - None

        Returns:
        - None
        """
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
            
    async def add_trs(self,number, mint_address, collection_name, token_account_address,creator_id):
        """
        Adds a new token to the database.

        This function connects to the database, checks if a connection is available, and then inserts a new token record
        into the 'collections' table. If the connection is not available, it prints a message indicating the lack of a
        database connection.

        Parameters:
    
        - mint_address (str): The address of the mint that created the token.
        - collection_name (str): The name of the collection to which the token belongs.
        - token_account_address (str): The address of the token account associated with the token.
        - creator_id (int): The unique identifier of the creator of the token.
        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            batch_values = []
            trs_id_values = []
            for i in range(number):
                trs_id = uuid.uuid4().int
                batch_values.append((str(trs_id), collection_name, str(mint_address), str(token_account_address),str(creator_id)))
                trs_id_values.append((creator_id,trs_id,collection_name,creator_id))
            query = f"INSERT INTO collections (trs_id, collection_name, mint_address, token_account_address,creator_id) VALUES (%s, %s, %s, %s,%s)"
            cursor.executemany(query,batch_values)
            self.connection.commit()
            await self.add_asset(trs_id_values)       
            logger.info(f"Added {number} tokens of collection name {collection_name} to {creator_id}.")
        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    async def add_paypal_transaction(self, transaction_number, buyer_id, seller_id, amount):
        """
        Adds a new PayPal transaction record to the database.

        This function connects to the database, checks if a connection is available, and then inserts a new PayPal transaction
        record into the 'paypal_transactions' table. If the connection is not available, it prints a message indicating the lack of a
        database connection.

        Parameters:
        - transaction_number (str): The unique identifier of the PayPal transaction.
        - buyer_id (str): The unique identifier of the buyer.
        - seller_id (str): The unique identifier of the seller.
        - amount (float): The amount of the transaction.
        - transaction_date (datetime): The date and time of the transaction.

        Returns:
        - None
        """
        if not self.connection:
            logger.critical("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO paypal_transactions (transaction_id, buyer_id, seller_id, amount) VALUES (%s,%s,%s,%s)"
            values = (str(transaction_number), str(buyer_id), str(seller_id), amount)

            cursor.execute(query, values)
            logger.info(f"Added PayPal transaction with transaction number {transaction_number}")
        except Error as e:
            logger.error(f"Error adding paypal transaction: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
    async def modify_paypal_transaction(self,transaction_id,status):
        if not self.connection:
            logger.critical("No database connection")
            return
        try: 
            cursor = self.connection.cursor()
            query = f"UPDATE paypal_transactions SET status = %s WHERE transaction_id = %s"
            values = (str(status),str(transaction_id))
            logger.info(f"Updated paypal transaction {transaction_id} to {status} ")
        except Error as e:
            logger.error(f"Error updating paypal transaction : {e}")
            raise HTTPException(status_code=400, detail=str(e))
    async def get_wallet(self, user_id):
        """
        Retrieves the wallet of a user from the database.

        This function connects to the database, checks if a connection is available, and then retrieves the wallet
        of a user from the 'trs' table based on the provided user ID. If the connection is not available, it prints a
        message indicating the lack of a database connection. If the user does not exist, it prints a message indicating
        the user not found.

        Parameters:
        - user_id (int): The unique identifier of the user.

        Returns:
        - list: A list of dictionaries containing the asset (token) details in the user's wallet.
                 If the user does not exist or there is an error, returns None.
        """
        if not self.connection:
            logger.critical("No Database connection.")
        elif not await self.get_user(user_id):
            logger.info(f"User not found {user_id}")
            return None
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT trs_id,collection_name FROM trs WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                result = cursor.fetchall()
                logger.info(f"Returned wallet of user {user_id}")
                return result
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                return None
            finally: 
                cursor.close()
    
    async def get_collection_data(self,name):
        if not self.connection:
            logger.critical("No database connection")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM collection_data WHERE name = %s"
            cursor.execute(query, (name,))
            result = cursor.fetchall()
            return result
        except Error as e:
            
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
        finally:
            cursor.close()
    async def get_approved_transactions(self,buyer_transaction_id):
        """
    Retrieves the approved transactions for a buyer from the database.

    Parameters:
    buyer_transaction_id (str): The unique identifier of the buyer.

    Returns:
    list: A list of dictionaries representing the approved transactions. Each dictionary contains the transaction details.

    Raises:
    HTTPException: If there is an error connecting to the database or retrieving the transactions.
    """
        if not self.connection:
            logger.critical("No Database connection.")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM transactions WHERE buyer_id = %s AND status = %s"
            cursor.execute(query, (buyer_transaction_id, "initiated"))
            result = cursor.fetchall()
            logger.info(f"Retrieved approved transactions for buyer {buyer_transaction_id}")
            return result
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
        finally:
            cursor.close()
        
    
    
    async def approve_initiated_transactions(self,buyer_transaction_id):
        """
    Retrieves the approved transactions for a buyer from the database.

    Parameters:
    buyer_transaction_id (str): The unique identifier of the buyer.

    Returns:
    list: A list of dictionaries representing the approved transactions. Each dictionary contains the transaction details.

    Raises:
    HTTPException: If there is an error connecting to the database or retrieving the transactions.
    """
        if not self.connection:
            logger.critical("No Database connection.")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "UPDATE transacations SET status = 'approved' where buyer_id = %s AND status = 'initiated'"
            cursor.execute(query, (buyer_transaction_id, ))
            result = cursor.fetchall()
            logger.info(f"Approved initiated transactions for buyer {buyer_transaction_id}")
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
        finally:
            cursor.close()
        return


    
    async def finish_approved_transactions(self,buyer_transaction_id):
        """
    Finishes the approved transactions for a buyer from the database.

    Parameters:
    buyer_transaction_id (str): The unique identifier of the buyer.

    Returns:
    bool: True if the transactions were successfully finished, False otherwise.

    Raises:
    HTTPException: If there is an error connecting to the database or finishing the transactions.
    """
        if not self.connection:
            logger.critical("No Database connection.")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "UPDATE transacations SET status = 'finished' where buyer_id = %s AND status = 'initiated'"
            cursor.execute(query, (buyer_transaction_id, ))
            result = cursor.fetchall()
            logger.info(f"Finished approved transactions for buyer {buyer_transaction_id}")
            return True
        except Exception as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            return None
        finally:
            cursor.close()
        return
    
    async def get_wallet_by_collection(self,user_id,collection_id):
        if not self.connection:
            logger.critical("No Database connection.")
        elif not await self.get_user(user_id):
            logger.error(f"User not found {user_id}")
            return None
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT trs_id, collection_name FROM trs WHERE user_id = %s AND collection_name = %s"
                cursor.execute(query, (user_id, collection_id))
                result = cursor.fetchall()
                logger.info(f"Selected wallet by collection {collection_id}, from {user_id}")
                return result
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                return None
            finally:
                cursor.close()
       
    async def get_mint_address(self,collection_name):
        if not self.connection:
            logger.critical("No Database connection.")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT mint_address FROM collections WHERE collection_name = %s"
                cursor.execute(query, (collection_name,))
                result = cursor.fetchall()
                logger.info(f"Retrieved Mint Address by collection {collection_name}")
                return result
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                
                return None
            finally:
                cursor.close()
        return 
    
    
    async def get_creator(self,collection_name):
        """
    Retrieves the creator id of a collection from the database.

    Parameters:
    collection_name (str): The name of the collection.

    Returns:
    str: The creator id of the collection.

    Raises:
    HTTPException: If there is an error connecting to the database or retrieving the creator id.
        """
        if not self.connection:
            logger.critical("No Database connection.")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT creator_id FROM collections WHERE collection_name = %s LIMIT 1"

                cursor.execute(query, (collection_name,))
                result = cursor.fetchall()
                logger.info(f"Retrieved Creator id of collection {collection_name}")
                return result['creator_id']
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
                return None
            finally:
                cursor.close()
        return
    
    
    async def get_wallet_formatted(self,user_id):
        """
    Retrieves the wallet of a user from the database and formats it.

    Parameters:
    user_id (int): The unique identifier of the user.

    Returns:
    dict: A dictionary containing the formatted wallet. The dictionary has the following keys:
        - "created_trs": A list of dictionaries representing the tokens created by the user.
        - "artisan_trs": A list of dictionaries representing the tokens that have artisan rights on.
        - "marketplace_trs": A list of dictionaries representing the tokens listed on the marketplace.
        - "trs": A list of dictionaries representing all the tokens in the user's wallet.

    Raises:
    HTTPException: If there is an error connecting to the database or retrieving the user's wallet.
        """
        if not self.connection:
            logger.critical("No Database connection.")
        elif not await self.get_user(user_id):
            logger.info(f"User not found {user_id}")
            return None
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)
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
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
                
    
    
    async def add_trs_to_marketplace(self,user_id,values,values2, collection_name):
        """
    Adds a token to the marketplace in the database.

    Parameters:
    trs_id (str): The unique identifier of the token.
    collection_name (str): The name of the collection to which the token belongs.
    user_id (int): The unique identifier of the user who is adding the token to the marketplace.
    bid_price (float): The price at which the user is bidding to sell the token.

    Returns:
    dict: A dictionary containing a success message.

    Raises:
    HTTPException: If there is an error adding the token to the marketplace.
        """
        if not self.connection:
            logger.critical("No Database connection.")
        elif not await self.get_user(user_id):
            logger.info(f"User not found {user_id}")
            return None
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)
                query = "INSERT INTO marketplace (trs_id,collection_name,order_type,buyer_seller_id,bid_price) VALUES (%s,%s,%s,%s,%s)"

                cursor.executemany(query, values)
                self.connection.commit()
                query = "UPDATE trs set marketplace = 1 WHERE trs_id = %s"
                
                cursor.executemany(query,values2)
                self.connection.commit()
                logger.info(f"Added {len(values)} trs of collection {collection_name} to the Marketplace")
                return {'message':f"Added trs {len(values)} of collection {collection_name} to the Marketplace"}


            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
                
                
    async def remove_trs_from_marketplace(self, values,user_id):
        """
    Adds a token to the marketplace in the database.

    Parameters:
    trs_id (str): The unique identifier of the token.
    collection_name (str): The name of the collection to which the token belongs.
    user_id (int): The unique identifier of the user who is adding the token to the marketplace.
    bid_price (float): The price at which the user is bidding to sell the token.

    Returns:
    dict: A dictionary containing a success message.

    Raises:
    HTTPException: If there is an error adding the token to the marketplace.
        """
        if not self.connection:
            logger.critical("No Database connection.")
        elif not await self.get_user(user_id):
            logger.info(f"User not found {user_id}")
            return None
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)
                query = "DELETE FROM marketplace where trs_id = %s"

                cursor.executemany(query, values)
                self.connection.commit()
                query = "UPDATE trs set marketplace = 0 WHERE trs_id = %s"
                cursor.executemany(query,values)
                self.connection.commit()
                logger.info(f"Removed trs from the Marketplace")
                return {'message':f"Removed trs from the Marketplace"}


            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()

    async def get_marketplace_all(self):
        """
        Retrieves all the tokens listed on the marketplace from the database.

        Parameters:
        None

        Returns:
        list: A list of dictionaries representing the tokens listed on the marketplace. Each dictionary contains the following keys:
            - "collection_name": The name of the collection to which the token belongs.
            - "bid_price": The price at which the user is bidding to buy the token.
            - "number_of_trs": The number of tokens listed on the marketplace for the given collection and bid price.

        Raises:
        HTTPException: If there is an error connecting to the database or retrieving the tokens from the marketplace.
        """
        if not self.connection:
            logger.critical("No database connection.")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT  collection_name, bid_price, COUNT(*) AS number_of_trs from  marketplace GROUP BY collection_name,bid_price "

                cursor.execute(query)
                results = cursor.fetchall()
                for collection in results: 
                    data = self.get_collection_data(collection['collection_name'])
                    collection['collection_data'] = data
                    
                logger.info(f"Entire Marketplace fetched successfully. ")
                return results


            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
                
    async def get_marketplace_collection(self, collection_name: str):
        """
        Retrieves the tokens listed on the marketplace for a specific collection from the database.

        Parameters:
        collection_name (str): The name of the collection for which to retrieve the tokens.

        Returns:
        List[Dict[str, Union[str, int]]]: A list of dictionaries representing the tokens listed on the marketplace for the given collection.
        Each dictionary contains the following keys:
            - "collection_name": The name of the collection to which the token belongs.
            - "bid_price": The price at which the user is bidding to buy the token.
            - "number_of_trs": The number of tokens listed on the marketplace for the given collection and bid price.

        Raises:
        HTTPException: If there is an error connecting to the database or retrieving the tokens from the marketplace.
        """
        if not self.connection:
            logger.critical("No database connection.")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "SELECT  collection_name, bid_price, COUNT(*) AS number_of_trs from  marketplace WHERE collection_name = %s GROUP BY collection_name,bid_price "

                cursor.execute(query, (collection_name,))
                results = cursor.fetchall()

                logger.info(f"Marketplace for collection {collection_name} fetched successfully. ")
                return results

            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
                

    async def add_admin(self, email: str) -> None:
        """
        Adds a user with the given email to the admin list in the database.

        Parameters:
        email (str): The email of the user to be added to the admin list.

        Returns:
        None

        Raises:
        HTTPException: If there is an error connecting to the database or adding the user to the admin list.
        """
        if not self.connection:
            logger.critical("No database connection.")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "UPDATE users set role = 'admin' WHERE email = %s"

                cursor.execute(query, (email,))
                self.connection.commit()

                logger.info(f"User {email} added to the admin list. ")

            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
        
    async def verify_user(self, email: str) -> None:
        """
        Verifies a user in the database

        Parameters:
        email (str): The email of the user to be verified. 

        Returns:
        None

        Raises:
        HTTPException: If there is an error connecting to the database or adding the user to the admin list.
        """
        if not self.connection:
            logger.critical("No database connection.")
        else:
            try:
                cursor = self.connection.cursor(dictionary=True)
                query = "UPDATE users set status = 'verified' WHERE email = %s"

                cursor.execute(query, (email,))
                self.connection.commit()

                logger.info(f"User {email} has been verified. ")

            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
                
                
    
    async def activate_artisan_trs(self,values, user_id):
        """
    Activates the artisan rights for a specific token in the database.

    Parameters:
    trs_id (str): The unique identifier of the token.
    user_id (int): The unique identifier of the user who is activating the artisan rights.

    Returns:
    dict: A dictionary containing a success message.

    Raises:
    HTTPException: If there is an error connecting to the database or activating the artisan rights.
    """
        if not self.connection:
            logger.critical("No Database connection.")
        elif not await self.get_user(user_id):
            logger.info(f"User not found {user_id}")
            return None
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)

                query = "UPDATE trs set artisan = 1 WHERE trs_id = %s"
                cursor.executemany(query,values)
                self.connection.commit()
                logger.info(f"Activated TRS rights for {user_id}")
                return {'message':f"Activated TRS rights for {user_id}"}


            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
                
    
    async def deactivate_artisan_trs(self,values, user_id):
        """
    Deactivates the artisan rights for a specific token in the database.

    Parameters:
    trs_id (str): The unique identifier of the token.
    user_id (int): The unique identifier of the user who is deactivating the artisan rights.

    Returns:
    dict: A dictionary containing a success message.

    Raises:
    HTTPException: If there is an error connecting to the database or deactivating the artisan rights.
    """
        if not self.connection:
            logger.critical("No Database connection.")
        elif not await self.get_user(user_id):
            logger.info(f"User not found {user_id}")
            return None
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)

                query = "UPDATE trs set artisan = 0 WHERE trs_id = %s"
                cursor.executemany(query,values)
                self.connection.commit()
                logger.info(f"Deactivated artisan rights for TRS {user_id}")
                return {'message':f"Deactivated artisan rights for TRS {user_id}"}


            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
                    
    
    async def add_trs_creation_request(self,model_name,title,description,creator_email, file_url_header):
        """
    Submits a new TRS creation request to the database.

    Parameters:
    model_name (str): The name of the 3D model associated with the TRS.
    title (str): The title of the TRS creation request.
    description (str): A detailed description of the TRS creation request.
    creator_email (str): The email of the user who is submitting the TRS creation request.
    file_url_header (str): The URL of the header image associated with the TRS creation request.

    Returns:
    None

    Raises:
    HTTPException: If there is an error connecting to the database or submitting the TRS creation request.
        """
        if not self.connection:
            logger.critical("No database connection")
            return
        try:
            cursor = self.connection.cursor()            
            query = "INSERT INTO trs_creation_requests (model_name, title, description, creator_email, file_url_header) VALUES (%s, %s, %s,%s,%s)"
            values = (model_name,title, description, creator_email, file_url_header)
            cursor.execute(query, values)
            self.connection.commit()
            logger.info(f"New TRS request submitted from {creator_email} with title {title}.")

        except Error as e:
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

        finally:
            cursor.close()

    async def get_trs_creation_requests(self,status):
        
        if not self.connection:
            logger.critical("No database connection")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM trs_creation_requests WHERE status = %s"
            cursor.execute(query, (status,))
            result = cursor.fetchall()
            return result
        except Error as e:
            
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
        finally:
            cursor.close()
    
    
    async def get_trs_creation_data(self,id):
        if not self.connection:
            logger.critical("No database connection")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM trs_creation_requests WHERE id = %s"
            cursor.execute(query, (id,))
            result = cursor.fetchall()
            return result
        except Error as e:
            
            logger.error(f"Error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
            
        finally:
            cursor.close()

    async def add_collection_data(self,name,creator,description,number,url_header):
        if not self.connection:
            logger.critical("No Database connection.")
        else:
            try:
                cursor = self.connection.cursor()
                user_id = str(uuid.uuid4())
                cid = storage.get_file_cid(f'{url_header}thumbnail.png')
                image_uri = 'https://ipfs.filebase.io/ipfs/' + str(cid)
                query = "INSERT INTO collection_data (name,creator, description, number, image_uri) VALUES (%s, %s, %s,%s,%s)"
                
                values = (name,creator,description,number,image_uri)
                cursor.execute(query, values)
                self.connection.commit()
                logger.info(f"Collection data has been added for {name} . ")
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            finally:
                cursor.close()
                
        
    async def approve_trs_creation_request(self,id,creator_email,number,mint_address,collection_name,token_account_address):

        if not self.connection:
            logger.critical("No Database connection.")
        else:
            try: 
                cursor = self.connection.cursor(dictionary=True)

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
                
                self.connection.commit()
            except Error as e:
                logger.error(f"Error: {e}")
                raise HTTPException(status_code=400, detail=str(e))

            finally: 
                cursor.close()
    

    