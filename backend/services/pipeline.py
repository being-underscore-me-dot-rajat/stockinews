"""
Phase 3 — News ingestion pipeline.
Stages: Crawl → Clean → Chunk → Embed → Store (pgvector).
"""
import gc
import hashlib
import logging
import uuid
from datetime import datetime, timezone

import psutil

from services.supabase_client import supabase_admin
from services.news_crawler import crawl_news, crawl_news_for_ticker

log = logging.getLogger(__name__)

# ~500 tokens at 4 chars/token
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200

MAX_MEMORY_MB = 12_000  # ~75% of 16 GB — halt pipeline if exceeded
_process = psutil.Process()

_status: dict = {
    "last_run_at": None,
    "last_run_status": None,
    "articles_processed": 0,
    "chunks_stored": 0,
    "running": False,
    "last_error": None,
}


def get_status() -> dict:
    return dict(_status)


def run_pipeline() -> dict:
    """Called by the APScheduler job or the manual /api/pipeline/run route."""
    if _status["running"]:
        return {"status": "already_running"}

    _status["running"] = True
    _status["last_run_at"] = datetime.now(timezone.utc).isoformat()
    _status["last_error"] = None

    try:
        result = _execute()
        _status.update(result)
        _status["last_run_status"] = "ok"
    except Exception as exc:
        log.exception("Pipeline failed")
        _status["last_run_status"] = "error"
        _status["last_error"] = str(exc)
        result = {"status": "error", "detail": str(exc)}
    finally:
        _status["running"] = False

    return result


def _crawl_tracked_tickers(cfg: dict) -> list[dict]:
    """Fetch company-specific news for each tracked ticker via targeted Google News search."""
    articles = []
    for ticker in cfg["tracked_tickers"]:
        _check_memory()
        try:
            items = crawl_news_for_ticker(
                ticker=ticker,
                limit=cfg["per_ticker_limit"],
                min_summary_len=cfg["min_summary_len"],
            )
            for item in items:
                item.setdefault("companies", [ticker])
            articles.extend(items)
            log.debug("Ticker crawl %s: %d articles", ticker, len(items))
        except Exception as exc:
            log.warning("Ticker crawl failed %s: %s", ticker, exc)
    return articles


def _check_memory() -> None:
    """Raise RuntimeError if RSS exceeds the hard limit."""
    rss_mb = _process.memory_info().rss / 1024 / 1024
    if rss_mb > MAX_MEMORY_MB:
        raise RuntimeError(f"Memory limit exceeded: {rss_mb:.0f} MB > {MAX_MEMORY_MB} MB — aborting pipeline")
    if rss_mb > MAX_MEMORY_MB * 0.8:
        log.warning("Pipeline memory at %.0f MB (%.0f%% of limit)", rss_mb, rss_mb / MAX_MEMORY_MB * 100)


# ── Pipeline configs ──────────────────────────────────────────────────────────
# Select with PIPELINE_MODE=dev (default) or PIPELINE_MODE=prod in .env

_CONFIGS = {
    "dev": {
        # Uses RSS feed descriptions directly — skips per-article HTTP fetches.
        # Full pipeline completes in ~5 minutes.
        "crawl_limit": 120,
        "min_summary_len": 200,   # skip full fetch if RSS description >= 200 chars
        "per_ticker_limit": 3,
        "tracked_tickers": [
            "RELIANCE", "TCS", "HDFCBANK", "SBIN", "ICICIBANK",
            "LT", "NTPC", "ONGC",
            "MAZDOCK", "HAL", "BEL",
            "SUNPHARMA", "DRREDDY",
            "TATAMOTORS", "ADANIPORTS",
        ],
    },
    "prod": {
        # Fetches full article text for every URL — richer embeddings, longer runtime (30-60 min).
        "crawl_limit": 300,
        "min_summary_len": 0,     # always fetch full article
        "per_ticker_limit": 5,
        "tracked_tickers": [
            "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK",
            "WIPRO", "HCLTECH", "LT", "MARUTI", "TATAMOTORS", "BAJFINANCE",
            "MAZDOCK", "HAL", "BEL", "BEML", "COCHINSHIP",
            "NTPC", "POWERGRID", "COALINDIA", "ONGC", "IOC",
            "ADANIPORTS", "ADANIENT", "JSWSTEEL", "TATASTEEL", "HINDALCO",
            "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB",
            "IRFC", "IRCON", "RVNL", "NBCC",
        ],
    },
}


