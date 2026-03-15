-- init_schema.sql
--
-- Purpose:
--     Initialises the public schema with global tables (organizations, businesses, users,
--     system_settings). Run once during initial setup.
--
-- Usage:
--     psql -h <host> -U <user> -d minerva -f init_schema.sql
--

-- Enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 1. Organizations (Top-level billing entities)
CREATE TABLE IF NOT EXISTS public.organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 2. Businesses (Tenants within an organization)
CREATE TABLE IF NOT EXISTS public.businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    schema_name TEXT NOT NULL UNIQUE,
    industry TEXT,
    allowed_domains JSONB DEFAULT '[]'::jsonb,
    allowed_ips JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT true,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 3. Users
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT DEFAULT 'viewer', -- org_admin | business_admin | viewer
    org_id UUID REFERENCES public.organizations(id),
    is_active BOOLEAN DEFAULT true,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 4. User Access (Join table for business-level roles)
CREATE TABLE IF NOT EXISTS public.user_access (
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    business_id UUID NOT NULL REFERENCES public.businesses(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, business_id)
);

-- 5. System Settings
CREATE TABLE IF NOT EXISTS public.system_settings (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);
-- 6. Key Indexes
CREATE INDEX IF NOT EXISTS idx_businesses_org_id ON public.businesses(org_id);
CREATE INDEX IF NOT EXISTS idx_businesses_slug ON public.businesses(slug);
