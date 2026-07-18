# Ce fichier définit le schéma de la base de données via les modèles SQLAlchemy.
# Chaque classe correspond à une table ; les relations décrivent les liens
# entre elles (clé étrangère + relation ORM pour la navigation objet).
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# =====================================================
# TABLE UTILISATEURS
# =====================================================
# Compte de connexion générique. Un User peut être un simple compte admin,
# ou être prolongé par un profil Tuteur ou Etudiant (relations 1-1 ci-dessous).
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # Mot de passe stocké sous forme de hash (jamais en clair), voir werkzeug.security
    password_hash = db.Column(db.String(255), nullable=False)
    # Seul un compte peut avoir is_admin=True ; posé uniquement dans app.py
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # cascade="all, delete-orphan" : supprimer le User supprime aussi son profil lié
    tuteur = db.relationship("Tuteur", back_populates="user", uselist=False, cascade="all, delete-orphan")
    etudiant = db.relationship("Etudiant", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

# =====================================================
# TABLE MATIERES
# =====================================================
# Catalogue des matières proposées sur la plateforme (affiché sur la page publique)
class Matiere(db.Model):
    __tablename__ = "matieres"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    icone = db.Column(db.String(10), default="📚")
    description = db.Column(db.String(255))

# =====================================================
# TABLE TUTEURS
# =====================================================
# Profil tuteur, lié à un User. Un nouveau tuteur démarre avec statut
# "En attente" et doit être validé par un admin avant d'apparaître publiquement.
class Tuteur(db.Model):
    __tablename__ = "tuteurs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    matiere = db.Column(db.String(80), nullable=False)
    # "En attente" -> "Actif" (validé par l'admin) ou supprimé si refusé
    statut = db.Column(db.String(20), default="En attente")
    date_inscription = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="tuteur")

# =====================================================
# TABLE ETUDIANTS
# =====================================================
# Profil étudiant, lié à un User (même principe que Tuteur ci-dessus)
class Etudiant(db.Model):
    __tablename__ = "etudiants"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    niveau = db.Column(db.String(80))
    etablissement = db.Column(db.String(120))
    date_inscription = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="etudiant")

# =====================================================
# AUTRES TABLES (Annonce, Paiement, Reservation, Avis)
# =====================================================

# Annonce publiée par un admin, visible sur le tableau de bord (tous ou ciblée)
class Annonce(db.Model):
    __tablename__ = "annonces"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    # Public visé : "Tous", "Tuteurs" ou "Étudiants"
    public = db.Column(db.String(20), default="Tous")
    date_publication = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# Paiement reçu par un tuteur pour une ou plusieurs séances données
class Paiement(db.Model):
    __tablename__ = "paiements"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(30), unique=True, nullable=False)
    montant = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(20), default="En attente")
    date_paiement = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    tuteur_id = db.Column(db.Integer, db.ForeignKey("tuteurs.id"), nullable=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiants.id"), nullable=True)
    reservation_id = db.Column(db.Integer, db.ForeignKey("reservations.id"), nullable=True)
    tuteur = db.relationship("Tuteur", backref="paiements")
    etudiant = db.relationship("Etudiant", backref="paiements")
    reservation = db.relationship("Reservation", backref=db.backref("paiement", uselist=False))

# Réservation d'une séance entre un étudiant et un tuteur pour une matière donnée
class Reservation(db.Model):
    __tablename__ = "reservations"
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiants.id"), nullable=False)
    tuteur_id = db.Column(db.Integer, db.ForeignKey("tuteurs.id"), nullable=False)
    matiere = db.Column(db.String(80), nullable=False)
    date_seance = db.Column(db.DateTime, nullable=False)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # "En attente" -> "Confirmée" (acceptée) / "Annulée" (refusée) / "Terminée"
    statut = db.Column(db.String(20), default="En attente")
    etudiant = db.relationship("Etudiant", backref="reservations")
    tuteur = db.relationship("Tuteur", backref="reservations")

# Avis (note + commentaire) laissé par un élève sur un tuteur
class Avis(db.Model):
    __tablename__ = "avis"
    id = db.Column(db.Integer, primary_key=True)
    tuteur_id = db.Column(db.Integer, db.ForeignKey("tuteurs.id"), nullable=False)
    eleve = db.Column(db.String(120), nullable=False)
    # Note sur 5, utilisée pour calculer la moyenne du tuteur
    note = db.Column(db.Integer, nullable=False)
    commentaire = db.Column(db.Text)
    date_avis = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    tuteur = db.relationship("Tuteur", backref="avis")