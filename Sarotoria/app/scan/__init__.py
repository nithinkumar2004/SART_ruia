from flask import Blueprint

scan_bp = Blueprint("scan", __name__, url_prefix="/scan")

from app.scan import routes
