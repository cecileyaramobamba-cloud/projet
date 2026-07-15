import os
from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env dans l'environnement
load_dotenv()


class Config:
    # Active/désactive le mode debug de Flask
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    # Clé secrète utilisée pour signer les sessions et les cookies
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # URL de connexion à la base de données (SQLite en local)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
