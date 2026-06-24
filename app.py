from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

import os

from database.db import db

from routes.auth_routes import auth_bp
from routes.geojson_routes import geojson_bp
from routes.chat_routes import chat_bp
from routes.historial_routes import historial_bp
from routes.user_routes import user_bp
from routes.conversacion_routes import (conversacion_bp)

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(geojson_bp, url_prefix="/api")
app.register_blueprint(chat_bp, url_prefix="/api")
app.register_blueprint(historial_bp,url_prefix="/api")
app.register_blueprint(user_bp,url_prefix="/api")
app.register_blueprint(conversacion_bp,url_prefix="/api")

@app.route("/")
def home():

    return {
        "mensaje": "Backend movilidad IA funcionando"
    }

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(
        debug=True,
        port=5000
    )