-- Initialize FillTheWord database
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we add some basic ones here

-- Index for language codes
CREATE INDEX IF NOT EXISTS idx_language_code ON language(code);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);

-- Index for card queries
CREATE INDEX IF NOT EXISTS idx_card_is_active ON card(is_active);

-- Index for user card state queries (critical for SM-2 performance)
CREATE INDEX IF NOT EXISTS idx_user_card_state_user_id ON user_card_state(user_id);
CREATE INDEX IF NOT EXISTS idx_user_card_state_next_review ON user_card_state(next_review_at);
CREATE INDEX IF NOT EXISTS idx_user_card_state_status ON user_card_state(status);

-- Index for review events
CREATE INDEX IF NOT EXISTS idx_review_event_user_id ON review_event(user_id);
CREATE INDEX IF NOT EXISTS idx_review_event_card_id ON review_event(card_id);

-- Full-text search index for words and sentences
CREATE INDEX IF NOT EXISTS idx_word_text_fts ON word USING gin(to_tsvector('english', text));
CREATE INDEX IF NOT EXISTS idx_sentence_text_fts ON sentence USING gin(to_tsvector('english', text));

-- Set up proper permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ftw_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ftw_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'FillTheWord database initialized successfully';
END $$;
