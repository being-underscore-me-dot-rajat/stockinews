-- Run in Supabase SQL Editor after 001_initial_schema.sql
-- Phase 3: tracks which URLs have already been ingested to avoid reprocessing.

CREATE TABLE IF NOT EXISTS crawled_urls (
    id          BIGSERIAL PRIMARY KEY,
    url_hash    TEXT UNIQUE NOT NULL,
    url         TEXT NOT NULL,
    crawled_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS crawled_urls_hash_idx ON crawled_urls (url_hash);
