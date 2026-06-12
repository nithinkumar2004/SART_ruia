from flask import Blueprint

tryon_bp = Blueprint("tryon", __name__, url_prefix="/tryon")

from app.tryon import routes
