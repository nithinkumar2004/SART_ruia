import os
import uuid
from flask import render_template, redirect, url_for, session, request, flash
from werkzeug.utils import secure_filename
from app.tryon import tryon_bp
from app.utils.db_client import DatabaseHelper, Config
from app.utils.tryon_service import TryOnService

@tryon_bp.route("/")
def index():
    """Initial virtual fitting screen where user selects avatar or uploads portrait."""
    user_id = session.get("user_id")
    profile = session.get("profile")

    if not user_id or not profile:
        flash("Login session required to run AI Virtual Fittings.", "danger")
        return redirect(url_for("auth.login"))

    garment_id = request.args.get("garment_id")
    
    # If no garment is selected, let them choose from the shared catalog!
    garment = None
    if garment_id:
        garment = DatabaseHelper.get_garment(garment_id)
        if not garment:
            flash("Garment credentials not found.", "danger")
            return redirect(url_for("dashboard.index"))
    else:
        # Fallback: pull catalog garments so they can select one to try on
        catalog = DatabaseHelper.get_all_garments()
        return render_template("tryon/select.html", catalog=catalog, garment=None)

    # Curated standard model avatars list
    avatars = [
        {"id": "model_female_1", "gender": "Female", "label": "Model Amber (Light Female)", "avatar_url": "/static/images/avatars/model_amber.png"},
        {"id": "model_female_2", "gender": "Female", "label": "Model Chloe (Medium Female)", "avatar_url": "/static/images/avatars/model_chloe.png"},
        {"id": "model_male_1", "gender": "Male", "label": "Model Marcus (Light Male)", "avatar_url": "/static/images/avatars/model_marcus.png"},
        {"id": "model_male_2", "gender": "Male", "label": "Model Dev (Tan Male)", "avatar_url": "/static/images/avatars/model_dev.png"}
    ]

    return render_template("tryon/select.html", garment=garment, avatars=avatars)

@tryon_bp.route("/run", methods=["POST"])
def run_tryon():
    """Triggers the Visual compositing simulated tryon session."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("auth.login"))

    garment_id = request.form.get("garment_id")
    avatar_id = request.form.get("avatar_id")
    
    if not garment_id:
        flash("Target garment credentials missing.", "danger")
        return redirect(url_for("tryon.index"))

    user_image_path = None
    
    # Handle user portrait upload if selected
    if "user_portrait" in request.files:
        file = request.files["user_portrait"]
        if file and file.filename:
            # Validate extension
            ext = file.filename.split(".")[-1].lower()
            if ext in Config.ALLOWED_EXTENSIONS:
                temp_dir = os.path.join(Config.UPLOAD_FOLDER, "temp")
                os.makedirs(temp_dir, exist_ok=True)
                filename = f"user_{uuid.uuid4().hex}.{ext}"
                temp_path = os.path.join(temp_dir, filename)
                file.save(temp_path)
                user_image_path = temp_path
            else:
                flash("Supported image file extensions: png, jpg, jpeg, webp.", "danger")
                return redirect(url_for("tryon.index", garment_id=garment_id))

    try:
        # Execute fitting visual compositing (Supabase buckets + SQLite logs)
        result = TryOnService.generate_tryon(
            user_id=user_id,
            garment_id=garment_id,
            user_image_path=user_image_path,
            avatar_id=avatar_id
        )
        
        # Pull generated fitted details
        garment = DatabaseHelper.get_garment(garment_id)
        
        # Clean temporary portrait upload if it existed
        if user_image_path and os.path.exists(user_image_path):
            try:
                os.remove(user_image_path)
            except Exception:
                pass

        flash("AI Fitting composite complete! Review visual scans.", "success")
        return render_template("tryon/result.html", result=result, garment=garment)
        
    except Exception as e:
        flash(f"Virtual Try-On error: {e}", "danger")
        return redirect(url_for("tryon.index", garment_id=garment_id))

@tryon_bp.route("/purchase", methods=["POST"])
def purchase():
    """Simulates a premium standalone store payment checkout."""
    garment_name = request.form.get("garment_name", "Fashion Outfit")
    flash(f"Order Success! Premium checkout completed for: {garment_name}.", "success")
    return redirect(url_for("dashboard.index"))

@tryon_bp.route("/save-puter-result", methods=["POST"])
def save_puter_result():
    """Saves the AI try-on image generated on the frontend using Puter.js."""
    import base64
    user_id = session.get("user_id")
    if not user_id:
        return {"success": False, "error": "Unauthorized"}, 401
        
    data = request.get_json()
    if not data:
        return {"success": False, "error": "Missing payload"}, 400
        
    garment_id = data.get("garment_id")
    image_base64 = data.get("image_base64")
    
    if not garment_id or not image_base64:
        return {"success": False, "error": "Missing garment_id or image_base64"}, 400
        
    # Remove header prefix if present (e.g., 'data:image/png;base64,')
    if "," in image_base64:
        image_base64 = image_base64.split(",")[1]
        
    try:
        image_bytes = base64.b64decode(image_base64)
        
        # Save image locally
        output_filename = f"tryon_{uuid.uuid4().hex}.png"
        output_local_path = os.path.join(Config.TRYON_FOLDER, output_filename)
        os.makedirs(Config.TRYON_FOLDER, exist_ok=True)
        
        with open(output_local_path, "wb") as f:
            f.write(image_bytes)
            
        # Apply the premium futuristic scan cyber overlays on top!
        TryOnService._apply_cyber_hud(output_local_path, output_local_path)
            
        final_url = f"/static/uploads/tryon/{output_filename}"
        
        # Upload to Supabase Storage if configured
        from app.utils.db_client import supabase_client
        if Config.USE_SUPABASE and supabase_client:
            try:
                storage_path = f"tryon/{output_filename}"
                response = supabase_client.storage.from_("processed-images").upload(
                    path=storage_path,
                    file=image_bytes,
                    file_options={"content-type": "image/png"}
                )
                final_url = supabase_client.storage.from_("processed-images").get_public_url(storage_path)
            except Exception as e:
                print(f"Supabase storage upload failed: {e}. Falling back to local static URL.")
                
        # Log tryon in DB
        DatabaseHelper.save_tryon(user_id, garment_id, final_url)
        
        # Save to session so we can render in results
        session["latest_tryon_result"] = {
            "tryon_image_url": final_url,
            "garment_id": garment_id,
            "garment_name": data.get("garment_name", "AI Outfit"),
            "category": data.get("category", "T-Shirts"),
            "style": data.get("style", "Futuristic Slim-fit")
        }
        
        return {"success": True, "redirect_url": "/tryon/puter-result"}
    except Exception as e:
        print(f"Save Puter result error: {e}")
        return {"success": False, "error": str(e)}, 500

@tryon_bp.route("/puter-result")
def puter_result():
    """Renders the latest Puter tryon result."""
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
        
    result = session.get("latest_tryon_result")
    if not result:
        flash("No active try-on session found.", "warning")
        return redirect(url_for("dashboard.index"))
        
    garment = DatabaseHelper.get_garment(result["garment_id"])
    return render_template("tryon/result.html", result=result, garment=garment)
