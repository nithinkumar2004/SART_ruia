from flask import render_template, redirect, url_for, session, flash
from app.dashboard import dashboard_bp
from app.utils.db_client import DatabaseHelper

@dashboard_bp.route("/dashboard")
def index():
    """Main customer dashboard portal."""
    user_id = session.get("user_id")
    profile = session.get("profile")

    if not user_id or not profile:
        flash("Login session required to access your AI Fashion space.", "danger")
        return redirect(url_for("auth.login"))

    # 1. Fetch customer wardrobe items
    wardrobe = DatabaseHelper.get_wardrobe(user_id)
    total_wardrobe = len(wardrobe)
    
    # 2. Fetch customer virtual try-ons
    tryons = DatabaseHelper.get_tryons(user_id)
    total_tryons = len(tryons)
    
    # 3. Pull dynamic suggestions from shared database catalog (Nexus catalog)
    catalog = DatabaseHelper.get_all_garments(limit=8)
    
    # 4. Pull customer outfit history
    outfits = DatabaseHelper.get_outfit_history(user_id)
    total_recommendations = len(outfits)

    # 5. Dynamic welcome advice
    quick_tips = [
        "Calibrate your weight metrics weekly to secure extremely precise AI size matching.",
        "Scan clothing tags offline in boutiques to immediately preview fits digitally.",
        "Add garments to specific wardrobe occasion folders to guide your Gemini conversational advisor."
    ]

    return render_template(
        "dashboard/index.html",
        profile=profile,
        total_wardrobe=total_wardrobe,
        total_tryons=total_tryons,
        total_recommendations=total_recommendations,
        wardrobe=wardrobe[:4], # Show recent 4
        tryons=tryons[:4],     # Show recent 4
        catalog=catalog,
        quick_tips=quick_tips
    )
