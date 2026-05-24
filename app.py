from flask import Flask
from routes.public import public_bp
from routes.admin import admin_bp
from models.db import init_db
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret-key-change-in-production'
    
    # Initialize DB (creates file and tables if not exist)
    init_db()
    
    # Register blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)