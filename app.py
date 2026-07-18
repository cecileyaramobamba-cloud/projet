from flask import Flask, session
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash
from config import Config
from models import db, User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Initialisation de la base de données
    db.init_app(app)

    # 2. Import et enregistrement du blueprint, strictement après l'initialisation de la BDD
    # Import local pour éviter les cycles de dépendances circulaires
    from routes import main
    app.register_blueprint(main)

    # 3. Injecteur de contexte : rend `current_user` disponible dans tous les templates
    # sans avoir à le passer manuellement à chaque render_template()
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

    # 4. Création des tables (si elles n'existent pas déjà)
    with app.app_context():
        db.create_all()
        _ensure_is_admin_column()
        _ensure_paiements_columns()
        _ensure_admin_account(app)

    return app


def _ensure_is_admin_column():
    """Ajoute la colonne is_admin si la base existait déjà sans elle.

    db.create_all() ne modifie jamais les tables existantes : sur une base
    SQLite créée avant l'ajout de User.is_admin, la colonne doit être posée
    manuellement pour éviter une erreur "no such column" au premier login.
    """
    inspector = inspect(db.engine)
    if "users" not in inspector.get_table_names():
        return
    colonnes = [c["name"] for c in inspector.get_columns("users")]
    if "is_admin" not in colonnes:
        with db.engine.begin() as connexion:
            connexion.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))


def _ensure_paiements_columns():
    """Ajoute etudiant_id/reservation_id si la base existait avant leur ajout au modèle.

    Même raison que _ensure_is_admin_column() : db.create_all() ne modifie
    jamais les tables déjà présentes.
    """
    inspector = inspect(db.engine)
    if "paiements" not in inspector.get_table_names():
        return
    colonnes = [c["name"] for c in inspector.get_columns("paiements")]
    with db.engine.begin() as connexion:
        if "etudiant_id" not in colonnes:
            connexion.execute(text("ALTER TABLE paiements ADD COLUMN etudiant_id INTEGER REFERENCES etudiants(id)"))
        if "reservation_id" not in colonnes:
            connexion.execute(text("ALTER TABLE paiements ADD COLUMN reservation_id INTEGER REFERENCES reservations(id)"))


def _ensure_admin_account(app):
    """Garantit l'existence d'un unique compte administrateur.

    L'admin ne peut jamais être obtenu via les formulaires d'inscription
    (étudiant/tuteur) : c'est le seul endroit où is_admin=True est posé.
    """
    email = app.config["ADMIN_EMAIL"].strip().lower()
    admin = User.query.filter_by(email=email).first()

    if admin is None:
        admin = User(
            username="admin",
            email=email,
            password_hash=generate_password_hash(app.config["ADMIN_PASSWORD"]),
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()
    elif not admin.is_admin:
        admin.is_admin = True
        db.session.commit()