# EduSen

EduSen est une application web Flask de mise en relation entre tuteurs et étudiants : inscription, recherche de tuteurs par matière, réservation de séances, messagerie, avis, paiements et back-office administrateur.

## Fonctionnalités

- **Authentification** : inscription étudiant / tuteur, connexion, sessions sécurisées.
- **Espace étudiant** : tableau de bord, recherche de cours, réservations, devoirs, messagerie, profil.
- **Espace tuteur** : tableau de bord, gestion des disponibilités, des cours, des étudiants, des revenus et des avis.
- **Espace administrateur** : gestion des utilisateurs, tuteurs, étudiants, matières, annonces, paiements, réservations et statistiques.
- **Pages publiques** : accueil, liste des tuteurs, matières, FAQ, à propos, contact, recrutement.

## Stack technique

- [Flask](https://flask.palletsprojects.com/) 3.1
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) + [Flask-Migrate](https://flask-migrate.readthedocs.io/) (SQLite en local)
- [Flask-WTF](https://flask-wtf.readthedocs.io/) pour les formulaires
- Jinja2 pour les templates

## Prérequis

- Python 3.11+
- pip

## Installation

```bash
# Cloner le dépôt puis se placer dans le dossier du projet
cd edusen

# Créer et activer un environnement virtuel
python -m venv venv
venv/Scripts/activate      # Windows
source venv/bin/activate   # macOS / Linux

# Installer les dépendances
pip install -r requirements.txt
```

## Configuration

Créer un fichier `.env` à la racine du projet (non versionné) avec les variables suivantes :

```env
FLASK_DEBUG=True
SECRET_KEY=une_cle_secrete_aleatoire
DATABASE_URL=sqlite:///database.db
```

## Lancer l'application

```bash
python run.py
```

L'application est accessible sur [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Structure du projet

```
edusen/
├── app.py              # Factory de l'application Flask
├── run.py              # Point d'entrée pour lancer le serveur
├── config.py           # Configuration (variables d'environnement)
├── models.py            # Modèles SQLAlchemy (User, Tuteur, Etudiant, Reservation, ...)
├── forms.py             # Formulaires WTForms
├── routes.py             # Routes de l'application
├── requirements.txt
└── templates/
    ├── accueil/          # Page d'accueil
    ├── auth/              # Connexion / inscription
    ├── etudiant/          # Espace étudiant
    ├── tuteur/            # Espace tuteur
    ├── admin/             # Back-office
    ├── public/            # Pages publiques (matières, contact, FAQ, ...)
    └── fragments/         # Navbar, footer
```

## Base de données

Les migrations sont gérées avec Flask-Migrate (Alembic) :

```bash
flask db init      # une seule fois
flask db migrate -m "message"
flask db upgrade
```

## Déploiement (Render)

Le projet se déploie sur [Render](https://render.com) via le fichier [`render.yaml`](render.yaml) à la racine du dépôt (Blueprint), qui décrit :

- un service web Python (`gunicorn run:app`)
- une base PostgreSQL gratuite (`edusen-db`), branchée automatiquement sur `DATABASE_URL`

### Étapes

1. Sur [render.com](https://render.com), connecter le compte GitHub puis choisir **New +** → **Blueprint** et sélectionner le dépôt.
2. Render détecte `render.yaml` et propose de créer le service web + la base : valider.
3. Render demande de saisir manuellement `ADMIN_EMAIL` et `ADMIN_PASSWORD` (marqués `sync: false` dans le blueprint, donc jamais stockés dans le code versionné) — utiliser un mot de passe fort, différent de la valeur par défaut de dev.
4. `SECRET_KEY` est généré automatiquement par Render et `FLASK_DEBUG` est forcé à `False`.
5. Chaque push sur la branche configurée redéclenche un déploiement automatique.

### Notes

- SQLite (utilisé en local) n'est pas adapté à Render : le disque du service web est éphémère, les données seraient perdues à chaque redémarrage/redéploiement. En prod, `DATABASE_URL` pointe donc vers la base PostgreSQL gérée par Render.
- `config.py` convertit automatiquement les URL `postgres://` (format fourni par Render) en `postgresql://`, requis par SQLAlchemy 2.0.
- Le compte administrateur unique est (re)créé automatiquement au démarrage de l'app à partir de `ADMIN_EMAIL` / `ADMIN_PASSWORD` (voir `_ensure_admin_account` dans `app.py`).
