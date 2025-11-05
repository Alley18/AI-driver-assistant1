from flask import Flask
from .api.routes import api_bp
#from .extensions import socketio_obj

def create_app():
    app = Flask(__name__)
    app.register_blueprint(api_bp, url_prefix="/api")
    return app
