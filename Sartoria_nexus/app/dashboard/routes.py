from flask import Blueprint, render_template, redirect, flash
from flask_login import login_required, current_user
from app.utils.db_helper import DatabaseHelper

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def overview():
    """Renders the main fashion-tech seller workspace with stats cards and metrics overview."""
    if not current_user.business_name:
        flash("Please complete your business profile registration.", "info")
        return redirect("/register-business")
        
    # Gather aggregated stats
    stats = DatabaseHelper.get_analytics_summary(current_user.id)
    
    # Get recent uploads
    garments = DatabaseHelper.get_garments_by_user(current_user.id)[:6]
    
    return render_template(
        "dashboard/overview.html",
        stats=stats,
        recent_garments=garments
    )

@dashboard_bp.route("/analytics")
@login_required
def analytics():
    """Renders detailed scan traffic reports, devices breakdowns, and full logs table."""
    if not current_user.business_name:
        flash("Please complete your business profile registration.", "info")
        return redirect("/register-business")
        
    stats = DatabaseHelper.get_analytics_summary(current_user.id)
    
    return render_template(
        "dashboard/analytics.html",
        stats=stats
    )
