# Development.md — Saturn Garment QR Converter Platform

> Brand Theme Palette
> Primary Gradient System:

* `#F44336` — Saturn Red
* `#E91E63` — Neon Pink
* `#9C27B0` — Royal Purple
* `#673AB7` — Deep Violet
* `#3F51B5` — Tech Indigo

---

# 1. Project Overview

## Product Name

**Saturn Nexus QR**

## Core Idea

A Flask-based SaaS web platform where fashion brands, boutiques, and garment sellers upload garment images and automatically generate QR codes linked to a virtual fashion experience.

When a garment QR code is scanned:

* It redirects users to:

  `https://saturnnetworks.netlify.app/`

* The QR code acts as a digital identity for the garment.

* Future-ready architecture for AI try-on integration.

---

# 2. Primary Features

## Authentication System

### User Signup/Login

Support:

* Email + Password
* Phone Number + OTP

Using:

* Supabase Auth

---

# 3. Seller Registration Flow

## Registration Page Fields

### Business Profile

| Field                 | Type         |
| --------------------- | ------------ |
| Brand/Boutique Name   | Text         |
| Primary Contact Email | Email        |
| Phone Number          | Phone        |
| Business Type         | Dropdown     |
| Business Logo         | Image Upload |
| Website URL           | Optional     |
| GST/Business ID       | Optional     |

---

## Business Type Options

* Boutique
* Fashion Brand
* Garment Seller
* Textile Manufacturer
* Reseller
* Designer Studio
* Clothing Startup

---

# 4. Operational Details

## Inventory Source

Options:

* Mobile Device Uploads
* DSLR/Professional Catalog
* Warehouse Bulk Upload
* API Integration

---

## Product Categories

Multi-select:

* Shirts
* T-Shirts
* Jeans
* Sarees
* Dresses
* Hoodies
* Blazers
* Ethnic Wear
* Kids Wear
* Shoes
* Accessories

---

# 5. QR Workflow Architecture

## Upload Flow

```text
Seller Uploads Garment Image
        ↓
Flask Backend Receives Image
        ↓
AI Processing Layer
- Remove Background
- Resize
- Optimize
- Metadata Extraction
        ↓
Save Garment Data in Supabase
        ↓
Generate Unique QR Code
        ↓
QR Encodes:
https://saturnnetworks.netlify.app/
        ↓
Store QR Code in Database
        ↓
Display QR to Seller
```

---

# 6. System Architecture

```text
Frontend (Flask + Jinja)
        ↓
Flask API Layer
        ↓
Supabase Backend
 ├── Authentication
 ├── PostgreSQL Database
 ├── Storage Bucket
 └── Realtime
        ↓
AI Processing Services
        ↓
QR Generator Engine
```

---

# 7. Tech Stack

## Frontend

| Technology         | Purpose           |
| ------------------ | ----------------- |
| Flask              | Backend Rendering |
| Jinja2             | Templates         |
| Bootstrap/Tailwind | UI                |
| Alpine.js          | Interactivity     |

---

## Backend

| Technology | Purpose           |
| ---------- | ----------------- |
| Flask      | Core API          |
| Supabase   | Database/Auth     |
| PostgreSQL | Data Storage      |
| Gunicorn   | Production Server |

---

## AI/Image Processing

| Tool      | Purpose             |
| --------- | ------------------- |
| rembg     | Background Removal  |
| Pillow    | Image Optimization  |
| OpenCV    | Computer Vision     |
| CLIP/BLIP | Metadata Extraction |

---

## QR Code System

| Tool   | Purpose       |
| ------ | ------------- |
| qrcode | QR Generation |
| Pillow | QR Rendering  |

---

# 8. Recommended Folder Structure

```text
saturn_qr/
│
├── app/
│   ├── auth/
│   ├── dashboard/
│   ├── garments/
│   ├── qr/
│   ├── ai/
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── uploads/
│   │   └── qr/
│   ├── utils/
│   └── config.py
│
├── migrations/
├── requirements.txt
├── run.py
└── README.md
```

---

# 9. Supabase Database Design

## Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    business_name TEXT,
    business_type TEXT,
    inventory_source TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Garments Table

```sql
CREATE TABLE garments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    garment_name TEXT,
    category TEXT,
    image_url TEXT,
    qr_url TEXT,
    qr_image TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## QR Analytics Table

```sql
CREATE TABLE qr_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    garment_id UUID REFERENCES garments(id),
    scanned_at TIMESTAMP DEFAULT NOW(),
    device_type TEXT,
    country TEXT,
    ip_address TEXT
);
```

---

# 10. QR Code Generation Logic

## QR Payload

```python
QR_REDIRECT_URL = "https://saturnnetworks.netlify.app/"
```

---

## QR Generator

```python
import qrcode

def generate_qr():
    qr = qrcode.make("https://saturnnetworks.netlify.app/")
    qr.save("static/qr/garment_qr.png")
