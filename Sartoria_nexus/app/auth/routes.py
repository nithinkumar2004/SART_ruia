import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.utils import secure_filename
from app.config import Config
from app.utils.db_helper import DatabaseHelper

auth_bp = Blueprint("auth", __name__)

class User(UserMixin):
    """Flask-Login representation of the Seller User."""
    def __init__(self, user_id, email, phone=None, business_name=None):
        self.id = user_id
        self.email = email
        self.phone = phone
        self.business_name = business_name

    @property
    def is_registered(self):
        """Returns True if the business details have been set."""
        return bool(self.business_name)

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Handles User Signup (Email/Password or Phone OTP triggers)."""
    if current_user.is_authenticated:
        return redirect("/dashboard")
        
    if request.method == "POST":
        auth_type = request.form.get("auth_type", "email") # email or phone
        
        if auth_type == "email":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password")
            
            if not email or not password:
                flash("Email and Password are required.", "danger")
                return render_template("auth/signup.html")
                
            # Check if user already exists
            existing_user = DatabaseHelper.get_user_by_email(email)
            if existing_user:
                flash("An account with this email already exists.", "warning")
                return render_template("auth/signup.html")
                
            # Create user record (in SQLite or Supabase)
            # In MVP, we use the email as id prefix or standard UUID
            user_id = str(uuid.uuid4())
            new_user = DatabaseHelper.create_user(user_id=user_id, email=email)
            
            if new_user:
                # Log the user in
                user_obj = User(user_id, email)
                login_user(user_obj)
                flash("Signup successful! Let's register your business details.", "success")
                return redirect("/register-business")
            else:
                flash("An error occurred during signup. Please try again.", "danger")
                
        elif auth_type == "phone":
            phone = request.form.get("phone", "").strip()
            if not phone:
                flash("Phone number is required.", "danger")
                return render_template("auth/signup.html")
                
            # Generate a 6-digit verification code
            otp = "777888" # High quality standard test OTP
            session["phone_auth"] = {"phone": phone, "otp": otp, "is_signup": True}
            
            flash(f"[DEMO OTP] A verification code {otp} has been simulated for phone: {phone}", "info")
            return redirect(url_for("auth.verify_otp"))
            
    return render_template("auth/signup.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles Seller Sign-In."""
    if current_user.is_authenticated:
        return redirect("/dashboard")
        
    if request.method == "POST":
        auth_type = request.form.get("auth_type", "email")
        
        if auth_type == "email":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password")
            
            # Retrieve user
            user_dict = DatabaseHelper.get_user_by_email(email)
            if user_dict:
                user_obj = User(user_dict["id"], user_dict["email"], user_dict.get("phone"), user_dict.get("business_name"))
                login_user(user_obj)
                
                # Check onboarding status
                if not user_obj.is_registered:
                    flash("Please complete your business profile registration.", "info")
                    return redirect("/register-business")
                    
                flash("Welcome back to Sartoria Nexus!", "success")
                return redirect("/dashboard")
            else:
                flash("Invalid credentials or user does not exist.", "danger")
                
        elif auth_type == "phone":
            phone = request.form.get("phone", "").strip()
            if not phone:
                flash("Phone number is required.", "danger")
                return render_template("auth/login.html")
                
            # Check if user exists
            user_dict = DatabaseHelper.get_user_by_phone(phone)
            otp = "123456" # Demo OTP for quick testing
            
            session["phone_auth"] = {
                "phone": phone, 
                "otp": otp, 
                "is_signup": False,
                "user_id": user_dict["id"] if user_dict else None
            }
            
            flash(f"[DEMO OTP] A verification code {otp} has been simulated for phone: {phone}", "info")
            return redirect(url_for("auth.verify_otp"))
            
    return render_template("auth/login.html")

