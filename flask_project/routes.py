from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, send_from_directory, current_app, session
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, Matiere, Tuteur, Annonce, Etudiant, Paiement, Avis, Reservation, User
from forms import RegistrationForm, LoginForm

# Blueprint regroupant toutes les routes de l'application (enregistré dans app.py)
main = Blueprint("main", __name__)

MOIS_LABELS_FR = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]

# Dictionnaire conservé uniquement pour mapper les slugs d'URL aux vrais noms de matières en BDD
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


# ==========================
# HELPER DE RÔLES FACTICES (À remplacer plus tard par un vrai système de session)
# ==========================
def _tuteur_courant():
    # Récupère le vrai tuteur en BDD basé sur l'email de démonstration
    return Tuteur.query.filter_by(email="fall@gmail.com").first() or Tuteur.query.first()


def _etudiant_courant():
    # Récupère le vrai étudiant en BDD basé sur l'email de démonstration
    return Etudiant.query.filter_by(email="diop@gmail.com").first() or Etudiant.query.first()


# ==========================
# STATISTIQUES MULTI-VUES
# ==========================
def _repartition_matieres():
    # Nombre de tuteurs par matière, trié du plus grand au plus petit
    compte = dict(
        db.session.query(Tuteur.matiere, func.count(Tuteur.id)).group_by(Tuteur.matiere).all()
    )
    return sorted(compte.items(), key=lambda item: item[1], reverse=True)


def _paiements_par_mois():
    # Total des paiements payés, regroupé par mois
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


# ==========================
# FAVICON
# ==========================
@main.route("/favicon.ico")
def favicon():
    return send_from_directory(
        current_app.static_folder,
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon"
    )


# ==========================
# PAGE D'ACCUEIL
# ==========================
@main.route("/")
def accueil():
    return render_template("accueil/index.html")


# ==========================
# PROFIL D'UN TUTEUR (ESPACE TUTEUR CONNECTÉ)
# ==========================
@main.route("/tuteur/profil")
def profil_tuteur():
    tuteur_bdd = _tuteur_courant()
    if not tuteur_bdd:
        flash("Aucun profil tuteur trouvé.", "danger")
        return redirect(url_for("main.accueil"))

    # Extraction des données réelles de la base de données
    tuteur = {
        "nom": tuteur_bdd.nom,
        "matiere": tuteur_bdd.matiere,
        "experience": "Donnée non renseignée",  # À ajouter à ton modèle Tuteur si nécessaire
        "prix": "À négocier"  # À ajouter à ton modèle Tuteur si nécessaire
    }

    return render_template(
        "tuteur/profil_tuteur.html",
        tuteur=tuteur
    )


# ==========================
# DÉCONNEXION
# ==========================
@main.route("/auth/deconnexion")
def deconnexion():
    session.pop("user_id", None)
    flash("Vous avez été déconnecté avec succès.", "success")
    return redirect(url_for("main.accueil"))


# ==========================
# DASHBOARDS
# ==========================
@main.route("/admin/dashboard")
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
    activites.sort(key=lambda a: a["date"], reverse=True)

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


@main.route("/etudiant/dashboard")
def dashboard_etudiant():
    return render_template("etudiant/dashboard_etudiant.html")


@main.route("/tuteur/dashboard")
def dashboard_tuteur():
    return render_template("tuteur/dashboard_tuteur.html")


# ==========================
# ADMIN MANAGEMENT
# ==========================
@main.route("/admin/reservations")
def reservations_admin():
    reservations = Reservation.query.order_by(Reservation.date_seance.desc()).all()
    return render_template("admin/reservation_admin.html", reservations=reservations)


