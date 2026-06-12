import json
from app.config import Config

# Initialize genai client conditionally if key exists
gemini_available = False
if Config.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # We use the fast and highly capable gemini-1.5-flash model
        model = genai.GenerativeModel('gemini-1.5-flash')
        gemini_available = True
        print("Google Gemini API successfully configured.")
    except Exception as e:
        print(f"Failed to configure Google Gemini API: {e}. Running in Simulated Advisor Mode.")
        gemini_available = False

class GeminiStylistClient:
    
    @staticmethod
    def get_outfit_recommendations(occasion, weather_temp, body_type, wardrobe_list=None):
        """
        Submits structured parameters to Gemini for occasion-aware recommendations.
        Returns a structured dictionary with outfit selection and tips.
        """
        wardrobe_list = wardrobe_list or []
        wardrobe_desc = ""
        if wardrobe_list:
            wardrobe_desc = "\n".join([
                f"- {item.get('garments', {}).get('garment_name', 'Unknown Garment')} ({item.get('garments', {}).get('category', 'Category')})"
                for item in wardrobe_list if item.get('garments')
            ])
        else:
            wardrobe_desc = "Customer's digital wardrobe is currently empty. Suggest looks from a standard fashionable catalog."

        prompt = f"""
You are "Sartoria AI" — a world-class fashion architect and personal stylist.
We need a custom styling plan for a customer under the following specifications:
- Occasion: {occasion}
- Weather/Temperature: {weather_temp}°C
- Body Type: {body_type}
- Current Wardrobe Items Available:
{wardrobe_desc}

Generate a premium, detailed styling guide in valid JSON format. Do not wrap it in anything other than markdown json codeblock.
The JSON must contain precisely these fields:
1. "recommended_outfit": A detailed description of the main outfit combination (e.g., blazer, shirt, trousers).
2. "matching_colors": A list of highly coordinated matching colors (with hex codes) suited for their skin tone and style.
3. "styling_tips": A list of 3 specific and highly actionable styling recommendations for this occasion and body type.
4. "alternative_look": A description of an alternative styling option if the primary is not preferred.
5. "confidence_score": An integer between 1 and 100 representing the styling compatibility match score.
"""
        
        if gemini_available:
            try:
                response = model.generate_content(prompt)
                text = response.text.strip()
                # Parse markdown codeblock if present
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                return json.loads(text)
            except Exception as e:
                print(f"Gemini API request failed: {e}. Falling back to high-end simulation.")
                # Fall back to simulation if API key limit hit or network fails
        
        # Premium Simulator Fallback
        return GeminiStylistClient._generate_simulated_recommendation(occasion, weather_temp, body_type)

    @staticmethod
    def chat_stylist(message, history=None):
        """
        Interactive conversational chatbot powered by Gemini.
        """
        history = history or []
        
        # Build prompt context
        context = "You are 'Sartoria AI' — a highly charismatic, professional, and knowledgeable digital fashion stylist assistant. You help customers design outfits, choose styles, predict sizing, and organize wardrobes. Be concise, highly professional, polite, and premium in your tone. Keep answers under 3 short paragraphs.\n\n"
        
        for h in history:
            role = "Customer" if h.get("is_user") else "Sartoria AI"
            context += f"{role}: {h.get('text')}\n"
        
        context += f"Customer: {message}\n"
        context += "Sartoria AI:"

        if gemini_available:
            try:
                response = model.generate_content(context)
                return response.text.strip()
            except Exception as e:
                print(f"Gemini chat failed: {e}. Falling back to simulation.")
        
        return GeminiStylistClient._generate_simulated_chat(message, occasion_detected=message.lower())

    @staticmethod
    def _generate_simulated_recommendation(occasion, weather_temp, body_type):
        """Generates premium simulated recommendations as a fallback."""
        occasion = occasion.lower()
        if "office" in occasion or "meeting" in occasion or "work" in occasion:
            return {
                "recommended_outfit": "A tailored unstructured Navy Blazer paired with a crisp Linen White Dress Shirt and Camel Chino Trousers. Complete the look with tan leather double-strap monks.",
                "matching_colors": ["#1d3864 (Midnight Navy)", "#ffffff (Pure White)", "#c2b280 (Camel Sand)", "#8b5a2b (Tan Leather)"],
                "styling_tips": [
                    "For an athletic body type, select an unstructured blazer to show off natural shoulders without looking bulky.",
                    "Linen shirts keep you cool in 30°C weather while keeping an elevated styling silhouette.",
                    "Ensure trouser cuffs hit right at the ankle (no break) for a clean modern style."
                ],
                "alternative_look": "A premium knitted polo shirt in Steel Grey tucked into Charcoal pleated wool trousers, paired with leather loafers.",
                "confidence_score": 95
            }
        elif "wedding" in occasion or "party" in occasion or "formal" in occasion:
            return {
                "recommended_outfit": "A premium Royal Velvet Tuxedo jacket with satin silk lapels, styled with a pleated white formal shirt, black silk bow tie, and patent leather oxford lace-ups.",
                "matching_colors": ["#4a0e2e (Royal Velvet Burgundy)", "#000000 (Satin Black)", "#ffffff (Crisp White)", "#d4af37 (Glint Gold)"],
                "styling_tips": [
                    "Pair dark velvet colors with deep metallic or gold accents for maximum premium contrast.",
                    "Ensure the tuxedo sleeves allow 1/2 inch of shirt cuffs to show for standard elegance.",
                    "A silk pocket square matching your bowtie elevates formal wedding wear seamlessly."
                ],
                "alternative_look": "A modern bespoke Bandhgala or Nehru jacket in rich Indigo brocade with ivory churidar pants.",
                "confidence_score": 92
            }
        else:
            # Default premium look
            return {
                "recommended_outfit": "An elevated Cyber Pink bomber jacket layered over a luxury heavyweight off-white cotton t-shirt and light wash Japanese selvedge denim jeans. Finish with clean minimalist white leather sneakers.",
                "matching_colors": ["#FF2EBE (Cyber Pink)", "#FAF9F6 (Off-White)", "#00D4FF (Aqua Accents)", "#E5E7EB (Soft Gray)"],
                "styling_tips": [
                    "Keep casual layering lightweight for hot weather by utilizing open breathable weave fabrics.",
                    "Choose tapered-fit denim to create a balanced length and sophisticated visual proportion.",
                    "Minimalist white sneakers are highly versatile and complete high-low combinations perfectly."
                ],
                "alternative_look": "A pastel linen button-down shirt paired with tailored drawstring shorts and leather slide sandals.",
                "confidence_score": 88
            }

    @staticmethod
    def _generate_simulated_chat(message, occasion_detected=""):
        """Generates premium simulated conversational answers."""
        msg = message.lower()
        if "size" in msg or "fit" in msg:
            return "Based on your onboarding metrics (height, weight, body type), our **AI Size Selector** runs real-time coordinate fits. I recommend selecting your suggested size on the Garment Details page, which typically boasts a **92% size confidence score** based on brand specifications!"
        elif "wardrobe" in msg or "save" in msg:
            return "You can easily categorize and organize your fashion items into dedicated Occasion Folders (like **Casual, Office, Travel, Wedding, Party**) in your **AI Wardrobe**! Simply scan a garment tag or click 'Save to Wardrobe' to catalog a look."
        elif "try" in msg or "avatar" in msg:
            return "Our **AI Virtual Try-On** allows you to upload a front-facing selfie or choose from our beautiful model avatars. We'll instantly blend the garment texture onto your avatar for a digital fitting. Try it out on any garment catalog item!"
        else:
            return "Hello! I am **Sartoria AI**, your personal fashion advisor. I can help you select outfits for meetings, plan travel styling wardrobes, suggest color coordinate matches, or guide you through virtual fittings. What fashion styling can I help you create today?"
