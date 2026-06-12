import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "saturn_nexus_super_secret_key_1337_!")
    
    # Supabase Configuration (Optional - Falls back to local SQLite if empty)
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Determine the database engine
    USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
    
    # SQLite Database Name
    DB_NAME = "saturn_nexus.db"
    
    # Path configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(os.path.dirname(BASE_DIR), DB_NAME)
    
    # Storage folders
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    QR_FOLDER = os.path.join(BASE_DIR, "static", "qr")
    
    # Supported File Formats
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
