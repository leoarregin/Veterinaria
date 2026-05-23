"""
REEMPLAZAR el método index() en dashboard_controller.py
"""
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, session
from app.services.hospital_service import HospitalService

bp = dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

ICONOS = {"canino":"🐶","felino":"🐱","perro":"🐶","gato":"🐱",
          "ave":"🐦","conejo":"🐰","reptil":"🦎"}

ESTADOS_ACTIVOS     = {"presente", "en_consulta", "en_pausa",
                       "pendiente", "confirmado"}
ESTADOS_FINALIZADOS = {"atendido", "cancelado", "ausente"}


def _edad(fecha_nac):
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
    rol    = session.get("user_role", "")
    vet_id = session.get("user_id") if rol == "Veterinario" else None

    turnos = svc.get_turnos_hoy(vet_id)
    for t in turnos:
        t["especie_icon"] = ICONOS.get(t["especie"].lower(), "🐾")
        t["edad"]         = _edad(t.get("fecha_nac"))
        t["urgencia"]     = (t.get("urgencia") or "normal").lower()
        t["estado"]       = (t.get("estado") or "pendiente").lower()

    # ── separación EXCLUSIVA — cada turno aparece en UNA sola sección ──
    #
    # Prioridad de clasificación:
    # 1. en_pausa      → siempre EN PAUSA (sin importar urgencia)
    # 2. emergencia    → EMERGENCIAS (solo si NO está en pausa)
    # 3. urgente       → URGENTES (solo si NO está en pausa)
    # 4. presente      → EN SALA (normal, no pausado)
    # 5. confirmado/
    #    pendiente     → PRÓXIMOS
    # 6. atendido/
    #    cancelado/
    #    ausente       → FINALIZADOS

    en_pausa    = [t for t in turnos
                   if t["estado"] == "en_pausa"]

    pausados_ids = {t["id"] for t in en_pausa}

    emergencias = [t for t in turnos
                   if t["urgencia"] == "emergencia"
                   and t["id"] not in pausados_ids
                   and t["estado"] in ESTADOS_ACTIVOS]

    urgentes    = [t for t in turnos
                   if t["urgencia"] == "urgente"
                   and t["id"] not in pausados_ids
                   and t["estado"] in ESTADOS_ACTIVOS]

    excluidos   = pausados_ids | {t["id"] for t in emergencias} \
                               | {t["id"] for t in urgentes}

    presentes   = [t for t in turnos
                   if t["estado"] in ("presente", "en_consulta")
                   and t["id"] not in excluidos]

    proximos    = [t for t in turnos
                   if t["estado"] in ("pendiente", "confirmado")
                   and t["id"] not in excluidos]

    finalizados = [t for t in turnos
                   if t["estado"] in ESTADOS_FINALIZADOS]

    # para el formulario de urgencia rápida
    try:
        pacientes    = svc.paciente_repository.list_all()
        veterinarios = [u for u in svc.user_repository.list_all()
                        if u.role == "Veterinario" and u.status == "Activo"]
    except Exception:
        pacientes    = []
        veterinarios = []

    return render_template(
        "dashboard.html",
        turnos=turnos,
        en_pausa=en_pausa,
        emergencias=emergencias,
        urgentes=urgentes,
        presentes=presentes,
        proximos=proximos,
        finalizados=finalizados,
        hoy=date.today().strftime("%A %d de %B de %Y").capitalize(),
        pacientes=pacientes,
        veterinarios=veterinarios,
        current_user=session,
    )


@bp.route("/<int:turno_id>/presente", methods=["POST"])
def marcar_presente(turno_id: int):
    HospitalService().marcar_presente(turno_id)
    return redirect(url_for("dashboard.index"))