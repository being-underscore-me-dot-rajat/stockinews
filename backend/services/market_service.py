import json
import logging
import os
import threading
import time
from pathlib import Path

log = logging.getLogger(__name__)

import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

from .company_catalog import get_company_name_map, normalize_nse_symbol

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache"
WATCHLIST_CACHE_FILE = CACHE_DIR / "watchlist_quotes.json"
WATCHLIST_CACHE_TTL = 8 * 60 * 60
WATCHLIST_STALE_TTL = 24 * 60 * 60
WATCHLIST_CACHE_VERSION = "open-v5"

_wl_lock = threading.Lock()
_wl_refreshing: set = set()

_MARKET_NAMES = {
    "^GSPC": "S&P 500", "^DJI": "Dow Jones", "^IXIC": "NASDAQ",
    "^FTSE": "FTSE 100", "^GDAXI": "DAX", "^FCHI": "CAC 40",
    "^N225": "Nikkei 225", "^HSI": "Hang Seng", "000001.SS": "Shanghai Composite",
    "^NSEI": "NIFTY 50", "GC=F": "Gold", "SI=F": "Silver",
    "CL=F": "Crude Oil (WTI)", "BZ=F": "Brent Crude",
    "NG=F": "Natural Gas", "HG=F": "Copper",
}

_market_cache: dict = {"data": None, "at": 0.0}
_MARKET_TTL = 8 * 60 * 60


# ─── Market overview ──────────────────────────────────────────────────────────

def get_market_overview():
    now = time.time()
    if _market_cache["data"] is not None and now - _market_cache["at"] < _MARKET_TTL:
        return _market_cache["data"]

    symbols = list(_MARKET_NAMES.keys())
    try:
        raw = yf.download(symbols, period="5d", interval="1d", progress=False,
                          auto_adjust=True, group_by="ticker")
        data = []
        for sym, name in _MARKET_NAMES.items():
            try:
                opens = (raw[sym]["Open"].dropna()
                         if isinstance(raw.columns, pd.MultiIndex)
                         else raw["Open"].dropna())
                open_price = round(float(opens.iloc[-1]), 2) if len(opens) else None
            except Exception:
                open_price = None
            data.append({"symbol": sym, "name": name, "open_price": open_price})
        _market_cache["data"] = data
        _market_cache["at"] = now
        return data
    except Exception as exc:
        log.error("Market overview error: %s", exc)
        return _market_cache["data"] or []


# ─── Watchlist quotes ─────────────────────────────────────────────────────────

def get_watchlist_quotes(symbols: list[str]) -> list[dict]:
    cached = _get_cached_quotes(symbols, WATCHLIST_CACHE_TTL)
    if cached is not None:
        return cached
    stale = _get_cached_quotes(symbols, WATCHLIST_STALE_TTL)
    if stale is not None:
        _refresh_async(symbols)
        return stale
    return _fetch_and_cache(symbols)


def _get_cached_quotes(symbols, max_age):
    cache = _read_cache()
    now = time.time()
    result = []
    for sym in symbols:
        item = cache.get(sym)
        if (not item or item.get("version") != WATCHLIST_CACHE_VERSION
                or "open_price" not in item or item.get("open_price") is None
                or now - item.get("cached_at", 0) > max_age):
            return None
        result.append({"symbol": sym, "name": item.get("name", sym), "open_price": item["open_price"]})
    return result


def _refresh_async(symbols):
    key = tuple(sorted(symbols))
    with _wl_lock:
        if key in _wl_refreshing:
            return
        _wl_refreshing.add(key)

    def worker():
        try:
            _fetch_and_cache(symbols)
        finally:
            with _wl_lock:
                _wl_refreshing.discard(key)

    threading.Thread(target=worker, daemon=True).start()


def _fetch_and_cache(symbols: list[str]) -> list[dict]:
    cache = _read_cache()
    names = get_company_name_map()
    now = time.time()
    result = []

    try:
        history = yf.download(" ".join(symbols), period="5d", interval="1d",
                               group_by="ticker", threads=True, progress=False, auto_adjust=True)
    except Exception as exc:
        log.error("Watchlist batch fetch error: %s", exc)
        return [{"symbol": s, "name": names.get(s.replace(".NS", ""), s), "open_price": None} for s in symbols]

    for sym in symbols:
        quote = _quote_from_history(history, sym)
        if quote.get("open_price") is None:
            quote = _single_quote(sym)
        quote["name"] = names.get(sym.replace(".NS", ""), sym)
        quote["cached_at"] = now
        quote["version"] = WATCHLIST_CACHE_VERSION
        cache[sym] = quote
        result.append({"symbol": sym, "name": quote["name"], "open_price": quote.get("open_price")})

    _write_cache(cache)
    return result


