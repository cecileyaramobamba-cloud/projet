from functools import wraps
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, send_from_directory, current_app, session
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Matiere, Tuteur, Annonce, Etudiant, Paiement, Avis, Reservation, User
from forms import RegistrationForm, StudentRegistrationForm, LoginForm

main = Blueprint("main", __name__)

# Libellés courts des mois utilisés pour les graphiques (revenus, statistiques)
MOIS_LABELS_FR = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]

# Fait le lien entre le slug de l'URL (/matieres/<slug>) et le nom affiché,
# utilisé aussi pour filtrer la liste des tuteurs par matière
MATIERES_COURS = {
    "maths": "Mathématiques",
    "informatique": "Informatique",
    "francais": "Français",
    "anglais": "Anglais",
    "physique": "Physique",
    "svt": "SVT",
    "web": "Développement Web",
    "economie": "Économie",
    "droit": "Droit",
    "python": "Python",
    "mysql": "MySQL",
}


# ====================================
# DÉCORATEUR DE SÉCURITÉ DE SESSION
# ====================================
# Protège une route : redirige vers /login si l'utilisateur n'est pas connecté,
# et vers l'accueil si son rôle en session ne correspond pas au rôle attendu.
# Usage : @login_required() pour "connecté uniquement", @login_required(role="admin") pour restreindre le rôle.
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Veuillez vous connecter pour accéder à cette page.", "warning")
                return redirect(url_for("main.login"))

            if role:
                user_role = session.get("role")
                if user_role != role:
                    flash("Accès non autorisé à cet espace.", "danger")
                    return redirect(url_for("main.accueil"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ====================================
# HELPERS DE SESSION SÉCURISÉS
# ====================================
# Récupère le profil Tuteur/Etudiant correspondant à l'utilisateur actuellement
# connecté (via son user_id en session), ou None si personne n'est connecté.
def _tuteur_courant():
    user_id = session.get("user_id")
    if user_id:
        return Tuteur.query.filter_by(user_id=user_id).first()
    return None


def _etudiant_courant():
    user_id = session.get("user_id")
    if user_id:
        return Etudiant.query.filter_by(user_id=user_id).first()
    return None


# ====================================
# UTILS / STATS
# ====================================
# Nombre de tuteurs par matière, triés du plus au moins représenté
# (utilisé pour le graphique "répartition des matières" côté admin)
def _repartition_matieres():
    compte = dict(
        db.session.query(Tuteur.matiere, func.count(Tuteur.id)).group_by(Tuteur.matiere).all()
    )
    return sorted(compte.items(), key=lambda item: item[1], reverse=True)


# Total des paiements "Payé" regroupés par mois, formaté pour un graphique
# (ex: [{"mois": "Jan", "montant": 12000}, ...])
def _paiements_par_mois():
    totaux = {}
    paiements_payes = Paiement.query.filter_by(statut="Payé").all()
    for paiement in paiements_payes:
        if paiement.date_paiement:
            cle = (paiement.date_paiement.year, paiement.date_paiement.month)
            totaux[cle] = totaux.get(cle, 0) + paiement.montant

    return [
        {"mois": MOIS_LABELS_FR[mois - 1], "montant": montant}
        for (_annee, mois), montant in sorted(totaux.items())
    ]


# ====================================
# STATIC / FAVICON / ACCUEIL
# ====================================
@main.route("/favicon.ico")
def favicon():
    return send_from_directory(
        current_app.static_folder,
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )


@main.route("/")
def accueil():
    return render_template("accueil/index.html")


# ====================================
# SYSTEME D'AUTHENTIFICATION & SESSIONS
# ====================================
@main.route("/register_tuteurs", methods=["GET", "POST"])
def register_tuteurs():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        # Un email ou un nom d'utilisateur ne peut être utilisé qu'une seule fois
        if User.query.filter_by(email=email).first():
            flash("Un compte existe déjà avec cet email.", "danger")
            return redirect(url_for("main.register_tuteurs"))

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
            return redirect(url_for("main.register_tuteurs"))

        # Étape 1 : création du compte de connexion (User)
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()

        # Étape 2 : création du profil Tuteur lié, en attente de validation admin
        tuteur = Tuteur(
            user_id=user.id,
            nom=username,
            email=email,
            matiere=form.matiere.data.strip(),
            statut="En attente"
        )
        db.session.add(tuteur)
        db.session.commit()

        # Connexion automatique après inscription
        session.clear()
        session["user_id"] = user.id
        session["role"] = "tuteur"
        session["prenom"] = username

        flash("Compte tuteur créé avec succès ! Bienvenue sur votre espace.", "success")
        return redirect(url_for("main.dashboard_tuteur"))

    return render_template("auth/register_tuteurs.html", form=form)


@main.route("/register_etudiant", methods=["GET", "POST"])
def register_etudiants():
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        if User.query.filter_by(email=email).first():
            flash("Un compte existe déjà avec cet email.", "danger")
            return redirect(url_for("main.register_etudiants"))

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
            return redirect(url_for("main.register_etudiants"))

        # Même principe que l'inscription tuteur : User puis profil Etudiant lié
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()

        etudiant = Etudiant(
            user_id=user.id,
            nom=username,
            email=email,
            niveau=form.niveau.data.strip(),
            etablissement=form.etablissement.data.strip()
        )
        db.session.add(etudiant)
        db.session.commit()

        session.clear()
        session["user_id"] = user.id
        session["role"] = "etudiant"
        session["prenom"] = username

        flash("Compte étudiant créé avec succès ! Bienvenue sur votre espace.", "success")
        return redirect(url_for("main.dashboard_etudiant"))

    return render_template("auth/register_etudiants.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash("Email ou mot de passe incorrect.", "danger")
            return redirect(url_for("main.login"))

        session.clear()
        session["user_id"] = user.id
        session["prenom"] = user.username

        # Le rôle n'est pas stocké sur User : on le déduit en cherchant
        # dans quelle table (admin / Tuteur / Etudiant) ce compte existe
        if user.is_admin:
            session["role"] = "admin"
            flash(f"Bienvenue Administrateur, {user.username} !", "success")
            return redirect(url_for("main.dashboard_admin"))

        tuteur = Tuteur.query.filter_by(user_id=user.id).first()
        if tuteur:
            session["role"] = "tuteur"
            flash(f"Bienvenue Tuteur, {user.username} !", "success")
            return redirect(url_for("main.dashboard_tuteur"))

        etudiant = Etudiant.query.filter_by(user_id=user.id).first()
        if etudiant:
            session["role"] = "etudiant"
            flash(f"Bienvenue Étudiant, {user.username} !", "success")
            return redirect(url_for("main.dashboard_etudiant"))

        flash(f"Bienvenue, {user.username} !", "success")
        return redirect(url_for("main.accueil"))

    return render_template("auth/login.html", form=form)


@main.route("/auth/deconnexion")
@main.route("/logout")
def deconnexion():
    session.clear()
    flash("Vous avez été déconnecté avec succès.", "success")
    return redirect(url_for("main.accueil"))


# ====================================
# ESPACE SÉCURISÉ : ADMIN
# ====================================
@main.route("/admin/dashboard")
@login_required(role="admin")
def dashboard_admin():
    revenus_payes = db.session.query(func.sum(Paiement.montant)).filter_by(statut="Payé").scalar() or 0

    tuteurs_en_attente = (
        Tuteur.query.filter_by(statut="En attente")
        .order_by(Tuteur.date_inscription.desc())
        .limit(5)
        .all()
    )
    derniers_paiements = Paiement.query.order_by(Paiement.date_paiement.desc()).limit(3).all()
    dernieres_reservations = Reservation.query.order_by(Reservation.date_creation.desc()).limit(3).all()

    # Fil d'activité : on agrège les derniers événements de chaque table,
    # puis on les trie tous ensemble par date pour ne garder que les 6 plus récents
    activites = []
    for tuteur in Tuteur.query.order_by(Tuteur.date_inscription.desc()).limit(3):
        activites.append({"icone": "✅", "texte": f"Nouveau tuteur inscrit : {tuteur.nom}", "date": tuteur.date_inscription})
    for etudiant in Etudiant.query.order_by(Etudiant.date_inscription.desc()).limit(3):
        activites.append({"icone": "👨‍🎓", "texte": f"Nouvel étudiant inscrit : {etudiant.nom}", "date": etudiant.date_inscription})
    for avis in Avis.query.order_by(Avis.date_avis.desc()).limit(3):
        activites.append({"icone": "⭐", "texte": f"Nouvel avis publié par {avis.eleve}", "date": avis.date_avis})
    for paiement in Paiement.query.order_by(Paiement.date_paiement.desc()).limit(3):
        activites.append({"icone": "💳", "texte": f"Paiement {paiement.reference} ({paiement.statut})", "date": paiement.date_paiement})
    for reservation in Reservation.query.order_by(Reservation.date_creation.desc()).limit(3):
        activites.append({"icone": "📅", "texte": f"Réservation : {reservation.etudiant.nom} avec {reservation.tuteur.nom}", "date": reservation.date_creation})

    activites.sort(key=lambda a: a["date"] if a["date"] else datetime.min, reverse=True)

    return render_template(
        "admin/dashboard_admin.html",
        nb_tuteurs=Tuteur.query.count(),
        nb_etudiants=Etudiant.query.count(),
        nb_reservations=Reservation.query.count(),
        nb_matieres=Matiere.query.count(),
        nb_avis=Avis.query.count(),
        nb_en_attente=Tuteur.query.filter_by(statut="En attente").count(),
        revenus_payes=revenus_payes,
        tuteurs_en_attente=tuteurs_en_attente,
        derniers_paiements=derniers_paiements,
        dernieres_reservations=dernieres_reservations,
        repartition_matieres=_repartition_matieres(),
        paiements_par_mois=_paiements_par_mois(),
        activites=activites[:6],
    )


@main.route("/admin/reservations")
@login_required(role="admin")
def reservations_admin():
    reservations = Reservation.query.order_by(Reservation.date_seance.desc()).all()
    return render_template("admin/reservation_admin.html", reservations=reservations)


@main.route("/admin/reservations/<int:reservation_id>/confirmer", methods=["POST"])
@login_required(role="admin")
def confirmer_reservation_admin(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Confirmée"
    db.session.commit()
    flash("La réservation a été confirmée.", "success")
    return redirect(request.referrer or url_for("main.reservations_admin"))


@main.route("/admin/reservations/<int:reservation_id>/annuler", methods=["POST"])
@login_required(role="admin")
def annuler_reservation_admin(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Annulée"
    db.session.commit()
    flash("La réservation a été annulée.", "danger")
    return redirect(request.referrer or url_for("main.reservations_admin"))


@main.route("/admin/reservations/<int:reservation_id>/terminer", methods=["POST"])
@login_required(role="admin")
def terminer_reservation_admin(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Terminée"
    db.session.commit()
    flash("La réservation a été marquée comme terminée.", "success")
    return redirect(request.referrer or url_for("main.reservations_admin"))


@main.route("/admin/utilisateurs")
@login_required(role="admin")
def utilisateurs_admin():
    utilisateurs = User.query.all()
    return render_template("admin/utilisateurs_admin.html", utilisateurs=utilisateurs)


@main.route("/admin/tuteurs")
@login_required(role="admin")
def tuteurs_admin():
    tuteurs = Tuteur.query.order_by(Tuteur.date_inscription.desc()).all()
    return render_template("admin/tuteurs_admin.html", tuteurs=tuteurs)


@main.route("/admin/tuteurs/ajouter", methods=["GET", "POST"])
@login_required(role="admin")
def ajouter_tuteur_admin():
    if request.method == "POST":
        nom = (request.form.get("nom") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        matiere = (request.form.get("matiere") or "").strip()

        if not nom or not email or not matiere:
            flash("Merci de renseigner le nom, l'email et la matière du tuteur.", "danger")
            return redirect(url_for("main.ajouter_tuteur_admin"))

        if User.query.filter_by(email=email).first() or Tuteur.query.filter_by(email=email).first():
            flash("Un compte ou un tuteur existe déjà avec cet email.", "danger")
            return redirect(url_for("main.ajouter_tuteur_admin"))

        user = User(
            username=nom,
            email=email,
            password_hash=generate_password_hash("12345678")
        )
        db.session.add(user)
        db.session.commit()

        tuteur = Tuteur(
            user_id=user.id,
            nom=nom,
            email=email,
            matiere=matiere,
            statut="Actif"
        )
        db.session.add(tuteur)
        db.session.commit()

        flash("Le tuteur a été ajouté avec succès et est visible sur la page « Trouver un tuteur ».", "success")
        return redirect(url_for("main.tuteurs_admin"))

    return render_template("admin/ajouter_tuteur.html")


@main.route("/admin/tuteurs/<int:tuteur_id>/valider", methods=["POST"])
@login_required(role="admin")
def valider_tuteur_admin(tuteur_id):
    tuteur = Tuteur.query.get_or_404(tuteur_id)
    tuteur.statut = "Actif"
    db.session.commit()
    flash(f"Le tuteur « {tuteur.nom} » a été validé.", "success")
    return redirect(request.referrer or url_for("main.dashboard_admin"))


@main.route("/admin/tuteurs/<int:tuteur_id>/refuser", methods=["POST"])
@login_required(role="admin")
def refuser_tuteur_admin(tuteur_id):
    tuteur = Tuteur.query.get_or_404(tuteur_id)
    nom = tuteur.nom
    user = User.query.get(tuteur.user_id)

    # Un tuteur refusé n'a pas de raison de garder un compte de connexion :
    # on supprime le profil Tuteur ET le User associé
    db.session.delete(tuteur)
    if user:
        db.session.delete(user)

    db.session.commit()
    flash(f"Le profil et le compte du tuteur « {nom} » ont été supprimés.", "danger")
    return redirect(request.referrer or url_for("main.dashboard_admin"))


@main.route("/admin/etudiants")
@login_required(role="admin")
def etudiants_admin():
    etudiants = Etudiant.query.order_by(Etudiant.date_inscription.desc()).all()
    return render_template("admin/etudiants_admin.html", etudiants=etudiants)


@main.route("/admin/matieres")
@login_required(role="admin")
def matieres_admin():
    matieres = Matiere.query.order_by(Matiere.nom).all()
    compte_tuteurs = dict(
        db.session.query(Tuteur.matiere, func.count(Tuteur.id)).group_by(Tuteur.matiere).all()
    )
    # Attribut ajouté dynamiquement (non stocké en base) pour affichage dans le template
    for m in matieres:
        m.nb_tuteurs = compte_tuteurs.get(m.nom, 0)

    return render_template("admin/matieres_admin.html", matieres=matieres)


@main.route("/admin/matieres/ajouter", methods=["GET", "POST"])
@login_required(role="admin")
def ajouter_matiere_admin():
    if request.method == "POST":
        nom = (request.form.get("nom") or "").strip()
        icone = (request.form.get("icone") or "📚").strip()
        description = (request.form.get("description") or "").strip()

        if not nom:
            flash("Merci de renseigner le nom de la matière.", "danger")
            return redirect(url_for("main.ajouter_matiere_admin"))

        if Matiere.query.filter_by(nom=nom).first():
            flash("Cette matière existe déjà.", "danger")
            return redirect(url_for("main.ajouter_matiere_admin"))

        db.session.add(Matiere(nom=nom, icone=icone, description=description or "Aucune description"))
        db.session.commit()
        flash(f"La matière « {nom} » a été ajoutée avec succès.", "success")
        return redirect(url_for("main.matieres_admin"))

    return render_template("admin/ajouter_matiere.html")


@main.route("/admin/annonces", methods=["GET", "POST"])
@login_required(role="admin")
def annonces_admin():
    if request.method == "POST":
        titre = (request.form.get("titre") or "").strip()
        contenu = (request.form.get("contenu") or "").strip()
        public = (request.form.get("public") or "Tous").strip()

        if not titre or not contenu:
            flash("Merci de renseigner un titre et un contenu pour l'annonce.", "danger")
            return redirect(url_for("main.annonces_admin"))

        db.session.add(Annonce(titre=titre, contenu=contenu, public=public))
        db.session.commit()
        flash("Votre annonce a été publiée avec succès.", "success")
        return redirect(url_for("main.annonces_admin"))

    annonces = Annonce.query.order_by(Annonce.date_publication.desc()).all()
    return render_template("admin/annonces_admin.html", annonces=annonces)


@main.route("/admin/paiements")
@login_required(role="admin")
def paiements_admin():
    paiements = Paiement.query.order_by(Paiement.date_paiement.desc()).all()
    return render_template("admin/paiements_admin.html", paiements=paiements)


@main.route("/admin/paiements/<int:paiement_id>/valider", methods=["POST"])
@login_required(role="admin")
def valider_paiement_admin(paiement_id):
    paiement = Paiement.query.get_or_404(paiement_id)
    paiement.statut = "Payé"
    db.session.commit()

    # Une fois le paiement validé, la réservation liée est automatiquement confirmée
    if paiement.reservation and paiement.reservation.statut == "En attente":
        paiement.reservation.statut = "Confirmée"
        db.session.commit()

    flash(f"Le paiement « {paiement.reference} » a été validé.", "success")
    return redirect(url_for("main.paiements_admin"))


@main.route("/admin/statistiques")
@login_required(role="admin")
def statistiques_admin():
    revenus_totaux = db.session.query(func.sum(Paiement.montant)).filter_by(statut="Payé").scalar() or 0
    satisfaction_moyenne = db.session.query(func.avg(Avis.note)).scalar()

    # Top 3 des tuteurs par note moyenne (nécessite au moins un avis, via le JOIN)
    meilleurs_tuteurs = (
        db.session.query(Tuteur, func.avg(Avis.note).label("moyenne"), func.count(Avis.id).label("nb_avis"))
        .join(Avis, Avis.tuteur_id == Tuteur.id)
        .group_by(Tuteur.id)
        .order_by(func.avg(Avis.note).desc())
        .limit(3)
        .all()
    )

    return render_template(
        "admin/statistiques_admin.html",
        nb_tuteurs_actifs=Tuteur.query.filter_by(statut="Actif").count(),
        nb_etudiants=Etudiant.query.count(),
        revenus_totaux=revenus_totaux,
        satisfaction_moyenne=round(satisfaction_moyenne, 1) if satisfaction_moyenne else None,
        repartition_matieres=_repartition_matieres(),
        nb_tuteurs=Tuteur.query.count(),
        paiements_par_mois=_paiements_par_mois(),
        meilleurs_tuteurs=[
            {"nom": tuteur.nom, "matiere": tuteur.matiere, "note": round(moyenne, 1), "nb_avis": nb_avis}
            for tuteur, moyenne, nb_avis in meilleurs_tuteurs
        ],
    )


@main.route("/admin/parametres", methods=["GET", "POST"])
@login_required(role="admin")
def parametres_admin():
    if request.method == "POST":
        flash("Les paramètres ont été enregistrés avec succès.", "success")
        return redirect(url_for("main.parametres_admin"))
    return render_template("admin/parametres_admin.html")


# ====================================
# ESPACE SÉCURISÉ : ÉTUDIANT
# ====================================
@main.route("/etudiant/dashboard")
@login_required(role="etudiant")
def dashboard_etudiant():
    return render_template("etudiant/dashboard_etudiant.html")


@main.route("/etudiant/messages")
@login_required(role="etudiant")
def messages_etudiant():
    return render_template("etudiant/messages_etudiant.html")


@main.route("/etudiant/profil")
@login_required(role="etudiant")
def profil_etudiant():
    return render_template("etudiant/profil_etudiant.html")


@main.route("/etudiant/reservations")
@login_required(role="etudiant")
def reservations_etudiant():
    etudiant = _etudiant_courant()
    reservations = (
        Reservation.query.filter_by(etudiant_id=etudiant.id).order_by(Reservation.date_seance.desc()).all()
        if etudiant else []
    )
    return render_template("etudiant/reservations.html", reservations=reservations)


@main.route("/etudiant/reservations/<int:reservation_id>/annuler", methods=["POST"])
@login_required(role="etudiant")
def annuler_reservation_etudiant(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Annulée"
    db.session.commit()
    flash("La réservation a été annulée.", "danger")
    return redirect(request.referrer or url_for("main.reservations_etudiant"))


@main.route("/etudiant/cours")
@login_required(role="etudiant")
def cours_etudiant():
    return render_template("etudiant/cours_etudiant.html")


@main.route("/etudiant/devoirs")
@login_required(role="etudiant")
def devoirs_etudiant():
    return render_template("etudiant/devoirs_etudiant.html")


@main.route("/etudiant/examens")
@login_required(role="etudiant")
def examens_etudiant():
    return render_template("etudiant/examens_etudiant.html")


@main.route("/etudiant/certificats")
@login_required(role="etudiant")
def certificats_etudiant():
    return render_template("etudiant/certificats_etudiant.html")


# ====================================
# ESPACE SÉCURISÉ : TUTEUR
# ====================================
@main.route("/tuteur/dashboard")
@login_required(role="tuteur")
def dashboard_tuteur():
    return render_template("tuteur/dashboard_tuteur.html")


@main.route("/tuteur/profil")
@login_required(role="tuteur")
def profil_tuteur():
    tuteur_bdd = _tuteur_courant()
    if not tuteur_bdd:
        flash("Aucun profil tuteur trouvé.", "danger")
        return redirect(url_for("main.accueil"))

    tuteur = {
        "nom": tuteur_bdd.nom,
        "matiere": tuteur_bdd.matiere,
        "experience": "Donnée non renseignée",
        "prix": "À négocier"
    }
    return render_template("tuteur/profil_tuteur.html", tuteur=tuteur)


@main.route("/tuteur/disponibilites")
@login_required(role="tuteur")
def disponibilites_tuteur():
    return render_template("tuteur/disponibilites.html")


@main.route("/tuteur/reservation")
@login_required(role="tuteur")
def reservation_tuteur():
    tuteur = _tuteur_courant()
    reservations = (
        Reservation.query.filter_by(tuteur_id=tuteur.id).order_by(Reservation.date_seance.desc()).all()
        if tuteur else []
    )
    return render_template("tuteur/reservation_tuteur.html", reservations=reservations)


@main.route("/tuteur/reservations/<int:reservation_id>/accepter", methods=["POST"])
@login_required(role="tuteur")
def accepter_reservation_tuteur(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Confirmée"
    db.session.commit()
    flash("La réservation a été acceptée.", "success")
    return redirect(request.referrer or url_for("main.reservation_tuteur"))


@main.route("/tuteur/reservations/<int:reservation_id>/refuser", methods=["POST"])
@login_required(role="tuteur")
def refuser_reservation_tuteur(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Annulée"
    db.session.commit()
    flash("La réservation a été refusée.", "danger")
    return redirect(request.referrer or url_for("main.reservation_tuteur"))


@main.route("/tuteur/cours")
@login_required(role="tuteur")
def cours_tuteur():
    return render_template("tuteur/cours_tuteur.html")


@main.route("/tuteur/messages")
@login_required(role="tuteur")
def messages_tuteur():
    return render_template("tuteur/messages_tuteur.html")


@main.route("/tuteur/etudiants")
@login_required(role="tuteur")
def etudiants_tuteur():
    tuteur = _tuteur_courant()
    etudiants_uniques = []

    if tuteur:
        # Un même étudiant peut avoir plusieurs réservations : on ne veut
        # qu'une seule ligne par étudiant, donc on déduplique avec un set
        reservations = Reservation.query.filter(
            Reservation.tuteur_id == tuteur.id,
            Reservation.statut.in_(["Confirmée", "Terminée"])
        ).all()

        vus = set()
        for res in reservations:
            if res.etudiant_id not in vus:
                vus.add(res.etudiant_id)
                nb_sessions = Reservation.query.filter_by(
                    tuteur_id=tuteur.id,
                    etudiant_id=res.etudiant_id
                ).count()

                etudiants_uniques.append({
                    "nom": res.etudiant.nom,
                    "matiere": res.matiere,
                    "niveau": res.etudiant.niveau or "Non renseigné",
                    "sessions": nb_sessions,
                    "note": "-"
                })

    return render_template("tuteur/etudiants_tuteur.html", etudiants=etudiants_uniques)


@main.route("/tuteur/revenus")
@login_required(role="tuteur")
def revenus_tuteur():
    tuteur = _tuteur_courant()
    paiements = []
    totaux_mensuels = {}

    if tuteur:
        # Somme des paiements "Payé" regroupée par mois pour ce tuteur uniquement
        paiements = Paiement.query.filter_by(tuteur_id=tuteur.id).order_by(Paiement.date_paiement.desc()).all()
        for p in paiements:
            if p.statut == "Payé" and p.date_paiement:
                mois_str = MOIS_LABELS_FR[p.date_paiement.month - 1]
                totaux_mensuels[mois_str] = totaux_mensuels.get(mois_str, 0) + p.montant

    revenus_mensuels = [{"mois": m, "montant": v} for m, v in totaux_mensuels.items()]
    if not revenus_mensuels:
        revenus_mensuels = [{"mois": "Aucun", "montant": 0}]

    return render_template(
        "tuteur/revenus_tuteur.html",
        revenus_mensuels=revenus_mensuels,
        total_revenus=sum(r["montant"] for r in revenus_mensuels),
        paiements=paiements
    )


@main.route("/tuteur/avis")
@login_required(role="tuteur")
def avis_tuteur():
    tuteur = _tuteur_courant()
    avis = (
        Avis.query.filter_by(tuteur_id=tuteur.id).order_by(Avis.date_avis.desc()).all()
        if tuteur else []
    )
    note_moyenne = round(sum(a.note for a in avis) / len(avis), 1) if avis else 0
    return render_template(
        "tuteur/avis_tuteur.html",
        avis=avis,
        note_moyenne=note_moyenne
    )


# ====================================
# PUBLIC / CHATBOT / PAGES STATIQUES
# ====================================
# Chatbot simple basé sur la détection de mots-clés (pas d'IA/LLM ici) :
# on répond dès qu'un mot-clé attendu est trouvé dans le message de l'utilisateur.
def generer_reponse_chatbot(message):
    message = message.lower()
    if any(mot in message for mot in ("bonjour", "salut", "hello")):
        return "Bonjour ! Je suis l'assistant IA d'EduSen 🤖 Comment puis-je vous aider aujourd'hui ?"
    if "tuteur" in message:
        return "Vous pouvez trouver un tuteur depuis la section « Trouver un tuteur » du menu."
    if "reservation" in message or "réservation" in message:
        return "Vous pouvez consulter et gérer vos réservations dans l'onglet « Réservations » de votre tableau de bord."
    if "devoir" in message:
        return "Retrouvez tous vos devoirs en cours dans la section « Devoirs »."
    if "cours" in message:
        return "La liste de vos cours est disponible dans la section « Mes cours »."
    if any(mot in message for mot in ("prix", "tarif", "coût", "cout")):
        return "Les tarifs varient généralement entre 4 500 et 6 000 FCFA/heure selon le tuteur."
    if "merci" in message:
        return "Avec plaisir ! N'hésitez pas si vous avez d'autres questions. 😊"
    return "Je suis encore en apprentissage 🤖 Pouvez-vous reformuler votre question ?"


@main.route("/api/chatbot", methods=["POST"])
def chatbot():
    donnees = request.get_json(silent=True) or {}
    message = (donnees.get("message") or "").strip()
    if not message:
        return jsonify({"reponse": "Merci d'écrire un message avant de l'envoyer."}), 400
    return jsonify({"reponse": generer_reponse_chatbot(message)})


@main.route("/public/avis")
def avis_public():
    tous_les_avis = Avis.query.order_by(Avis.date_avis.desc()).all()
    return render_template("public/avis_public.html", avis=tous_les_avis)


@main.route("/a_propos")
def a_propos():
    return render_template("public/A_propos.html")


@main.route("/faq")
def faq():
    return render_template("public/FAQ.html")


@main.route("/tuteurs")
def liste_tuteurs():
    matiere_slug = (request.args.get("matiere") or "").strip()
    matiere_nom = MATIERES_COURS.get(matiere_slug)

    # Seuls les tuteurs validés par un admin sont visibles publiquement
    requete = Tuteur.query.filter(Tuteur.statut != "En attente")
    if matiere_nom:
        requete = requete.filter_by(matiere=matiere_nom)

    tuteurs = requete.order_by(Tuteur.nom).all()
    return render_template(
        "public/liste_tuteurs.html",
        tuteurs=tuteurs,
        matiere_nom=matiere_nom
    )


@main.route("/tuteurs/<int:tuteur_id>")
def profil_tuteur_public(tuteur_id):
    tuteur = Tuteur.query.get_or_404(tuteur_id)
    if tuteur.statut == "En attente":
        abort(404)

    avis = Avis.query.filter_by(tuteur_id=tuteur.id).order_by(Avis.date_avis.desc()).all()
    note_moyenne = round(sum(a.note for a in avis) / len(avis), 1) if avis else None

    return render_template(
        "public/profil_tuteur_public.html",
        tuteur=tuteur,
        avis=avis,
        note_moyenne=note_moyenne
    )


@main.route("/tuteurs/<int:tuteur_id>/reserver", methods=["POST"])
@login_required(role="etudiant")
def reserver_tuteur(tuteur_id):
    tuteur = Tuteur.query.get_or_404(tuteur_id)
    etudiant = _etudiant_courant()

    if not etudiant:
        flash("Aucun profil étudiant trouvé.", "danger")
        return redirect(url_for("main.profil_tuteur_public", tuteur_id=tuteur.id))

    date_str = (request.form.get("date_seance") or "").strip()
    montant_str = (request.form.get("montant") or "").strip()

    if not date_str or not montant_str:
        flash("Merci de renseigner la date de la séance et le montant convenu.", "danger")
        return redirect(url_for("main.profil_tuteur_public", tuteur_id=tuteur.id))

    try:
        date_seance = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        montant = float(montant_str)
    except ValueError:
        flash("La date ou le montant renseigné est invalide.", "danger")
        return redirect(url_for("main.profil_tuteur_public", tuteur_id=tuteur.id))

    if montant <= 0:
        flash("Le montant doit être supérieur à 0.", "danger")
        return redirect(url_for("main.profil_tuteur_public", tuteur_id=tuteur.id))

    # Étape 1 : la réservation part "En attente" de confirmation par le tuteur
    reservation = Reservation(
        etudiant_id=etudiant.id,
        tuteur_id=tuteur.id,
        matiere=tuteur.matiere,
        date_seance=date_seance,
        statut="En attente"
    )
    db.session.add(reservation)
    db.session.commit()

    # Étape 2 : le paiement associé part aussi "En attente", à valider par un admin
    paiement = Paiement(
        reference=f"PAY-{reservation.id:05d}",
        montant=montant,
        statut="En attente",
        tuteur_id=tuteur.id,
        etudiant_id=etudiant.id,
        reservation_id=reservation.id
    )
    db.session.add(paiement)
    db.session.commit()

    flash("Votre demande de réservation a été envoyée. Le paiement sera validé par un administrateur.", "success")
    return redirect(url_for("main.reservations_etudiant"))


@main.route("/matieres")
def matieres():
    matieres_bdd = Matiere.query.order_by(Matiere.nom).all()
    return render_template("public/matieres.html", matieres=matieres_bdd)


@main.route("/matieres/<slug>")
def cours_matiere(slug):
    # Un template dédié existe pour chaque slug connu (public/cours/<slug>.html)
    if slug not in MATIERES_COURS:
        abort(404)
    return render_template(
        f"public/cours/{slug}.html",
        nom_matiere=MATIERES_COURS[slug]
    )


@main.route("/contact")
def contact():
    return render_template("public/notre_contact.html")


@main.route("/recrutement")
def recrutement():
    return render_template("public/recrutement.html")


# ====================================
# GESTIONNAIRES D'ERREURS
# ====================================
@main.app_errorhandler(404)
def erreur_404(error):
    return render_template("404.html"), 404


@main.app_errorhandler(500)
def erreur_500(error):
    return render_template("500.html"), 500
