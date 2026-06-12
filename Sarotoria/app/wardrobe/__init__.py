from flask import Blueprint

wardrobe_bp = Blueprint("wardrobe", __name__, url_prefix="/wardrobe")

from app.wardrobe import routes
