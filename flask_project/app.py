from flask import Flask
from config import Config
from models import db
from routes import main


def create_app():
    # Factory : construit et configure l'application Flask
    app = Flask(__name__)

    # Charge DEBUG, SECRET_KEY et SQLALCHEMY_DATABASE_URI depuis config.py (.env)
    app.config.from_object(Config)

    # Initialise SQLAlchemy avec cette application
    db.init_app(app)

    # Enregistrement du Blueprint contenant toutes les routes (routes.py)
    app.register_blueprint(main)

    # Crée les tables manquantes (User, Matiere, Tuteur, Annonce, ...) au démarrage
    with app.app_context():
        db.create_all()

    return app