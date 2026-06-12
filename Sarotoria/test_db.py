import os
import sys

# Ensure Sarotoria path is active
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.utils.db_client import DatabaseHelper, init_db, Config

def main():
    print("=" * 60)
    print("SAROTORIA CONSUMER PLATFORM — DATABASE CONNECTION DIAGNOSTIC")
    print("=" * 60)
    
    # 1. Inspect mode
    print(f"Supabase URL: {Config.SUPABASE_URL}")
    print(f"Active Mode: {'Supabase Cloud Mode' if Config.USE_SUPABASE else 'Local SQLite Mode'}")
    
    # 2. Bootstrap tables
    try:
        init_db()
        print("[SUCCESS] Database initialization completed successfully.")
    except Exception as e:
        print(f"[FAILED] Database schema bootstrapping failed: {e}")
        return

    # 3. Test insert & fetch mock profiles details
    import uuid
    test_id = str(uuid.uuid4())
    test_email = f"diagnostic_customer_{test_id[:8]}@sarotoria.app"
    
    print("\nTesting profile calibration...")
    try:
        res = DatabaseHelper.create_profile(
            user_id=test_id,
            full_name="Diagnostic Tester",
            email=test_email,
            gender="Male",
            age=26,
            height=180,
            weight=75,
            skin_tone="Warm Sand",
            body_type="Athletic",
            preferences=["Casual", "Minimalist"]
        )
        if res:
            print(f"[OK] Customer profile calibration saved: {res.get('full_name')} ({res.get('email')})")
            
            # Fetch back
            profile = DatabaseHelper.get_profile(test_id)
            if profile:
                print(f"[OK] Dynamic profile resolved back successfully. Body silhouette: {profile.get('body_type')}")
            else:
                print("[FAILED] Failed to fetch back profile details.")
        else:
            print("[FAILED] Customer profile creation failed.")
    except Exception as err:
        print(f"[ERROR] Calibration exception: {err}")

    # 4. Shared catalog specs fetch check
    print("\nTesting direct partner catalog reads (Sartoria Nexus)...")
    try:
        garments = DatabaseHelper.get_all_garments(limit=3)
        print(f"[OK] Synced partner garments loaded back: {len(garments)} items.")
        for g in garments:
            print(f"    - ID: {g.get('id')} | Name: {g.get('garment_name')} ({g.get('category')})")
    except Exception as err:
        print(f"[ERROR] Direct catalog read exception: {err}")

    print("=" * 60)

if __name__ == "__main__":
    main()
