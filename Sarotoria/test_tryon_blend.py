import os
import sys

# Ensure Sarotoria path is active
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.utils.db_client import DatabaseHelper
from app.utils.tryon_service import TryOnService

def main():
    print("=" * 60)
    print("SAROTORIA CONSUMER PLATFORM — VISUAL COMPOSITE DIAGNOSTIC")
    print("=" * 60)
    
    # 1. Fetch catalog garments
    garments = DatabaseHelper.get_all_garments(limit=1)
    if not garments:
        print("[WARNING] No garments found in database catalog. Please make sure Sartoria Nexus has garments uploaded.")
        return
        
    target_garment = garments[0]
    garment_id = target_garment['id']
    garment_name = target_garment['garment_name']
    category = target_garment['category']
    print(f"Target Garment: {garment_name} (Category: {category}, ID: {garment_id})")
    
    # 2. Run tryon compositor
    try:
        print("\nRunning visual tryon composite blend...")
        res = TryOnService.generate_tryon(
            user_id="diagnostic_tester",
            garment_id=garment_id,
            avatar_id="model_male_1"
        )
        print("[SUCCESS] Visual tryon composite completed!")
        print(f"Result details: {res}")
        
        # Verify output exists
        local_output_path = os.path.join("app", res['tryon_image_url'].lstrip("/"))
        if os.path.exists(local_output_path):
            print(f"[OK] Physical file output successfully saved at: {local_output_path} ({os.path.getsize(local_output_path)} bytes)")
        else:
            print(f"[FAILED] Physical file output not found at: {local_output_path}")
            
    except Exception as e:
        print(f"[ERROR] Try-on visual composite failed: {e}")
        
    print("=" * 60)

if __name__ == "__main__":
    main()
