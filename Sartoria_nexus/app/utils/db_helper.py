import sqlite3
import os
import uuid
from datetime import datetime
from app.config import Config

# Global Supabase client instance (initialized if credentials are provided)
supabase_client = None
if Config.USE_SUPABASE:
    try:
        # Monkeypatch re.match to bypass local JWT validation for the new Supabase keys format
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
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}. Falling back to Local SQLite mode.")
        # Force SQLite mode
        Config.USE_SUPABASE = False

def get_sqlite_conn():
    """Returns a thread-safe connection to the SQLite database."""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SQLite database schema if in Local Mode."""
    # Note: We ALWAYS initialize SQLite tables so they are ready as fallbacks!
    print(f"Database Running: Ensuring Local SQLite tables exist at {Config.DB_PATH}")
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    
    # Create Sellers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sellers (
        id TEXT PRIMARY KEY,
        auth_user_id TEXT,
        email TEXT UNIQUE,
        phone TEXT UNIQUE,
        business_name TEXT,
        business_type TEXT,
        inventory_source TEXT,
        website_url TEXT,
        gst_id TEXT,
        logo_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Check if garments table exists and requires migration from user_id to seller_id
    try:
        cursor.execute("PRAGMA table_info(garments)")
        columns = [row[1] for row in cursor.fetchall()]
        if columns:
            if "seller_id" not in columns:
                if "user_id" in columns:
                    print("Migration: Renaming 'user_id' to 'seller_id' in garments table.")
                    cursor.execute("ALTER TABLE garments RENAME COLUMN user_id TO seller_id;")
                else:
                    print("Migration: Adding 'seller_id' column to garments table.")
                    cursor.execute("ALTER TABLE garments ADD COLUMN seller_id TEXT;")
                conn.commit()
    except Exception as e:
        print(f"Migration error during garments table check: {e}")
    
    # Create Garments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS garments (
        id TEXT PRIMARY KEY,
        seller_id TEXT,
        garment_name TEXT,
        category TEXT,
        image_url TEXT,
        qr_url TEXT,
        qr_image TEXT,
        color TEXT,
        style TEXT,
        sleeve_type TEXT,
        pattern TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE
    );
    """)
    
    # Create QR Scans / Analytics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qr_scans (
        id TEXT PRIMARY KEY,
        garment_id TEXT,
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        device_type TEXT,
        country TEXT,
        ip_address TEXT,
        FOREIGN KEY (garment_id) REFERENCES garments(id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

class DatabaseHelper:
    
    @staticmethod
    def get_sqlite_conn():
        """Returns a thread-safe connection to the SQLite database."""
        return get_sqlite_conn()
    
    # ==========================================
    # USER OPERATIONS
    # ==========================================
    
    @staticmethod
    def create_user(user_id, email, phone=None, business_name=None, business_type=None, 
                    inventory_source=None, website_url=None, gst_id=None, logo_url=None):
        """Creates a new seller user in either Supabase or SQLite."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": user_id,
                    "auth_user_id": user_id,
                    "email": email,
                    "phone": phone,
                    "business_name": business_name,
                    "business_type": business_type,
                    "inventory_source": inventory_source,
                    "website_url": website_url,
                    "gst_id": gst_id,
                    "logo_url": logo_url
                }
                response = supabase_client.table("sellers").insert(data).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase create_user returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase create_user error: {e}. Falling back to SQLite.")

        # Local mode write fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO sellers (id, auth_user_id, email, phone, business_name, business_type, 
                                  inventory_source, website_url, gst_id, logo_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, user_id, email, phone, business_name, business_type, 
                  inventory_source, website_url, gst_id, logo_url))
            conn.commit()
            return {"id": user_id, "email": email, "phone": phone, "business_name": business_name}
        except Exception as e:
            print(f"SQLite create_user error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user(user_id):
        """Fetches a user profile by ID, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("sellers").select("*").eq("id", user_id).execute()
                if response.data:
                    return response.data[0]
            except Exception as e:
                print(f"Supabase get_user error: {e}. Falling back to SQLite.")

        # Local mode read fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM sellers WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_user_by_email(email):
        """Fetches a user profile by Email, with local SQLite fallback."""
        if not email:
            return None
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("sellers").select("*").eq("email", email).execute()
                if response.data:
                    return response.data[0]
            except Exception as e:
                print(f"Supabase get_user_by_email error: {e}. Falling back to SQLite.")

        # Local mode read fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM sellers WHERE email = ?", (email,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_user_by_phone(phone):
        """Fetches a user profile by Phone, with local SQLite fallback."""
        if not phone:
            return None
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("sellers").select("*").eq("phone", phone).execute()
                if response.data:
                    return response.data[0]
            except Exception as e:
                print(f"Supabase get_user_by_phone error: {e}. Falling back to SQLite.")

        # Local mode read fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM sellers WHERE phone = ?", (phone,)).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def update_user_profile(user_id, business_name, business_type, inventory_source, 
                            website_url=None, gst_id=None, logo_url=None):
        """Updates user business profile settings, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "business_name": business_name,
                    "business_type": business_type,
                    "inventory_source": inventory_source,
                    "website_url": website_url,
                    "gst_id": gst_id
                }
                if logo_url:
                    data["logo_url"] = logo_url
                    
                response = supabase_client.table("sellers").update(data).eq("id", user_id).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase update_user_profile returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase update_user_profile error: {e}. Falling back to SQLite.")

        # Local mode write fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            if logo_url:
                cursor.execute("""
                    UPDATE sellers
                    SET business_name = ?, business_type = ?, inventory_source = ?, 
                        website_url = ?, gst_id = ?, logo_url = ?
                    WHERE id = ?
                """, (business_name, business_type, inventory_source, website_url, gst_id, logo_url, user_id))
            else:
                cursor.execute("""
                    UPDATE sellers
                    SET business_name = ?, business_type = ?, inventory_source = ?, 
                        website_url = ?, gst_id = ?
                    WHERE id = ?
                """, (business_name, business_type, inventory_source, website_url, gst_id, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"SQLite update_user_profile error: {e}")
            return False
        finally:
            conn.close()

    # ==========================================
    # GARMENT OPERATIONS
    # ==========================================

    @staticmethod
    def create_garment(garment_id, user_id, garment_name, category, image_url, qr_url, qr_image,
                       color=None, style=None, sleeve_type=None, pattern=None):
        """Saves garment product entry, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": garment_id,
                    "seller_id": user_id,
                    "garment_name": garment_name,
                    "category": category,
                    "image_url": image_url,
                    "qr_url": qr_url,
                    "qr_image": qr_image,
                    "color": color,
                    "style": style,
                    "sleeve_type": sleeve_type,
                    "pattern": pattern
                }
                response = supabase_client.table("garments").insert(data).execute()
                if response.data:
                    g = response.data[0]
                    if g and "seller_id" in g:
                        g["user_id"] = g["seller_id"]
                    return g
                else:
                    print("Supabase create_garment returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase create_garment error: {e}. Falling back to SQLite.")

        # Local mode write fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO garments (id, seller_id, garment_name, category, image_url, qr_url, qr_image, 
                                      color, style, sleeve_type, pattern)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (garment_id, user_id, garment_name, category, image_url, qr_url, qr_image, 
                  color, style, sleeve_type, pattern))
            conn.commit()
            return {"id": garment_id, "garment_name": garment_name}
        except Exception as e:
            print(f"SQLite create_garment error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_garments_by_user(user_id):
        """Fetches all garments belonging to a user, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("garments").select("*").eq("seller_id", user_id).order("created_at", desc=True).execute()
                if response.data:
                    data = response.data
                    for g in data:
                        if "seller_id" in g:
                            g["user_id"] = g["seller_id"]
                    return data
            except Exception as e:
                print(f"Supabase get_garments_by_user error: {e}. Falling back to SQLite.")

        # Local mode read fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM garments WHERE seller_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
        conn.close()
        data = []
        for row in rows:
            g = dict(row)
            if "seller_id" in g:
                g["user_id"] = g["seller_id"]
            elif "user_id" in g:
                g["seller_id"] = g["user_id"]
            data.append(g)
        return data

    @staticmethod
    def get_garment(garment_id):
        """Fetches a specific garment by ID, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("garments").select("*").eq("id", garment_id).execute()
                if response.data:
                    g = response.data[0]
                    if g and "seller_id" in g:
                        g["user_id"] = g["seller_id"]
                    return g
            except Exception as e:
                print(f"Supabase get_garment error: {e}. Falling back to SQLite.")

        # Local mode read fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        row = cursor.execute("SELECT * FROM garments WHERE id = ?", (garment_id,)).fetchone()
        conn.close()
        if row:
            g = dict(row)
            if "seller_id" in g:
                g["user_id"] = g["seller_id"]
            elif "user_id" in g:
                g["seller_id"] = g["user_id"]
            return g
        return None

    @staticmethod
    def delete_garment(garment_id):
        """Deletes a specific garment by ID, with local SQLite fallback."""
        if Config.USE_SUPABASE and supabase_client:
            try:
                response = supabase_client.table("garments").delete().eq("id", garment_id).execute()
                if response.data:
                    return len(response.data) > 0
                else:
                    print("Supabase delete_garment returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase delete_garment error: {e}. Falling back to SQLite.")

        # Local mode write fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM garments WHERE id = ?", (garment_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"SQLite delete_garment error: {e}")
            return False
        finally:
            conn.close()

    # ==========================================
    # QR CODE SCAN & ANALYTICS OPERATIONS
    # ==========================================

    @staticmethod
    def log_qr_scan(garment_id, device_type="Mobile", country="Unknown", ip_address="127.0.0.1"):
        """Logs a scan hit from a customer scanning the tag, with local SQLite fallback."""
        scan_id = str(uuid.uuid4())
        if Config.USE_SUPABASE and supabase_client:
            try:
                data = {
                    "id": scan_id,
                    "garment_id": garment_id,
                    "device_type": device_type,
                    "country": country,
                    "ip_address": ip_address
                }
                response = supabase_client.table("qr_scans").insert(data).execute()
                if response.data:
                    return response.data[0]
                else:
                    print("Supabase log_qr_scan returned empty data. Falling back to SQLite.")
            except Exception as e:
                print(f"Supabase log_qr_scan error: {e}. Falling back to SQLite.")

        # Local mode write fallback
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO qr_scans (id, garment_id, device_type, country, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (scan_id, garment_id, device_type, country, ip_address))
            conn.commit()
            return {"id": scan_id, "garment_id": garment_id}
        except Exception as e:
            print(f"SQLite log_qr_scan error: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def get_analytics_summary(user_id):
        """Generates comprehensive aggregated dashboard stats for a seller."""
        default_stats = {
            "total_garments": 0,
            "total_scans": 0,
            "scans_by_device": {},
            "scans_by_country": {},
            "most_scanned": [],
            "scan_history": [],
            "daily_scans": []
        }

        # Try to pull from Supabase first if online, else fallback
        try:
            garments = DatabaseHelper.get_garments_by_user(user_id)
            garment_ids = [g["id"] for g in garments]
            
            if not garment_ids:
                return default_stats
                
            if Config.USE_SUPABASE and supabase_client:
                # Fetch scans from Supabase
                response = supabase_client.table("qr_scans").select("*").in_("garment_id", garment_ids).execute()
                scans = response.data or []
                return DatabaseHelper._aggregate_stats(garments, scans)
        except Exception as e:
            print(f"Supabase get_analytics_summary error: {e}. Falling back to SQLite.")

        # SQLite Mode Aggregates
        conn = get_sqlite_conn()
        cursor = conn.cursor()
        try:
            # Total Garments
            total_garments = cursor.execute("SELECT COUNT(*) FROM garments WHERE seller_id = ?", (user_id,)).fetchone()[0]
            
            # Total Scans
            total_scans = cursor.execute("""
                SELECT COUNT(*) FROM qr_scans s
                JOIN garments g ON s.garment_id = g.id
                WHERE g.seller_id = ?
            """, (user_id,)).fetchone()[0]
            
            # Scans by Device
            device_rows = cursor.execute("""
                SELECT s.device_type, COUNT(*) as count FROM qr_scans s
                JOIN garments g ON s.garment_id = g.id
                WHERE g.seller_id = ?
                GROUP BY s.device_type
            """, (user_id,)).fetchall()
            scans_by_device = {r["device_type"]: r["count"] for r in device_rows}
            
            # Scans by Country
            country_rows = cursor.execute("""
                SELECT s.country, COUNT(*) as count FROM qr_scans s
                JOIN garments g ON s.garment_id = g.id
                WHERE g.seller_id = ?
                GROUP BY s.country
            """, (user_id,)).fetchall()
            scans_by_country = {r["country"]: r["count"] for r in country_rows}
            
            # Most Scanned Products (Top 5)
            most_scanned_rows = cursor.execute("""
                SELECT g.id, g.garment_name, g.category, g.image_url, COUNT(s.id) as scan_count 
                FROM garments g
                LEFT JOIN qr_scans s ON g.id = s.garment_id
                WHERE g.seller_id = ?
                GROUP BY g.id
                ORDER BY scan_count DESC
                LIMIT 5
            """, (user_id,)).fetchall()
            most_scanned = [dict(r) for r in most_scanned_rows]
            
            # Scan History / Activity log (last 10 scans)
            activity_rows = cursor.execute("""
                SELECT g.garment_name, s.scanned_at, s.device_type, s.country, s.ip_address 
                FROM qr_scans s
                JOIN garments g ON s.garment_id = g.id
                WHERE g.seller_id = ?
                ORDER BY s.scanned_at DESC
                LIMIT 10
            """, (user_id,)).fetchall()
            scan_history = [dict(r) for r in activity_rows]
            
            # Chronological chart scan history (grouped by date of last 7 days)
            daily_scans_rows = cursor.execute("""
                SELECT DATE(s.scanned_at) as scan_date, COUNT(*) as count 
                FROM qr_scans s
                JOIN garments g ON s.garment_id = g.id
                WHERE g.seller_id = ?
                GROUP BY scan_date
                ORDER BY scan_date ASC
                LIMIT 7
            """, (user_id,)).fetchall()
            daily_scans = [dict(r) for r in daily_scans_rows]
            
            return {
                "total_garments": total_garments,
                "total_scans": total_scans,
                "scans_by_device": scans_by_device,
                "scans_by_country": scans_by_country,
                "most_scanned": most_scanned,
                "scan_history": scan_history,
                "daily_scans": daily_scans
            }
        except Exception as e:
            print(f"SQLite get_analytics_summary error: {e}")
            return default_stats
        finally:
            conn.close()

    @staticmethod
    def _aggregate_stats(garments, scans):
        """Utility method to perform statistics aggregation for Supabase lists."""
        garment_dict = {g["id"]: g for g in garments}
        total_garments = len(garments)
        total_scans = len(scans)
        
        scans_by_device = {}
        scans_by_country = {}
        garment_scan_counts = {g["id"]: 0 for g in garments}
        
        scan_history = []
        
        # Sort scans by scanned_at descending
        sorted_scans = sorted(scans, key=lambda x: x.get("scanned_at", ""), reverse=True)
        
        for scan in sorted_scans:
            dev = scan.get("device_type", "Mobile")
            country = scan.get("country", "Unknown")
            g_id = scan.get("garment_id")
            
            scans_by_device[dev] = scans_by_device.get(dev, 0) + 1
            scans_by_country[country] = scans_by_country.get(country, 0) + 1
            
            if g_id in garment_scan_counts:
                garment_scan_counts[g_id] += 1
                
            # Log history (max 10)
            if len(scan_history) < 10 and g_id in garment_dict:
                scan_history.append({
                    "garment_name": garment_dict[g_id]["garment_name"],
                    "scanned_at": scan.get("scanned_at"),
                    "device_type": dev,
                    "country": country,
                    "ip_address": scan.get("ip_address")
                })
        
        # Build most scanned items
        for g in garments:
            most_scanned = []
            for g in garments:
                most_scanned.append({
                    "id": g["id"],
                    "garment_name": g["garment_name"],
                    "category": g["category"],
                    "image_url": g["image_url"],
                    "scan_count": garment_scan_counts[g["id"]]
                })
            most_scanned = sorted(most_scanned, key=lambda x: x["scan_count"], reverse=True)[:5]
        
        # Group daily scans (last 7 days of activity)
        daily_scans_map = {}
        for scan in scans:
            dt_str = scan.get("scanned_at", "")
            if dt_str:
                date_part = dt_str.split("T")[0] if "T" in dt_str else dt_str.split(" ")[0]
                daily_scans_map[date_part] = daily_scans_map.get(date_part, 0) + 1
                
        daily_scans = [{"scan_date": d, "count": c} for d, c in sorted(daily_scans_map.items())][-7:]
        
        return {
            "total_garments": total_garments,
            "total_scans": total_scans,
            "scans_by_device": scans_by_device,
            "scans_by_country": scans_by_country,
            "most_scanned": most_scanned,
            "scan_history": scan_history,
            "daily_scans": daily_scans
        }