@main.route("/admin/reservations/<int:reservation_id>/confirmer", methods=["POST"])
def confirmer_reservation_admin(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Confirmée"
    db.session.commit()
    flash("La réservation a été confirmée.", "success")
    return redirect(request.referrer or url_for("main.reservations_admin"))


@main.route("/admin/reservations/<int:reservation_id>/annuler", methods=["POST"])
def annuler_reservation_admin(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Annulée"
    db.session.commit()
    flash("La réservation a été annulée.", "danger")
    return redirect(request.referrer or url_for("main.reservations_admin"))


@main.route("/admin/reservations/<int:reservation_id>/terminer", methods=["POST"])
def terminer_reservation_admin(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Terminée"
    db.session.commit()
    flash("La réservation a été marquée comme terminée.", "success")
    return redirect(request.referrer or url_for("main.reservations_admin"))


@main.route("/admin/utilisateurs")
def utilisateurs_admin():
    # Optionnel : Tu peux passer la liste globale des utilisateurs si ton template en a besoin
    utilisateurs = User.query.all()
    return render_template("admin/utilisateurs_admin.html", utilisateurs=utilisateurs)


@main.route("/admin/tuteurs")
def tuteurs_admin():
    tuteurs = Tuteur.query.order_by(Tuteur.date_inscription.desc()).all()
    return render_template("admin/tuteurs_admin.html", tuteurs=tuteurs)


@main.route("/admin/tuteurs/ajouter", methods=["GET", "POST"])
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
            statut="En attente"
        )
        db.session.add(tuteur)
        db.session.commit()

        flash("Le tuteur a été ajouté avec succès.", "success")
        return redirect(url_for("main.tuteurs_admin"))

    return render_template("admin/ajouter_tuteur.html")


@main.route("/admin/tuteurs/<int:tuteur_id>/valider", methods=["POST"])
def valider_tuteur_admin(tuteur_id):
    tuteur = Tuteur.query.get_or_404(tuteur_id)
    tuteur.statut = "Actif"
    db.session.commit()
    flash(f"Le tuteur « {tuteur.nom} » a été validé.", "success")
    return redirect(request.referrer or url_for("main.dashboard_admin"))


@main.route("/admin/tuteurs/<int:tuteur_id>/refuser", methods=["POST"])
def refuser_tuteur_admin(tuteur_id):
    tuteur = Tuteur.query.get_or_404(tuteur_id)
    nom = tuteur.nom
    db.session.delete(tuteur)
    db.session.commit()
    flash(f"Le tuteur « {nom} » a été refusé.", "danger")
    return redirect(request.referrer or url_for("main.dashboard_admin"))


@main.route("/admin/etudiants")
def etudiants_admin():
    etudiants = Etudiant.query.order_by(Etudiant.date_inscription.desc()).all()
    return render_template("admin/etudiants_admin.html", etudiants=etudiants)


@main.route("/admin/matieres")
def matieres_admin():
    matieres = Matiere.query.order_by(Matiere.nom).all()
    compte_tuteurs = dict(
        db.session.query(Tuteur.matiere, db.func.count(Tuteur.id)).group_by(Tuteur.matiere).all()
    )
    for m in matieres:
        m.nb_tuteurs = compte_tuteurs.get(m.nom, 0)

    return render_template("admin/matieres_admin.html", matieres=matieres)


@main.route("/admin/matieres/ajouter", methods=["GET", "POST"])
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
def paiements_admin():
    paiements = Paiement.query.order_by(Paiement.date_paiement.desc()).all()
    return render_template("admin/paiements_admin.html", paiements=paiements)


@main.route("/admin/statistiques")
def statistiques_admin():
    revenus_totaux = db.session.query(func.sum(Paiement.montant)).filter_by(statut="Payé").scalar() or 0
    satisfaction_moyenne = db.session.query(func.avg(Avis.note)).scalar()

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
def parametres_admin():
    if request.method == "POST":
        flash("Les paramètres ont été enregistrés avec succès.", "success")
        return redirect(url_for("main.parametres_admin"))
    return render_template("admin/parametres_admin.html")


# ==========================
# ESPACE ÉTUDIANT
# ==========================
@main.route("/etudiant/messages")
def messages_etudiant():
    return render_template("etudiant/messages_etudiant.html")


@main.route("/etudiant/profil")
def profil_etudiant():
    return render_template("etudiant/profil_etudiant.html")


@main.route("/etudiant/reservations")
def reservations_etudiant():
    etudiant = _etudiant_courant()
    reservations = (
        Reservation.query.filter_by(etudiant_id=etudiant.id).order_by(Reservation.date_seance.desc()).all()
        if etudiant else []
    )
    return render_template("etudiant/reservations.html", reservations=reservations)


@main.route("/etudiant/reservations/<int:reservation_id>/annuler", methods=["POST"])
def annuler_reservation_etudiant(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Annulée"
    db.session.commit()
    flash("La réservation a été annulée.", "danger")
    return redirect(request.referrer or url_for("main.reservations_etudiant"))


@main.route("/etudiant/cours")
def cours_etudiant():
    return render_template("etudiant/cours_etudiant.html")


@main.route("/etudiant/devoirs")
def devoirs_etudiant():
    return render_template("etudiant/devoirs_etudiant.html")


# ==========================
# ESPACE TUTEUR
# ==========================
@main.route("/tuteur/disponibilites")
def disponibilites_tuteur():
    return render_template("tuteur/disponibilites.html")


@main.route("/tuteur/reservation")
def reservation_tuteur():
    tuteur = _tuteur_courant()
    reservations = (
        Reservation.query.filter_by(tuteur_id=tuteur.id).order_by(Reservation.date_seance.desc()).all()
        if tuteur else []
    )
    return render_template("tuteur/reservation_tuteur.html", reservations=reservations)


@main.route("/tuteur/reservations/<int:reservation_id>/accepter", methods=["POST"])
def accepter_reservation_tuteur(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Confirmée"
    db.session.commit()
    flash("La réservation a été acceptée.", "success")
    return redirect(request.referrer or url_for("main.reservation_tuteur"))


@main.route("/tuteur/reservations/<int:reservation_id>/refuser", methods=["POST"])
def refuser_reservation_tuteur(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.statut = "Annulée"
    db.session.commit()
    flash("La réservation a été refusée.", "danger")
    return redirect(request.referrer or url_for("main.reservation_tuteur"))


@main.route("/tuteur/cours")
def cours_tuteur():
    return render_template("tuteur/cours_tuteur.html")


@main.route("/tuteur/messages")
def messages_tuteur():
    return render_template("tuteur/messages_tuteur.html")


@main.route("/tuteur/etudiants")
def etudiants_tuteur():
    tuteur = _tuteur_courant()
    etudiants_uniques = []

    if tuteur:
        # Récupère tous les étudiants uniques ayant réservé un cours (validé ou terminé) avec ce tuteur
        reservations = Reservation.query.filter(
            Reservation.tuteur_id == tuteur.id,
            Reservation.statut.in_(["Confirmée", "Terminée"])
        ).all()
        
        vus = set()
        for res in reservations:
            if res.etudiant_id not in vus:
                vus.add(res.etudiant_id)
                # Compte le nombre total de sessions pour cet étudiant spécifique avec ce tuteur
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

    return render_template(
        "tuteur/etudiants_tuteur.html",
        etudiants=etudiants_uniques
    )


@main.route("/tuteur/revenus")
def revenus_tuteur():
    tuteur = _tuteur_courant()
    paiements = []
    totaux_mensuels = {}

    if tuteur:
        # Récupère tous les paiements réels du tuteur depuis la BDD
        paiements = Paiement.query.filter_by(tuteur_id=tuteur.id).order_by(Paiement.date_paiement.desc()).all()
        
        # Calcule les revenus réels mensuels agrégés
        for p in paiements:
            if p.statut == "Payé" and p.date_paiement:
                mois_str = MOIS_LABELS_FR[p.date_paiement.month - 1]
                totaux_mensuels[mois_str] = totaux_mensuels.get(mois_str, 0) + p.montant

    # Formate le résultat pour le template Jinja
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


# ==========================
# CHATBOT ASSISTANT IA
# ==========================
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


# ==========================
# VUES PUBLIQUES DYNAMIQUES
# ==========================
@main.route("/public/avis")
def avis_public():
    # Liste tous les avis clients enregistrés en BDD
    tous_les_avis = Avis.query.order_by(Avis.date_avis.desc()).all()
    return render_template("public/avis_public.html", avis=tous_les_avis)


@main.route("/a-propos")
def a_propos():
    return render_template("public/A_propos.html")


@main.route("/faq")
def faq():
    return render_template("public/FAQ.html")


@main.route("/tuteurs")
def liste_tuteurs():
    # Liste tous les tuteurs actifs, avec filtre optionnel par matière (slug d'URL)
    matiere_slug = (request.args.get("matiere") or "").strip()
    matiere_nom = MATIERES_COURS.get(matiere_slug)

    requete = Tuteur.query.filter_by(statut="Actif")
    if matiere_nom:
        requete = requete.filter_by(matiere=matiere_nom)

    tuteurs = requete.order_by(Tuteur.nom).all()
    return render_template(
        "public/liste_tuteurs.html",
        tuteurs=tuteurs,
        matiere_nom=matiere_nom
    )


@main.route("/matieres")
def matieres():
    # Liste toutes les matières réelles enregistrées en BDD
    matieres_bdd = Matiere.query.order_by(Matiere.nom).all()
    return render_template("public/matieres.html", matieres=matieres_bdd)


@main.route("/matieres/<slug>")
def cours_matiere(slug):
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


# ==========================
# GESTIONNAIRES D'ERREURS
# ==========================
@main.app_errorhandler(404)
def erreur_404(error):
    return render_template("404.html"), 404


@main.app_errorhandler(500)
def erreur_500(error):
    return render_template("500.html"), 500


# ==========================
# SYSTEME D'AUTHENTIFICATION
# ==========================
@main.route("/register_tuteurs", methods=["GET", "POST"])
def register_tuteurs():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()

        if User.query.filter_by(email=email).first():
            flash("Un compte existe déjà avec cet email.", "danger")
            return redirect(url_for("main.register_tuteurs"))

        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur est déjà pris.", "danger")
            return redirect(url_for("main.register_tuteurs"))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()

        tuteur = Tuteur(
            user_id=user.id,
            nom=username,
            email=email,
            matiere=form.matiere.data.strip(),
            statut="En attente"
        )
        db.session.add(tuteur)
        db.session.commit()

        flash("Compte créé avec succès ! Votre profil tuteur est en attente de validation.", "success")
        return redirect(url_for("main.accueil"))

    return render_template("auth/register_tuteurs.html", form=form)


@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password_hash, form.password.data):
            flash("Email ou mot de passe incorrect.", "danger")
            return redirect(url_for("main.login"))

        session["user_id"] = user.id
        flash(f"Bienvenue, {user.username} !", "success")
        return redirect(url_for("main.accueil"))

    return render_template("auth/login.html", form=form)


@main.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Vous avez été déconnecté avec succès.", "success")
    return redirect(url_for("main.accueil"))