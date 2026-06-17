"""
Education router — serves content catalogue and live indicator data.
All heavy computation is in services/education_service.py.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from services import education_service as svc

router = APIRouter(prefix="/education", tags=["education"])


# ── Content catalogue ─────────────────────────────────────────────────────────

@router.get("/concepts")
def list_concepts():
    return {"concepts": svc.get_concepts_list()}


@router.get("/concepts/{slug}")
def get_concept(slug: str):
    item = svc.get_concept(slug)
    if not item:
        raise HTTPException(status_code=404, detail=f"Concept '{slug}' not found")
    return item


@router.get("/indicators")
def list_indicators():
    return {"indicators": svc.get_indicators_list()}


@router.get("/indicators/{slug}")
def get_indicator(slug: str):
    item = svc.get_indicator(slug)
    if not item:
        raise HTTPException(status_code=404, detail=f"Indicator '{slug}' not found")
    return item


@router.get("/options")
def list_options():
    return {"options": svc.get_options_list()}


@router.get("/options/{slug}")
def get_option_topic(slug: str):
    item = svc.get_option_topic(slug)
    if not item:
        raise HTTPException(status_code=404, detail=f"Options topic '{slug}' not found")
    return item


# ── Live indicator chart data ─────────────────────────────────────────────────

@router.get("/chart/rsi")
def chart_rsi(
    ticker: str = Query(default="^NSEI", description="Yahoo Finance ticker"),
    period: int = Query(default=14, ge=5, le=30),
):
    data = svc.compute_rsi(ticker, period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/macd")
def chart_macd(
    ticker: str = Query(default="^NSEI"),
    fast: int = Query(default=12, ge=5, le=50),
    slow: int = Query(default=26, ge=10, le=100),
    signal: int = Query(default=9, ge=3, le=20),
):
    if fast >= slow:
        raise HTTPException(status_code=422, detail="fast must be less than slow")
    data = svc.compute_macd(ticker, fast, slow, signal)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/bollinger")
def chart_bollinger(
    ticker: str = Query(default="^NSEI"),
    window: int = Query(default=20, ge=5, le=50),
    num_std: float = Query(default=2.0, ge=1.0, le=3.0),
):
    data = svc.compute_bollinger(ticker, window, num_std)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/ema")
def chart_ema(ticker: str = Query(default="^NSEI")):
    data = svc.compute_ema(ticker)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/atr")
def chart_atr(
    ticker: str = Query(default="^NSEI"),
    period: int = Query(default=14, ge=5, le=30),
):
    data = svc.compute_atr(ticker, period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/stochastic")
def chart_stochastic(
    ticker: str = Query(default="^NSEI"),
    k_period: int = Query(default=14, ge=5, le=30),
    d_period: int = Query(default=3, ge=1, le=10),
):
    data = svc.compute_stochastic(ticker, k_period, d_period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/obv")
def chart_obv(ticker: str = Query(default="^NSEI")):
    data = svc.compute_obv(ticker)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/adx")
def chart_adx(
    ticker: str = Query(default="^NSEI"),
    period: int = Query(default=14, ge=5, le=30),
):
    data = svc.compute_adx(ticker, period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/cci")
def chart_cci(
    ticker: str = Query(default="^NSEI"),
    period: int = Query(default=20, ge=5, le=50),
):
    data = svc.compute_cci(ticker, period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/williams-r")
def chart_williams_r(
    ticker: str = Query(default="^NSEI"),
    period: int = Query(default=14, ge=5, le=30),
):
    data = svc.compute_williams_r(ticker, period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/roc")
def chart_roc(
    ticker: str = Query(default="^NSEI"),
    period: int = Query(default=10, ge=3, le=50),
):
    data = svc.compute_roc(ticker, period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/mfi")
def chart_mfi(
    ticker: str = Query(default="^NSEI"),
    period: int = Query(default=14, ge=5, le=30),
):
    data = svc.compute_mfi(ticker, period)
    if not data:
        raise HTTPException(status_code=503, detail="Could not fetch market data")
    return data


@router.get("/chart/greek/{greek_name}")
def chart_greek(greek_name: str):
    valid = {"delta", "theta", "gamma", "vega"}
    if greek_name not in valid:
        raise HTTPException(status_code=404, detail=f"Greek must be one of: {', '.join(valid)}")
    data = svc.compute_greek_curves(greek_name)
    if not data:
        raise HTTPException(status_code=503, detail="Could not compute Greek curves")
    return data


# ── AI Tutor ──────────────────────────────────────────────────────────────────

class TutorRequest(BaseModel):
    question: str
    context: Optional[dict] = None  # chart data or concept context


@router.post("/ask")
async def ask_tutor(body: TutorRequest):
    if not body.question or not body.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")
    if len(body.question) > 1000:
        raise HTTPException(status_code=422, detail="Question too long (max 1000 chars)")

    try:
        answer = await svc.ask_tutor(body.question.strip(), body.context)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Tutor unavailable: {str(e)}")
