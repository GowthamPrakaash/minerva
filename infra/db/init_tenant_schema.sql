-- init_tenant_schema.sql
--
-- Purpose:
--     Definition of tables that exist within EACH tenant schema (tenant_<slug>).
--     These tables are created dynamically for each new business.
--
-- Implementation:
--     The dashboard (or internal service) should execute these commands 
--     after running 'CREATE SCHEMA tenant_<slug>;' and 'SET search_path TO tenant_<slug>;'
--


-- 1. In-Tenant Configurations
CREATE TABLE IF NOT EXISTS configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_key TEXT NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    description TEXT,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 2. API Keys (Moved to tenant schema for isolation)
-- Note: business_id is omitted here as the schema itself dictates the ownership.
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key TEXT UNIQUE NOT NULL,
    api_secret_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    
    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 3. Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL, -- pdf, docx, txt, etc.
    storage_path TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    chunk_count INTEGER,
    embedding_model TEXT,
    
    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 4. Ingestion Jobs
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_ids UUID[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'initiated', -- initiated, in_progress, success, failed
    error_message TEXT,
    chunks_processed INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 5. Sessions (Conversations)
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel TEXT NOT NULL, -- web, whatsapp, phone
    user_identifier TEXT,
    language TEXT,
    status TEXT DEFAULT 'active', -- active, ended, abandoned
    conversation_summary TEXT,
    audio_s3_path TEXT,
    goal_state_json JSONB,
    last_activity TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 6. Messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    audio_s3_path TEXT,
    is_unknown BOOLEAN DEFAULT false,
    rag_context JSONB,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);
-- 7. Usage Records
CREATE TABLE IF NOT EXISTS usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    metrics JSONB,
    latency_ms JSONB,
    cost_estimate FLOAT,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 8. Unknown Queries
CREATE TABLE IF NOT EXISTS unknown_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    resolved BOOLEAN DEFAULT false,
    resolved_by UUID, -- FK to public.users.id (not strictly enforced by FK across schemas in some setups, but logical)

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 9. Feedback
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,

    -- Audit columns
    created_by UUID,
    created_on TIMESTAMPTZ DEFAULT now(),
    last_updated_by UUID,
    last_updated_on TIMESTAMPTZ DEFAULT now()
);

-- 10. Key Indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_identifier ON sessions(user_identifier);
CREATE INDEX IF NOT EXISTS idx_sessions_created_on ON sessions(created_on);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_on ON messages(created_on);
CREATE INDEX IF NOT EXISTS idx_api_keys_api_key ON api_keys(api_key);