def _quote_from_history(history, symbol):
    if history is None or history.empty:
        return {"open_price": None}
    try:
        if isinstance(history.columns, pd.MultiIndex):
            sym_up = symbol.upper()
            lvl0 = [str(v).upper() for v in history.columns.get_level_values(0)]
            lvl1 = [str(v).upper() for v in history.columns.get_level_values(1)]
            if sym_up in lvl0:
                df = history.xs(sym_up, axis=1, level=0)
            elif sym_up in lvl1:
                df = history.xs(sym_up, axis=1, level=1)
            else:
                return {"open_price": None}
        else:
            df = history
        opens = df["Open"].dropna()
        return {"open_price": round(float(opens.iloc[-1]), 2)} if not opens.empty else {"open_price": None}
    except Exception:
        return {"open_price": None}


def _single_quote(symbol):
    try:
        h = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=True)
        opens = h["Open"].dropna()
        return {"open_price": round(float(opens.iloc[-1]), 2)} if not opens.empty else {"open_price": None}
    except Exception:
        return {"open_price": None}


def _read_cache() -> dict:
    with _wl_lock:
        if not WATCHLIST_CACHE_FILE.exists():
            return {}
        try:
            return json.loads(WATCHLIST_CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}


def _write_cache(cache: dict) -> None:
    with _wl_lock:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        WATCHLIST_CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")


# ─── Company info & developments ─────────────────────────────────────────────

def get_company_info(ticker: str) -> dict:
    ns = f"{ticker.upper().replace('.NS', '')}.NS"
    info = yf.Ticker(ns).info
    return {
        "symbol": ticker.upper().replace(".NS", ""),
        "name": info.get("longName") or info.get("shortName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "description": info.get("longBusinessSummary"),
        "website": info.get("website"),
        "country": info.get("country"),
        "employees": info.get("fullTimeEmployees"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "eps": info.get("trailingEps"),
        "book_value": info.get("bookValue"),
        "price_to_book": info.get("priceToBook"),
        "dividend_yield": info.get("dividendYield"),
        "week_52_high": info.get("fiftyTwoWeekHigh"),
        "week_52_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "exchange": info.get("exchange"),
        "price": info.get("regularMarketPrice"),
    }


def get_company_developments(ticker: str) -> dict:
    from datetime import datetime, timezone, date as date_type
    import re

    ns = f"{ticker.upper().replace('.NS', '')}.NS"
    stock = yf.Ticker(ns)

    news = []
    for item in (stock.news or [])[:10]:
        content = item.get("content") or {}
        title = item.get("title") or content.get("title")
        publisher = item.get("publisher") or content.get("provider", {}).get("displayName")
        url = (item.get("link") or content.get("canonicalUrl", {}).get("url")
               or content.get("clickThroughUrl", {}).get("url"))
        ts = item.get("providerPublishTime") or content.get("pubDate") or content.get("displayTime")
        if not title or not url:
            continue
        published = None
        if isinstance(ts, (int, float)):
            published = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        elif isinstance(ts, str):
            published = ts
        news.append({"title": title, "publisher": publisher or "Yahoo Finance",
                     "url": url, "published_at": published})

    corporate_actions = []
    try:
        df = stock.actions
        if df is not None and not df.empty:
            for dt, row in df.tail(10).iterrows():
                if row.get("Dividends", 0) > 0:
                    corporate_actions.append(
                        {"date": str(dt.date()), "type": "Dividend", "value": round(float(row["Dividends"]), 4)})
                if row.get("Stock Splits", 0) > 0:
                    corporate_actions.append(
                        {"date": str(dt.date()), "type": "Stock Split", "value": float(row["Stock Splits"])})
    except Exception:
        pass

    calendar = {}
    try:
        cal = stock.calendar
        if cal:
            for k, v in cal.items():
                if v is None:
                    continue
                if hasattr(v, "tolist"):
                    v = v.tolist()
                if isinstance(v, (list, tuple)):
                    v = ", ".join(
                        (d.strftime("%d %b %Y") if hasattr(d, "strftime") else str(d)) for d in v if d is not None)
                elif hasattr(v, "strftime"):
                    v = v.strftime("%d %b %Y")
                calendar[str(k).replace("_", " ").title()] = str(v)
    except Exception:
        pass

    return {
        "ticker": ticker.upper().replace(".NS", ""),
        "news": news,
        "corporate_actions": sorted(corporate_actions, key=lambda x: x["date"], reverse=True),
        "calendar": calendar,
    }


# ─── NewsAPI ──────────────────────────────────────────────────────────────────

def get_news_api_articles() -> list[dict]:
    import requests
    NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
    url = (f"https://newsapi.org/v2/everything"
           f"?q=Indian+Stocks+Nifty&sortBy=publishedAt&apiKey={NEWS_API_KEY}")
    try:
        data = requests.get(url, timeout=10).json()
        return [
            {"title": a["title"][:50], "url": a["url"], "description": a["description"],
             "source": a.get("source"), "publishedAt": a.get("publishedAt")}
            for a in data.get("articles", [])
        ]
    except Exception as exc:
        log.error("NewsAPI error: %s", exc)
        return []
