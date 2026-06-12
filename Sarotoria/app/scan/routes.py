from flask import render_template, redirect, url_for, session, request, flash
from app.scan import scan_bp
from app.utils.db_client import DatabaseHelper

@scan_bp.route("/")
def index():
    """Renders browser-based simulated camera scanner page."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Login to scan clothes and sync with your digital wardrobe.", "warning")
        return redirect(url_for("auth.login"))
        
    return render_template("scan/install.html", mode="manual_scan")

@scan_bp.route("/<garment_id>")
def handle_scan(garment_id):
    """
    Offline-to-online entrypoint when a physical tag QR code is scanned.
    URL structure: https://sartoria.app/scan/garment-id
    """
    # 1. Log scan hit in database (Shared table for seller dashboard!)
    user_id = session.get("user_id")
    
    device_type = "Mobile"
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'ipad' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        device_type = "Mobile"
    else:
        device_type = "Desktop"
        
    # Log to shared database
    DatabaseHelper.log_qr_scan(
        garment_id=garment_id,
        user_id=user_id,
        device_type=device_type,
        country="India",  # Simulating standard location context
        ip_address=request.remote_addr or "127.0.0.1"
    )
    
    # 2. Fetch Garment details
    garment = DatabaseHelper.get_garment(garment_id)
    if not garment:
        flash("Garment digital passport not found or invalid tag.", "danger")
        return redirect(url_for("dashboard.index"))
        
    # Check if user is logged in
    if not user_id:
        session["pending_scan_garment"] = garment_id
        flash("Scan detected! Please log in or create an account to view virtual fitting options.", "info")
        return redirect(url_for("auth.login"))

    # Renders the PWA Installation verification / redirection hub!
    return render_template("scan/install.html", mode="tag_scan", garment=garment)
