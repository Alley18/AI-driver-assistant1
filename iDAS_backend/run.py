from flask_cors import CORS
from app import create_app
#from app.extensions import socketio_obj

app = create_app()
CORS(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
