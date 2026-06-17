"""
Phase 4 — AI agent.
GPT-4.1-mini on Azure AI Foundry with tool use + RAG retrieval.

Retrieval strategy (same for all three routes):
  1. Pre-fetch live yfinance headlines for known tickers (deterministic, not model-driven)
  2. Model calls search_news for RAG context from the knowledge base
  3. Model calls get_stock_info if price/valuation metrics are needed
  4. Live news is queued for background ingestion so future searches benefit from it
"""
import gc
import json
import logging
import os
import threading

log = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import AzureOpenAI
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        if not endpoint or not api_key:
            raise RuntimeError(
                "Azure OpenAI credentials not configured — "
                "set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY"
            )
        _client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)
    return _client


# ── Tool definitions (search_news + get_stock_info only) ─────────────────────
# get_live_news is NOT a model tool — it is called programmatically before the
# model call and injected as context, so the model can never double-fetch it.

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_news",
            "description": (
                "Search the knowledge base for relevant news articles about a stock or topic. "
                "Use this first for thematic context, sector trends, and historical coverage."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query":  {"type": "string",  "description": "Search query"},
                    "ticker": {"type": "string",  "description": "Optional NSE ticker to filter, e.g. RELIANCE.NS"},
                    "limit":  {"type": "integer", "description": "Number of results, 1–8", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": (
                "Search Google News for very recent articles about a specific event or company. "
                "Use this when search_news returns no results, or for specific corporate events "
                "like stock splits, bonuses, quarterly results, mergers, demergers, acquisitions, "
                "regulatory orders, or contract wins that may not yet be in the knowledge base."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific search query, e.g. 'Tata Motors stock split 2025 NSE India'",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_info",
            "description": "Get current price, P/E, market cap, 52-week range, and key metrics for an NSE stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "NSE ticker, e.g. RELIANCE.NS"},
                },
                "required": ["ticker"],
            },
        },
    },
]

# ── Unified system prompt ─────────────────────────────────────────────────────
# One prompt for all three routes. The pre-fetched live news is injected into
# the user message, so no route-specific instructions are needed.

_SYSTEM = """You are a financial research assistant for StockiNews, an Indian stock market platform.

The user message already contains the latest live headlines for relevant stocks (pre-fetched before this call).

Tool usage order:
1. search_news — always call this first for context from the knowledge base
2. search_web — call this if search_news returns no results, OR for specific corporate events
   (stock split, bonus issue, quarterly results, merger, acquisition, order win, regulatory action)
   that may not yet be in the knowledge base. Be specific: "Tata Motors stock split 2025 NSE"
3. get_stock_info — only if current price or valuation metrics are needed

Respond with ONLY a JSON object — no markdown, no extra text:
{
  "sentiment": "Bullish" | "Bearish" | "Neutral",
  "confidence": <float 0.0–1.0 reflecting how much relevant data was found>,
  "key_themes": [<up to 5 short keyword strings>],
  "directional_impact": "<one sentence on likely near-term price direction>",
  "sources": [{"title": "...", "source": "...", "url": "...", "published_at": "..."}],
  "summary": "<2–4 sentence analysis grounded in retrieved data>"
}

Rules:
- sources must only reference articles actually seen in this conversation
- If data is scarce, set confidence ≤ 0.3 and note it in summary
- Focus on Indian market context (NSE/BSE, INR)"""


# ── Live news pre-fetch ───────────────────────────────────────────────────────

def _fetch_live_news_for_ticker(ticker: str) -> list[dict]:
    """Fetch yfinance headlines for one ticker. Returns up to 5 items."""
    import yfinance as yf
    from datetime import datetime, timezone as tz

    ns = ticker if ticker.upper().endswith(".NS") else f"{ticker.upper()}.NS"
    try:
        raw = yf.Ticker(ns).news or []
    except Exception as exc:
        log.warning("Live news fetch failed %s: %s", ticker, exc)
        return []

    results = []
    for item in raw[:5]:
        content = item.get("content") or {}
        title = item.get("title") or content.get("title", "")
        publisher = item.get("publisher") or content.get("provider", {}).get("displayName", "")
        url = (item.get("link")
               or content.get("canonicalUrl", {}).get("url")
               or content.get("clickThroughUrl", {}).get("url", ""))
        ts = item.get("providerPublishTime") or content.get("pubDate")
        published = ""
        if isinstance(ts, (int, float)):
            published = datetime.fromtimestamp(ts, tz=tz.utc).isoformat()
        elif isinstance(ts, str):
            published = ts
        if title:
            results.append({"title": title, "publisher": publisher,
                            "url": url, "published_at": published, "ticker": ticker})
    del raw
    gc.collect()
    return results


def _prefetch_and_ingest(tickers: list[str]) -> str:
    """
    Fetch live news for each ticker, format as a compact string for injection
    into the user message, and queue each ticker for background ingestion.
    Returns the formatted string (empty string if no news found).
    """
    all_items: list[dict] = []
    for t in tickers:
        items = _fetch_live_news_for_ticker(t)
        all_items.extend(items)
        if items:
            _queue_ingest(t)   # persist to pgvector in background

    if not all_items:
        return ""

    lines = [f"[{i['ticker']}] {i['title']} | {i.get('publisher','')} | {i.get('published_at','')[:10]}"
             for i in all_items]
    return "\n\nLatest live headlines (pre-fetched from Yahoo Finance):\n" + "\n".join(lines)


