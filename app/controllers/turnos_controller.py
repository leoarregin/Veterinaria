from datetime import datetime, date

from flask import (Blueprint, abort, flash, redirect,
                   render_template, request, session, url_for)

from app.services.hospital_service import HospitalService

bp = turnos_bp = Blueprint("turnos", __name__, url_prefix="/turnos")

ICONOS = {"canino":"🐶","felino":"🐱","perro":"🐶","gato":"🐱",
          "ave":"🐦","conejo":"🐰","reptil":"🦎"}
ROLES_VET = {"Veterinario", "Administrador"}
URGENCIAS = [
    ("normal", "Normal"),
    ("urgente", "Urgente"),
    ("emergencia", "Emergencia"),
]


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


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


# 2026-05-08 leo arregin / gonza arregin: nuevo flujo de turno exige paciente existente y permite buscarlo antes de registrar
@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    svc = HospitalService()
    veterinarios = svc.get_veterinarios()
    search_term = request.args.get("q", "").strip() or request.form.get("q", "").strip()
    pacientes = svc.search_pacientes(search_term) if search_term else []
    error = None
    form = {
        "q": search_term,
        "paciente_id": request.form.get("paciente_id", ""),
        "veterinario_id": request.form.get("veterinario_id", ""),
        "fecha_hora": request.form.get("fecha_hora", ""),
        "urgencia": request.form.get("urgencia", "normal"),
        "motivo": request.form.get("motivo", ""),
    }

    if request.method == "POST":
        paciente_id = request.form.get("paciente_id")
        if not paciente_id:
            error = (
                "Seleccioná una mascota existente o registrala con el botón "
                "Registrar mascota antes de crear el turno."
            )
        else:
            try:
                paciente_id = int(paciente_id)
            except ValueError:
                error = "Seleccioná una mascota válida."

        if not error:
            if not form["fecha_hora"]:
                error = "La fecha y hora del turno son obligatorias."
            elif not form["veterinario_id"]:
                error = "Debes seleccionar un veterinario."

        if not error:
            svc.crear_turno({
                "paciente_id": paciente_id,
                "veterinario_id": form["veterinario_id"],
                "recepcionista_id": session.get("user_id", 1),
                "fecha_hora": form["fecha_hora"],
                "motivo": form["motivo"],
                "urgencia": form["urgencia"],
            })
            flash("Turno creado correctamente.", "success")
            return redirect(url_for("dashboard.index"))

    return render_template(
        "turno_form.html",
        veterinarios=veterinarios,
        urgencias=URGENCIAS,
        pacientes=pacientes,
        search_term=search_term,
        error=error,
        form=form,
    )


@bp.route("/registrar", methods=["GET", "POST"])
def registrar():
    svc = HospitalService()
    error = None
    form = {
        "cliente_nombre": request.form.get("cliente_nombre", ""),
        "cliente_apellido": request.form.get("cliente_apellido", ""),
        "cliente_dni": request.form.get("cliente_dni", ""),
        "cliente_telefono": request.form.get("cliente_telefono", ""),
        "cliente_email": request.form.get("cliente_email", ""),
        "cliente_direccion": request.form.get("cliente_direccion", ""),
        "paciente_nombre": request.form.get("paciente_nombre", ""),
        "paciente_especie": request.form.get("paciente_especie", ""),
        "paciente_raza": request.form.get("paciente_raza", ""),
        "paciente_sexo": request.form.get("paciente_sexo", "M"),
        "paciente_fecha_nacimiento": request.form.get("paciente_fecha_nacimiento", ""),
    }

    if request.method == "POST":
        missing = [
            field for field in ["cliente_nombre", "cliente_apellido", "paciente_nombre", "paciente_especie"]
            if not form[field].strip()
        ]
        if missing:
            error = "Completa los datos del cliente y la mascota para poder registrar."
        else:
            cliente_id = svc.crear_cliente(
                form["cliente_nombre"],
                form["cliente_apellido"],
                form["cliente_dni"],
                form["cliente_telefono"],
                form["cliente_email"],
                form["cliente_direccion"],
            )
            svc.crear_paciente(
                cliente_id,
                form["paciente_nombre"],
                form["paciente_especie"],
                form["paciente_raza"],
                form["paciente_fecha_nacimiento"],
                form["paciente_sexo"],
            )
            flash("Cliente y mascota registrados correctamente.", "success")
            return redirect(url_for("turnos.nuevo"))

    return render_template("cliente_form.html", error=error, form=form)


# 2026-05-08 leo arregin / gonza arregin: flujo para registrar mascota vinculada a cliente existente
@bp.route("/registrar-mascota", methods=["GET", "POST"])
def registrar_mascota():
    svc = HospitalService()
    search_term = request.args.get("q", "").strip() or request.form.get("q", "").strip()
    clientes = svc.search_clientes(search_term) if search_term else []
    error = None
    form = {
        "q": search_term,
        "cliente_id": request.form.get("cliente_id", ""),
        "paciente_nombre": request.form.get("paciente_nombre", ""),
        "paciente_especie": request.form.get("paciente_especie", ""),
        "paciente_raza": request.form.get("paciente_raza", ""),
        "paciente_sexo": request.form.get("paciente_sexo", "M"),
        "paciente_fecha_nacimiento": request.form.get("paciente_fecha_nacimiento", ""),
    }

    if request.method == "POST":
        if not form["cliente_id"]:
            error = "Seleccioná un cliente existente válido para registrar la mascota."
        elif not form["paciente_nombre"].strip() or not form["paciente_especie"].strip():
            error = "Completa el nombre y especie de la mascota."

        if not error:
            try:
                cliente_id = int(form["cliente_id"])
            except ValueError:
                cliente_id = None
                error = "Seleccioná un cliente válido."

        if not error:
            svc.crear_paciente(
                cliente_id,
                form["paciente_nombre"],
                form["paciente_especie"],
                form["paciente_raza"],
                form["paciente_fecha_nacimiento"],
                form["paciente_sexo"],
            )
            flash("Mascota registrada correctamente.", "success")
            return redirect(url_for("turnos.nuevo"))

    return render_template(
        "mascota_form.html",
        clientes=clientes,
        error=error,
        form=form,
    )


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