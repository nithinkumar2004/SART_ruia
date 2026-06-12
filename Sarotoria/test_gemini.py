import os
import sys

# Ensure Sarotoria path is active
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.utils.gemini_client import GeminiStylistClient, Config, gemini_available

def main():
    print("=" * 60)
    print("SAROTORIA CONSUMER PLATFORM — GEMINI AI INTEGRATION DIAGNOSTIC")
    print("=" * 60)
    
    print(f"Gemini Key loaded: {'***' + Config.GEMINI_API_KEY[-8:] if Config.GEMINI_API_KEY else 'None'}")
    print(f"GenAI engine available: {gemini_available}")
    
    # Test conversational stylist chat query
    print("\nTesting conversational styling chatbot advisor...")
    try:
        response = GeminiStylistClient.chat_stylist(
            message="Suggest a smart casual look for a dinner meeting, weather is cool.",
            history=[]
        )
        print("[SUCCESS] Gemini Stylist responded:")
        print("-" * 50)
        print(response)
        print("-" * 50)
    except Exception as e:
        print(f"[FAILED] Gemini chat test failed: {e}")

    # Test structured Dress Selector recommendations
    print("\nTesting structured AI Dress Selector recommendations...")
    try:
        rec = GeminiStylistClient.get_outfit_recommendations(
            occasion="Office Meeting",
            weather_temp=22,
            body_type="Athletic"
        )
        print("[SUCCESS] Structured Dress recommendations generated:")
        print(f"    - Outfit: {rec.get('recommended_outfit')}")
        print(f"    - Colors: {rec.get('matching_colors')}")
        print(f"    - Tips: {rec.get('styling_tips')}")
        print(f"    - Confidence: {rec.get('confidence_score')}%")
    except Exception as e:
        print(f"[FAILED] Dress Selector recommendation failed: {e}")
        
    print("=" * 60)

if __name__ == "__main__":
    main()
