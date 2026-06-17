"""
company_data.py — deep yfinance extraction for company-page tabs.
Each function is independently cached; every yfinance call is wrapped in
try/except so partial results are returned when data is unavailable (common
for NSE stocks on certain fields).
"""
import json
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache" / "company_data"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

_TTL = {
    "financials": 24 * 3600,
    "analysts":   12 * 3600,
    "holders":    24 * 3600,
    "earnings":   24 * 3600,
    "options":     1 * 3600,
    "esg":        48 * 3600,
}


# ─── Cache helpers ────────────────────────────────────────────────────────────

def _cpath(ticker: str, key: str) -> Path:
    return CACHE_DIR / f"{ticker.replace('/', '_')}_{key}.json"


def _load(ticker: str, key: str):
    p = _cpath(ticker, key)
    if not p.exists():
        return None
    try:
        obj = json.loads(p.read_text())
        if time.time() - obj.get("_t", 0) < _TTL[key]:
            return obj["d"]
    except Exception:
        pass
    return None


def _save(ticker: str, key: str, data) -> None:
    try:
        _cpath(ticker, key).write_text(json.dumps({"_t": time.time(), "d": data}))
    except Exception:
        pass


# ─── Serialisation helpers ────────────────────────────────────────────────────

def _ts(val) -> str:
    """Stringify a value that may be a Timestamp."""
    return val.strftime("%Y-%m-%d") if hasattr(val, "strftime") else str(val)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.where(pd.notnull(df), None)
    return df.replace([float("inf"), float("-inf")], None)


def _fin_df(df) -> dict | None:
    """
    Financial statement DF: rows=metrics, cols=Timestamps.
    Returns {date_str: {metric: value}} — each top-level key is a period.
    """
    if df is None or df.empty:
        return None
    try:
        df = df.copy()
        df.columns = [_ts(c) for c in df.columns]
        df.index   = [str(i) for i in df.index]
        return _clean(df).to_dict()   # orient='dict' → {col: {idx: val}}
    except Exception:
        return None


def _records_df(df) -> list | None:
    """Tabular DF (rows=records): returns [{col: val, ...}] list."""
    if df is None or df.empty:
        return None
    try:
        df = df.copy()
        df.columns = [str(c) for c in df.columns]
        if not isinstance(df.index, pd.RangeIndex):
            idx_name = df.index.name or "date"
            df.index = [_ts(i) for i in df.index]
            df.index.name = idx_name
            df = df.reset_index()
        return _clean(df).to_dict(orient="records")
    except Exception:
        return None


def _series_records(s) -> list | None:
    """Series → [{date, value}]."""
    if s is None or s.empty:
        return None
    try:
        return [{"date": _ts(i), "value": (v if v == v else None)} for i, v in s.items()]
    except Exception:
        return None


def _safe(obj, attr):
    """Safely get an attribute from a yfinance Ticker object."""
    try:
        return getattr(obj, attr, None)
    except Exception:
        return None


# ─── Public service functions ─────────────────────────────────────────────────

def get_financials(ticker: str) -> dict:
    cached = _load(ticker, "financials")
    if cached is not None:
        return cached

    t = yf.Ticker(ticker)

    def _f(attr):
        df = _safe(t, attr)
        return _fin_df(df)

    data = {
        "income_statement": {
            "annual":    _f("financials"),
            "quarterly": _f("quarterly_financials"),
        },
        "balance_sheet": {
            "annual":    _f("balance_sheet"),
            "quarterly": _f("quarterly_balance_sheet"),
        },
        "cash_flow": {
            "annual":    _f("cashflow"),
            "quarterly": _f("quarterly_cashflow"),
        },
    }
    _save(ticker, "financials", data)
    return data


def get_analysts(ticker: str) -> dict:
    cached = _load(ticker, "analysts")
    if cached is not None:
        return cached

    t = yf.Ticker(ticker)

    def _r(attr):
        return _records_df(_safe(t, attr))

    data = {
        "recommendations":     _r("recommendations"),
        "upgrades_downgrades": _r("upgrades_downgrades"),
        "price_targets":       _r("analyst_price_targets"),
        "earnings_estimate":   _r("earnings_estimate"),
        "revenue_estimate":    _r("revenue_estimate"),
        "eps_trend":           _r("eps_trend"),
    }
    _save(ticker, "analysts", data)
    return data


def get_holders(ticker: str) -> dict:
    cached = _load(ticker, "holders")
    if cached is not None:
        return cached

    t = yf.Ticker(ticker)

    data = {
        "major_holders":         _records_df(_safe(t, "major_holders")),
        "institutional_holders": _records_df(_safe(t, "institutional_holders")),
        "mutualfund_holders":    _records_df(_safe(t, "mutualfund_holders")),
        "insider_transactions":  _records_df(_safe(t, "insider_transactions")),
    }
    _save(ticker, "holders", data)
    return data


def get_earnings(ticker: str) -> dict:
    cached = _load(ticker, "earnings")
    if cached is not None:
        return cached

    t = yf.Ticker(ticker)

    # Earnings history (quarterly EPS)
    earnings = _records_df(_safe(t, "earnings_history"))

    # Upcoming / recent earnings dates
    earnings_dates = None
    try:
        df = t.earnings_dates
        if df is not None and not df.empty:
            df = df.copy()
            df.index = df.index.strftime("%Y-%m-%d")
            df.index.name = "date"
            earnings_dates = _clean(df.reset_index()).to_dict(orient="records")
    except Exception:
        pass

    data = {
        "earnings_history": earnings,
        "earnings_dates":   earnings_dates,
        "dividends":        _series_records(_safe(t, "dividends")),
        "splits":           _series_records(_safe(t, "splits")),
    }
    _save(ticker, "earnings", data)
    return data


def get_options(ticker: str) -> dict:
    cached = _load(ticker, "options")
    if cached is not None:
        return cached

    t = yf.Ticker(ticker)
    expiry_dates = []
    calls = None
    puts  = None

    try:
        expiry_dates = list(t.options or [])
    except Exception:
        pass

    if expiry_dates:
        try:
            chain = t.option_chain(expiry_dates[0])
            calls = _records_df(chain.calls)
            puts  = _records_df(chain.puts)
        except Exception:
            pass

    data = {
        "expiry_dates":   expiry_dates,
        "nearest_expiry": expiry_dates[0] if expiry_dates else None,
        "calls": calls,
        "puts":  puts,
    }
    _save(ticker, "options", data)
    return data


def get_esg(ticker: str) -> dict:
    cached = _load(ticker, "esg")
    if cached is not None:
        return cached

    t = yf.Ticker(ticker)
    data: dict = {}

    try:
        sus = t.sustainability
        if sus is not None and not sus.empty:
            sus = sus.copy()
            sus.index = [str(i) for i in sus.index]
            # Usually a single-column DF with 'Value' column
            col = sus.columns[0]
            for idx, val in sus[col].items():
                data[idx] = None if (val != val) else val
    except Exception:
        pass

    _save(ticker, "esg", data)
    return data
