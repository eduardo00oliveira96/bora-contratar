from dotenv import load_dotenv
load_dotenv()

from flask import Flask, g, session
from src.config import Config
from routes.public import public_bp
from routes.admin import admin_bp
from routes.auth import auth_bp
from routes.solicitacao import solicitacao_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.before_request
    def carregar_usuario():
        g.usuario = session.get("user")

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp)
    app.register_blueprint(solicitacao_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, port=Config.PORT)
