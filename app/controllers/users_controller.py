from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.hospital_service import HospitalService


users_bp = Blueprint("users", __name__, url_prefix="/usuarios")
service = HospitalService()


@users_bp.route("/")
def index():
    users = service.get_users()
    return render_template("users.html", users=users, total_users=len(users))


@users_bp.route("/nuevo")
def new():
    return render_template("user_form.html", title="Nuevo usuario", user=None)


@users_bp.route("/editar/<int:user_id>")
def edit(user_id: int):
    user = service.user_repository.get_by_id(user_id)
    if user is None:
        flash("El usuario solicitado no existe.", "error")
        return redirect(url_for("users.index"))
    return render_template("user_form.html", title="Editar usuario", user=user)


@users_bp.route("/guardar", methods=["POST"])
def save():
    user_id = request.form.get("id", type=int)
    username = request.form["username"].strip()
    password = request.form.get("password", "").strip()
    full_name = request.form["full_name"].strip()
    role = request.form["role"].strip()
    status = request.form["status"].strip()

    try:
        if user_id:
            user = service.user_repository.get_by_id(user_id)
            if user is None:
                flash("El usuario solicitado no existe.", "error")
                return redirect(url_for("users.index"))
            email = user.email
            last_access = user.last_access.isoformat(timespec="minutes")
            service.user_repository.update(user_id, username, full_name, role, status, last_access, email)
            flash("Usuario actualizado correctamente.", "success")
        else:
            if not password:
                flash("La contrasena es obligatoria para crear un usuario.", "error")
                return redirect(url_for("users.new"))
            email = ""
            last_access = datetime.now().isoformat(timespec="minutes")
            service.user_repository.create(username, password, full_name, role, status, last_access, email)
            flash("Usuario creado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo guardar el usuario: {exc}", "error")

    return redirect(url_for("users.index"))


@users_bp.route("/eliminar/<int:user_id>", methods=["POST"])
def delete(user_id: int):
    try:
        service.user_repository.delete(user_id)
        flash("Usuario eliminado correctamente.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el usuario: {exc}", "error")
    return redirect(url_for("users.index"))
