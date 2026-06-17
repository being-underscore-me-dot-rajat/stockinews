"""
Education service — computes live indicator data for educational charts.
All computation is streaming/chunked; no unbounded lists.
"""
import gc
import json
import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import numpy as np
import yfinance as yf

from services.education_content import CONCEPTS, INDICATORS, OPTIONS

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", ".cache", "education")
os.makedirs(CACHE_DIR, exist_ok=True)

CACHE_TTL_SECONDS = 3600  # 1 hour for indicator charts


# ── Content catalogue ─────────────────────────────────────────────────────────

def get_concepts_list() -> list[dict]:
    return [
        {
            "slug": v["slug"],
            "title": v["title"],
            "category": v["category"],
            "tagline": v["tagline"],
        }
        for v in CONCEPTS.values()
    ]


def get_concept(slug: str) -> Optional[dict]:
    return CONCEPTS.get(slug)


def get_indicators_list() -> list[dict]:
    return [
        {
            "slug": v["slug"],
            "title": v["title"],
            "category": v["category"],
            "tagline": v["tagline"],
        }
        for v in INDICATORS.values()
    ]


def get_indicator(slug: str) -> Optional[dict]:
    return INDICATORS.get(slug)


def get_options_list() -> list[dict]:
    return [
        {
            "slug": v["slug"],
            "title": v["title"],
            "category": v["category"],
            "tagline": v["tagline"],
        }
        for v in OPTIONS.values()
    ]


def get_option_topic(slug: str) -> Optional[dict]:
    return OPTIONS.get(slug)


# ── Indicator data computation ────────────────────────────────────────────────