```

---

# 11. Flask API Endpoints

## Auth

```python
POST /signup
POST /login
POST /logout
POST /verify-otp
```

---

## Garments

```python
POST /upload-garment
GET /garments
GET /garment/<id>
DELETE /garment/<id>
```

---

## QR

```python
GET /generate-qr/<id>
GET /download-qr/<id>
GET /scan-analytics/<id>
```

---

# 12. AI Image Pipeline

## Processing Steps

### Step 1 — Upload

Accept:

* PNG
* JPG
* WEBP

---

### Step 2 — Background Removal

```python
from rembg import remove
```

---

### Step 3 — Resize

```python
img.thumbnail((1024, 1024))
```

---

### Step 4 — AI Metadata Extraction

Generate:

* Color
* Style
* Garment Type
* Sleeve Type
* Pattern

---

# 13. Dashboard Modules

## Seller Dashboard

Features:

* Total Garments
* QR Scan Count
* Most Viewed Products
* Upload History
* Analytics Graphs

---

# 14. UI/UX Design System

## Theme Style

Modern futuristic fashion-tech design.

---

## Background Gradient

```css
background: linear-gradient(
    135deg,
    #F44336,
    #E91E63,
    #9C27B0,
    #673AB7,
    #3F51B5
);
```

---

## Font Suggestions

* Poppins
* Inter
* Space Grotesk

---

## UI Components

* Glassmorphism cards
* Neon borders
* Soft shadows
* Animated hover effects
* Gradient buttons

---

# 15. Pages Required

| Page              | Purpose          |
| ----------------- | ---------------- |
| Landing Page      | Product showcase |
| Signup Page       | User onboarding  |
| Login Page        | Authentication   |
| Registration Page | Business details |
| Dashboard         | Analytics        |
| Upload Garment    | Add garments     |
| QR Management     | Manage QR codes  |
| Analytics         | Scan tracking    |

---

# 16. Security Implementation

## Required

* JWT Authentication
* Rate Limiting
* CSRF Protection
* Secure File Uploads
* File Validation
* HTTPS Only

---

## File Upload Validation

```python
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}
```

---

# 17. Deployment Architecture

## Frontend + Flask

Deploy:

* Render
* Railway
* DigitalOcean

---

## Supabase

Use for:

* PostgreSQL
* Auth
* Storage

---

# 18. Storage Structure

## Supabase Buckets

```text
garments/
qr-codes/
business-logos/
processed-images/
```

---

# 19. Future AI Features

## Phase 2

* AI Virtual Try-On
* AI Fashion Recommendations
* AI Auto-Tagging
* Smart Wardrobe
* AI Outfit Matching

---

# 20. Development Roadmap

## Phase 1 — MVP

Duration: 2 Weeks

### Build:

* Authentication
* Registration
* Upload System
* QR Generator
* Supabase Integration

---

## Phase 2 — AI Layer

Duration: 3 Weeks

### Build:

* Background Removal
* Metadata Extraction
* AI Classification

---

## Phase 3 — Analytics

Duration: 1 Week

### Build:

* QR Tracking
* Dashboard
* Scan Reports

---

# 21. Recommended Flask Extensions

```text
Flask-Login
Flask-WTF
Flask-Migrate
Flask-SQLAlchemy
Flask-Limiter
Flask-Mail
python-dotenv
supabase-py
```

---

# 22. Performance Optimization

## Important

* Compress uploads before storage
* Cache generated QR codes
* Use CDN for images
* Lazy load dashboard assets
* Async image processing queue

---

# 23. Scalability Strategy

## Recommended Later

* Convert Flask monolith into microservices
* Add Celery + Redis
* Move AI processing to FastAPI workers
* Use Cloudflare CDN

---

# 24. Critical Architecture Advice

## Do NOT:

* Store images locally in production
* Process heavy AI tasks synchronously
* Expose Supabase keys in frontend
* Allow unrestricted uploads

---

# 25. Recommended MVP Flow

```text
User Signup
    ↓
Business Registration
    ↓
Dashboard Access
    ↓
Upload Garment
    ↓
Generate QR
    ↓
Download QR
    ↓
Print QR on Garment Tag
    ↓
Customer Scans QR
    ↓
Redirect to Saturn Experience
```

---

# 26. Suggested Brand Positioning

## Tagline Ideas

* “Digitizing Fashion Identity”
* “Scan Fashion. Experience Virtually.”
* “AI-Powered Garment Intelligence”
* “From Fabric to Digital Experience”

---

# 27. Suggested Database Scaling

## Later Add:

* Multi-tenant architecture
* Subscription billing
* Team management
* Role-based access
* API access for brands

---

# 28. Suggested API Security

## Add:

```text
JWT Refresh Tokens
Email Verification
Phone OTP Expiry
Request Throttling
Signed Upload URLs
```

---

# 29. Final Recommendation

For long-term scalability:

### Better Architecture Eventually

```text
Frontend → Next.js
Backend → FastAPI
AI Workers → Python Microservices
Database → Supabase PostgreSQL
Storage → Cloudflare R2
```

But for MVP:

```text
Flask + Supabase
```

is the correct decision because:

* Faster iteration
* Simpler deployment
* Easier debugging
* Lower infrastructure cost

---

Based on your uploaded concept document: 
