# Saturn Nexus QR — Digital Fashion Identity SaaS Platform

**Saturn Nexus QR** is a Flask-based SaaS platform enabling boutiques, luxury fashion houses, and garment sellers to upload catalog photos and automatically generate customized QR code tags. These smart tags serve as a physical-to-digital gateway, linking clothes directly to interactive netlify-based virtual try-on experiences.

---

## 🚀 Instant Out-Of-The-Box Startup

To ensure a frictionless setup, the platform includes a **dual-driver database and authentication pipeline**:
- **Local Mode (Default):** If no `.env` credentials are found, the app automatically initializes a local SQLite database (`saturn_nexus.db`) and uses a secure local session-based authentication system. All folders for logos, uploads, and QR assets are built dynamically.
- **Supabase Cloud Mode:** Populating your cloud credentials in a `.env` file automatically upgrades the platform to query Supabase Auth, PostgreSQL tables, and Cloud Storage.

### 1. Installation

Install all required Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Platform
Start the local Flask development server:
```bash
python run.py
```
Open your browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## 🛠️ Production Cloud Setup (Supabase)

When you are ready to transition your MVP to the production database and auth servers on Supabase:

1. Create a **Supabase Project** (https://supabase.com).
2. Navigate to your Supabase SQL Editor and run the database schemas located in your concept document (or the `db_helper.py` schema annotations).
3. Create a `.env` file in the root directory of this workspace and supply your project keys:
   ```env
   SECRET_KEY=generate_your_custom_flask_session_secret
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-supabase-service-role-or-anon-key
   ```
4. Restart your Flask server. The application will instantly switch to Supabase Mode!

---

## 📐 Platform Core Architecture

### AI Image Optimization Pipeline
- **Smart Isolation:** Tries to use deep-learning packages like `rembg` for high-fidelity edge removal. If your local machine lacks GPU or C++ runtime compilers, the code seamlessly falls back to a **high-precision studio corner-sampling filter** that isolates the garment from light/contrast backdrops, saving it as a clean alpha-transparent PNG.
- **Dimensional Standardizer:** Bounds the canvas to a maximum of `1024x1024` with high-performance Lanczos interpolation.
- **Heuristic Classifier:** Scans opaque pixel channels to identify dominant hex palettes (e.g. *Saturn Crimson*, *Tech Indigo*) and automatically applies style patterns (e.g. *Tech Grid Print*, *Geometric Lines*).

### QR Redirection & Scanning Gateway
To capture real-time scan analytics, the generated QR codes point dynamically to:
```text
http://localhost:5000/qr/scan/<garment_id>
```
When scanned:
1. **Analytics Gate:** Logs the scanner's approximate location (e.g. *Paris, France*, *Milan, Italy*), device profile type (Mobile, Desktop, Tablet), IP address, and timestamp.
2. **Redirection Gate:** Instantly forwards the visitor to the Netlify destination:
   👉 `https://saturnnetworks.netlify.app/?garment_id=<garment_id>` (allowing the virtual try-on page to instantly fetch and adapt to the exact scanned garment!).
