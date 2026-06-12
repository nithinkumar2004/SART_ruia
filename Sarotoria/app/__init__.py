import os
from flask import Flask, render_template, session
from app.config import Config
from app.utils.db_client import init_db

def create_app():
    """Flask App Factory creating the Sarotoria Consumer AI Fashion Platform."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 1. Ensure required static folders exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["TRYON_FOLDER"], exist_ok=True)
    os.makedirs(app.config["AVATAR_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "temp"), exist_ok=True)
    
    # 2. Bootstrap database fallback schemas
    init_db()
    
    # 3. Register Blueprints
    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.scan import scan_bp
    from app.garment import garment_bp
    from app.tryon import tryon_bp
    from app.wardrobe import wardrobe_bp
    from app.assistant import assistant_bp
    from app.profile import profile_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(garment_bp)
    app.register_blueprint(tryon_bp)
    app.register_blueprint(wardrobe_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(profile_bp)
    
    # 4. Renders the main PWA / marketing landing entryway page
    @app.route("/")
    def index():
        return render_template("landing.html")
        
    return app
