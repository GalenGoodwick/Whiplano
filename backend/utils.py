import bcrypt

# Function to hash a password
def hash_password(password):
    # Generate a salt
    salt = bcrypt.gensalt()
    # Hash the password with the salt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Function to check if the password matches the hashed password
def verify_password(password, hashed_password):
    # Verify the password by hashing it with the same salt and comparing
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

