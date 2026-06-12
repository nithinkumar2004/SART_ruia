import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.config import Config
from app.utils.db_helper import DatabaseHelper
from app.ai.processor import process_garment_image, extract_style_metadata
from app.qr.routes import generate_branded_qr

garments_bp = Blueprint("garments", __name__)

@garments_bp.route("/upload-garment", methods=["GET", "POST"])
@login_required
def upload_garment():
    """Allows sellers to upload fashion garment images and automatically processes them."""
    if not current_user.business_name:
        flash("Please complete your business registration first.", "warning")
        return redirect("/register-business")
        
    if request.method == "POST":
        garment_name = request.form.get("garment_name", "").strip()
        category = request.form.get("category")
        
        if not garment_name or not category:
            flash("Garment name and category are required.", "danger")
            return render_template("garments/upload.html")
            
        image_file = request.files.get("garment_image")
        if not image_file or not image_file.filename:
            flash("Please upload a garment image file.", "danger")
            return render_template("garments/upload.html")
            
        # Verify file extension
        ext = image_file.filename.rsplit(".", 1)[-1].lower()
        if ext not in Config.ALLOWED_EXTENSIONS:
            flash("Invalid format. Allowed: PNG, JPG, JPEG, WEBP.", "danger")
            return render_template("garments/upload.html")
            
        # 1. Save raw temp file
        os.makedirs(os.path.join(current_app.config["UPLOAD_FOLDER"], "temp"), exist_ok=True)
        temp_filename = f"temp_{uuid.uuid4().hex}.{ext}"
        temp_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp", temp_filename)
        image_file.save(temp_path)
        
        try:
            # 2. Process image (background removal, resize, dominant color)
            output_dir = current_app.config["UPLOAD_FOLDER"]
            processed_data = process_garment_image(temp_path, output_dir)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            # 3. Extract extra fashion metadata
            extra_meta = extract_style_metadata(category)
            
            # 4. Generate unique ID for garment
            garment_id = str(uuid.uuid4())
            
            # 5. Generate Branded QR Code
            # Points to the tracking redirection gateway: /qr/scan/<garment_id>
            target_url = f"{request.url_root}qr/scan/{garment_id}"
            qr_filename = f"qr_{garment_id}.png"
            qr_path = os.path.join(current_app.config["QR_FOLDER"], qr_filename)
            generate_branded_qr(target_url, qr_path)
            
            # 6. Save records to DB
            DatabaseHelper.create_garment(
                garment_id=garment_id,
                user_id=current_user.id,
                garment_name=garment_name,
                category=category,
                image_url=processed_data["image_url"],
                qr_url=target_url,
                qr_image=f"qr/{qr_filename}",
                color=processed_data["color"],
                style=extra_meta["style"],
                sleeve_type=extra_meta["sleeve_type"],
                pattern=extra_meta["pattern"]
            )
            
            flash(f"'{garment_name}' uploaded, background removed, and QR code generated!", "success")
            return redirect(f"/garment/{garment_id}")
            
        except Exception as e:
            # Clean up temp file if something crashed
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print(f"Garment processing error: {e}")
            flash("AI Image Pipeline failed. Make sure your upload image is clear and try again.", "danger")
            
    return render_template("garments/upload.html")

@garments_bp.route("/garments")
@login_required
def list_garments():
    """Renders catalog gallery of seller garments."""
    garments = DatabaseHelper.get_garments_by_user(current_user.id)
    return render_template("garments/manage.html", garments=garments)

@garments_bp.route("/garment/<garment_id>")
@login_required
def view_garment(garment_id):
    """Renders single garment details and QR manager page."""
    garment = DatabaseHelper.get_garment(garment_id)
    if not garment:
        flash("Garment not found.", "danger")
        return redirect("/dashboard")
        
    if garment["user_id"] != current_user.id:
        flash("Access Denied.", "danger")
        return redirect("/dashboard")
        
    # Fetch scan logs specific to this garment
    conn = DatabaseHelper.get_sqlite_conn() if not Config.USE_SUPABASE else None
    scan_history = []
    
    if conn:
        cursor = conn.cursor()
        rows = cursor.execute("""
            SELECT scanned_at, device_type, country, ip_address 
            FROM qr_scans 
            WHERE garment_id = ? 
            ORDER BY scanned_at DESC 
            LIMIT 5
        """, (garment_id,)).fetchall()
        scan_history = [dict(r) for r in rows]
        conn.close()
        
    return render_template("garments/details.html", garment=garment, scan_history=scan_history)

@garments_bp.route("/garment/delete/<garment_id>", methods=["POST"])
@login_required
def delete_garment(garment_id):
    """Deletes garment, its DB entry, and associated local static files."""
    garment = DatabaseHelper.get_garment(garment_id)
    if not garment:
        flash("Garment not found.", "danger")
        return redirect("/dashboard")
        
    if garment["user_id"] != current_user.id:
        flash("Access Denied.", "danger")
        return redirect("/dashboard")
        
    # 1. Delete local garment optimized image file
    try:
        img_filename = os.path.basename(garment["image_url"])
        img_path = os.path.join(current_app.config["UPLOAD_FOLDER"], img_filename)
        if os.path.exists(img_path):
            os.remove(img_path)
    except Exception as e:
        print(f"Error removing garment image file: {e}")
        
    # 2. Delete local QR code image file
    try:
        qr_filename = os.path.basename(garment["qr_image"])
        qr_path = os.path.join(current_app.config["QR_FOLDER"], qr_filename)
        if os.path.exists(qr_path):
            os.remove(qr_path)
    except Exception as e:
        print(f"Error removing QR code image file: {e}")
        
    # 3. Delete database records (cascades scan analytics automatically)
    success = DatabaseHelper.delete_garment(garment_id)
    
    if success:
        flash("Garment and digital identity deleted successfully.", "success")
    else:
        flash("Error occurred deleting garment from database.", "danger")
        
    return redirect("/dashboard")
