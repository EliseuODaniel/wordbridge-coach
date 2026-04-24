-- Initialize WordBridge Coach database
-- This script runs before Alembic migrations on a fresh PostgreSQL volume.

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Table schema and indexes are owned by Alembic migrations.
-- Keeping init.sql table-agnostic allows first boot to succeed on an empty volume.

-- Set up proper permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ftw_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ftw_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'WordBridge Coach database initialized successfully';
END $$;