def _get_config() -> dict:
    import os
    mode = os.getenv("PIPELINE_MODE", "dev").strip().lower()
    if mode not in _CONFIGS:
        log.warning("Unknown PIPELINE_MODE '%s', falling back to dev", mode)
        mode = "dev"
    cfg = _CONFIGS[mode]
    log.info("Pipeline mode: %s (limit=%d, tickers=%d, min_summary_len=%d)",
             mode, cfg["crawl_limit"], len(cfg["tracked_tickers"]), cfg["min_summary_len"])
    return cfg


def _execute() -> dict:
    # Lazy import — fails gracefully if Azure env vars are not configured
    from services.embedder import embed_texts

    cfg = _get_config()

    # ── Stage 1: broad news crawl across all sources ──────────────────────────
    articles = crawl_news(
        source="all",
        limit=cfg["crawl_limit"],
        min_summary_len=cfg["min_summary_len"],
    )
    log.info("Pipeline: crawled %d articles from broad sources", len(articles))

    # ── Stage 2: targeted crawl for tracked tickers ───────────────────────────
    ticker_articles = _crawl_tracked_tickers(cfg)
    log.info("Pipeline: crawled %d ticker-specific articles", len(ticker_articles))
    articles.extend(ticker_articles)

    processed, stored = _process_articles(articles)
    return {"status": "done", "articles_processed": processed, "chunks_stored": stored}


def _process_articles(articles: list[dict]) -> tuple[int, int]:
    """Embed and store a list of pre-crawled article dicts. Returns (processed, chunks_stored)."""
    from services.embedder import embed_texts

    articles_processed = 0
    chunks_stored = 0

    for article in articles:
        _check_memory()

        url = article.get("url", "")
        if not url or _is_seen(url):
            continue

        article_text = article.get("article_text") or article.get("summary", "")
        title = article.get("title", "")
        full_text = f"{title}. {article_text}".strip() if article_text else title
        if len(full_text) < 30:
            _mark_seen(url)
            continue

        chunks = _chunk_text(full_text)
        if not chunks:
            _mark_seen(url)
            continue

        try:
            embeddings = embed_texts(chunks)
        except Exception as exc:
            log.warning("Embedding failed for %s: %s", url, exc)
            _mark_seen(url)
            continue

        article_id = str(uuid.uuid4())
        tickers_list = article.get("companies") or []
        rows = []
        for chunk_text, embedding in zip(chunks, embeddings):
            rows.append({
                "article_id": article_id,
                "tickers": tickers_list if tickers_list else None,
                "sector": article.get("sector") or None,
                "source": article.get("source") or None,
                "published_at": article.get("published_at") or None,
                "url": url,
                "chunk_text": chunk_text,
                "embedding": f"[{','.join(str(round(x, 6)) for x in embedding)}]",
            })

        try:
            supabase_admin.table("article_chunks").insert(rows).execute()
            chunks_stored += len(rows)
            articles_processed += 1
        except Exception as exc:
            log.warning("DB insert failed for %s: %s", url, exc)

        _mark_seen(url)
        del embeddings, rows
        gc.collect()

    return articles_processed, chunks_stored


def ingest_ticker(ticker: str) -> None:
    """Crawl, embed, and store fresh articles for one ticker. Safe to call from a background thread."""
    try:
        cfg = _get_config()
        bare = ticker.upper().replace(".NS", "")
        articles = crawl_news_for_ticker(
            ticker=bare,
            limit=cfg["per_ticker_limit"],
            min_summary_len=cfg["min_summary_len"],
        )
        # Tag each article with the ticker so RAG can filter by it
        for a in articles:
            a.setdefault("companies", [bare])
        processed, stored = _process_articles(articles)
        log.info("ingest_ticker %s: %d articles, %d chunks", bare, processed, stored)
    except Exception as exc:
        log.warning("ingest_ticker failed %s: %s", ticker, exc)


# ── Deduplication ──────────────────────────────────────────────────────────────

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _is_seen(url: str) -> bool:
    try:
        res = supabase_admin.table("crawled_urls").select("id").eq("url_hash", _url_hash(url)).execute()
        return bool(res.data)
    except Exception:
        return False


def _mark_seen(url: str) -> None:
    try:
        supabase_admin.table("crawled_urls").insert({
            "url_hash": _url_hash(url),
            "url": url,
        }).execute()
    except Exception:
        pass  # UNIQUE constraint hit = already seen, fine


# ── Chunking ───────────────────────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            # prefer breaking at a sentence boundary
            last_period = text.rfind(".", start + CHUNK_SIZE // 2, end)
            if last_period > 0:
                end = last_period + 1
        chunk = text[start:end].strip()
        if len(chunk) >= 50:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP
    return chunks
