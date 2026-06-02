from flask import Flask, redirect, request, session, url_for

from app.controllers.auth_controller      import auth_bp
from app.controllers.main_controller      import main_bp
from app.controllers.users_controller     import users_bp
from app.controllers.dashboard_controller import dashboard_bp   # nuevo
from app.controllers.turnos_controller    import turnos_bp      # nuevo
from app.controllers.reports_controller   import reports_bp    # nuevos reportes
# 2026-05-29 Leo Arregin: Registro del blueprint de reportes para habilitar
# la nueva sección de informes.


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "hospital-veterinario-dev"

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(dashboard_bp)   # nuevo
    app.register_blueprint(turnos_bp)      # nuevo
    app.register_blueprint(reports_bp)     # nuevos reportes

    # filtro de fecha para los templates
    @app.template_filter("format_datetime")
    def format_datetime(value):
        from datetime import datetime
        try:
            return datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y  %H:%M")
        except Exception:
            return value

    @app.before_request
    def require_login():
        public_endpoints = {"auth.login", "auth.register", "static"}
        if request.endpoint in public_endpoints or request.endpoint is None:
            return None
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return None

    @app.context_processor
    def inject_current_user():
        from flask import session
        return {
            "current_user": {
                "user_id":   session.get("user_id"),
                "user_name": session.get("user_name"),
                "user_role": session.get("user_role"),
                # alias para simplificar en templates:
                "rol":       session.get("user_role", "").lower(),
            }
        }
    
    return app