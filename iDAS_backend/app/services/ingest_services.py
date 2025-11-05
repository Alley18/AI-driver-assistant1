from app.services.database_services import save_state, save_event

def store_state(payload: dict):
    state_data = payload.get("state")
    save_state(state_data)
    return {"status": "processed"}

def store_event(payload: dict):
    result_data = payload.get("event") 
    save_event(result_data)
    return {"status": "processed"}

def store_user(payload: dict):
    result_data = payload.get("user") 
    save_event(result_data)
    return {"status": "processed"}