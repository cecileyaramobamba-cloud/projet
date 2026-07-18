import os
from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env dans l'environnement
load_dotenv()


class Config:
    # Active/désactive le mode debug de Flask
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")

    # Clé secrète utilisée pour signer les sessions et les cookies
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # URL de connexion à la base de données (SQLite en local, PostgreSQL en prod)
    # Render (et d'autres hébergeurs) fournissent une URL préfixée "postgres://",
    # non reconnue par SQLAlchemy 1.4+/2.0 qui exige "postgresql://".
    _database_url = os.environ.get("DATABASE_URL", "sqlite:///database.db")
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Identifiants du compte administrateur unique, créé automatiquement
    # au démarrage s'il n'existe pas encore (voir app.py)
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@edusen.sn")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMoi123!")
