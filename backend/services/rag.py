"""Phase 4 — RAG retrieval: embed query → pgvector cosine similarity search."""
import gc
import logging
from datetime import datetime, timedelta, timezone

from services.supabase_client import supabase_admin

log = logging.getLogger(__name__)


def search_chunks(
    query: str,
    ticker: str | None = None,
    limit: int = 5,
    min_similarity: float = 0.3,
    max_age_days: int | None = 30,
) -> list[dict]:
    """
    Return top-k article chunks most similar to query.
    max_age_days: if set, prefers recent articles; falls back to all results if
                  the recency filter would return nothing.
    """
    from services.embedder import embed_text

    try:
        embedding = embed_text(query)
        vec_str = f"[{','.join(str(round(x, 6)) for x in embedding)}]"
        del embedding
        gc.collect()
    except Exception as exc:
        log.warning("RAG embed failed: %s", exc)
        return []

    try:
        res = supabase_admin.rpc("match_article_chunks", {
            "query_embedding": vec_str,
            "match_count": min(limit * 2, 16),  # fetch extra so recency filter has headroom
            "filter_ticker": ticker,
            "min_similarity": min_similarity,
        }).execute()
        results = res.data or []
    except Exception as exc:
        log.warning("RAG search failed: %s", exc)
        return []

    # Prefer recent articles; fall back to full result set if filter empties it
    if max_age_days and results:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        recent = [r for r in results if _after(r.get("published_at"), cutoff)]
        results = recent if recent else results

    return results[:limit]


def _after(value: str | None, cutoff: datetime) -> bool:
    if not value:
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt >= cutoff
    except (ValueError, TypeError):
        return False
