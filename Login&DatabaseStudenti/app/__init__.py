from flask import Flask
from app.routes.login_routes import login_bp
from app.routes.studenti_routes import studenti_bp

def create_app():
    app = Flask(__name__)
    app.secret_key = "una-chiave-super-segreta"

    app.register_blueprint(login_bp)
    app.register_blueprint(studenti_bp)

    return app