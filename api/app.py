import os
import sys

# Adiciona o diretório raiz do projeto ao sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from flask import Flask
from routes.public import public_bp
from routes.admin import admin_bp
from models.db import init_db
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def create_app():
    # Define a pasta raiz correta onde os templates e static estão
    app = Flask(__name__, 
                template_folder=os.path.join(BASE_DIR, 'templates'),
                static_folder=os.path.join(BASE_DIR, 'static'))
                
    app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'
    
    # Inicializa o DB (cria as tabelas se não existirem)
    init_db()
    
    # Registra as rotas (Blueprints)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)