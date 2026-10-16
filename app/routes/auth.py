from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.forms import LoginForm, RegistroForm
from app.models import Usuario

auth_bp = Blueprint("auth", __name__)

MENSAJE_CREDENCIALES = "Correo o contraseña incorrectos."
MENSAJE_CUENTA_INACTIVA = "Tu cuenta no está activa. Contacta a la administración."


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistroForm()
    if form.validate_on_submit():
        Usuario.registrar_ciudadano(
            nombres=form.nombres.data,
            apellidos=form.apellidos.data,
            correo=form.correo.data,
            password=form.contrasena.data,
        )
        flash("Tu cuenta se creó correctamente. Ya puedes iniciar sesión.", "exito")
        return redirect(url_for("auth.login"))

    return render_template("registro.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        usuario = Usuario.autenticar(form.correo.data, form.contrasena.data)
        if usuario is None:
            flash(MENSAJE_CREDENCIALES, "error")
        elif not usuario.is_active:
            flash(MENSAJE_CUENTA_INACTIVA, "error")
        elif login_user(usuario):
            flash(f"Bienvenido o bienvenida, {usuario.nombres}.", "exito")
            return redirect(url_for("main.index"))
        else:
            flash(MENSAJE_CREDENCIALES, "error")

    return render_template("login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión correctamente.", "exito")
    return redirect(url_for("auth.login"))
