import os
from flask import Flask, render_template, redirect
from flask_login import LoginManager
from app.config import Config
from app.utils.db_helper import init_db, DatabaseHelper

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 1. Ensure required local directories exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "logos"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "temp"), exist_ok=True)
    os.makedirs(app.config["QR_FOLDER"], exist_ok=True)
    
    # 2. Bootstrap database
    init_db()
    
    # 3. Setup Session Login Manager
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)
    
    from app.auth.routes import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Standard Flask-Login callback to retrieve user details from the database."""
        user_dict = DatabaseHelper.get_user(user_id)
        if user_dict:
            return User(
                user_id=user_dict["id"],
                email=user_dict["email"],
                phone=user_dict.get("phone"),
                business_name=user_dict.get("business_name")
            )
        return None
        
    # 4. Register Blueprints
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.garments.routes import garments_bp
    from app.qr.routes import qr_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(garments_bp)
    app.register_blueprint(qr_bp, url_prefix="/qr")
    
    # 5. Public Landing Page Routing
    @app.route("/")
    def index():
        """Renders the Saturn futuristic fashion-tech homepage showcase."""
        return render_template("landing.html")
        
    return app
