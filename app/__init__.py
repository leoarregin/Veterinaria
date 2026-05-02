from flask import Flask, redirect, request, session, url_for

from app.controllers.auth_controller import auth_bp
from app.controllers.main_controller import main_bp
from app.controllers.users_controller import users_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "hospital-veterinario-dev"
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(users_bp)

    @app.before_request
    def require_login():
        public_endpoints = {"auth.login", "auth.register", "static"}
        if request.endpoint in public_endpoints or request.endpoint is None:
            return None
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return None

    return app
