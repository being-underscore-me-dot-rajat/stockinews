import json
import threading
import time
from pathlib import Path

import pandas as pd
import yfinance as yf


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / ".cache" / "charts"
CACHE_TTL_SECONDS = 6 * 60 * 60
CACHE_VERSION = "v3"
PERIODS = ("7d", "1mo", "6mo", "1y", "max")
INTERVALS = {
    "7d": "1d",
    "1mo": "1d",
    "6mo": "1d",
    "1y": "1d",
    "max": "1mo",
}

_warm_locks = set()
_warm_lock = threading.Lock()


def _cache_path(ticker, period):
    safe_ticker = ticker.upper().replace("/", "_").replace(":", "_")
    return CACHE_DIR / f"{CACHE_VERSION}_{safe_ticker}_{period}.json"


def _read_cache(ticker, period, allow_stale=False):
    path = _cache_path(ticker, period)
    if not path.exists():
        return None
    is_stale = time.time() - path.stat().st_mtime > CACHE_TTL_SECONDS
    if is_stale and not allow_stale:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        try:
            path.unlink()
        except OSError:
            pass
        return None


def _write_cache(ticker, period, data):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(ticker, period).write_text(json.dumps(data), encoding="utf-8")


def _fetch_data(ticker, period):
    interval = INTERVALS.get(period, "1d")
    data = yf.Ticker(ticker).history(period=period, interval=interval)
    data = pd.DataFrame(data).reset_index()
    if data.empty or "Close" not in data:
        return []

    date_column = "Datetime" if "Datetime" in data else "Date"
    data["Datetime"] = pd.to_datetime(data[date_column]).dt.strftime("%d-%m-%y")
    data = data[["Datetime", "Close"]]
    return json.loads(data.to_json(orient="records"))


def getdata(ticker, period="7d"):
    period = period if period in PERIODS else "7d"
    cached = _read_cache(ticker, period)
    if cached is not None:
        return cached

    stale_cached = _read_cache(ticker, period, allow_stale=True)
    if stale_cached is not None:
        warm_cache(ticker, periods=(period,))
        return stale_cached

    data = _fetch_data(ticker, period)
    _write_cache(ticker, period, data)
    return data


def warm_cache(ticker, periods=PERIODS):
    cache_key = ticker.upper()
    with _warm_lock:
        if cache_key in _warm_locks:
            return
        _warm_locks.add(cache_key)

    def worker():
        try:
            for period in periods:
                if _read_cache(ticker, period) is None:
                    try:
                        data = _fetch_data(ticker, period)
                        _write_cache(ticker, period, data)
                    except Exception as exc:
                        print(f"Chart cache warm failed for {ticker} {period}: {exc}")
        finally:
            with _warm_lock:
                _warm_locks.discard(cache_key)

    threading.Thread(target=worker, daemon=True).start()
