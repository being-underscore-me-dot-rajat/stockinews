-- Run this in the Supabase SQL editor after creating your project.
-- Dashboard → SQL Editor → New query → paste and run.

-- Enable pgvector (needed for Phase 3 embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- ─── profiles ────────────────────────────────────────────────────────────────
-- Extends Supabase auth.users with app-specific fields (e.g. display name).
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_update_own" ON profiles FOR UPDATE USING (auth.uid() = id);

-- Auto-create a profile row whenever a new user signs up.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO profiles (id, name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'name');
    RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE handle_new_user();

-- ─── stocks (portfolio transaction log) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS stocks (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker      TEXT NOT NULL,
    quantity    INTEGER NOT NULL,
    price       REAL NOT NULL,
    action      TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE stocks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "stocks_own" ON stocks USING (auth.uid() = user_id);

-- ─── watchlist ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS watchlist (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker      TEXT NOT NULL,
    added_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, ticker)
);

ALTER TABLE watchlist ENABLE ROW LEVEL SECURITY;
CREATE POLICY "watchlist_own" ON watchlist USING (auth.uid() = user_id);

-- ─── article_chunks (Phase 3 — vector store) ─────────────────────────────────
CREATE TABLE IF NOT EXISTS article_chunks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id   UUID,
    tickers      TEXT[],
    sector       TEXT,
    source       TEXT,
    published_at TIMESTAMPTZ,
    url          TEXT,
    chunk_text   TEXT,
    embedding    VECTOR(1536),      -- adjust dim to match your embedding model
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS article_chunks_embedding_idx
    ON article_chunks USING hnsw (embedding vector_cosine_ops);

-- ─── RPC helpers (called by the FastAPI backend via supabase.rpc()) ───────────

-- Net portfolio per user: returns ticker, net_quantity, total_cost.
CREATE OR REPLACE FUNCTION get_user_portfolio(p_user_id UUID)
RETURNS TABLE(ticker TEXT, net_quantity BIGINT, total_cost DOUBLE PRECISION)
LANGUAGE sql STABLE AS $$
    SELECT
        ticker,
        SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END)  AS net_quantity,
        SUM(CASE WHEN action = 'BUY' THEN quantity * price  ELSE 0 END) AS total_cost
    FROM stocks
    WHERE user_id = p_user_id
    GROUP BY ticker
    HAVING SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) > 0;
$$;

-- Net quantity held for a single ticker (used to validate sell orders).
CREATE OR REPLACE FUNCTION get_ticker_quantity(p_user_id UUID, p_ticker TEXT)
RETURNS TABLE(quantity BIGINT)
LANGUAGE sql STABLE AS $$
    SELECT SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) AS quantity
    FROM stocks
    WHERE user_id = p_user_id AND ticker = p_ticker;
$$;
