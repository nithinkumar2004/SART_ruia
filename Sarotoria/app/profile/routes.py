from flask import render_template, redirect, url_for, session, request, flash
from app.profile import profile_bp
from app.utils.db_client import DatabaseHelper

@profile_bp.route("/")
def index():
    """Renders customer body calibration settings panel."""
    user_id = session.get("user_id")
    profile = session.get("profile")

    if not user_id or not profile:
        flash("Login session required to access profile configurations.", "danger")
        return redirect(url_for("auth.login"))

    # Force sync profile details from DB
    synced_profile = DatabaseHelper.get_profile(user_id)
    if synced_profile:
        session["profile"] = synced_profile
        profile = synced_profile

    return render_template("profile/view.html", profile=profile)

@profile_bp.route("/update", methods=["POST"])
def update_profile():
    """Updates customer's body measurements metrics and preferred styles."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Unauthorized session.", "danger")
        return redirect(url_for("auth.login"))
        
    full_name = request.form.get("full_name")
    gender = request.form.get("gender")
    age = request.form.get("age")
    height = request.form.get("height")
    weight = request.form.get("weight")
    skin_tone = request.form.get("skin_tone")
    body_type = request.form.get("body_type")
    
    preferences = request.form.getlist("preferences")
    
    email = session.get("profile", {}).get("email") or f"customer_{user_id[:8]}@sarotoria.app"
    
    # Save updates
    updated_profile = DatabaseHelper.create_profile(
        user_id=user_id,
        full_name=full_name,
        email=email,
        gender=gender,
        age=age,
        height=height,
        weight=weight,
        skin_tone=skin_tone,
        body_type=body_type,
        preferences=preferences
    )
    
    if updated_profile:
        session["profile"] = updated_profile
        flash("Body metrics profile updated successfully!", "success")
    else:
        flash("Failed to update measurements profile.", "danger")
        
    return redirect(url_for("profile.index"))
