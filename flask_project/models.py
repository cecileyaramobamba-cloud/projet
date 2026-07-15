from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# =====================================================
# Initialisation de SQLAlchemy
# =====================================================
db = SQLAlchemy()


# =====================================================
# TABLE UTILISATEURS
# =====================================================
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # Relation 1-1 avec un tuteur
    tuteur = db.relationship(
        "Tuteur",
        back_populates="user",
        uselist=False
    )

    def __repr__(self):
        return f"<User {self.email}>"


# =====================================================
# TABLE MATIERES
# =====================================================
class Matiere(db.Model):
    __tablename__ = "matieres"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    icone = db.Column(
        db.String(10),
        default="📚"
    )

    description = db.Column(db.String(255))

    def __repr__(self):
        return f"<Matiere {self.nom}>"


# =====================================================
# TABLE TUTEURS
# =====================================================
class Tuteur(db.Model):
    __tablename__ = "tuteurs"

    id = db.Column(db.Integer, primary_key=True)

    # Liaison obligatoire avec la table users
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    nom = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    matiere = db.Column(
        db.String(80),
        nullable=False
    )

    statut = db.Column(
        db.String(20),
        default="En attente"
    )

    date_inscription = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    # Relation avec User
    user = db.relationship(
        "User",
        back_populates="tuteur"
    )

    def __repr__(self):
        return f"<Tuteur {self.nom}>"


# =====================================================
# TABLE ANNONCES
# =====================================================
class Annonce(db.Model):
    __tablename__ = "annonces"

    id = db.Column(db.Integer, primary_key=True)

    titre = db.Column(
        db.String(150),
        nullable=False
    )

    contenu = db.Column(
        db.Text,
        nullable=False
    )

    public = db.Column(
        db.String(20),
        default="Tous"
    )

    date_publication = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Annonce {self.titre}>"


# =====================================================
# TABLE ETUDIANTS
# =====================================================
class Etudiant(db.Model):
    __tablename__ = "etudiants"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    niveau = db.Column(db.String(80))

    date_inscription = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Etudiant {self.nom}>"


# =====================================================
# TABLE PAIEMENTS
# =====================================================
class Paiement(db.Model):
    __tablename__ = "paiements"

    id = db.Column(db.Integer, primary_key=True)

    reference = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    eleve = db.Column(
        db.String(120),
        nullable=False
    )

    matiere = db.Column(db.String(80))

    montant = db.Column(
        db.Integer,
        nullable=False
    )

    statut = db.Column(
        db.String(20),
        default="En attente"
    )

    date_paiement = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    tuteur_id = db.Column(
        db.Integer,
        db.ForeignKey("tuteurs.id")
    )

    tuteur = db.relationship(
        "Tuteur",
        backref="paiements"
    )

    def __repr__(self):
        return f"<Paiement {self.reference}>"


# =====================================================
# TABLE AVIS
# =====================================================
class Avis(db.Model):
    __tablename__ = "avis"

    id = db.Column(db.Integer, primary_key=True)

    eleve = db.Column(
        db.String(120),
        nullable=False
    )

    note = db.Column(
        db.Integer,
        nullable=False
    )

    commentaire = db.Column(db.Text)

    date_avis = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    tuteur_id = db.Column(
        db.Integer,
        db.ForeignKey("tuteurs.id"),
        nullable=False
    )

    tuteur = db.relationship(
        "Tuteur",
        backref="avis"
    )

    def __repr__(self):
        return f"<Avis {self.eleve} - {self.note}>"


# =====================================================
# TABLE RESERVATIONS
# =====================================================
class Reservation(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)

    matiere = db.Column(
        db.String(80),
        nullable=False
    )

    date_seance = db.Column(
        db.Date,
        nullable=False
    )

    heure_debut = db.Column(
        db.String(5),
        nullable=False
    )

    heure_fin = db.Column(
        db.String(5),
        nullable=False
    )

    lieu = db.Column(
        db.String(80),
        default="En ligne"
    )

    statut = db.Column(
        db.String(20),
        default="En attente"
    )

    date_creation = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    etudiant_id = db.Column(
        db.Integer,
        db.ForeignKey("etudiants.id"),
        nullable=False
    )

    tuteur_id = db.Column(
        db.Integer,
        db.ForeignKey("tuteurs.id"),
        nullable=False
    )

    etudiant = db.relationship(
        "Etudiant",
        backref="reservations"
    )

    tuteur = db.relationship(
        "Tuteur",
        backref="reservations"
    )

    def __repr__(self):
        return f"<Reservation {self.id}>"