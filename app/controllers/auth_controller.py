import re
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.hospital_service import HospitalService


auth_bp = Blueprint("auth", __name__)
service = HospitalService()


def validar_email(email: str) -> bool:
    return bool(re.match(r"^[\w._%+\-]+@[\w.\-]+\.[a-zA-Z]{2,}$", email))


def validar_password(password: str) -> str | None:
    if len(password) < 8:
        return "Minimo 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return "Debe tener al menos una mayuscula."
    if not re.search(r"[a-z]", password):
        return "Debe tener al menos una minuscula."
    if not re.search(r"\d", password):
        return "Debe tener al menos un numero."
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    login_value = request.form["login"].strip()
    password = request.form["password"]

    if not login_value or not password:
        flash("Completa todos los campos.", "error")
        return redirect(url_for("auth.login"))

    user = service.user_repository.authenticate(login_value, password)
    if user is None:
        flash("Usuario, email o contrasena incorrectos.", "error")
        return redirect(url_for("auth.login"))

    session["user_id"] = user.id
    session["user_name"] = user.full_name
    session["user_role"] = user.role
    flash(f"Bienvenido, {user.full_name}.", "success")
    return redirect(url_for("main.home"))


@auth_bp.route("/registro", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    nombre = request.form["nombre"].strip()
    apellido = request.form["apellido"].strip()
    email = request.form["email"].strip().lower()
    username = request.form["username"].strip()
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if not all([nombre, apellido, email, username, password, confirm_password]):
        flash("Completa todos los campos.", "error")
        return redirect(url_for("auth.register"))
    if len(nombre) < 2 or len(apellido) < 2:
        flash("Nombre y apellido deben tener al menos 2 caracteres.", "error")
        return redirect(url_for("auth.register"))
    if not validar_email(email):
        flash("El email no tiene un formato valido.", "error")
        return redirect(url_for("auth.register"))
    if len(username) < 4:
        flash("El usuario debe tener al menos 4 caracteres.", "error")
        return redirect(url_for("auth.register"))

    password_error = validar_password(password)
    if password_error:
        flash(password_error, "error")
        return redirect(url_for("auth.register"))
    if password != confirm_password:
        flash("Las contrasenas no coinciden.", "error")
        return redirect(url_for("auth.register"))

    try:
        service.user_repository.create(
            username=username,
            password=password,
            full_name=f"{nombre} {apellido}",
            role="Administrativo",
            status="Activo",
            last_access=datetime.now().isoformat(timespec="minutes"),
            email=email,
        )
    except Exception as exc:
        flash(f"No se pudo registrar el usuario: {exc}", "error")
        return redirect(url_for("auth.register"))

    flash("Usuario registrado. Inicia sesion para continuar.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesion cerrada correctamente.", "success")
    return redirect(url_for("auth.login"))
