import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.auth_utils import get_current_user
from services.supabase_client import supabase_admin
from services.agent_service import run_agent

router = APIRouter()
log = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    ticker: str
    question: str


class PortfolioQueryRequest(BaseModel):
    question: str


@router.post("/api/agent/query")
def agent_query(body: QueryRequest, user=Depends(get_current_user)):
    """Ask a question about a specific stock."""
    try:
        return run_agent(
            question=body.question,
            ticker=body.ticker,
            tickers=[body.ticker],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        log.exception("agent/query failed")
        raise HTTPException(status_code=500, detail="Agent request failed")


@router.post("/api/agent/portfolio")
def agent_portfolio(body: PortfolioQueryRequest, user=Depends(get_current_user)):
    """Ask a question about the user's portfolio."""
    user_id = user["sub"]
    rows = supabase_admin.rpc("get_user_portfolio", {"p_user_id": user_id}).execute().data or []
    if not rows:
        return {
            "sentiment": "Neutral",
            "confidence": 0.0,
            "key_themes": [],
            "directional_impact": "No portfolio holdings to analyze.",
            "sources": [],
            "summary": "Your portfolio is empty. Add stocks to get AI-powered analysis.",
        }

    # Pass top 5 tickers by quantity so live news is pre-fetched for the most significant holdings
    sorted_rows = sorted(rows, key=lambda r: int(r.get("net_quantity", 0)), reverse=True)
    top_tickers = [r["ticker"] for r in sorted_rows[:5]]
    holdings = ", ".join(
        f"{r['ticker']} ({r['net_quantity']} shares)" for r in rows
    )

    try:
        return run_agent(
            question=body.question,
            portfolio_context=f"Current holdings: {holdings}",
            tickers=top_tickers,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        log.exception("agent/portfolio failed")
        raise HTTPException(status_code=500, detail="Agent request failed")


@router.get("/api/agent/briefing")
def agent_briefing(user=Depends(get_current_user)):
    """Generate a daily market briefing for the user's watchlist."""
    user_id = user["sub"]
    rows = (supabase_admin.table("watchlist")
            .select("ticker").eq("user_id", user_id).execute().data or [])
    tickers = [r["ticker"] for r in rows]

    if not tickers:
        return {
            "sentiment": "Neutral",
            "confidence": 0.0,
            "key_themes": [],
            "directional_impact": "Add stocks to your watchlist for a personalised briefing.",
            "sources": [],
            "summary": "Your watchlist is empty. Add NSE stocks to receive a daily AI briefing.",
        }

    ticker_list = ", ".join(tickers[:8])
    question = (
        f"Give me a market briefing for my watchlist: {ticker_list}. "
        "What is the overall sentiment, any significant news, and what should I watch out for?"
    )

    try:
        return run_agent(
            question=question,
            tickers=tickers[:5],   # pre-fetch live news for first 5
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        log.exception("agent/briefing failed")
        raise HTTPException(status_code=500, detail="Briefing generation failed")
