from app.db.arango_db import db
from app.services.time_services import preprocess_timestamp
from app.services.auth_services import hash_password
from arango.exceptions import DocumentInsertError


#----------------------------------------------------------#
#-------------------hardware ingest------------------------#
#----------------------------------------------------------#
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

#----------------------------------------------------------#
#-------------------frontend ingest------------------------#
#----------------------------------------------------------#

#/signup-route
def save_user(data: dict):
    try:
        col = db.collection("users")
        col.insert(data)
        print("[DB] User saved:", data)
        return True, "User saved successfully"
    except DocumentInsertError as e:
        print("[DB ERROR] Insert failed:", e)
        if 'unique constraint violated' in str(e).lower():
            return False, "Username already exists"
        return False, "Insert failed"
    except Exception as e:
        print("[ERROR]", e)
        return False, str(e)



#/register-device
def save_device(data: dict):
    try:
        user_id = data.get("user_id")
        if not user_id:
            return {"error": "missing user_id"}

        query = """
        UPSERT { user_id: @user_id }
        INSERT @data
        UPDATE @data
        IN users_devices
        """
        bind_vars = {"user_id": user_id, "data": data}

        db.aql.execute(query, bind_vars=bind_vars)
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        return {"error": str(e)}


#----------------------------------------------------------#
#-------------------session ingest-------------------------#
#----------------------------------------------------------#
def save_session(data: dict): 
    try:
        col = db.collection('sessions')
        col.insert(data)
        print("[DB] Session saved:", data)
    except Exception as e:
        print("[Error] Failed to save session:", e)

#----------------------------------------------------------#
#-------------------summary ingest-------------------------#
#----------------------------------------------------------#
def save_trend(data: dict): 
    try:
        col = db.collection("trend")  
        col.insert(data)  
        print("[DB] Trend generated:", data)
    except Exception as e:
        print("[Error] Failed to store trend summary:", e)