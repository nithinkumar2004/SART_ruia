from flask import render_template, redirect, url_for, session, request, flash
from app.wardrobe import wardrobe_bp
from app.utils.db_client import DatabaseHelper

@wardrobe_bp.route("/")
def index():
    """Renders smart wardrobe categorized by occasion folders."""
    user_id = session.get("user_id")
    profile = session.get("profile")

    if not user_id or not profile:
        flash("Login session required to access your AI Wardrobe.", "danger")
        return redirect(url_for("auth.login"))

    category_filter = request.args.get("category")
    if category_filter == "All":
        category_filter = None

    # Fetch matching items from the customer's wardrobes table
    items = DatabaseHelper.get_wardrobe(user_id, category_filter)
    
    # Calculate folder aggregates for visual badge counters
    all_items = DatabaseHelper.get_wardrobe(user_id)
    counts = {
        "All": len(all_items),
        "Casual": len([i for i in all_items if i.get("folder_category") == "Casual"]),
        "Office": len([i for i in all_items if i.get("folder_category") == "Office"]),
        "Travel": len([i for i in all_items if i.get("folder_category") == "Travel"]),
        "Wedding": len([i for i in all_items if i.get("folder_category") == "Wedding"]),
        "Party": len([i for i in all_items if i.get("folder_category") == "Party"])
    }

    return render_template(
        "wardrobe/index.html",
        items=items,
        counts=counts,
        active_cat=category_filter or "All"
    )

@wardrobe_bp.route("/delete", methods=["POST"])
def delete_item():
    """Removes garment from wardrobe."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401
        
    wardrobe_id = request.form.get("wardrobe_id")
    if not wardrobe_id:
        flash("Wardrobe item credentials missing.", "danger")
        return redirect(url_for("wardrobe.index"))
        
    success = DatabaseHelper.remove_from_wardrobe(user_id, wardrobe_id)
    if success:
        flash("Garment successfully removed from your digital wardrobe.", "success")
    else:
        flash("Failed to remove garment from wardrobe.", "danger")
        
    return redirect(url_for("wardrobe.index"))
