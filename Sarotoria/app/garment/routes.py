import uuid
from flask import render_template, redirect, url_for, session, request, flash, jsonify
from app.garment import garment_bp
from app.utils.db_client import DatabaseHelper
from app.utils.size_engine import SizePredictionEngine

@garment_bp.route("/<garment_id>")
def detail(garment_id):
    """
    Renders detailed garment specification sheet, pulling data directly from 
    Nexus database tables and performing smart size predictions.
    """
    user_id = session.get("user_id")
    profile = session.get("profile")
    
    # 1. Fetch garment specs from database
    garment = DatabaseHelper.get_garment(garment_id)
    if not garment:
        # Create a mock garment if scanned a simulated ID
        if garment_id.startswith("test-garment-"):
            garment = self._create_mock_catalog_garment(garment_id)
        else:
            flash("Garment specifications not found or invalid digital passport.", "danger")
            return redirect(url_for("dashboard.index"))

    # 2. Execute sizing analyzer if customer profile exists
    size_suggestion = None
    if profile:
        size_suggestion = SizePredictionEngine.predict_size(profile, garment)
    else:
        # User not calibrated or anonymous
        size_suggestion = {
            "recommended_size": "M",
            "confidence": 75,
            "explanation": "Calibrate your body measurements (height, weight, body type) in settings to unlock personal size predictions."
        }

    return render_template(
        "garment/detail.html",
        garment=garment,
        profile=profile,
        size_suggestion=size_suggestion
    )

@garment_bp.route("/save", methods=["POST"])
def save_to_wardrobe():
    """Saves garment to customer's smart wardrobe."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Authenticate session to add clothes to your wardrobe.", "danger")
        return redirect(url_for("auth.login"))
        
    garment_id = request.form.get("garment_id")
    folder_category = request.form.get("folder_category", "Casual")
    
    if not garment_id:
        flash("Garment credentials missing.", "danger")
        return redirect(url_for("dashboard.index"))
        
    res = DatabaseHelper.add_to_wardrobe(
        user_id=user_id,
        garment_id=garment_id,
        folder_category=folder_category
    )
    
    if res:
        flash(f"Successfully saved to your digital {folder_category} wardrobe!", "success")
    else:
        flash("Failed to add garment to digital wardrobe.", "danger")
        
    return redirect(url_for("garment.detail", garment_id=garment_id))

def _create_mock_catalog_garment(garment_id):
    """Creates fallback mock garment for simulation scans."""
    if "1" in garment_id:
        return {
            "id": garment_id,
            "garment_name": "Cyberpunk Techwear Hooded Blazer",
            "category": "Blazers",
            "image_url": "/static/images/logo_pwa_512.png", # Fallback
            "color": "#1d3864",
            "style": "Futuristic Techwear",
            "sleeve_type": "Long Sleeve",
            "pattern": "Solid cyber panels"
        }
    elif "2" in garment_id:
        return {
            "id": garment_id,
            "garment_name": "Premium Off-White Linen Shirt",
            "category": "Shirts",
            "image_url": "/static/images/logo_pwa_512.png",
            "color": "#ffffff",
            "style": "Smart Casual Luxury",
            "sleeve_type": "Long Sleeve",
            "pattern": "Plain Linen texture"
        }
    else:
        return {
            "id": garment_id,
            "garment_name": "Neon Pink Silk Floral Saree",
            "category": "Ethnic Wear",
            "image_url": "/static/images/logo_pwa_512.png",
            "color": "#FF2EBE",
            "style": "Elegant Festive wear",
            "sleeve_type": "Unisex",
            "pattern": "Floral borders weaving"
        }
