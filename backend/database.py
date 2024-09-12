import mysql.connector
from mysql.connector import Error
import uuid

class DatabaseManager:
    def __init__(self, host, user, password, database):
        """
        Initialize a new instance of the DatabaseManager class.

        This method establishes a connection to a MySQL database using the provided host, user, password, and database.
        If the connection is successful, it prints a success message. If an error occurs during the connection, it prints
        the error message and sets the connection to None.

        Parameters:
        - host (str): The host address of the MySQL database.
        - user (str): The username for the MySQL database.
        - password (str): The password for the MySQL database.
        - database (str): The name of the MySQL database.

        Returns:
        - None
        """
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            if self.connection.is_connected():
                print("Successfully connected to the database")
        except Error as e:
            print(f"Error: {e}")
            self.connection = None

    def add_user(self, username, email, password_hash):
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
            print("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            user_id = uuid.uuid4()
            query = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            values = (user_id,username, email, password_hash)
            cursor.execute(query, values)
            self.connection.commit()
            print(f"User {username} with id {user_id} added successfully")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()

    def get_user(self, user_id):
        """
        Retrieves a user's details from the database based on the provided user ID.

        Parameters:
        - user_id (int): The unique identifier of the user.

        Returns:
        - dict: A dictionary containing the user's details if the user exists in the database.
                 If the user does not exist or there is an error, returns None.
        """
        if not self.connection:
            print("No database connection")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()

    def get_user_by_email(self, email):
        """
        Retrieves a user's details from the database based on the provided email address.

        Parameters:
        - email (str): The email address of the user.

        Returns:
        - dict: A dictionary containing the user's details if the user exists in the database.
                 If the user does not exist or there is an error, returns None.
        """
        if not self.connection:
            print("No Database Connection")
            return
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()
            
    def update_user(self, user_id, username=None, email=None, password_hash=None):
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
            print("No database connection")
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
                print("No updates provided")
                return
            query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s"
            values.append(user_id)
            cursor.execute(query, tuple(values))
            self.connection.commit()
            print("User updated successfully")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()

    def delete_user(self, user_id):
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
            print("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            self.connection.commit()
            print(f"User {user_id} deleted successfully")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()

    def add_asset(self, user_id, trs_id, collection_id,creator):
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
            print("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO trs (user_id,trs_id,collection_id,creator) VALUES (%s, %s,%s,%s)"
            values = (user_id, trs_id, collection_id,creator)
            cursor.execute(query, values)
            self.connection.commit()
            print(f"Token {trs_id} added to {user_id}'s wallet.")
        except Error as e:
            print(f"Error: {e}")
        
    def get_owner(self, trs_id):
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
            print("No database connection")
            return None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT user_id FROM trs WHERE trs_id = %s"
            cursor.execute(query, (trs_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
    
    def add_transaction(self, transaction_number, trs_id, buyer_id, seller_id, amount, number):
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
            print('No Database Connection')
        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO transactions (transaction_number,trs_id,buyer_id,seller_id,amount,number) VALUES (%s, %s,%s,%s,%s)"
            values = (transaction_number, trs_id, buyer_id, seller_id, amount, number)
            cursor.execute(query, values)
            self.connection.commit()
            print(f"Transaction {transaction_number} added successfully")
        except Error as e:
            print(f"Error: {e}")
            
    def transfer_asset(self, user_id, trs_id):
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
            print("No database connection")
        try:
            cursor = self.connection.cursor()
            query = f"UPDATE trs SET user_id = %s WHERE trs_id = %s"

            cursor.execute(query, (user_id, trs_id))
            print(f"Transferred TRS {trs_id} to {user_id}.")
        except Error as e:
            print(f"Error: {e}")
    
    
    def close_connection(self):
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
            print("Database connection closed")
            
    def add_trs(self,number, mint_address, collection_name, token_account_address,creator_id):
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
            print("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            for i in range(number):
                trs_id = uuid.uuid4().int
                query = f"INSERT INTO collections (trs_id, collection_name, mint_address, token_account_address,creator_id) VALUES (%s, %s, %s, %s,%s)"
                values =  (str(trs_id), collection_name, str(mint_address), str(token_account_address),str(creator_id))
                cursor.execute(query, values)
                self.connection.commit()
                print(f"Token {trs_id} ; {str(i+1)} of collection {collection_name} added successfully")
                self.add_asset(creator_id, trs_id, collection_name,creator_id)
        except Error as e:
            print(f"Error: {e}")

    def add_paypal_transaction(self, transaction_number, buyer_id, seller_id, amount, transaction_date):
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
            print("No database connection")
            return
        try:
            cursor = self.connection.cursor()
            query = f"INSERT INTO paypal_transactions (transaction_id, buyer_id, seller_id, amount) VALUES (%s,%s,%s,%s)"
            values = (str(transaction_number), str(buyer_id), str(seller_id), amount)

            cursor.execute(query, values)
            print(f"Added PayPal transaction with transaction number {transaction_number}")
        except Error as e:
            print(f"Error: {e}")
    