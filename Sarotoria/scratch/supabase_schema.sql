-- =========================================================================
-- SARTORIA + SATURN NEXUS: UNIFIED SUPABASE POSTGRESQL SCHEMA
-- =========================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. DROP EXISTING TABLES IN DEPENDENCY ORDER TO PREVENT CONFLICTS
DROP TABLE IF EXISTS public.orders CASCADE;
DROP TABLE IF EXISTS public.wishlist CASCADE;
DROP TABLE IF EXISTS public.outfit_history CASCADE;
DROP TABLE IF EXISTS public.tryons CASCADE;
DROP TABLE IF EXISTS public.wardrobes CASCADE;
DROP TABLE IF EXISTS public.qr_scans CASCADE;
DROP TABLE IF EXISTS public.garments CASCADE;
DROP TABLE IF EXISTS public.sellers CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;

-- 2. CREATE PROFILES TABLE (Sarotoria Customers)
-- References auth.users(id) representing the main authenticated customer identity
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    gender TEXT,
    age INTEGER,
    height NUMERIC,
    weight NUMERIC,
    skin_tone TEXT,
    body_type TEXT,
    fashion_preferences TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. CREATE SELLERS TABLE (Sartoria Nexus)
-- References auth.users(id) for auth matching, with business metadata
CREATE TABLE public.sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE,
    phone TEXT UNIQUE,
    business_name TEXT, -- Nullable during initial signup stages
    business_type TEXT,
    inventory_source TEXT,
    website_url TEXT,
    gst_id TEXT,
    logo_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. CREATE GARMENTS TABLE (Shared Catalog)
-- References public.sellers(id) with strict UUID matching
CREATE TABLE public.garments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seller_id UUID REFERENCES public.sellers(id) ON DELETE CASCADE,
    garment_name TEXT NOT NULL,
    category TEXT,
    image_url TEXT,
    qr_url TEXT,
    qr_image TEXT,
    color TEXT,
    style TEXT,
    sleeve_type TEXT,
    pattern TEXT,
    price NUMERIC,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. CREATE QR SCANS TABLE (Shared Analytics)
CREATE TABLE public.qr_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    garment_id UUID REFERENCES public.garments(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    scanned_at TIMESTAMPTZ DEFAULT NOW(),
    device_type TEXT DEFAULT 'Mobile',
    country TEXT DEFAULT 'Unknown',
    ip_address TEXT DEFAULT '127.0.0.1'
);

-- 6. CREATE WARDROBES TABLE (Sarotoria)
CREATE TABLE public.wardrobes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    garment_id UUID REFERENCES public.garments(id) ON DELETE CASCADE,
    folder_category TEXT DEFAULT 'Casual',
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, garment_id)
);

-- 7. CREATE TRYONS TABLE (Sarotoria)
CREATE TABLE public.tryons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    garment_id UUID REFERENCES public.garments(id) ON DELETE CASCADE,
    original_image TEXT,
    output_image TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. CREATE OUTFIT HISTORY TABLE (Sarotoria)
CREATE TABLE public.outfit_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    occasion TEXT NOT NULL,
    prompt TEXT,
    generated_result JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. CREATE WISHLIST TABLE (Highly Recommended for Sarotoria)
CREATE TABLE public.wishlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    garment_id UUID REFERENCES public.garments(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, garment_id)
);

-- 10. CREATE ORDERS TABLE (Sarotoria)
CREATE TABLE public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    garment_id UUID REFERENCES public.garments(id) ON DELETE SET NULL,
    amount NUMERIC,
    status TEXT DEFAULT 'pending',
    payment_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =========================================================================
-- STORAGE BUCKETS CONFIGURATION (REFERENCE GUIDE FOR SUPABASE DASHBOARD)
-- =========================================================================
-- Note: Execute these in your Supabase dashboard or via API
-- Buckets to create manually in Supabase Storage:
-- 1. 'avatars'      (Public: true)
-- 2. 'garments'     (Public: true)
-- 3. 'tryons'       (Public: true)
-- 4. 'qr-codes'     (Public: true)
-- 5. 'seller-logos' (Public: true)

-- =========================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =========================================================================

-- Enable RLS on core tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sellers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.garments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wardrobes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tryons ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.wishlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;

-- 1. Profiles Policies
CREATE POLICY "Allow public read on profiles" 
ON public.profiles FOR SELECT USING (true);

CREATE POLICY "Allow users to update their own profile" 
ON public.profiles FOR ALL USING (auth.uid() = id);

-- 2. Sellers Policies
CREATE POLICY "Allow public read on sellers" 
ON public.sellers FOR SELECT USING (true);

CREATE POLICY "Allow sellers to manage their own business settings" 
ON public.sellers FOR ALL USING (auth.uid() = auth_user_id);

-- 3. Garments Policies
CREATE POLICY "Allow public read access on garments catalog" 
ON public.garments FOR SELECT USING (true);

CREATE POLICY "Allow sellers to manage their own garments" 
ON public.garments FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.sellers 
        WHERE public.sellers.id = public.garments.seller_id 
        AND public.sellers.auth_user_id = auth.uid()
    )
);

-- 4. Wardrobe Policies
CREATE POLICY "Allow customers to manage their own wardrobe" 
ON public.wardrobes FOR ALL USING (auth.uid() = user_id);

-- 5. Tryon Policies
CREATE POLICY "Allow customers to manage their own try-ons" 
ON public.tryons FOR ALL USING (auth.uid() = user_id);

-- 6. Wishlist Policies
CREATE POLICY "Allow customers to manage their own wishlist" 
ON public.wishlist FOR ALL USING (auth.uid() = user_id);

-- 7. Orders Policies
CREATE POLICY "Allow customers to view their own orders" 
ON public.orders FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Allow customers to insert their orders" 
ON public.orders FOR INSERT WITH CHECK (auth.uid() = user_id);

-- =========================================================================
-- AUTOMATED USER ONBOARDING TRIGGER (SUPABASE AUTH INTEGRATION)
-- =========================================================================

-- Automatically creates a public profile row whenever a new Auth User signs up
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        new.id,
        new.email,
        COALESCE(new.raw_user_meta_data->>'full_name', 'Sartoria User'),
        new.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger activation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();
