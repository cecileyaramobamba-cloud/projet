from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# =====================================================
# TABLE UTILISATEURS
# =====================================================
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    tuteur = db.relationship("Tuteur", back_populates="user", uselist=False, cascade="all, delete-orphan")
    etudiant = db.relationship("Etudiant", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

# =====================================================
# TABLE MATIERES
# =====================================================
class Matiere(db.Model):
    __tablename__ = "matieres"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(80), unique=True, nullable=False)
    icone = db.Column(db.String(10), default="📚")
    description = db.Column(db.String(255))

# =====================================================
# TABLE TUTEURS
# =====================================================
class Tuteur(db.Model):
    __tablename__ = "tuteurs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    matiere = db.Column(db.String(80), nullable=False)
    statut = db.Column(db.String(20), default="En attente")
    date_inscription = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="tuteur")

# =====================================================
# TABLE ETUDIANTS (CORRIGÉE : Ajout de 'etablissement')
# =====================================================
class Etudiant(db.Model):
    __tablename__ = "etudiants"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nom = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    niveau = db.Column(db.String(80))
    # Ajout du champ pour correspondre au formulaire
    etablissement = db.Column(db.String(120)) 
    date_inscription = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="etudiant")

# =====================================================
# AUTRES TABLES (Annonce, Paiement, Reservation, Avis)
# inchangées, conservées telles quelles pour la structure
# =====================================================
class Annonce(db.Model):
    __tablename__ = "annonces"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    public = db.Column(db.String(20), default="Tous")
    date_publication = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Paiement(db.Model):
    __tablename__ = "paiements"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(30), unique=True, nullable=False)
    montant = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(20), default="En attente")
    date_paiement = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    tuteur_id = db.Column(db.Integer, db.ForeignKey("tuteurs.id"), nullable=True)
    tuteur = db.relationship("Tuteur", backref="paiements")

class Reservation(db.Model):
    __tablename__ = "reservations"
    id = db.Column(db.Integer, primary_key=True)
    etudiant_id = db.Column(db.Integer, db.ForeignKey("etudiants.id"), nullable=False)
    tuteur_id = db.Column(db.Integer, db.ForeignKey("tuteurs.id"), nullable=False)
    matiere = db.Column(db.String(80), nullable=False)
    date_seance = db.Column(db.DateTime, nullable=False)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    statut = db.Column(db.String(20), default="En attente")
    etudiant = db.relationship("Etudiant", backref="reservations")
    tuteur = db.relationship("Tuteur", backref="reservations")

class Avis(db.Model):
    __tablename__ = "avis"
    id = db.Column(db.Integer, primary_key=True)
    tuteur_id = db.Column(db.Integer, db.ForeignKey("tuteurs.id"), nullable=False)
    eleve = db.Column(db.String(120), nullable=False)
    note = db.Column(db.Integer, nullable=False)
    commentaire = db.Column(db.Text)
    date_avis = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    tuteur = db.relationship("Tuteur", backref="avis")