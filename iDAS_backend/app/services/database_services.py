from app.db.arango_db import db
from app.services.time_services import preprocess_timestamp

def get_user_id_by_username(username):

    query = """
    FOR user IN users
    FILTER user.username == @username 
    RETURN user._key
    """

    cursor = db.aql.execute(query, bind_vars={"username": username})
    return next(cursor, None)

def add_user_id(data: dict, username):
    pass

def save_state(data: dict): 
    data = preprocess_timestamp(data)
    try:
        col = db.collection("state")  
        col.insert(data)  
        print("[DB] State saved:", data)
    except Exception as e:
        print("[Error] Failed to save state:", e)


def save_event(data: dict): 
    data = preprocess_timestamp(data)
    try:
        col = db.collection("event")  
        col.insert(data)  
        print("[DB] Event saved:", data)
    except Exception as e:
        print("[Error] Failed to save event:", e)

def save_user(data: dict): 
    try:
        col = db.collection("user")  
        col.insert(data)  
        print("[DB] User saved:", data)
    except Exception as e:
        print("[Error] Failed to save user:", e)