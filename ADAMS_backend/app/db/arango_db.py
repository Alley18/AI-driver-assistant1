from arango import ArangoClient

# Connect to ArangoDB server
client = ArangoClient()

# setup
DB_NAME = "ADAMSdb"
USERNAME = "root"
PASSWORD = "123"

# system connection
sys_db = client.db("_system", username=USERNAME, password=PASSWORD)

# if not exist, create
if not sys_db.has_database(DB_NAME):
    sys_db.create_database(DB_NAME)

# connect actual db
db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)

# Create collections if missing
for name in ["state", "event", "sessions", "summary", "trend", "users", 
             "users_devices", "authorized_device", "feedback"]:
    if not db.has_collection(name):
        db.create_collection(name)