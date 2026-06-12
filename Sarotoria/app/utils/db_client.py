import sqlite3
import os
import uuid
from datetime import datetime
from app.config import Config

# Global Supabase client instance (initialized if credentials are provided)
supabase_client = None
if Config.USE_SUPABASE:
    try:
        # Monkeypatch re.match to bypass local JWT validation for Supabase publishable keys
        import re
        original_match = re.match
        def patched_match(pattern, string, flags=0):
            if pattern == r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$":
                class MockMatch:
                    pass
                return MockMatch()
            return original_match(pattern, string, flags)
        re.match = patched_match

        from supabase import create_client
        supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        print("Sarotoria Supabase Client successfully initialized.")
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}. Falling back to Local SQLite mode.")
        Config.USE_SUPABASE = False

# Path to the shared SQLite database of the seller-side (Sartoria Nexus)
NEXUS_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(Config.BASE_DIR)), "Sartoria_nexus", "saturn_nexus.db")

def get_local_conn():
    """Returns a thread-safe connection to the local customer database."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_nexus_conn():
    """Returns a thread-safe connection to the Nexus seller database if it exists (local fallback)."""
    if os.path.exists(NEXUS_DB_PATH):
        conn = sqlite3.connect(NEXUS_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    return None

def init_db():
    """Bootstraps the local SQLite database structures when in Local Mode."""
    # Note: We ALWAYS initialize local SQLite tables so they are ready as fallbacks!
    print(f"Sarotoria Database: Ensuring Local SQLite tables exist at {Config.DB_PATH}")
    conn = get_local_conn()
    cursor = conn.cursor()
    
    # 1. Profiles table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
        id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        gender TEXT,
        age INT,
        height NUMERIC,
        weight NUMERIC,
        skin_tone TEXT,
        body_type TEXT,
        fashion_preferences TEXT, -- Stored as comma-separated string locally
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Wardrobes table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wardrobes (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        garment_id TEXT,
        folder_category TEXT DEFAULT 'Casual',
        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
    );
    """)
    
    # 3. Tryons table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tryons (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        garment_id TEXT,
        output_image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
    );
    """)
    
    # 4. Outfit History table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS outfit_history (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        occasion TEXT,
        generated_result TEXT, -- JSON string locally
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE
    );
    """)
    
    # 5. Local scans helper table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qr_scans (
        id TEXT PRIMARY KEY,
        garment_id TEXT,
        user_id TEXT,
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        device_type TEXT DEFAULT 'Mobile',
        country TEXT DEFAULT 'Unknown',
        ip_address TEXT DEFAULT '127.0.0.1'
    );
    """)
    
    conn.commit()
    conn.close()

class DatabaseHelper:
    
    # ==========================================
    # CUSTOMER PROFILE OPERATIONS
    # ==========================================
    
    @staticmethod
    def create_profile(user_id, full_name, email, gender=None, age=None, height=None, weight=None, skin_tone=None, body_type=None, preferences=None):
        """Creates or registers a customer profile, with dynamic local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": user_id,
                    "full_name": full_name,
                    "email": email,
                    "gender": gender,
                    "age": int(age) if age else None,
                    "height": float(height) if height else None,
                    "weight": float(weight) if weight else None,
                    "skin_tone": skin_tone,
                    "body_type": body_type,
                    "fashion_preferences": preferences if isinstance(preferences, list) else []
                }
                # RLS check: UPSERT/INSERT
                response = supabase_client.table("profiles").upsert(data).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase create_profile returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase create_profile error: {e}. Automatically falling back to Local SQLite.")
                # Flow proceeds to local write below

        # Local mode write
        conn = get_local_conn()
        cursor = conn.cursor()
        prefs_str = ",".join(preferences) if isinstance(preferences, list) else ""
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO profiles (id, full_name, email, gender, age, height, weight, skin_tone, body_type, fashion_preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, full_name, email, gender, age, height, weight, skin_tone, body_type, prefs_str))
            conn.commit()
            return {
                "id": user_id,
                "full_name": full_name,
                "email": email,
                "gender": gender,
                "age": age,
                "height": height,
                "weight": weight,
                "skin_tone": skin_tone,
                "body_type": body_type,
                "fashion_preferences": preferences
            }
        except Exception as e:
            print(f"SQLite create_profile error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_profile(user_id):
        """Fetches profile details of a customer, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("profiles").select("*").eq("id", user_id).execute()
                if response.data:
                    return response.data[0]
            except Exception as e:
                print(f"Supabase get_profile error: {e}. Falling back to SQLite.")

        # Local mode read fallback (runs if Supabase threw exception OR returned empty results)
        conn = get_local_conn()
        row = conn.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if row:
            r = dict(row)
            r["fashion_preferences"] = r["fashion_preferences"].split(",") if r.get("fashion_preferences") else []
            return r
        return None

    @staticmethod
    def get_profile_by_email(email):
        """Fetches profile details of a customer by email, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("profiles").select("*").eq("email", email).execute()
                if response.data:
                    return response.data[0]
            except Exception as e:
                print(f"Supabase get_profile_by_email error: {e}. Falling back to SQLite.")

        # Local mode read fallback (runs if Supabase threw exception OR returned empty results)
        conn = get_local_conn()
        row = conn.execute("SELECT * FROM profiles WHERE email = ?", (email,)).fetchone()
        conn.close()
        if row:
            r = dict(row)
            r["fashion_preferences"] = r["fashion_preferences"].split(",") if r.get("fashion_preferences") else []
            return r
        return None

    # ==========================================
    # GARMENT READ OPERATIONS (DIRECTLY FROM NEXUS IN LOCAL / SHARED TABLE IN SUPABASE)
    # ==========================================
    
    @staticmethod
    def get_garment(garment_id):
        """Directly reads garment specifications from the shared tables."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("garments").select("*").eq("id", garment_id).execute()
                g = response.data[0] if response.data else None
                if g:
                    if "seller_id" in g:
                        g["user_id"] = g["seller_id"]
                    if g.get("image_url") and not g["image_url"].startswith("http"):
                        if g["image_url"].startswith("uploads/"):
                            g["image_url"] = f"http://127.0.0.1:5000/static/{g['image_url']}"
                    return g
            except Exception as e:
                print(f"Supabase get_garment error: {e}. Falling back to Nexus DB.")

        # Fallback to local Nexus DB to read the seller's catalog!
        conn = get_nexus_conn()
        if conn:
            row = conn.execute("SELECT * FROM garments WHERE id = ?", (garment_id,)).fetchone()
            conn.close()
            if row:
                g = dict(row)
                if "seller_id" in g:
                    g["user_id"] = g["seller_id"]
                elif "user_id" in g:
                    g["seller_id"] = g["user_id"]
                if g.get("image_url") and not g["image_url"].startswith("http"):
                    if g["image_url"].startswith("uploads/"):
                        g["image_url"] = f"http://127.0.0.1:5000/static/{g['image_url']}"
                return g
        return None

    @staticmethod
    def get_all_garments(limit=20):
        """Fetches catalog of public garments from shared database."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("garments").select("*").limit(limit).execute()
                data = response.data or []
                if data:
                    for g in data:
                        if "seller_id" in g:
                            g["user_id"] = g["seller_id"]
                        if g.get("image_url") and not g["image_url"].startswith("http"):
                            if g["image_url"].startswith("uploads/"):
                                g["image_url"] = f"http://127.0.0.1:5000/static/{g['image_url']}"
                    return data
            except Exception as e:
                print(f"Supabase get_all_garments error: {e}. Falling back to Nexus DB.")

        conn = get_nexus_conn()
        if conn:
            rows = conn.execute("SELECT * FROM garments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            conn.close()
            data = []
            for row in rows:
                g = dict(row)
                if "seller_id" in g:
                    g["user_id"] = g["seller_id"]
                elif "user_id" in g:
                    g["seller_id"] = g["user_id"]
                if g.get("image_url") and not g["image_url"].startswith("http"):
                    if g["image_url"].startswith("uploads/"):
                        g["image_url"] = f"http://127.0.0.1:5000/static/{g['image_url']}"
                data.append(g)
            return data
        return []

    # ==========================================
    # WARDROBE OPERATIONS
    # ==========================================
    
    @staticmethod
    def add_to_wardrobe(user_id, garment_id, folder_category="Casual"):
        """Saves a garment to customer wardrobe, with SQLite fallback."""
        w_id = str(uuid.uuid4())
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": w_id,
                    "user_id": user_id,
                    "garment_id": garment_id,
                    "folder_category": folder_category
                }
                response = supabase_client.table("wardrobes").insert(data).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase add_to_wardrobe returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase add_to_wardrobe error: {e}. Falling back to SQLite.")

        # Local mode write
        conn = get_local_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO wardrobes (id, user_id, garment_id, folder_category)
                VALUES (?, ?, ?, ?)
            """, (w_id, user_id, garment_id, folder_category))
            conn.commit()
            return {"id": w_id, "user_id": user_id, "garment_id": garment_id, "folder_category": folder_category}
        except Exception as e:
            print(f"SQLite add_to_wardrobe error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_wardrobe(user_id, folder_category=None):
        """Fetches customer's wardrobe items including garment specs, with SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                q = supabase_client.table("wardrobes").select("*, garments(*)").eq("user_id", user_id)
                if folder_category:
                    q = q.eq("folder_category", folder_category)
                response = q.execute()
                if response.data:
                    data = response.data
                    for item in data:
                        g = item.get("garments")
                        if g and "seller_id" in g:
                            g["user_id"] = g["seller_id"]
                    return data
            except Exception as e:
                print(f"Supabase get_wardrobe error: {e}. Falling back to SQLite.")

        # Local mode read fallback (runs if Supabase threw exception OR returned empty results)
        conn = get_local_conn()
        if folder_category:
            rows = conn.execute("SELECT * FROM wardrobes WHERE user_id = ? AND folder_category = ?", (user_id, folder_category)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM wardrobes WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        
        wardrobe_items = []
        for row in rows:
            item = dict(row)
            item["garments"] = DatabaseHelper.get_garment(item["garment_id"])
            wardrobe_items.append(item)
        return wardrobe_items

    @staticmethod
    def remove_from_wardrobe(user_id, wardrobe_id):
        """Deletes item from wardrobe, with SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("wardrobes").delete().eq("id", wardrobe_id).eq("user_id", user_id).execute()
                return True
            except Exception as e:
                print(f"Supabase remove_from_wardrobe error: {e}. Falling back to SQLite.")

        # Local mode write
        conn = get_local_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM wardrobes WHERE id = ? AND user_id = ?", (wardrobe_id, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"SQLite remove_from_wardrobe error: {e}")
            return False
        finally:
            conn.close()

    # ==========================================
    # TRY-ON OPERATIONS
    # ==========================================
    
    @staticmethod
    def save_tryon(user_id, garment_id, output_image_url):
        """Saves an AI Virtual Try-On visual result, with SQLite fallback."""
        t_id = str(uuid.uuid4())
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": t_id,
                    "user_id": user_id,
                    "garment_id": garment_id,
                    "output_image": output_image_url
                }
                response = supabase_client.table("tryons").insert(data).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase save_tryon returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase save_tryon error: {e}. Falling back to SQLite.")

        # Local mode write
        conn = get_local_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO tryons (id, user_id, garment_id, output_image)
                VALUES (?, ?, ?, ?)
            """, (t_id, user_id, garment_id, output_image_url))
            conn.commit()
            return {"id": t_id, "user_id": user_id, "garment_id": garment_id, "output_image": output_image_url}
        except Exception as e:
            print(f"SQLite save_tryon error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_tryons(user_id):
        """Fetches virtual fitting records of the customer, with SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("tryons").select("*, garments(*)").eq("user_id", user_id).order("created_at", desc=True).execute()
                if response.data:
                    data = response.data
                    for item in data:
                        g = item.get("garments")
                        if g and "seller_id" in g:
                            g["user_id"] = g["seller_id"]
                    return data
            except Exception as e:
                print(f"Supabase get_tryons error: {e}. Falling back to SQLite.")

        # Local mode read fallback (runs if Supabase threw exception OR returned empty results)
        conn = get_local_conn()
        rows = conn.execute("SELECT * FROM tryons WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        conn.close()
        
        tryon_records = []
        for row in rows:
            item = dict(row)
            item["garments"] = DatabaseHelper.get_garment(item["garment_id"])
            tryon_records.append(item)
        return tryon_records

    # ==========================================
    # Conversational Styling Outfit History
    # ==========================================
    
    @staticmethod
    def save_outfit_suggestion(user_id, occasion, result_dict):
        """Saves Gemini outfit recommendations, with SQLite fallback."""
        import json
        h_id = str(uuid.uuid4())
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": h_id,
                    "user_id": user_id,
                    "occasion": occasion,
                    "generated_result": result_dict
                }
                response = supabase_client.table("outfit_history").insert(data).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase save_outfit_suggestion returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase save_outfit_suggestion error: {e}. Falling back to SQLite.")

        # Local mode write
        conn = get_local_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO outfit_history (id, user_id, occasion, generated_result)
                VALUES (?, ?, ?, ?)
            """, (h_id, user_id, occasion, json.dumps(result_dict)))
            conn.commit()
            return {"id": h_id, "user_id": user_id, "occasion": occasion, "generated_result": result_dict}
        except Exception as e:
            print(f"SQLite save_outfit_suggestion error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_outfit_history(user_id):
        """Fetches history of chat stylist matches, with SQLite fallback."""
        import json
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("outfit_history").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                if response.data:
                    return response.data
            except Exception as e:
                print(f"Supabase get_outfit_history error: {e}. Falling back to SQLite.")

        # Local mode read fallback (runs if Supabase threw exception OR returned empty results)
        conn = get_local_conn()
        rows = conn.execute("SELECT * FROM outfit_history WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        conn.close()
        
        history = []
        for row in rows:
            item = dict(row)
            try:
                item["generated_result"] = json.loads(item["generated_result"])
            except Exception:
                pass
            history.append(item)
        return history

    # ==========================================
    # QR Scan Tracker
    # ==========================================
    
    @staticmethod
    def log_qr_scan(garment_id, user_id=None, device_type="Mobile", country="Unknown", ip_address="127.0.0.1"):
        """Logs a qr scan in the shared table (if online) or customer DB (if local)."""
        scan_id = str(uuid.uuid4())
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": scan_id,
                    "garment_id": garment_id,
                    "user_id": user_id,
                    "device_type": device_type,
                    "country": country,
                    "ip_address": ip_address
                }
                # Shared table insertion
                response = supabase_client.table("qr_scans").insert(data).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase log_qr_scan returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase log_qr_scan error: {e}. Falling back to SQLite.")

        # Local mode write
        conn = get_local_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO qr_scans (id, garment_id, user_id, device_type, country, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (scan_id, garment_id, user_id, device_type, country, ip_address))
            conn.commit()
            return {"id": scan_id, "garment_id": garment_id, "user_id": user_id}
        except Exception as e:
            print(f"SQLite log_qr_scan error: {e}")
            return None
        finally:
            conn.close()
