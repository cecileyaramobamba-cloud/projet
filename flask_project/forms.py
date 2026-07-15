from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegistrationForm(FlaskForm):
    username = StringField(
        "Nom d'utilisateur",
        validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
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
