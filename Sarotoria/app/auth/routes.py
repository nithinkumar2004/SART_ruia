import uuid
from flask import render_template, redirect, url_for, request, flash, session
from app.auth import auth_bp
from app.utils.db_client import DatabaseHelper, supabase_client, Config

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Customer portal login."""
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not email or not password:
            flash("Provide both email and password credentials.", "danger")
            return render_template("auth/login.html")

        if Config.USE_SUPABASE and supabase_client:
            try:
                # Direct Supabase Auth Sign-In
                auth_res = supabase_client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                if auth_res and auth_res.user:
                    user_id = auth_res.user.id
                    session["user_id"] = user_id
                    
                    # Fetch or build customer profile details
                    profile = DatabaseHelper.get_profile(user_id)
                    if profile:
                        session["profile"] = profile
                        flash(f"Welcome back, {profile.get('full_name')}!", "success")
                        return redirect(url_for("dashboard.index"))
                    else:
                        # Redirect to Onboarding to populate profile details if first login!
                        session["temp_email"] = email
                        flash("Authentication successful! Let's calibrate your style body profiles.", "warning")
                        return redirect(url_for("auth.onboarding"))
            except Exception as e:
                err_msg = str(e)
                if "invalid login credentials" in err_msg.lower():
                    flash("Invalid email or password credentials. Please try again.", "danger")
                elif "rate limit" in err_msg.lower():
                    flash(
                        "Login failed: Supabase rate limit exceeded. "
                        "To continue testing immediately, comment out the SUPABASE_URL and SUPABASE_KEY in your '.env' file "
                        "to switch the application into Local SQLite Offline Mode.",
                        "warning"
                    )
                else:
                    flash(f"Login failed: {err_msg}", "danger")
                return render_template("auth/login.html")
        else:
            # Local Offline Mode - Auto-create or resolve user profile directly!
            # Since local mode doesn't have an auth provider, we match or create based on email!
            profile = DatabaseHelper.get_profile_by_email(email)
            if profile:
                user_id = profile["id"]
                session["user_id"] = user_id
                session["profile"] = profile
                flash(f"Offline Mode: Logged in successfully as {profile.get('full_name')}!", "success")
                return redirect(url_for("dashboard.index"))
            else:
                # Direct signup redirection
                flash("Email not registered locally. Creating a new profile now!", "warning")
                user_id = str(uuid.uuid4())
                session["user_id"] = user_id
                session["temp_email"] = email
                return redirect(url_for("auth.onboarding"))

    return render_template("auth/login.html")

@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Customer account signup portal."""
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        
        if not email or not password or not confirm_password:
            flash("Complete all required signup fields.", "danger")
            return render_template("auth/signup.html")
            
        if password != confirm_password:
            flash("Passwords do not match. Please verify your entries.", "danger")
            return render_template("auth/signup.html")

        if Config.USE_SUPABASE and supabase_client:
            try:
                # Direct Supabase Auth Sign-Up
                auth_res = supabase_client.auth.sign_up({
                    "email": email,
                    "password": password
                })
                if auth_res and auth_res.user:
                    user_id = auth_res.user.id
                    session["user_id"] = user_id
                    session["temp_email"] = email
                    
                    flash("Account created! Let's build your AI Fashion Profile.", "success")
                    return redirect(url_for("auth.onboarding"))
            except Exception as e:
                err_msg = str(e)
                if "rate limit" in err_msg.lower():
                    flash(
                        "Registration failed: Supabase email rate limit exceeded. "
                        "To bypass this and continue testing instantly, comment out the SUPABASE_URL and SUPABASE_KEY "
                        "in your '.env' file to switch to Local SQLite Offline Mode!",
                        "warning"
                    )
                else:
                    flash(f"Registration failed: {err_msg}", "danger")
                return render_template("auth/signup.html")
        else:
            # Local Offline Mode - Bypass auth, create session and proceed to onboarding!
            user_id = str(uuid.uuid4())
            session["user_id"] = user_id
            session["temp_email"] = email
            flash("Account registered locally! Calibration onboarding triggered.", "success")
            return redirect(url_for("auth.onboarding"))

    return render_template("auth/signup.html")

@auth_bp.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    """Collects customer measurements and styles profile parameters."""
    user_id = session.get("user_id")
    if not user_id:
        flash("Start authentication sequence before profile creation.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "Customer Name")
        gender = request.form.get("gender", "Unisex")
        age = request.form.get("age", 25)
        height = request.form.get("height", 170)
        weight = request.form.get("weight", 70)
        skin_tone = request.form.get("skin_tone", "Neutral")
        body_type = request.form.get("body_type", "Average")
        
        # Check fashion checkboxes
        preferences = request.form.getlist("preferences")
        
        email = session.get("temp_email") or f"customer_{user_id[:8]}@sarotoria.app"
        
        # Write to profiles table
        profile = DatabaseHelper.create_profile(
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
        
        if profile:
            session["profile"] = profile
            # Clean temporary storage
            session.pop("temp_email", None)
            flash("Onboarding calibration complete! Welcome to Sartoria AI.", "success")
            return redirect(url_for("dashboard.index"))
        else:
            flash("Onboarding database entry failed. Please review values.", "danger")

    return render_template("auth/onboarding.html")

@auth_bp.route("/logout")
def logout():
    """Terminates customer session."""
    if Config.USE_SUPABASE and supabase_client and session.get("user_id"):
        try:
            supabase_client.auth.sign_out()
        except Exception:
            pass
            
    session.clear()
    flash("Session terminated successfully.", "success")
    return redirect(url_for("auth.login"))
