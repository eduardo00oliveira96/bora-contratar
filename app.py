from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(name)s %(levelname)s %(message)s')

from flask import Flask, g, session, render_template
from flask_wtf.csrf import CSRFProtect
from src.config import Config
from routes.public import public_bp
from routes.admin import admin_bp
from routes.auth import auth_bp, limiter
from routes.solicitacao import solicitacao_bp
from routes.entrevista import entrevista_bp
from routes.notificacao import notificacao_bp
from models.notificacao import notificacoes_nao_lidas

csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    csrf.init_app(app)
    limiter.init_app(app)

    @app.before_request
    def carregar_usuario():
        g.usuario = session.get("user")

    @app.context_processor
    def inject_notificacoes():
        usuario = g.get("usuario")
        count = 0
        if usuario:
            try:
                count = notificacoes_nao_lidas(usuario.get("id"))
            except Exception:
                pass
        return {"notificacoes_nao_lidas": count}

    @app.after_request
    def add_security_headers(resp):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
        resp.headers['X-XSS-Protection'] = '1; mode=block'
        resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        resp.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return resp

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp)
    app.register_blueprint(solicitacao_bp)
    app.register_blueprint(entrevista_bp)
    app.register_blueprint(notificacao_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=Config.DEBUG, port=Config.PORT, use_reloader=False)
