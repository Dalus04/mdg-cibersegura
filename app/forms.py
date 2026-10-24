from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models import Usuario


def _limpiar_texto(valor: str | None) -> str:
    return valor.strip() if isinstance(valor, str) else ""


def _limpiar_correo(valor: str | None) -> str:
    return valor.strip().lower() if isinstance(valor, str) else ""


class RegistroForm(FlaskForm):
    nombres = StringField(
        "Nombres",
        filters=[_limpiar_texto],
        validators=[
            DataRequired(message="Ingresa tus nombres."),
            Length(min=2, max=100, message="Los nombres deben tener entre 2 y 100 caracteres."),
        ],
    )
    apellidos = StringField(
        "Apellidos",
        filters=[_limpiar_texto],
        validators=[
            DataRequired(message="Ingresa tus apellidos."),
            Length(min=2, max=100, message="Los apellidos deben tener entre 2 y 100 caracteres."),
        ],
    )
    correo = EmailField(
        "Correo electrónico",
        filters=[_limpiar_correo],
        validators=[
            DataRequired(message="Ingresa tu correo electrónico."),
            Email(message="Ingresa un correo electrónico válido."),
            Length(max=255, message="El correo es demasiado largo."),
        ],
    )
    contrasena = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="Ingresa una contraseña."),
            Length(min=8, max=128, message="La contraseña debe tener al menos 8 caracteres."),
        ],
    )
    confirmar_contrasena = PasswordField(
        "Confirmar contraseña",
        validators=[
            DataRequired(message="Confirma tu contraseña."),
            EqualTo("contrasena", message="Las contraseñas no coinciden."),
        ],
    )
    enviar = SubmitField("Crear cuenta")

    def validate_correo(self, field: EmailField) -> None:
        if Usuario.buscar_por_correo(field.data):
            raise ValidationError("Ya existe una cuenta con este correo electrónico.")


class LoginForm(FlaskForm):
    correo = EmailField(
        "Correo electrónico",
        filters=[_limpiar_correo],
        validators=[
            DataRequired(message="Ingresa tu correo electrónico."),
            Email(message="Ingresa un correo electrónico válido."),
        ],
    )
    contrasena = PasswordField(
        "Contraseña",
        validators=[
            DataRequired(message="Ingresa tu contraseña."),
        ],
    )
    enviar = SubmitField("Iniciar sesión")
