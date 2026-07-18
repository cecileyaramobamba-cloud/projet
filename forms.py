from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


# Formulaire d'inscription pour un tuteur
class RegistrationForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur",
        validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    # Matière que le tuteur souhaite enseigner (saisie libre)
    matiere = StringField(
        "Matière enseignée",
        validators=[DataRequired(), Length(min=2, max=80)]
    )
    password = PasswordField(
        "Mot de passe",
        validators=[DataRequired(), Length(min=6)]
    )
    # Doit être identique au champ "password" pour valider le formulaire
    password_confirm = PasswordField(
        "Confirmation du mot de passe",
        validators=[DataRequired(), EqualTo("password", message="Les mots de passe ne correspondent pas.")]
    )
    submit = SubmitField("S'inscrire")


# Formulaire d'inscription pour un étudiant
class StudentRegistrationForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur",
        validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    # Niveau scolaire de l'étudiant (ex: Terminale, Licence 2, ...)
    niveau = StringField(
        "Niveau",
        validators=[DataRequired(), Length(min=2, max=80)]
    )
    # Établissement fréquenté par l'étudiant
    etablissement = StringField(
        "Établissement",
        validators=[DataRequired(), Length(min=2, max=120)]
    )
    password = PasswordField(
        "Mot de passe",
        validators=[DataRequired(), Length(min=6)]
    )
    password_confirm = PasswordField(
        "Confirmation du mot de passe",
        validators=[DataRequired(), EqualTo("password", message="Les mots de passe ne correspondent pas.")]
    )
    submit = SubmitField("S'inscrire")


# Formulaire de connexion, commun à tous les rôles (admin, tuteur, étudiant)
# Le rôle réel est déterminé après authentification dans la route /login
class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        "Mot de passe",
        validators=[DataRequired()]
    )
    submit = SubmitField("Se connecter")
