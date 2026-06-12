from flask import Blueprint

garment_bp = Blueprint("garment", __name__, url_prefix="/garment")

from app.garment import routes
