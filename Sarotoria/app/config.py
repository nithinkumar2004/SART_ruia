import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "sarotoria_customer_app_secret_key_9876_!")
    
    # Supabase Configuration (Falls back to SQLite locally if missing)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
    
    # Gemini AI Key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Local SQLite DB for fallback testing
    DB_NAME = "sarotoria_customer.db"
    
    # Paths configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(os.path.dirname(BASE_DIR), DB_NAME)
    
    # Shared storage folder structures
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    TRYON_FOLDER = os.path.join(UPLOAD_FOLDER, "tryon")
    AVATAR_FOLDER = os.path.join(BASE_DIR, "static", "images", "avatars")
    
    # Sizing limits & file validations
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload limit
