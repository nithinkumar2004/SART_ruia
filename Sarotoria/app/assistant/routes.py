from flask import render_template, redirect, url_for, session, request, jsonify, flash
from app.assistant import assistant_bp
from app.utils.db_client import DatabaseHelper
from app.utils.gemini_client import GeminiStylistClient

@assistant_bp.route("/")
def index():
    """Renders real conversational chatbot powered by Google Gemini API."""
    user_id = session.get("user_id")
    profile = session.get("profile")

    if not user_id or not profile:
        flash("Login session required to access your conversational AI stylist.", "danger")
        return redirect(url_for("auth.login"))

    # Initialize chat log list in session
    if "chat_history" not in session:
        session["chat_history"] = [
            {
                "is_user": False,
                "text": f"Hello {profile.get('full_name')}! I am **Sartoria AI**, your personal fashion advisor. Calibrated on your body metrics, I can help you select clothes, match color coordinate schemes, or manage digital wardrobes. Ask me anything!"
            }
        ]

    return render_template("assistant/chat.html", history=session["chat_history"])

@assistant_bp.route("/message", methods=["POST"])
def send_message():
    """Sends text query to Google Gemini and parses outfit advice payload."""
    user_id = session.get("user_id")
    profile = session.get("profile")
    
    if not user_id or not profile:
        return jsonify({"success": False, "error": "Unauthorized session"}), 401
        
    message = request.json.get("message")
    if not message:
        return jsonify({"success": False, "error": "Empty message query"}), 400

    history = session.get("chat_history", [])
    
    # 1. Save user query in history
    history.append({"is_user": True, "text": message})
    
    # 2. Submit to production Google Gemini client
    bot_response = GeminiStylistClient.chat_stylist(message, history[:-1])
    
    # 3. Detect occasion coordinates for smart recommendations
    occasion = None
    msg_l = message.lower()
    for keyword in ["office", "meeting", "wedding", "party", "travel", "hiking", "beach", "dinner", "formal"]:
        if keyword in msg_l:
            occasion = keyword
            break
            
    recommendation_data = None
    if occasion:
        # Pull digital wardrobes items list
        wardrobes_list = DatabaseHelper.get_wardrobe(user_id)
        
        # Trigger Gemini structured outfit recommendations!
        recommendation_data = GeminiStylistClient.get_outfit_recommendations(
            occasion=occasion,
            weather_temp=30,  # Contextual temperature fallback
            body_type=profile.get("body_type", "Average"),
            wardrobe_list=wardrobes_list
        )
        
        # Save outfit history log in database!
        DatabaseHelper.save_outfit_suggestion(
            user_id=user_id,
            occasion=occasion,
            result_dict=recommendation_data
        )

    # 4. Save assistant response in history
    history.append({"is_user": False, "text": bot_response})
    session["chat_history"] = history
    session.modified = True

    return jsonify({
        "success": True,
        "bot_response": bot_response,
        "recommendation": recommendation_data
    })

@assistant_bp.route("/clear", methods=["POST"])
def clear_history():
    """Resets conversational chatbot logs."""
    session.pop("chat_history", None)
    return jsonify({"success": True})