@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    """Verifies simulated phone OTP."""
    phone_auth = session.get("phone_auth")
    if not phone_auth:
        flash("No active phone verification session found.", "warning")
        return redirect(url_for("auth.login"))
        
    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        
        if entered_otp == phone_auth["otp"]:
            phone = phone_auth["phone"]
            is_signup = phone_auth["is_signup"]
            
            if is_signup:
                user_id = str(uuid.uuid4())
                # Create user with phone
                email = f"phone_{phone.replace('+', '')}@sartoria.nexus"
                DatabaseHelper.create_user(user_id=user_id, email=email, phone=phone)
                user_obj = User(user_id, email, phone)
                login_user(user_obj)
                session.pop("phone_auth", None)
                flash("Phone verified! Setup your business profile.", "success")
                return redirect("/register-business")
            else:
                # Existing user login
                user_id = phone_auth["user_id"]
                if not user_id:
                    # Treat as auto-signup if phone was not found
                    user_id = str(uuid.uuid4())
                    email = f"phone_{phone.replace('+', '')}@sartoria.nexus"
                    DatabaseHelper.create_user(user_id=user_id, email=email, phone=phone)
                    user_obj = User(user_id, email, phone)
                    login_user(user_obj)
                    session.pop("phone_auth", None)
                    return redirect("/register-business")
                    
                user_dict = DatabaseHelper.get_user(user_id)
                user_obj = User(user_dict["id"], user_dict["email"], user_dict.get("phone"), user_dict.get("business_name"))
                login_user(user_obj)
                session.pop("phone_auth", None)
                
                if not user_obj.is_registered:
                    return redirect("/register-business")
                    
                flash("Phone logged in successfully!", "success")
                return redirect("/dashboard")
        else:
            flash("Invalid OTP code. Please enter the simulated code again.", "danger")
            
    return render_template("auth/verify_otp.html", phone=phone_auth["phone"])

@auth_bp.route("/register-business", methods=["GET", "POST"])
@login_required
def register_business():
    """Onboarding Page: Collects brand business details and logo."""
    if current_user.is_registered:
        return redirect("/dashboard")
        
    if request.method == "POST":
        business_name = request.form.get("business_name", "").strip()
        business_type = request.form.get("business_type")
        inventory_source = request.form.get("inventory_source")
        website_url = request.form.get("website_url", "").strip()
        gst_id = request.form.get("gst_id", "").strip()
        
        if not business_name or not business_type or not inventory_source:
            flash("Please fill in all mandatory fields.", "danger")
            return render_template("auth/registration.html")
            
        # Handle business logo upload
        logo_file = request.files.get("business_logo")
        logo_url = None
        
        if logo_file and logo_file.filename:
            # Validate format
            ext = logo_file.filename.rsplit(".", 1)[-1].lower()
            if ext in Config.ALLOWED_EXTENSIONS:
                os.makedirs(os.path.join(current_app.config["UPLOAD_FOLDER"], "logos"), exist_ok=True)
                logo_filename = f"logo_{current_user.id}_{int(uuid.uuid4().int % 100000)}.{ext}"
                logo_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "logos", logo_filename)
                logo_file.save(logo_path)
                logo_url = f"uploads/logos/{logo_filename}"
            else:
                flash("Unsupported logo format. Allowed: PNG, JPG, JPEG, WEBP.", "warning")
                
        # Save business registration profile
        success = DatabaseHelper.update_user_profile(
            user_id=current_user.id,
            business_name=business_name,
            business_type=business_type,
            inventory_source=inventory_source,
            website_url=website_url if website_url else None,
            gst_id=gst_id if gst_id else None,
            logo_url=logo_url
        )
        
        if success:
            # Refresh current session object name
            current_user.business_name = business_name
            flash("Business Profile Registered! Welcome to Sartoria Nexus.", "success")
            return redirect("/dashboard")
        else:
            flash("Failed to update profile. Please try again.", "danger")
            
    return render_template("auth/registration.html")

@auth_bp.route("/logout")
@login_required
def logout():
    """Logs the user out and clears the session."""
    logout_user()
    flash("You have logged out successfully.", "success")
    return redirect("/")