def _queue_ingest(ticker: str) -> None:
    """Fire-and-forget: crawl and embed fresh articles for this ticker in background."""
    def _worker():
        try:
            from services.pipeline import ingest_ticker
            ingest_ticker(ticker)
        except Exception as exc:
            log.warning("Background ingest failed %s: %s", ticker, exc)
    threading.Thread(target=_worker, daemon=True).start()


# ── Tool executor ─────────────────────────────────────────────────────────────

def _run_tool(name: str, args: dict) -> str:
    try:
        if name == "search_news":
            from services.rag import search_chunks
            chunks = search_chunks(
                query=args.get("query", ""),
                ticker=args.get("ticker"),
                limit=min(int(args.get("limit", 5)), 8),
                max_age_days=30,
            )
            if not chunks:
                return json.dumps({"results": [], "message": "No relevant articles found in knowledge base"})
            return json.dumps({
                "results": [
                    {
                        "chunk_text": c.get("chunk_text", "")[:600],
                        "source": c.get("source"),
                        "url": c.get("url"),
                        "published_at": str(c.get("published_at", "")),
                        "similarity": round(float(c.get("similarity", 0)), 3),
                    }
                    for c in chunks
                ]
            })

        if name == "search_web":
            import xml.etree.ElementTree as ET
            import requests as _req
            from urllib.parse import urlencode
            query = args.get("query", "").strip()
            if not query:
                return json.dumps({"error": "query is required"})
            params = urlencode({"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
            rss_url = f"https://news.google.com/rss/search?{params}"
            resp = _req.get(rss_url, headers={"User-Agent": "Mozilla/5.0",
                                              "Accept": "application/rss+xml,application/xml"},
                            timeout=8)
            root = ET.fromstring(resp.content)
            results = []
            for entry in root.findall(".//item")[:8]:
                def _t(tag):
                    el = entry.find(tag)
                    return el.text.strip() if el is not None and el.text else ""
                src = entry.find("source")
                title = _t("title")
                if title:
                    results.append({
                        "title": title,
                        "url": _t("link") or _t("guid"),
                        "source": src.text.strip() if src is not None and src.text else "",
                        "published_at": _t("pubDate"),
                    })
            if not results:
                return json.dumps({"message": f"No web results found for: {query}"})
            return json.dumps({"web_results": results})

        if name == "get_stock_info":
            from services.market_service import get_company_info
            info = get_company_info(args.get("ticker", ""))
            info.pop("description", None)
            return json.dumps(info)

    except Exception as exc:
        log.warning("Tool %s error: %s", name, exc)
        return json.dumps({"error": str(exc)})

    return json.dumps({"error": f"Unknown tool: {name}"})


# ── Public entry point ────────────────────────────────────────────────────────

def run_agent(
    question: str,
    ticker: str | None = None,
    portfolio_context: str | None = None,
    tickers: list[str] | None = None,
) -> dict:
    """
    Run the agent and return a structured dict.

    tickers: list of NSE ticker strings to pre-fetch live news for.
             For /query, pass [ticker]. For /portfolio, pass top holdings.
             For /briefing, pass watchlist tickers.
    """
    client = _get_client()
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4.1-mini")

    # ── Resolve ticker list ───────────────────────────────────────────────────
    fetch_tickers: list[str] = []
    if ticker:
        fetch_tickers = [ticker]
    elif tickers:
        fetch_tickers = tickers[:5]   # cap to control latency and token cost

    # ── Pre-fetch live news (same for all routes) ─────────────────────────────
    live_context = _prefetch_and_ingest(fetch_tickers) if fetch_tickers else ""

    # ── Build user message ────────────────────────────────────────────────────
    if ticker:
        user_content = f"[Stock: {ticker}]\n\nQuestion: {question}{live_context}"
    elif portfolio_context:
        user_content = (
            f"Portfolio holdings:\n{portfolio_context}\n\n"
            f"Question: {question}{live_context}"
        )
    else:
        user_content = f"{question}{live_context}"

    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": user_content},
    ]

    raw = "{}"
    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            tools=_TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            raw = msg.content or "{}"
            break

        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = _run_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
    else:
        messages.append({"role": "user", "content": "Provide your final JSON analysis now."})
        response = client.chat.completions.create(model=deployment, messages=messages)
        raw = response.choices[0].message.content or "{}"

    del messages
    gc.collect()

    return _parse(raw)


def _parse(raw: str) -> dict:
    try:
        text = raw.strip()
        if text.startswith("```"):
            parts = text.split("```")
            text = parts[1].lstrip("json").strip() if len(parts) >= 2 else text
        return json.loads(text)
    except Exception:
        return {
            "sentiment": "Neutral",
            "confidence": 0.0,
            "key_themes": [],
            "directional_impact": "",
            "sources": [],
            "summary": raw[:500] if raw else "Unable to parse agent response.",
        }
