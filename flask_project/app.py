from flask import Flask, session
from config import Config
from models import db 

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Initialize Database
    db.init_app(app)

    # 2. Import and Register Blueprint strictly after DB initialization
    # We use a local import to break circular dependency cycles
    from routes import main
    app.register_blueprint(main)

    # 3. Context Processor
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
                prenom = session.get('prenom', 'Utilisateur')
            return dict(current_user=LoggedUser())
            
        return dict(current_user=GuestUser())

    # 4. Create Tables
    with app.app_context():
        db.create_all()

    return app