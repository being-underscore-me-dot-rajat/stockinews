from fastapi import APIRouter, Depends, HTTPException
from models.schemas import WatchlistAdd
from services.auth_utils import get_current_user
from services.supabase_client import supabase_admin
from services.company_catalog import normalize_nse_symbol
from services.market_service import get_watchlist_quotes

router = APIRouter()


@router.get("/watchlist")
def get_watchlist(user=Depends(get_current_user)):
    user_id = user["sub"]
    rows = supabase_admin.table("watchlist").select("ticker").eq("user_id", user_id).execute().data or []
    raw_symbols = [r["ticker"] for r in rows]

    normalized = []
    for raw in raw_symbols:
        ns = normalize_nse_symbol(raw)
        if ns and ns != raw:
            supabase_admin.table("watchlist").update({"ticker": ns}).eq("user_id", user_id).eq("ticker", raw).execute()
        if ns and ns not in normalized:
            normalized.append(ns)

    if not normalized:
        return []
    return get_watchlist_quotes(normalized)


@router.post("/watchlist", status_code=201)
def add_to_watchlist(body: WatchlistAdd, user=Depends(get_current_user)):
    user_id = user["sub"]
    ticker = normalize_nse_symbol(body.symbol)
    if not ticker:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    try:
        supabase_admin.table("watchlist").insert({"user_id": user_id, "ticker": ticker}).execute()
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(status_code=400, detail="Already in watchlist")
        raise HTTPException(status_code=500, detail=str(exc))
    return {"message": "Added to watchlist"}


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, user=Depends(get_current_user)):
    user_id = user["sub"]
    ticker = normalize_nse_symbol(symbol) or symbol
    supabase_admin.table("watchlist").delete().eq("user_id", user_id).eq("ticker", ticker).execute()
    return {"message": "Removed from watchlist"}
