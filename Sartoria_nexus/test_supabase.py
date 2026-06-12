import os
from dotenv import load_dotenv

def main():
    print("=" * 60)
    print("SATURN NEXUS QR - SUPABASE CONNECTION DIAGNOSTIC")
    print("=" * 60)

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

    # 1. Load env variables
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    print(f"Supabase URL loaded: {supabase_url}")
    print(f"Supabase Key loaded: {'***' + supabase_key[-8:] if supabase_key else 'None'}")

    if not supabase_url or not supabase_key:
        print("\n[ERROR] Missing Supabase URL or Key. Please check your .env file!")
        return

    # 2. Try to initialize client
    try:
        from supabase import create_client
        print("\nConnecting to Supabase...")
        client = create_client(supabase_url, supabase_key)
        print("[SUCCESS] Supabase Client Initialized Successfully.")
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Failed to initialize Supabase client: {e}")
        traceback.print_exc()
        return

    # 3. Test tables existence and access
    required_tables = ["profiles", "sellers", "garments", "qr_scans", "wardrobes", "tryons", "outfit_history"]
    missing_tables = []
    
    print("\nTesting Access to Database Tables:")
    print("-" * 40)
    
    for table_name in required_tables:
        try:
            # We select with a limit of 1 to make it lightweight
            response = client.table(table_name).select("*").limit(1).execute()
            print(f"[OK] Table '{table_name}' exists and is accessible. (Returned {len(response.data)} rows)")
        except Exception as e:
            err_msg = str(e)
            print(f"[FAILED] Table '{table_name}' access failed.")
            print(f"    Details: {err_msg}")
            missing_tables.append(table_name)

    print("-" * 40)
    if missing_tables:
        print(f"\n[ATTENTION] The following tables are missing or inaccessible in your Supabase DB: {missing_tables}")
        print("Please log into your Supabase Dashboard, open the SQL Editor, and execute the")
        print("schema queries from C:\\Users\\satya\\.gemini\\antigravity-ide\\brain\\4a70047d-2e5a-400d-8e7c-6f3a1b96586d\\scratch\\supabase_schema.sql")
    else:
        print("\n[CONGRATULATIONS] All database tables are present and connected properly!")
        print("Your project is ready to run in Supabase Cloud Mode.")
        
        print("\n[TEST] Attempting to insert a dummy seller into 'sellers' table...")
        try:
            test_uuid = "da82c5e5-f5b2-4d27-8a62-671c66708779"
            test_data = {"id": test_uuid, "email": "test_diagnostic@saturn.nexus", "business_name": "Diagnostic Brand"}
            # Delete if exists first to avoid duplicate key errors
            try:
                client.table("sellers").delete().eq("id", test_uuid).execute()
            except Exception:
                pass
            
            insert_response = client.table("sellers").insert(test_data).execute()
            print(f"[TEST SUCCESS] Successfully inserted dummy seller: {insert_response.data}")
            
            # Clean up
            client.table("sellers").delete().eq("id", test_uuid).execute()
            print("[TEST SUCCESS] Successfully cleaned up dummy seller.")
        except Exception as insert_err:
            print(f"[TEST FAILED] Dummy seller insertion failed.")
            print(f"    Details: {insert_err}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
