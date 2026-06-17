-- Run in Supabase SQL Editor (Dashboard → SQL Editor → New query).
-- Adds the vector similarity search function used by the Phase 4 RAG agent.

CREATE OR REPLACE FUNCTION match_article_chunks(
    query_embedding vector(1536),
    match_count     int          DEFAULT 5,
    filter_ticker   text         DEFAULT NULL,
    min_similarity  float        DEFAULT 0.3
)
RETURNS TABLE (
    id           uuid,
    article_id   uuid,
    chunk_text   text,
    url          text,
    source       text,
    published_at timestamptz,
    tickers      text[],
    similarity   float
)
LANGUAGE sql STABLE AS $$
    SELECT
        id,
        article_id,
        chunk_text,
        url,
        source,
        published_at,
        tickers,
        1 - (embedding <=> query_embedding) AS similarity
    FROM article_chunks
    WHERE
        (filter_ticker IS NULL OR filter_ticker = ANY(tickers))
        AND 1 - (embedding <=> query_embedding) >= min_similarity
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
