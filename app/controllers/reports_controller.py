from datetime import datetime
from io import BytesIO

from flask import Blueprint, make_response, render_template, request
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.hospital_service import HospitalService

reports_bp = Blueprint("reports", __name__, url_prefix="/reportes")

# 2026-05-29 Leo Arregin: Se agrega controlador de reportes para gestionar
# la generación y visualización de los informes solicitados.

def _normalize_date(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    return value if value else None


def _build_report_context() -> tuple[HospitalService, dict]:
    svc = HospitalService()
    start_date = _normalize_date(request.args.get("start_date"))
    end_date = _normalize_date(request.args.get("end_date"))
    report_type = request.args.get("report_type", "historial")
    sort_by = request.args.get("sort_by", "total")
    sort_dir = request.args.get("sort_dir", "desc").lower()
    periodo_sort_by = request.args.get("periodo_sort_by", "dia")
    periodo_sort_dir = request.args.get("periodo_sort_dir", "desc").lower()
    client_sort_by = request.args.get("client_sort_by", "atenciones")
    client_sort_dir = request.args.get("client_sort_dir", "desc").lower()
    paciente_id = request.args.get("paciente_id", type=int)

    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"
    if periodo_sort_dir not in ("asc", "desc"):
        periodo_sort_dir = "desc"
    if client_sort_dir not in ("asc", "desc"):
        client_sort_dir = "desc"

    selected_paciente = None
    historial = []
    if paciente_id:
        selected_paciente = svc.paciente_repository.get_info_completa(paciente_id)
        historial = svc.get_historial(paciente_id)

    context = {
        "report_date": datetime.now().strftime("%d/%m/%Y"),
        "pacientes": svc.paciente_repository.list_all(),
        "veterinarios": svc.get_veterinarios(),
        "selected_paciente": selected_paciente,
        "historial": historial,
        "atenciones_periodo": svc.get_atenciones_totales_por_periodo(
            start_date, end_date, periodo_sort_by, periodo_sort_dir
        ),
        "periodo_sort_by": periodo_sort_by,
        "periodo_sort_dir": periodo_sort_dir,
        "atenciones_medico": svc.get_atenciones_totales_por_medico(
            start_date, end_date, sort_by, sort_dir
        ),
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "frecuencia_cliente": svc.get_frecuencia_atencion_por_cliente(
            start_date, end_date, client_sort_by, client_sort_dir
        ),
        "client_sort_by": client_sort_by,
        "client_sort_dir": client_sort_dir,
        "start_date": start_date or "",
        "end_date": end_date or "",
        "paciente_id": paciente_id or "",
        "report_type": report_type,
    }
    return svc, context


@reports_bp.route("/", methods=["GET"])
def index():
    _, context = _build_report_context()
    return render_template("reports.html", **context)


@reports_bp.route("/pdf", methods=["GET"])
def pdf():
    svc, context = _build_report_context()
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 50
    pdf_canvas.setFont("Helvetica-Bold", 16)
    pdf_canvas.drawString(50, y, "Reporte clínico veterinario")
    y -= 25
    pdf_canvas.setFont("Helvetica", 10)
    pdf_canvas.drawString(50, y, f"Tipo de reporte: {context['report_type']}")
    y -= 15
    pdf_canvas.drawString(50, y, f"Fecha del reporte: {context['report_date']}")
    y -= 15
    if context["start_date"] or context["end_date"]:
        pdf_canvas.drawString(50, y, f"Rango: {context['start_date'] or '—'} a {context['end_date'] or '—'}")
        y -= 15

    if context["report_type"] == "historial" and context["selected_paciente"]:
        pdf_canvas.drawString(50, y, f"Mascota: {context['selected_paciente']['nombre']}")
        y -= 15
        pdf_canvas.drawString(50, y, f"Propietario: {context['selected_paciente']['propietario']}")
        y -= 15
        pdf_canvas.drawString(50, y, f"Especie: {context['selected_paciente']['especie']}")
        y -= 20
        for idx, item in enumerate(context["historial"], start=1):
            if y < 80:
                pdf_canvas.showPage(); y = height - 50
            pdf_canvas.setFont("Helvetica-Bold", 11)
            pdf_canvas.drawString(50, y, f"{idx}. {item['fecha_hora']}")
            y -= 14
            pdf_canvas.setFont("Helvetica", 10)
            pdf_canvas.drawString(60, y, f"Veterinario: {item.get('veterinario', '—')}")
            y -= 14
            pdf_canvas.drawString(60, y, f"Tipo: {item.get('tipo_atencion', 'Normal')}")
            y -= 14
            pdf_canvas.drawString(60, y, f"Motivo: {item.get('motivo_consulta', '—')}")
            y -= 14
            pdf_canvas.drawString(60, y, f"Diagnóstico: {item.get('diagnostico', '—')}")
            y -= 14
            pdf_canvas.drawString(60, y, f"Tratamiento: {item.get('tratamiento', '—')}")
            y -= 18
    elif context["report_type"] == "periodo":
        pdf_canvas.drawString(50, y, "Total de atenciones por día")
        y -= 18
        for item in context["atenciones_periodo"]:
            if y < 80:
                pdf_canvas.showPage(); y = height - 50
            pdf_canvas.drawString(50, y, f"{item.get('dia', '—')}: total={item.get('total_atenciones', 0)}, normal={item.get('normal', 0)}, urgente={item.get('urgente', 0)}, emergencia={item.get('emergencia', 0)}")
            y -= 14
    elif context["report_type"] == "medico":
        pdf_canvas.drawString(50, y, "Total de atenciones por médico")
        y -= 18
        for item in context["atenciones_medico"]:
            if y < 80:
                pdf_canvas.showPage(); y = height - 50
            pdf_canvas.drawString(50, y, f"{item.get('veterinario', '—')}: total={item.get('total_atenciones', 0)}, normal={item.get('normal', 0)}, urgente={item.get('urgente', 0)}, emergencia={item.get('emergencia', 0)}")
            y -= 14
    else:
        pdf_canvas.drawString(50, y, "Frecuencia de atención por cliente")
        y -= 18
        for item in context["frecuencia_cliente"]:
            if y < 80:
                pdf_canvas.showPage(); y = height - 50
            pdf_canvas.drawString(50, y, f"{item.get('cliente', '—')}: atenciones={item.get('atenciones', 0)}, mascotas={item.get('mascotas', 0)}, promedio/mascota={item.get('promedio_por_mascota', 0)}, última={item.get('ultima_atencion', '—')}")
            y -= 14

    pdf_canvas.save()
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=reporte_clinico.pdf"
    return response
    start_date = _normalize_date(request.args.get("start_date"))
    end_date = _normalize_date(request.args.get("end_date"))
    report_type = request.args.get("report_type", "historial")
    sort_by = request.args.get("sort_by", "total")
    sort_dir = request.args.get("sort_dir", "desc").lower()
    periodo_sort_by = request.args.get("periodo_sort_by", "dia")
    periodo_sort_dir = request.args.get("periodo_sort_dir", "desc").lower()
    client_sort_by = request.args.get("client_sort_by", "atenciones")
    client_sort_dir = request.args.get("client_sort_dir", "desc").lower()
    paciente_id = request.args.get("paciente_id", type=int)

    if sort_dir not in ("asc", "desc"):
        sort_dir = "desc"
    if periodo_sort_dir not in ("asc", "desc"):
        periodo_sort_dir = "desc"
    if client_sort_dir not in ("asc", "desc"):
        client_sort_dir = "desc"

    selected_paciente = None
    historial = []
    if paciente_id:
        selected_paciente = svc.paciente_repository.get_info_completa(paciente_id)
        historial = svc.get_historial(paciente_id)

    report_date = datetime.now().strftime("%d/%m/%Y")

    return render_template(
        "reports.html",
        report_date=report_date,
        pacientes=svc.paciente_repository.list_all(),
        veterinarios=svc.get_veterinarios(),
        selected_paciente=selected_paciente,
        historial=historial,
        atenciones_periodo=svc.get_atenciones_totales_por_periodo(
            start_date, end_date, periodo_sort_by, periodo_sort_dir
        ),
        periodo_sort_by=periodo_sort_by,
        periodo_sort_dir=periodo_sort_dir,
        atenciones_medico=svc.get_atenciones_totales_por_medico(
            start_date, end_date, sort_by, sort_dir
        ),
        sort_by=sort_by,
        sort_dir=sort_dir,
        frecuencia_cliente=svc.get_frecuencia_atencion_por_cliente(
            start_date, end_date, client_sort_by, client_sort_dir
        ),
        client_sort_by=client_sort_by,
        client_sort_dir=client_sort_dir,
        start_date=start_date or "",
        end_date=end_date or "",
        paciente_id=paciente_id or "",
        report_type=report_type,
    )
