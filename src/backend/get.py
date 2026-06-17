from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
import json
import threading
import time
from company_catalog import get_company_name_map, normalize_nse_symbol

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = BASE_DIR / "stockinews.db"
CACHE_DIR = BASE_DIR / ".cache"
WATCHLIST_CACHE_FILE = CACHE_DIR / "watchlist_quotes.json"
WATCHLIST_CACHE_TTL_SECONDS = 8 * 60 * 60   # 8 hours — open price is fixed for the day
WATCHLIST_STALE_TTL_SECONDS = 24 * 60 * 60  # serve stale if today's fetch fails
WATCHLIST_CACHE_VERSION = "open-v5"

_watchlist_cache_lock = threading.Lock()
_watchlist_refreshing = set()

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_user(decoded_token):
    user_id = decoded_token["user_id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return {"name": row[0], "email": row[1]}

def get_portfolio(decoded_token):
    user_id=decoded_token['user_id']
    # print("User_id for portfolio recieved")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''SELECT 
    ticker, 
    SUM(CASE WHEN action = 'BUY' THEN quantity ELSE 0 END) AS total_bought,
    SUM(CASE WHEN action = 'SELL' THEN quantity ELSE 0 END) AS total_sold,
    AVG(CASE WHEN action = 'BUY' THEN price ELSE NULL END) AS average_buy_price
    FROM stocks
    WHERE user_id = ?
    GROUP BY ticker
    HAVING total_bought - total_sold > 0
''', (user_id,))
    rows = cursor.fetchall()

    conn.close()
    if not rows:
        return jsonify({"error": "User not found"}), 404

    portfolio = []
    for row in rows:
        ticker = row[0]
        quantity = row[1]
        buy_price = row[3]
        current_price = get_price(ticker)  # Fetch live price
        portfolio.append({
            "ticker": ticker,
            "quantity": quantity,
            "buy_price": buy_price,
            "current_price": current_price
        })

        # print(portfolio)
    return jsonify({"portfolio": portfolio}), 200

def get_price(ticker):
    import yfinance as yf
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get("regularMarketPrice")
        if price is None:
            raise ValueError(f"No market price found for {ticker}")
        return round(price, 2)
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None 

_MARKET_NAMES = {
    "^GSPC":      "S&P 500",
    "^DJI":       "Dow Jones",
    "^IXIC":      "NASDAQ",
    "^FTSE":      "FTSE 100",
    "^GDAXI":     "DAX",
    "^FCHI":      "CAC 40",
    "^N225":      "Nikkei 225",
    "^HSI":       "Hang Seng",
    "000001.SS":  "Shanghai Composite",
    "^NSEI":      "NIFTY 50",
    "GC=F":       "Gold",
    "SI=F":       "Silver",
    "CL=F":       "Crude Oil (WTI)",
    "BZ=F":       "Brent Crude",
    "NG=F":       "Natural Gas",
    "HG=F":       "Copper",
}

_market_cache: dict = {"data": None, "at": 0.0}
_MARKET_TTL = 8 * 60 * 60.0  # 8 hours — open price is fixed for the day


def get_market_overview():
    import yfinance as yf
    import pandas as pd

    now = time.time()
    if _market_cache["data"] is not None and now - _market_cache["at"] < _MARKET_TTL:
        return _market_cache["data"]

    symbols = list(_MARKET_NAMES.keys())
    try:
        raw = yf.download(
            symbols,
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=True,
            group_by="ticker",
        )

        data = []
        for sym, name in _MARKET_NAMES.items():
            try:
                opens = (
                    raw[sym]["Open"].dropna()
                    if isinstance(raw.columns, pd.MultiIndex)
                    else raw["Open"].dropna()
                )
                open_price = round(float(opens.iloc[-1]), 2) if len(opens) else None
                data.append({
                    "symbol": sym,
                    "name": name,
                    "open_price": open_price,
                })
            except Exception as exc:
                print(f"Market ticker error {sym}: {exc}")
                data.append({"symbol": sym, "name": name, "open_price": None})

        _market_cache["data"] = data
        _market_cache["at"] = now
        return data

    except Exception as exc:
        print(f"Market overview batch error: {exc}")
        return _market_cache["data"] or []



def get_watchlist_data(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ticker FROM watchlist WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    # print(rows)
    raw_symbols = [row[0] for row in rows]
    normalized_pairs = [
        (raw_symbol, normalize_nse_symbol(raw_symbol))
        for raw_symbol in raw_symbols
    ]
    _repair_watchlist_symbols(cur, user_id, normalized_pairs)
    conn.commit()
    conn.close()
    symbols = []
    seen = set()
    for _, normalized_symbol in normalized_pairs:
        if normalized_symbol and normalized_symbol not in seen:
            seen.add(normalized_symbol)
            symbols.append(normalized_symbol)
    if not symbols:
        return []

    cached = _get_watchlist_cached_quotes(symbols, max_age=WATCHLIST_CACHE_TTL_SECONDS)
    if cached is not None:
        return cached

    stale = _get_watchlist_cached_quotes(symbols, max_age=WATCHLIST_STALE_TTL_SECONDS)
    if stale is not None:
        _refresh_watchlist_quotes_async(symbols)
        return stale

    return _fetch_and_cache_watchlist_quotes(symbols)


def _repair_watchlist_symbols(cursor, user_id, symbol_pairs):
    for raw_symbol, normalized_symbol in symbol_pairs:
        if raw_symbol and normalized_symbol and raw_symbol.upper() != normalized_symbol:
            cursor.execute(
                "UPDATE watchlist SET ticker = ? WHERE user_id = ? AND ticker = ?",
                (normalized_symbol, user_id, raw_symbol),
            )


def _get_watchlist_cached_quotes(symbols, max_age):
    cache = _read_watchlist_cache()
    now = time.time()
    result = []

    for symbol in symbols:
        item = cache.get(symbol)
        if (
            not item
            or item.get("version") != WATCHLIST_CACHE_VERSION
            or "open_price" not in item
            or item.get("open_price") is None
            or now - item.get("cached_at", 0) > max_age
        ):
            return None
        result.append(_public_watchlist_quote(symbol, item))

    return result


def _refresh_watchlist_quotes_async(symbols):
    key = tuple(sorted(symbols))
    with _watchlist_cache_lock:
        if key in _watchlist_refreshing:
            return
        _watchlist_refreshing.add(key)

    def worker():
        try:
            _fetch_and_cache_watchlist_quotes(symbols)
        finally:
            with _watchlist_cache_lock:
                _watchlist_refreshing.discard(key)

    threading.Thread(target=worker, daemon=True).start()


def _fetch_and_cache_watchlist_quotes(symbols):
    import yfinance as yf

    cache = _read_watchlist_cache()
    names = get_company_name_map()
    tickers_arg = " ".join(symbols)

    try:
        history = yf.download(
            tickers_arg,
            period="5d",
            interval="1d",
            group_by="ticker",
            threads=True,
            progress=False,
            auto_adjust=True,
        )
    except Exception as exc:
        print(f"Error fetching watchlist batch: {exc}")
        return [_public_watchlist_quote(symbol, cache.get(symbol, {})) for symbol in symbols]

    now = time.time()
    result = []
    for symbol in symbols:
        quote = _quote_from_history(history, symbol)
        if quote.get("open_price") is None:
            quote = _fetch_single_watchlist_quote(symbol)
        quote["name"] = names.get(symbol.replace(".NS", ""), symbol)
        quote["cached_at"] = now
        quote["version"] = WATCHLIST_CACHE_VERSION
        cache[symbol] = quote
        result.append(_public_watchlist_quote(symbol, quote))

    _write_watchlist_cache(cache)
    return result


def _fetch_single_watchlist_quote(symbol):
    import yfinance as yf

    try:
        history = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=True)
        return _quote_from_history(history, symbol)
    except Exception as exc:
        print(f"Error fetching single watchlist quote for {symbol}: {exc}")
        return {"open_price": None}


def _quote_from_history(history, symbol):
    import pandas as pd

    empty_quote = {"open_price": None}
    if history is None or history.empty:
        return empty_quote

    try:
        stock_df = _extract_stock_history_frame(history, symbol)

        if stock_df is None or "Open" not in stock_df:
            return empty_quote

        opens = stock_df["Open"].dropna()
        if opens.empty:
            return empty_quote

        return {"open_price": round(float(opens.iloc[-1]), 2)}
    except Exception as exc:
        print(f"Error parsing watchlist quote for {symbol}: {exc}")
        return empty_quote


def _extract_stock_history_frame(history, symbol):
    import pandas as pd

    if not isinstance(history.columns, pd.MultiIndex):
        return history

    symbol = symbol.upper()
    level_zero = [str(value).upper() for value in history.columns.get_level_values(0)]
    level_one = [str(value).upper() for value in history.columns.get_level_values(1)]

    if symbol in level_zero:
        return history.xs(symbol, axis=1, level=0)

    if symbol in level_one:
        return history.xs(symbol, axis=1, level=1)

    return None


def _public_watchlist_quote(symbol, quote):
    return {
        "symbol": symbol,
        "name": quote.get("name") or symbol,
        "open_price": quote.get("open_price"),
    }


def _read_watchlist_cache():
    with _watchlist_cache_lock:
        if not WATCHLIST_CACHE_FILE.exists():
            return {}
        try:
            return json.loads(WATCHLIST_CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}


def _write_watchlist_cache(cache):
    with _watchlist_cache_lock:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        WATCHLIST_CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")


def get_company_info(ticker: str) -> dict:
    import yfinance as yf
    ticker_upper = ticker.upper().replace(".NS", "")
    ns_ticker = f"{ticker_upper}.NS"
    stock = yf.Ticker(ns_ticker)
    info = stock.info
    return {
        "symbol": ticker_upper,
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
    import yfinance as yf
    ticker_upper = ticker.upper().replace(".NS", "")
    ns_ticker = f"{ticker_upper}.NS"
    stock = yf.Ticker(ns_ticker)

    news = []
    try:
        for item in (stock.news or [])[:10]:
            content = item.get("content") or {}
            title = item.get("title") or content.get("title")
            publisher = item.get("publisher") or content.get("provider", {}).get("displayName")
            url = item.get("link") or content.get("canonicalUrl", {}).get("url") or content.get("clickThroughUrl", {}).get("url")
            ts = item.get("providerPublishTime") or content.get("pubDate") or content.get("displayTime")
            published = _format_yahoo_datetime(ts)
            if not title or not url:
                continue
            news.append({
                "title": title,
                "publisher": publisher or "Yahoo Finance",
                "url": url,
                "published_at": published,
            })
    except Exception as exc:
        print(f"Error fetching Yahoo Finance news for {ticker}: {exc}")

    corporate_actions = []
    try:
        df = stock.actions
        if df is not None and not df.empty:
            for date, row in df.tail(10).iterrows():
                if row.get("Dividends", 0) > 0:
                    corporate_actions.append({
                        "date": str(date.date()),
                        "type": "Dividend",
                        "value": round(float(row["Dividends"]), 4),
                    })
                if row.get("Stock Splits", 0) > 0:
                    corporate_actions.append({
                        "date": str(date.date()),
                        "type": "Stock Split",
                        "value": float(row["Stock Splits"]),
                    })
    except Exception:
        pass

    calendar = {}
    try:
        cal = stock.calendar
        if cal:
            calendar = {
                _humanize_calendar_key(k): _format_calendar_value(v)
                for k, v in cal.items()
                if v is not None
            }
    except Exception as exc:
        print(f"Error fetching calendar for {ticker}: {exc}")

    return {
        "ticker": ticker_upper,
        "news": news,
        "corporate_actions": sorted(corporate_actions, key=lambda x: x["date"], reverse=True),
        "calendar": calendar,
    }


def _format_yahoo_datetime(value):
    from datetime import datetime, timezone
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def _humanize_calendar_key(key):
    label = str(key).replace("_", " ")
    words = []
    for word in label.split():
        expanded = ""
        for index, char in enumerate(word):
            if index and char.isupper() and word[index - 1].islower():
                expanded += " "
            expanded += char
        words.append(expanded)
    return " ".join(words).title()


def _format_calendar_value(value):
    from datetime import date, datetime
    import re

    if hasattr(value, "tolist"):
        value = value.tolist()

    if isinstance(value, (list, tuple, set)):
        formatted = [_format_calendar_value(item) for item in value if item is not None]
        return ", ".join(item for item in formatted if item)

    if isinstance(value, datetime):
        return value.strftime("%d %b %Y")

    if isinstance(value, date):
        return value.strftime("%d %b %Y")

    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d %b %Y")
        except Exception:
            pass

    text = str(value)
    matches = re.findall(r"datetime\.date\((\d{4}),\s*(\d{1,2}),\s*(\d{1,2})\)", text)
    if matches:
        return ", ".join(
            date(int(year), int(month), int(day)).strftime("%d %b %Y")
            for year, month, day in matches
        )
    return text


def getnewsdata():
    from dotenv import load_dotenv
    import os
    import requests
    load_dotenv()
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    keyz='Indian Stocks Nifty'
    url = f"https://newsapi.org/v2/everything?q={keyz}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    # print(data)
    if 'articles' not in data or len(data['articles']) == 0:
        return [{"title": "No News Available", "url": "", "description": "No news articles were found for this company."}]
    return [
        {
            "title": article['title'][:50],
            "url": article['url'],
            "description": article['description']
        }
        for article in data['articles']
    ]
