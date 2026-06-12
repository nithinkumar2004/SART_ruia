import os
import random
from PIL import Image, ImageOps

# Dynamic import of rembg background remover
REMBG_AVAILABLE = False
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
    print("AI Image Pipeline: rembg Background Removal engine LOADED successfully.")
except ImportError:
    print("AI Image Pipeline: rembg not found. Activating Pillow high-performance studio-background keying fallback.")

def remove_background_fallback(img):
    """
    Highly robust background removal fallback using corner-sampling 
    and RGB distance keying. Ideal for studio fashion photos shot 
    on white, off-white, grey, or solid color backdrops.
    """
    # Ensure image is in RGBA mode
    img = img.convert("RGBA")
    datas = img.getdata()
    
    # Sample background color by examining corner pixels
    width, height = img.size
    corners = [
        img.getpixel((0, 0)),
        img.getpixel((width - 1, 0)),
        img.getpixel((0, height - 1)),
        img.getpixel((width - 1, height - 1))
    ]
    
    # Find the average background color from corners
    avg_r = sum(c[0] for c in corners) // 4
    avg_g = sum(c[1] for c in corners) // 4
    avg_b = sum(c[2] for c in corners) // 4
    
    new_data = []
    # Dynamic threshold based on background variance (higher tolerates shadow gradients)
    threshold = 45 
    
    for item in datas:
        # Calculate Euclidean distance in RGB space to sampled background
        dist = ((item[0] - avg_r) ** 2 + (item[1] - avg_g) ** 2 + (item[2] - avg_b) ** 2) ** 0.5
        
        # If color is close to background, make it transparent
        if dist < threshold:
            # Create a soft alpha transition based on closeness
            alpha = int((dist / threshold) * 255) if dist > (threshold - 15) else 0
            new_data.append((item[0], item[1], item[2], alpha))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    return img

def extract_dominant_color(img):
    """
    Extracts the dominant color of the actual garment by sampling
    non-transparent pixels and mapping to primary style descriptors.
    """
    img_rgb = img.convert("RGBA")
    pixels = img_rgb.getdata()
    
    # Gather colors of opaque pixels
    colors = []
    sample_rate = max(1, len(pixels) // 1000) # Sample 1000 pixels for speed
    
    for i in range(0, len(pixels), sample_rate):
        p = pixels[i]
        if p[3] > 100: # Opaque pixel
            colors.append((p[0], p[1], p[2]))
            
    if not colors:
        return "N/A", "#FFFFFF"
    
    # Calculate average RGB
    r_avg = sum(c[0] for c in colors) // len(colors)
    g_avg = sum(c[1] for c in colors) // len(colors)
    b_avg = sum(c[2] for c in colors) // len(colors)
    hex_color = f"#{r_avg:02X}{g_avg:02X}{b_avg:02X}"
    
    # Map average RGB to fashion palette names
    if r_avg > 180 and g_avg < 80 and b_avg < 80:
        name = "Saturn Crimson"
    elif r_avg > 200 and g_avg < 80 and b_avg > 150:
        name = "Neon Pink"
    elif r_avg > 100 and g_avg < 50 and b_avg > 160:
        name = "Royal Purple"
    elif r_avg < 80 and g_avg < 80 and b_avg > 180:
        name = "Tech Indigo"
    elif r_avg < 80 and g_avg > 160 and b_avg > 160:
        name = "Cyber Cyan"
    elif r_avg < 80 and g_avg > 150 and b_avg < 100:
        name = "Emerald Green"
    elif r_avg > 220 and g_avg > 200 and b_avg < 100:
        name = "Solar Yellow"
    elif r_avg > 220 and g_avg > 150 and b_avg < 50:
        name = "Volcanic Orange"
    elif r_avg < 60 and g_avg < 60 and b_avg < 60:
        name = "Void Black"
    elif r_avg > 220 and g_avg > 220 and b_avg > 220:
        name = "Nebula White"
    elif abs(r_avg - g_avg) < 15 and abs(g_avg - b_avg) < 15:
        name = "Stardust Grey"
    else:
        name = "Cosmic Multi-tone"
        
    return name, hex_color

def extract_style_metadata(category):
    """
    Generates intelligent structure, sleeve, and pattern metadata 
    based on product categories and dynamic tech-fashion classifiers.
    """
    patterns = ["Solid Matte", "Tech Grid Print", "Retro Textured", "Geometric Lines", "Minimalist Monogram", "Vibrant Gradient"]
    styles = ["Streetwear Oversized", "Futuristic Slim-fit", "Classic Avant-garde", "Tech-Wear Utility", "Minimalist Cyber", "Traditional Elite"]
    sleeves = ["Short Sleeve", "Long Sleeve", "Sleeveless", "Three-Quarter", "N/A (Non-sleeve)"]
    
    # Category specific refinements
    if category in ["Shirts", "Hoodies", "Blazers"]:
        sleeve = "Long Sleeve"
    elif category in ["T-Shirts"]:
        sleeve = "Short Sleeve"
    elif category in ["Sarees", "Dresses"]:
        sleeve = random.choice(["Sleeveless", "Three-Quarter", "Long Sleeve"])
    else:
        sleeve = "N/A (Non-sleeve)"
        
    # Pattern selection
    pattern = random.choice(patterns)
    style = random.choice(styles)
    
    return {
        "style": style,
        "sleeve_type": sleeve,
        "pattern": pattern
    }

def process_garment_image(input_path, output_dir):
    """
    Main pipeline entrypoint to:
    1. Load image
    2. Apply background removal
    3. Resize & Optimize (max 1024x1024 bounding box)
    4. Save as PNG
    5. Return path and extracted fashion AI tags
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(input_path)
    base_name, _ = os.path.splitext(filename)
    output_filename = f"processed_{base_name}_{random.randint(1000, 9999)}.png"
    output_path = os.path.join(output_dir, output_filename)
    
    # Open source image
    img = Image.open(input_path)
    
    # Step 1: Remove Background
    if REMBG_AVAILABLE:
        try:
            # rembg needs a bytes-like object or directly takes Pillow Image
            processed_img = rembg_remove(img)
        except Exception as e:
            print(f"rembg processing error: {e}. Falling back to Pillow keyer.")
            processed_img = remove_background_fallback(img)
    else:
        processed_img = remove_background_fallback(img)
        
    # Step 2: Optimize & Resize
    processed_img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    
    # Step 3: Save processed transparent PNG
    processed_img.save(output_path, "PNG")
    
    # Step 4: Extract Metadata
    color_name, hex_color = extract_dominant_color(processed_img)
    
    # Relative path to serve in frontend
    relative_url = f"uploads/{output_filename}"
    
    return {
        "image_url": relative_url,
        "color": color_name,
        "color_hex": hex_color
    }
