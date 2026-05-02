from flask import Blueprint, render_template

from app.services.hospital_service import HospitalService


main_bp = Blueprint("main", __name__)
service = HospitalService()


@main_bp.route("/")
def home():
    summary = service.get_dashboard_summary()
    return render_template("home.html", summary=summary)
