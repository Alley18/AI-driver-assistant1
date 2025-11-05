from arango import ArangoClient

# Connect to ArangoDB server
client = ArangoClient()

# setup
DB_NAME = "iDASdb"
USERNAME = "root"
PASSWORD = "needhelp"

# system connection
sys_db = client.db("_system", username=USERNAME, password=PASSWORD)

# if not exist, create
if not sys_db.has_database(DB_NAME):
    sys_db.create_database(DB_NAME)

# connect actual db
db = client.db(DB_NAME, username=USERNAME, password=PASSWORD)

# Create collections if missing
for name in ["state", "event", "users"]:
    if not db.has_collection(name):
        db.create_collection(name)
