from flask import jsonify
from app.db.arango_db import db
import bcrypt

#-------------------------------------------------------
#-----------------------login---------------------------
#-------------------------------------------------------

def hash_password(plain_password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def auth_match(name, password):
    
    query = """
    FOR u IN users
      FILTER u.username == @name || u.email == @name
      RETURN u
    """
    cursor = db.aql.execute(query, bind_vars={"name": name})
    user = next(cursor, None)

    if not user:
        return False, "Invalid username or password", None, None

    if not check_password(password, user.get('password_hash', '')):
        return False, "Invalid username or password", None, None

    return True, None, user['_key'], user['username']

#--------------------------------------------------
#---------------find id----------------------------
#--------------------------------------------------

#return to client

#return to client
def get_userid(username):
    query = """
    FOR user IN users
    FILTER user.username == @username
    RETURN user._key
    """
    cursor = db.aql.execute(query, bind_vars={"username": username})
    result = next(cursor, None)
    if result:
        return result  
    else:
        return None  

#use for mapping
def get_deviceid(user_id):
    query = """
    FOR device IN users_devices
    FILTER device.user_id == @user_id
    RETURN device.device_id
    """

    cursor = db.aql.execute(query, bind_vars={"user_id": user_id})
    return next(cursor, None)

#--------------------------------------------------
#---------------validate ----------------------------
#--------------------------------------------------

def is_userid_provided(userid):
    # If no username provided
    if not userid:
        return jsonify({"error": "Username required"}), 400

def is_authorized_device(device_id):
    query = """
    FOR d IN authorized_device
        FILTER d.device_id == @device_id
        RETURN d
    """
    cursor = db.aql.execute(query, bind_vars={"device_id": device_id})
    # Return True if any document is found
    return any(cursor)