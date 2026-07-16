from flask import Flask, session
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

    # === INJECTION GLOBALE DE CURRENT_USER DANS JINJA2 ===
    # Permet de simuler current_user à partir des données stockées dans la session
    @app.context_processor
    def inject_current_user():
        class GuestUser:
            is_authenticated = False
            role = None
            prenom = ""

        if session.get('user_id'):
            class LoggedUser:
                is_authenticated = True
                id = session.get('user_id')
                role = session.get('role')
                # Utilise le prénom en session, ou "Utilisateur" par défaut
                prenom = session.get('prenom', 'Utilisateur')
            return dict(current_user=LoggedUser())
            
        return dict(current_user=GuestUser())

    # Crée les tables manquantes au démarrage
    with app.app_context():
        db.create_all()

    return app