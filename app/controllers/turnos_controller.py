from datetime import datetime, date

from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, session, url_for)

from app.services.hospital_service import HospitalService

bp = turnos_bp = Blueprint("turnos", __name__, url_prefix="/turnos")

ICONOS = {"canino":"🐶","felino":"🐱","perro":"🐶","gato":"🐱",
          "ave":"🐦","conejo":"🐰","reptil":"🦎"}
ROLES_VET = {"Veterinario", "Administrador"}


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


def _enriquecer_mascota(mascota: dict) -> dict:
    mascota["especie_icon"] = ICONOS.get(mascota["especie"].lower(), "🐾")
    mascota["sexo_label"]   = {"M": "Macho", "F": "Hembra"}.get(
                                mascota.get("sexo", ""), "N/D")
    mascota["edad"]         = _edad(mascota.get("fecha_nacimiento"))
    return mascota


def _meds_from_form() -> list[dict]:
    nombres     = request.form.getlist("med_medicamento[]")
    dosis       = request.form.getlist("med_dosis[]")
    vias        = request.form.getlist("med_via[]")
    frecuencias = request.form.getlist("med_frecuencia[]")
    duraciones  = request.form.getlist("med_duracion[]")
    return [
        {
            "medicamento":   n,
            "dosis":         dosis[i]       if i < len(dosis)       else "",
            "via":           vias[i]        if i < len(vias)        else "",
            "frecuencia":    frecuencias[i] if i < len(frecuencias) else "",
            "duracion_dias": duraciones[i]  if i < len(duraciones) and duraciones[i] else None,
        }
        for i, n in enumerate(nombres) if n.strip()
    ]


def _ests_from_form() -> list[dict]:
    tipos      = request.form.getlist("est_tipo[]")
    resultados = request.form.getlist("est_resultado[]")
    return [
        {
            "tipo":      tp,
            "resultado": resultados[i] if i < len(resultados) else "",
            "fecha":     date.today().isoformat(),
        }
        for i, tp in enumerate(tipos) if tp.strip()
    ]


@bp.route("/<int:turno_id>/atender", methods=["GET", "POST"])
def atender(turno_id: int):
    if session.get("user_role") not in ROLES_VET:
        flash("No tenés permiso para acceder a esta sección.", "error")
        return redirect(url_for("dashboard.index"))

    svc   = HospitalService()
    turno = svc.get_turno_by_id(turno_id)
    
    if not turno:
        abort(404)

    mascota  = _enriquecer_mascota(svc.get_paciente_info(turno["paciente_id"]))
    historial = svc.get_historial(turno["paciente_id"])

    if request.method == "POST":
        diagnostico = request.form.get("diagnostico", "").strip()

        if not diagnostico:
            return render_template(
                "paciente.html",
                turno=turno, mascota=mascota, historial=historial,
                hoy_datetime=datetime.now().strftime("%d/%m/%Y  %H:%M"),
                form=request.form,
                error="El diagnóstico es obligatorio.",
                success=None,
            )

        svc.guardar_atencion({
            "turno_id":       turno_id,
            "paciente_id":    turno["paciente_id"],
            "veterinario_id": session["user_id"],
            "anamnesis":      request.form.get("anamnesis", ""),
            "examen_fisico":  request.form.get("examen_fisico", ""),
            "diagnostico":    diagnostico,
            "tratamiento":    request.form.get("tratamiento", ""),
            "observaciones":  request.form.get("observaciones", ""),
            #"monto":          float(request.form.get("monto") or 0),
            # constantes vitales
            "temperatura_c":     request.form.get("temperatura_c") or None,
            "peso_consulta_kg":  request.form.get("peso_consulta_kg") or None,
            "fc_rpm":            request.form.get("fc_rpm") or None,
            "fr_rpm":            request.form.get("fr_rpm") or None,
            "trc_seg":           request.form.get("trc_seg") or None,
            "mucosas":           request.form.get("mucosas", ""),
            "condicion_corporal":request.form.get("condicion_corporal") or None,
            "dolor":             request.form.get("dolor") or None,
            "medicaciones":   _meds_from_form(),
            "estudios":       _ests_from_form(),
        })

        flash("Atención guardada correctamente.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template(
        "paciente.html",
        turno=turno, mascota=mascota, historial=historial,
        hoy_datetime=datetime.now().strftime("%d/%m/%Y  %H:%M"),
        form={}, error=None, success=None,
    )


@bp.route("/<int:turno_id>/cancelar", methods=["POST"])
def cancelar(turno_id: int):
    HospitalService().cancelar_turno(turno_id)
    flash("Turno cancelado.", "success")
    return redirect(url_for("dashboard.index"))

@bp.route("/urgente", methods=["POST"])
def urgente():
    """Crea un turno urgente desde el formulario de recepción."""
    if session.get("user_role") not in {"Recepcionista", "Administrador",
                                         "Veterinario"}:
        flash("Sin permiso.", "error")
        return redirect(url_for("dashboard.index"))
 
    paciente_id    = request.form.get("paciente_id", "").strip()
    veterinario_id = request.form.get("veterinario_id", "").strip()
    motivo         = request.form.get("motivo", "Urgencia").strip()
 
    if not paciente_id or not veterinario_id:
        flash("Seleccioná paciente y veterinario.", "error")
        return redirect(url_for("dashboard.index"))
 
    svc = HospitalService()
    svc.crear_turno_urgente(
        mascota_id=int(paciente_id),
        veterinario_id=int(veterinario_id),
        recepcionista_id=session["user_id"],
        motivo=motivo,
    )
    flash("🚨 Turno urgente creado.", "success")
    return redirect(url_for("dashboard.index"))