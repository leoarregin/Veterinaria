from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, session

from app.services.hospital_service import HospitalService

bp = dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

ICONOS = {"canino":"🐶","felino":"🐱","perro":"🐶","gato":"🐱",
          "ave":"🐦","conejo":"🐰","reptil":"🦎"}


def _edad(fecha_nac: str | None) -> str:
    if not fecha_nac:
        return ""
    try:
        nac  = datetime.strptime(fecha_nac, "%Y-%m-%d")
        diff = datetime.now() - nac
        y = diff.days // 365
        m = (diff.days % 365) // 30
        return f"{y} a {m} m" if y else f"{m} meses"
    except Exception:
        return ""


@bp.route("/")
def index():
    svc    = HospitalService()
    rol    = session.get("rol", "")
    vet_id = session.get("user_id") if rol == "Veterinario" else None

    turnos = svc.get_turnos_hoy(vet_id)
    for t in turnos:
        t["especie_icon"] = ICONOS.get(t["especie"].lower(), "🐾")
        t["edad"]         = _edad(t.get("fecha_nac"))

    return render_template(
        "dashboard.html",
        turnos=turnos,
        hoy=date.today().strftime("%A %d de %B de %Y").capitalize(),
    )


@bp.route("/<int:turno_id>/presente", methods=["POST"])
def marcar_presente(turno_id: int):
    HospitalService().marcar_presente(turno_id)
    return redirect(url_for("dashboard.index"))