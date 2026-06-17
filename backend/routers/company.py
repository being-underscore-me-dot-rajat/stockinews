import logging
import requests as _req
from fastapi import APIRouter, HTTPException, Query
from services.company_catalog import load_companies, get_display_symbols
from services.ticker_data import getdata, warm_cache
from services.market_service import get_company_info, get_company_developments
from services.news_crawler import crawl_news_for_ticker_cached, SOURCES
from services.company_data import (
    get_financials, get_analysts, get_holders,
    get_earnings, get_options, get_esg,
)

router = APIRouter()
log = logging.getLogger(__name__)


@router.get("/api/companies")
def get_companies():
    companies = load_companies()
    symbols = get_display_symbols()
    return {"Symbols": symbols, "companies": companies}


@router.get("/api/companies/search")
def search_companies(q: str = Query("")):
    """
    Live company search: queries Yahoo Finance first (current listings, correct names),
    supplements with local CSV if fewer than 5 results are returned.
    """
    q = q.strip()
    if len(q) < 2:
        return {"results": []}

    results: list[dict] = []
    seen: set[str] = set()

    # ── Yahoo Finance (live) ──────────────────────────────────────────────────
    try:
        resp = _req.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": q, "quotesCount": 8, "newsCount": 0, "listsCount": 0},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=6,
        )
        for quote in resp.json().get("quotes", []):
            sym = quote.get("symbol", "")
            if not sym.endswith(".NS") or quote.get("quoteType") != "EQUITY":
                continue
            bare = sym[:-3]
            name = quote.get("longname") or quote.get("shortname") or bare
            results.append({
                "symbol": bare,
                "nse_symbol": sym,
                "name": name,
                "display": f"{bare} : {name}",
            })
            seen.add(bare)
    except Exception as exc:
        log.warning("Yahoo Finance company search failed: %s", exc)

    # ── Local CSV supplement (fast, no network) ───────────────────────────────
    if len(results) < 5:
        q_lower = q.lower()
        for c in load_companies():
            if c["symbol"] in seen:
                continue
            if q_lower in c["symbol"].lower() or q_lower in c["name"].lower():
                results.append(c)
                seen.add(c["symbol"])
            if len(results) >= 10:
                break

    return {"results": results[:10]}


@router.get("/api/chart")
def get_chart(ticker: str = Query(...), period: str = Query("7d")):
    t = ticker.split(":")[0]
    data = getdata(t, period)
    warm_cache(t)
    return data


@router.get("/api/company/info")
def company_info(ticker: str = Query(...)):
    try:
        return get_company_info(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/developments")
def company_developments(ticker: str = Query(...)):
    try:
        return get_company_developments(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/news")
def company_news(ticker: str = Query(...), limit: int = Query(15)):
    try:
        ticker = ticker.strip().upper()
        articles = crawl_news_for_ticker_cached(ticker=ticker, limit=min(limit, 50))
        return {"ticker": ticker, "articles": articles, "count": len(articles)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/financials")
def company_financials(ticker: str = Query(...)):
    try:
        return get_financials(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/analysts")
def company_analysts(ticker: str = Query(...)):
    try:
        return get_analysts(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/holders")
def company_holders(ticker: str = Query(...)):
    try:
        return get_holders(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/earnings")
def company_earnings(ticker: str = Query(...)):
    try:
        return get_earnings(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/options")
def company_options(ticker: str = Query(...)):
    try:
        return get_options(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/company/esg")
def company_esg(ticker: str = Query(...)):
    try:
        return get_esg(ticker.strip().upper())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