def _cache_path(key: str) -> str:
    safe = key.replace("/", "_").replace("^", "")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _load_cache(key: str) -> Optional[dict]:
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        mtime = os.path.getmtime(path)
        if (datetime.now().timestamp() - mtime) > CACHE_TTL_SECONDS:
            return None
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(key: str, data: dict) -> None:
    try:
        with open(_cache_path(key), "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def _fetch_ohlcv(ticker: str, period: str = "6mo", interval: str = "1d") -> Optional[pd.DataFrame]:
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df is None or df.empty or len(df) < 30:
            return None
        # Flatten MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception:
        return None


def _dates(df: pd.DataFrame) -> list[str]:
    return [d.strftime("%Y-%m-%d") for d in df.index]


def _round(series: pd.Series, decimals: int = 2) -> list:
    return [round(float(v), decimals) if pd.notna(v) else None for v in series]


# RSI ────────────────────────────────────────────────────────────────────────

def compute_rsi(ticker: str, period: int = 14) -> Optional[dict]:
    cache_key = f"rsi_{ticker}_{period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    close = df["Close"]
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(com=period - 1, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(com=period - 1, min_periods=period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    # Find notable signals: crossings of 70/30
    signals = []
    rsi_vals = rsi.values
    dates = _dates(df)
    for i in range(1, len(rsi_vals)):
        if pd.isna(rsi_vals[i]) or pd.isna(rsi_vals[i - 1]):
            continue
        if rsi_vals[i - 1] < 70 <= rsi_vals[i]:
            signals.append({"date": dates[i], "type": "overbought", "value": round(float(rsi_vals[i]), 1)})
        elif rsi_vals[i - 1] > 30 >= rsi_vals[i]:
            signals.append({"date": dates[i], "type": "oversold", "value": round(float(rsi_vals[i]), 1)})

    result = {
        "ticker": ticker,
        "indicator": "rsi",
        "dates": dates,
        "price": _round(close),
        "rsi": _round(rsi, 1),
        "period": period,
        "signals": signals[-10:],  # last 10 signals
        "current": {
            "price": round(float(close.iloc[-1]), 2),
            "rsi": round(float(rsi.iloc[-1]), 1) if pd.notna(rsi.iloc[-1]) else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_rsi(rsi.iloc[-1] if pd.notna(rsi.iloc[-1]) else 50),
    }
    del df, close, delta, gain, loss, rs, rsi
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_rsi(val: float) -> str:
    if val >= 80:
        return "Extremely overbought — momentum is very extended. High probability of pullback or consolidation. Avoid new long entries."
    if val >= 70:
        return "Overbought territory. Momentum is strong but stretched. Watch for bearish divergence or reversal candles before shorting."
    if val >= 60:
        return "Bullish momentum. RSI is in the upper half with room to run. Trend is intact; look to buy on dips to 50-zone."
    if val >= 50:
        return "Neutral-to-bullish. RSI is above the centerline, suggesting buyers have marginal control. No strong signal."
    if val >= 40:
        return "Neutral-to-bearish. RSI below centerline; sellers are in control. Avoid aggressive longs."
    if val >= 30:
        return "Approaching oversold. Selling pressure is high but not exhausted. Watch for bullish divergence."
    if val >= 20:
        return "Oversold territory. Selling may be exhausted. Potential relief bounce likely but verify with price action."
    return "Extremely oversold — panic selling may be near exhaustion. High-risk contrarian long opportunity with tight stops."


# MACD ───────────────────────────────────────────────────────────────────────

def compute_macd(ticker: str, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[dict]:
    cache_key = f"macd_{ticker}_{fast}_{slow}_{signal}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="1y")
    if df is None:
        return None

    close = df["Close"]
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    # Keep only valid rows (after slow EMA warmup)
    valid = df.index[slow - 1:]
    dates = [d.strftime("%Y-%m-%d") for d in valid]

    # Detect crossovers
    crossovers = []
    macd_arr = macd_line[valid].values
    sig_arr = signal_line[valid].values
    for i in range(1, len(macd_arr)):
        prev_above = macd_arr[i - 1] > sig_arr[i - 1]
        curr_above = macd_arr[i] > sig_arr[i]
        if not prev_above and curr_above:
            crossovers.append({"date": dates[i], "type": "bullish"})
        elif prev_above and not curr_above:
            crossovers.append({"date": dates[i], "type": "bearish"})

    result = {
        "ticker": ticker,
        "indicator": "macd",
        "dates": dates,
        "price": _round(close[valid]),
        "macd": _round(macd_line[valid], 3),
        "signal": _round(signal_line[valid], 3),
        "histogram": _round(histogram[valid], 3),
        "params": {"fast": fast, "slow": slow, "signal": signal},
        "crossovers": crossovers[-8:],
        "current": {
            "price": round(float(close.iloc[-1]), 2),
            "macd": round(float(macd_line.iloc[-1]), 3),
            "signal": round(float(signal_line.iloc[-1]), 3),
            "histogram": round(float(histogram.iloc[-1]), 3),
            "date": dates[-1],
        },
        "interpretation": _interpret_macd(
            float(macd_line.iloc[-1]),
            float(signal_line.iloc[-1]),
            float(histogram.iloc[-1]),
        ),
    }
    del df, close, ema_fast, ema_slow, macd_line, signal_line, histogram
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_macd(macd: float, signal: float, hist: float) -> str:
    above = macd > signal
    hist_grow = hist > 0
    if above and hist_grow:
        return "MACD is above Signal and histogram is expanding — strong bullish momentum. Trend followers would hold or add longs."
    if above and not hist_grow:
        return "MACD is above Signal but histogram is shrinking — bullish trend may be losing steam. Watch for a bearish crossover."
    if not above and not hist_grow:
        return "MACD is below Signal and histogram is expanding (more negative) — strong bearish momentum. Trend followers would stay short."
    return "MACD is below Signal but histogram is shrinking (less negative) — bearish trend may be exhausting. Watch for bullish crossover."


# Bollinger Bands ─────────────────────────────────────────────────────────────

def compute_bollinger(ticker: str, window: int = 20, num_std: float = 2.0) -> Optional[dict]:
    cache_key = f"bb_{ticker}_{window}_{num_std}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    close = df["Close"]
    sma = close.rolling(window).mean()
    std = close.rolling(window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    pct_b = (close - lower) / (upper - lower)
    bandwidth = (upper - lower) / sma * 100

    valid = df.index[window - 1:]
    dates = [d.strftime("%Y-%m-%d") for d in valid]

    # Detect squeezes: bandwidth below 6-month 20th percentile
    bw_vals = bandwidth[valid].dropna()
    squeeze_thresh = float(bw_vals.quantile(0.20)) if len(bw_vals) > 10 else 0

    squeezes = []
    bw_arr = bandwidth[valid].values
    in_squeeze = False
    for i, bw in enumerate(bw_arr):
        if pd.isna(bw):
            continue
        if bw < squeeze_thresh and not in_squeeze:
            in_squeeze = True
            squeezes.append({"date": dates[i], "type": "squeeze_start"})
        elif bw >= squeeze_thresh and in_squeeze:
            in_squeeze = False
            squeezes.append({"date": dates[i], "type": "squeeze_end"})

    last_close = float(close.iloc[-1])
    last_upper = float(upper.iloc[-1])
    last_lower = float(lower.iloc[-1])
    last_sma   = float(sma.iloc[-1])

    result = {
        "ticker": ticker,
        "indicator": "bollinger",
        "dates": dates,
        "price": _round(close[valid]),
        "upper": _round(upper[valid]),
        "middle": _round(sma[valid]),
        "lower": _round(lower[valid]),
        "pct_b": _round(pct_b[valid], 3),
        "bandwidth": _round(bandwidth[valid], 2),
        "params": {"window": window, "num_std": num_std},
        "squeezes": squeezes[-6:],
        "squeeze_threshold": round(squeeze_thresh, 2),
        "current": {
            "price": round(last_close, 2),
            "upper": round(last_upper, 2),
            "middle": round(last_sma, 2),
            "lower": round(last_lower, 2),
            "pct_b": round(float(pct_b.iloc[-1]), 3) if pd.notna(pct_b.iloc[-1]) else None,
            "bandwidth": round(float(bandwidth.iloc[-1]), 2) if pd.notna(bandwidth.iloc[-1]) else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_bollinger(last_close, last_upper, last_lower, last_sma, float(bandwidth.iloc[-1])),
    }
    del df, close, sma, std, upper, lower, pct_b, bandwidth
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_bollinger(price: float, upper: float, lower: float, mid: float, bw: float) -> str:
    pct = (price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
    if pct > 0.95:
        return "Price is touching or above the upper band — overbought in the short-term. Either a strong trend (walk the band) or reversal setup depending on volume and context."
    if pct < 0.05:
        return "Price is touching or below the lower band — oversold in the short-term. Watch for a reversal candle to signal mean reversion back to the middle band."
    if 0.45 < pct < 0.55:
        return "Price is near the middle band (SMA-20) — a neutral zone. A break above or below here confirms the next short-term direction."
    if pct > 0.7:
        return "Price is in the upper half of the bands — bullish bias. The SMA-20 is support to watch."
    return "Price is in the lower half of the bands — bearish bias. The SMA-20 is resistance to watch."


# EMA / SMA ──────────────────────────────────────────────────────────────────

def compute_ema(ticker: str) -> Optional[dict]:
    cache_key = f"ema_{ticker}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="1y")
    if df is None:
        return None

    close = df["Close"]
    ema20  = close.ewm(span=20,  adjust=False).mean()
    ema50  = close.ewm(span=50,  adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    sma20  = close.rolling(20).mean()
    sma50  = close.rolling(50).mean()

    dates = _dates(df)

    # Detect golden/death crosses (50 vs 200 EMA)
    crosses = []
    e50 = ema50.values
    e200 = ema200.values
    for i in range(1, len(e50)):
        if pd.isna(e50[i]) or pd.isna(e200[i]):
            continue
        if e50[i - 1] <= e200[i - 1] and e50[i] > e200[i]:
            crosses.append({"date": dates[i], "type": "golden_cross"})
        elif e50[i - 1] >= e200[i - 1] and e50[i] < e200[i]:
            crosses.append({"date": dates[i], "type": "death_cross"})

    last_price  = float(close.iloc[-1])
    last_ema200 = float(ema200.iloc[-1])
    result = {
        "ticker": ticker,
        "indicator": "ema",
        "dates": dates,
        "price":  _round(close),
        "ema20":  _round(ema20),
        "ema50":  _round(ema50),
        "ema200": _round(ema200),
        "sma20":  _round(sma20),
        "sma50":  _round(sma50),
        "crosses": crosses[-6:],
        "current": {
            "price":  round(last_price, 2),
            "ema20":  round(float(ema20.iloc[-1]), 2),
            "ema50":  round(float(ema50.iloc[-1]), 2),
            "ema200": round(last_ema200, 2),
            "above_200": last_price > last_ema200,
            "date":   dates[-1],
        },
        "interpretation": _interpret_ema(last_price, float(ema20.iloc[-1]), float(ema50.iloc[-1]), last_ema200),
    }
    del df, close, ema20, ema50, ema200, sma20, sma50
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_ema(price: float, ema20: float, ema50: float, ema200: float) -> str:
    if price > ema20 > ema50 > ema200:
        return "Perfect bullish alignment: Price > EMA20 > EMA50 > EMA200. This is the strongest bullish structure — all time frames are trending up. Institutional trend-following systems are long."
    if price > ema50 > ema200:
        return "Price is above EMA50 and EMA200 — medium and long-term trends are bullish. Some short-term weakness may exist but the bigger picture is positive."
    if price > ema200 and price < ema50:
        return "Price is above EMA200 (long-term bullish) but below EMA50 — a potential pullback within a larger uptrend. Watch if price reclaims EMA50 as a re-entry signal."
    if price < ema200:
        return "Price is below the 200 EMA — the stock is in a long-term downtrend or bear market phase. High-risk for longs; short sellers and defensive players dominate."
    return "Mixed signal — price is near key EMAs without clear alignment. Wait for confirmation before committing directionally."


# ATR ────────────────────────────────────────────────────────────────────────

def compute_atr(ticker: str, period: int = 14) -> Optional[dict]:
    cache_key = f"atr_{ticker}_{period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    high = df["High"]
    low  = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)

    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)

    atr = tr.ewm(com=period - 1, min_periods=period).mean()

    dates = _dates(df)
    last_price = float(close.iloc[-1])
    last_atr   = float(atr.iloc[-1])
    atr_pct    = (last_atr / last_price * 100) if last_price > 0 else 0

    result = {
        "ticker": ticker,
        "indicator": "atr",
        "dates": dates,
        "price": _round(close),
        "atr":   _round(atr, 2),
        "atr_pct": _round(atr / close * 100, 2),
        "period": period,
        "current": {
            "price":   round(last_price, 2),
            "atr":     round(last_atr, 2),
            "atr_pct": round(atr_pct, 2),
            "stop_1x": round(last_price - last_atr, 2),
            "stop_15x": round(last_price - 1.5 * last_atr, 2),
            "stop_2x":  round(last_price - 2.0 * last_atr, 2),
            "date": dates[-1],
        },
        "interpretation": _interpret_atr(atr_pct),
    }
    del df, high, low, close, prev_close, tr, atr
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_atr(atr_pct: float) -> str:
    if atr_pct > 4:
        return f"ATR is {atr_pct:.1f}% of price — very high volatility. Stop losses must be wide; reduce position size significantly to maintain fixed-risk per trade."
    if atr_pct > 2.5:
        return f"ATR is {atr_pct:.1f}% of price — elevated volatility. Use 1.5–2× ATR for stop placement. This asset moves significantly day-to-day; size accordingly."
    if atr_pct > 1.5:
        return f"ATR is {atr_pct:.1f}% of price — moderate volatility, typical for large-caps. A 1.5–2× ATR stop is reasonable for swing trades."
    return f"ATR is {atr_pct:.1f}% of price — low volatility. Tight stop losses are valid here. ATM options will be cheap — good for buyers, poor for sellers."


# ── Stochastic Oscillator ────────────────────────────────────────────────────

def compute_stochastic(ticker: str, k_period: int = 14, d_period: int = 3) -> Optional[dict]:
    cache_key = f"stoch_{ticker}_{k_period}_{d_period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    high  = df["High"].rolling(k_period).max()
    low   = df["Low"].rolling(k_period).min()
    close = df["Close"]
    k = 100 * (close - low) / (high - low).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    dates = _dates(df)

    signals = []
    k_arr, d_arr = k.values, d.values
    for i in range(1, len(k_arr)):
        if pd.isna(k_arr[i]) or pd.isna(d_arr[i]):
            continue
        if k_arr[i - 1] <= d_arr[i - 1] and k_arr[i] > d_arr[i] and k_arr[i] < 30:
            signals.append({"date": dates[i], "type": "bullish_cross", "value": round(float(k_arr[i]), 1)})
        elif k_arr[i - 1] >= d_arr[i - 1] and k_arr[i] < d_arr[i] and k_arr[i] > 70:
            signals.append({"date": dates[i], "type": "bearish_cross", "value": round(float(k_arr[i]), 1)})

    last_k = float(k.iloc[-1]) if pd.notna(k.iloc[-1]) else None
    result = {
        "ticker": ticker, "indicator": "stochastic",
        "dates": dates,
        "price": _round(close),
        "k": _round(k, 1),
        "d": _round(d, 1),
        "params": {"k_period": k_period, "d_period": d_period},
        "signals": signals[-8:],
        "current": {
            "price": round(float(close.iloc[-1]), 2),
            "k": round(last_k, 1) if last_k is not None else None,
            "d": round(float(d.iloc[-1]), 1) if pd.notna(d.iloc[-1]) else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_stoch(last_k or 50),
    }
    del df, high, low, close, k, d
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_stoch(k: float) -> str:
    if k > 80:
        return f"Stochastic %K at {k:.0f} — overbought. Price is near the top of its recent range. Watch for %K to cross below %D as a sell trigger."
    if k < 20:
        return f"Stochastic %K at {k:.0f} — oversold. Price is near the bottom of its recent range. Watch for %K to cross above %D as a buy trigger."
    return f"Stochastic %K at {k:.0f} — neutral zone. No strong directional signal from Stochastic alone."


# ── OBV ───────────────────────────────────────────────────────────────────────

def compute_obv(ticker: str) -> Optional[dict]:
    cache_key = f"obv_{ticker}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    close = df["Close"]
    volume = df["Volume"]
    direction = np.where(close > close.shift(1), 1, np.where(close < close.shift(1), -1, 0))
    obv = pd.Series((direction * volume.values).cumsum(), index=df.index)
    dates = _dates(df)

    last_obv = float(obv.iloc[-1])
    obv_7d_ago = float(obv.iloc[-7]) if len(obv) > 7 else float(obv.iloc[0])
    obv_trend = "rising" if last_obv > obv_7d_ago else "falling"

    result = {
        "ticker": ticker, "indicator": "obv",
        "dates": dates,
        "price": _round(close),
        "obv": [round(float(v), 0) for v in obv],
        "current": {
            "price": round(float(close.iloc[-1]), 2),
            "obv": round(last_obv, 0),
            "obv_trend": obv_trend,
            "date": dates[-1],
        },
        "interpretation": (
            f"OBV is {obv_trend} over the last 7 sessions — "
            + ("volume is flowing into this asset, suggesting accumulation by institutions. "
               "A rising OBV before a price breakout is a leading indicator of strength."
               if obv_trend == "rising"
               else "volume is leaving this asset, suggesting distribution. "
                    "Watch for price to confirm with a breakdown.")
        ),
    }
    del df, close, volume, obv
    gc.collect()
    _save_cache(cache_key, result)
    return result


# ── ADX ───────────────────────────────────────────────────────────────────────

def compute_adx(ticker: str, period: int = 14) -> Optional[dict]:
    cache_key = f"adx_{ticker}_{period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)

    plus_dm  = (high - prev_high).clip(lower=0)
    minus_dm = (prev_low - low).clip(lower=0)
    plus_dm  = np.where(plus_dm > minus_dm, plus_dm, 0)
    minus_dm = np.where(pd.Series(minus_dm) > pd.Series(plus_dm), pd.Series(minus_dm), 0)

    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr_s = tr.ewm(com=period - 1, min_periods=period).mean()

    plus_di  = 100 * pd.Series(plus_dm, index=df.index).ewm(com=period - 1, min_periods=period).mean() / atr_s
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(com=period - 1, min_periods=period).mean() / atr_s
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan) * 100
    adx = dx.ewm(com=period - 1, min_periods=period).mean()

    dates = _dates(df)
    last_adx = float(adx.iloc[-1]) if pd.notna(adx.iloc[-1]) else None

    result = {
        "ticker": ticker, "indicator": "adx",
        "dates": dates,
        "price": _round(close),
        "adx":      _round(adx, 1),
        "plus_di":  _round(plus_di, 1),
        "minus_di": _round(minus_di, 1),
        "current": {
            "price":    round(float(close.iloc[-1]), 2),
            "adx":      round(last_adx, 1) if last_adx else None,
            "plus_di":  round(float(plus_di.iloc[-1]), 1) if pd.notna(plus_di.iloc[-1]) else None,
            "minus_di": round(float(minus_di.iloc[-1]), 1) if pd.notna(minus_di.iloc[-1]) else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_adx(last_adx or 0, float(plus_di.iloc[-1] or 0), float(minus_di.iloc[-1] or 0)),
    }
    del df, high, low, close, tr, plus_di, minus_di, dx, adx
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_adx(adx: float, pdi: float, mdi: float) -> str:
    direction = "bullish (+DI > -DI)" if pdi > mdi else "bearish (-DI > +DI)"
    if adx < 20:
        return f"ADX at {adx:.0f} — trend is weak or absent. Market is ranging. Avoid trend-following entries; mean-reversion has more edge here."
    if adx < 35:
        return f"ADX at {adx:.0f} with {direction} direction — moderate trend developing. Trend-following strategies are gaining an edge; consider entries in the trend direction."
    if adx < 50:
        return f"ADX at {adx:.0f} with {direction} — strong trend. High-confidence trend following. Stay with the trend; countertrend fades are dangerous."
    return f"ADX at {adx:.0f} with {direction} — extremely strong trend, potentially parabolic. Very high momentum but also elevated reversal risk when trend exhausts."


# ── CCI ───────────────────────────────────────────────────────────────────────

def compute_cci(ticker: str, period: int = 20) -> Optional[dict]:
    cache_key = f"cci_{ticker}_{period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    sma_tp = tp.rolling(period).mean()
    mean_dev = tp.rolling(period).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    cci = (tp - sma_tp) / (0.015 * mean_dev.replace(0, np.nan))
    dates = _dates(df)

    last_cci = float(cci.iloc[-1]) if pd.notna(cci.iloc[-1]) else None
    result = {
        "ticker": ticker, "indicator": "cci",
        "dates": dates,
        "price": _round(df["Close"]),
        "cci": _round(cci, 1),
        "current": {
            "price": round(float(df["Close"].iloc[-1]), 2),
            "cci": round(last_cci, 1) if last_cci is not None else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_cci(last_cci or 0),
    }
    del df, tp, sma_tp, mean_dev, cci
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_cci(cci: float) -> str:
    if cci > 150:
        return f"CCI at {cci:.0f} — extremely overbought. Price is significantly above its statistical average. High reversal risk; look for bearish signals to exit longs."
    if cci > 100:
        return f"CCI at {cci:.0f} — overbought zone. Strong upward momentum. Classic CCI system would look to exit longs as CCI falls back below +100."
    if cci < -150:
        return f"CCI at {cci:.0f} — extremely oversold. Price is significantly below its average. Potential high-quality bounce setup; wait for CCI to recover above -100 as entry trigger."
    if cci < -100:
        return f"CCI at {cci:.0f} — oversold zone. Strong selling pressure. Classic CCI system would look to enter longs when CCI rises back above -100."
    return f"CCI at {cci:.0f} — neutral zone (between ±100). No strong CCI signal; wait for ±100 crossover."


# ── Williams %R ───────────────────────────────────────────────────────────────

def compute_williams_r(ticker: str, period: int = 14) -> Optional[dict]:
    cache_key = f"willr_{ticker}_{period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    highest_high = df["High"].rolling(period).max()
    lowest_low   = df["Low"].rolling(period).min()
    wr = -100 * (highest_high - df["Close"]) / (highest_high - lowest_low).replace(0, np.nan)
    dates = _dates(df)

    last_wr = float(wr.iloc[-1]) if pd.notna(wr.iloc[-1]) else None
    result = {
        "ticker": ticker, "indicator": "williams_r",
        "dates": dates,
        "price": _round(df["Close"]),
        "williams_r": _round(wr, 1),
        "current": {
            "price": round(float(df["Close"].iloc[-1]), 2),
            "williams_r": round(last_wr, 1) if last_wr is not None else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_wr(last_wr or -50),
    }
    del df, highest_high, lowest_low, wr
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_wr(wr: float) -> str:
    if wr >= -20:
        return f"Williams %R at {wr:.0f} — overbought (close near the period high). Potential distribution zone. Watch for %R to turn down from this level."
    if wr <= -80:
        return f"Williams %R at {wr:.0f} — oversold (close near the period low). Potential accumulation zone. High-probability bounce setup when %R starts rising from this level."
    return f"Williams %R at {wr:.0f} — neutral zone. No strong signal. Wait for a move toward ±80 or ±20 for a tradeable extreme."


# ── ROC ───────────────────────────────────────────────────────────────────────

def compute_roc(ticker: str, period: int = 10) -> Optional[dict]:
    cache_key = f"roc_{ticker}_{period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    close = df["Close"]
    roc = ((close - close.shift(period)) / close.shift(period).replace(0, np.nan)) * 100
    dates = _dates(df)

    last_roc = float(roc.iloc[-1]) if pd.notna(roc.iloc[-1]) else None
    result = {
        "ticker": ticker, "indicator": "roc",
        "dates": dates,
        "price": _round(close),
        "roc": _round(roc, 2),
        "period": period,
        "current": {
            "price": round(float(close.iloc[-1]), 2),
            "roc": round(last_roc, 2) if last_roc is not None else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_roc(last_roc or 0),
    }
    del df, close, roc
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_roc(roc: float) -> str:
    if roc > 20:
        return f"ROC at +{roc:.1f}% — strong positive momentum. The stock is significantly higher than {10} sessions ago. Momentum is on the buyer's side."
    if roc > 5:
        return f"ROC at +{roc:.1f}% — moderate positive momentum. Trend is healthy and buyers are in control."
    if roc < -20:
        return f"ROC at {roc:.1f}% — strong negative momentum. The stock has fallen significantly. Avoid longs until momentum stabilises above -5%."
    if roc < -5:
        return f"ROC at {roc:.1f}% — moderate negative momentum. Sellers are in control. Wait for ROC to cross back above 0 before considering longs."
    return f"ROC at {roc:.1f}% — near zero. Momentum is neutral. No directional edge from ROC alone."


# ── MFI ───────────────────────────────────────────────────────────────────────

def compute_mfi(ticker: str, period: int = 14) -> Optional[dict]:
    cache_key = f"mfi_{ticker}_{period}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    df = _fetch_ohlcv(ticker, period="6mo")
    if df is None:
        return None

    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    rmf = tp * df["Volume"]
    pos_mf = rmf.where(tp > tp.shift(1), 0)
    neg_mf = rmf.where(tp < tp.shift(1), 0)
    pos_sum = pos_mf.rolling(period).sum()
    neg_sum = neg_mf.rolling(period).sum()
    mfr = pos_sum / neg_sum.replace(0, np.nan)
    mfi = 100 - (100 / (1 + mfr))
    dates = _dates(df)

    last_mfi = float(mfi.iloc[-1]) if pd.notna(mfi.iloc[-1]) else None
    result = {
        "ticker": ticker, "indicator": "mfi",
        "dates": dates,
        "price": _round(df["Close"]),
        "mfi": _round(mfi, 1),
        "current": {
            "price": round(float(df["Close"].iloc[-1]), 2),
            "mfi": round(last_mfi, 1) if last_mfi is not None else None,
            "date": dates[-1],
        },
        "interpretation": _interpret_mfi(last_mfi or 50),
    }
    del df, tp, rmf, pos_mf, neg_mf, pos_sum, neg_sum, mfr, mfi
    gc.collect()
    _save_cache(cache_key, result)
    return result


def _interpret_mfi(mfi: float) -> str:
    if mfi > 80:
        return f"MFI at {mfi:.0f} — volume-confirmed overbought. Both price and volume indicate excessive buying. Higher reversal risk than RSI alone — volume participation confirms the excess."
    if mfi < 20:
        return f"MFI at {mfi:.0f} — volume-confirmed oversold. Both price and volume indicate excessive selling. A recovery above 20 confirmed by rising price is a strong buy signal."
    return f"MFI at {mfi:.0f} — neutral. No volume-confirmed extreme. Monitor for divergence between MFI and price as an early warning of trend change."


# Option Greek curves (mathematical, not live data) ──────────────────────────

def compute_greek_curves(greek: str) -> dict:
    """Returns mathematical curve data for option Greek visualisation."""
    cache_key = f"greek_{greek}"
    cached = _load_cache(cache_key)
    if cached:
        return cached

    try:
        if greek == "delta":
            result = _delta_curves()
        elif greek == "theta":
            result = _theta_curves()
        elif greek == "gamma":
            result = _gamma_curves()
        elif greek == "vega":
            result = _vega_curves()
        else:
            return {}
    except ImportError:
        return {"error": "scipy not installed — run: pip install scipy", "greek": greek}

    _save_cache(cache_key, result)
    return result


def _delta_curves() -> dict:
    # Delta vs underlying price for call/put at different strikes
    # Using Black-Scholes simplified approximation for illustration
    from scipy.stats import norm

    def bs_delta(S, K, T, r=0.065, sigma=0.20, option="call"):
        if T <= 0:
            return 1.0 if (option == "call" and S > K) else 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return float(norm.cdf(d1)) if option == "call" else float(norm.cdf(d1) - 1)

    S_range = np.linspace(80, 120, 60)  # price as % of strike
    K = 100
    result = {
        "greek": "delta",
        "x_label": "Underlying Price (% of Strike)",
        "y_label": "Delta",
        "x": [round(float(s), 1) for s in S_range],
        "series": []
    }
    for T, label in [(0.25, "3 months"), (0.08, "1 month"), (0.02, "1 week")]:
        result["series"].append({
            "label": f"Call Δ — {label}",
            "type": "call",
            "tte": T,
            "values": [round(bs_delta(s, K, T), 3) for s in S_range],
        })
        result["series"].append({
            "label": f"Put Δ — {label}",
            "type": "put",
            "tte": T,
            "values": [round(bs_delta(s, K, T, option="put"), 3) for s in S_range],
        })
    result["annotations"] = [
        {"x": 100, "label": "ATM", "color": "#00d296"},
        {"x": 110, "label": "10% OTM (Call)", "color": "#5ab4e5"},
        {"x": 90,  "label": "10% ITM (Call)", "color": "#f59e0b"},
    ]
    return result


def _theta_curves() -> dict:
    from scipy.stats import norm

    def bs_theta(S, K, T, r=0.065, sigma=0.20):
        if T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        theta = (
            -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
            - r * K * np.exp(-r * T) * norm.cdf(d2)
        ) / 365  # daily theta
        return float(theta)

    days_range = np.linspace(90, 0.5, 100)  # days to expiry
    T_range = days_range / 365
    S, K = 100, 100  # ATM option

    atm_theta = [round(bs_theta(S, K, T), 4) for T in T_range]
    otm_theta = [round(bs_theta(S, K * 1.05, T), 4) for T in T_range]

    return {
        "greek": "theta",
        "x_label": "Days to Expiry",
        "y_label": "Daily Theta (₹ lost per day per ₹100 notional)",
        "x": [round(float(d), 1) for d in days_range],
        "series": [
            {"label": "ATM Option Theta", "values": atm_theta, "color": "#ef4444"},
            {"label": "5% OTM Option Theta", "values": otm_theta, "color": "#f59e0b"},
        ],
        "annotations": [
            {"x": 30, "label": "30 DTE — decay accelerates", "color": "#00d296"},
            {"x": 7,  "label": "7 DTE — rapid decay zone",  "color": "#ef4444"},
        ],
        "key_insight": "Notice how theta decay is NOT linear — it accelerates exponentially as expiry approaches. The last 30 days see the sharpest premium erosion.",
    }


def _gamma_curves() -> dict:
    from scipy.stats import norm

    def bs_gamma(S, K, T, r=0.065, sigma=0.20):
        if T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))

    S_range = np.linspace(80, 120, 60)
    K = 100

    result = {
        "greek": "gamma",
        "x_label": "Underlying Price (% of Strike)",
        "y_label": "Gamma",
        "x": [round(float(s), 1) for s in S_range],
        "series": [],
    }
    for T, label in [(0.25, "3 months"), (0.08, "1 month"), (0.02, "1 week")]:
        result["series"].append({
            "label": f"Gamma — {label}",
            "tte": T,
            "values": [round(bs_gamma(s, K, T), 5) for s in S_range],
        })
    result["annotations"] = [{"x": 100, "label": "ATM — Peak Gamma", "color": "#00d296"}]
    result["key_insight"] = "Gamma peaks sharply at the ATM strike and is amplified near expiry — this is why near-expiry ATM options are the most explosive (and dangerous) to hold."
    return result


def _vega_curves() -> dict:
    from scipy.stats import norm

    def bs_vega(S, K, T, r=0.065, sigma=0.20):
        if T <= 0:
            return 0.0
        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        return float(S * norm.pdf(d1) * np.sqrt(T) / 100)  # per 1% IV change

    S_range = np.linspace(80, 120, 60)
    K = 100

    result = {
        "greek": "vega",
        "x_label": "Underlying Price (% of Strike)",
        "y_label": "Vega (₹ gain per 1% IV increase per ₹100 notional)",
        "x": [round(float(s), 1) for s in S_range],
        "series": [],
    }
    for T, label in [(0.25, "3 months"), (0.08, "1 month"), (0.02, "1 week")]:
        result["series"].append({
            "label": f"Vega — {label}",
            "tte": T,
            "values": [round(bs_vega(s, K, T), 4) for s in S_range],
        })
    result["annotations"] = [{"x": 100, "label": "ATM — Peak Vega", "color": "#00d296"}]
    result["key_insight"] = "Vega is highest for longer-dated, ATM options. When IV collapses after an event (IV crush), long-dated options suffer the most. Short-dated options have low vega — they are less affected by IV changes but have high gamma risk."
    return result


# AI Tutor ────────────────────────────────────────────────────────────────────

TUTOR_SYSTEM = """You are an elite financial education AI for the StockiNews platform, equivalent to a Bloomberg Terminal education layer combined with Zerodha Varsity depth.

Your role: Explain financial concepts at CFA / professional trader level — mathematically precise, practically grounded, market-aware.

Rules:
1. Never give specific investment advice or stock recommendations.
2. Answer education questions only — what concepts mean, how they work, how professionals use them, where they fail.
3. Be technically accurate. Assume the user is a serious retail trader or finance student.
4. When explaining with numbers, use Indian market context (NIFTY, BANKNIFTY, Rupees) wherever possible.
5. Keep responses focused and structured — use short paragraphs, not walls of text.
6. If chart data is provided in the context, reference it specifically in your explanation.
7. Acknowledge nuance and limitations of every concept — avoid oversimplification.
8. Do not be a beginner tutorial. Go deep."""


async def ask_tutor(question: str, context: Optional[dict] = None) -> str:
    """Ask the AI tutor an educational question, optionally with chart context."""
    from openai import AsyncAzureOpenAI

    endpoint   = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key    = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini"))

    if not endpoint or not api_key:
        raise RuntimeError("Azure OpenAI credentials not configured — set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in backend/.env")

    client = AsyncAzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)

    user_content = question
    if context:
        ctx_str = _format_chart_context(context)
        user_content = f"[Chart context]\n{ctx_str}\n\n[Question]\n{question}"

    response = await client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": TUTOR_SYSTEM},
            {"role": "user",   "content": user_content},
        ],
        max_tokens=800,
        temperature=0.3,
    )
    await client.close()
    return response.choices[0].message.content


def _format_chart_context(ctx: dict) -> str:
    lines = []
    if "indicator" in ctx:
        lines.append(f"Indicator: {ctx['indicator'].upper()}")
    if "ticker" in ctx:
        lines.append(f"Ticker: {ctx['ticker']}")
    if "current" in ctx:
        cur = ctx["current"]
        lines.append(f"Current snapshot: {json.dumps(cur)}")
    if "interpretation" in ctx:
        lines.append(f"Auto-interpretation: {ctx['interpretation']}")
    if "signals" in ctx and ctx["signals"]:
        lines.append(f"Recent signals: {json.dumps(ctx['signals'][-3:])}")
    return "\n".join(lines)
