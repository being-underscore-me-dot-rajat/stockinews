from fastapi import APIRouter, HTTPException, Query
from services.market_service import get_news_api_articles
from services.news_crawler import crawl_news, SOURCES

router = APIRouter()


@router.get("/news")
def get_news():
    try:
        return {"news": get_news_api_articles()}
    except Exception as exc:
        return {"news": [], "error": str(exc)}


@router.get("/api/crawler/news")
def crawl_news_route(
    source: str = Query("all"),
    query: str | None = Query(None),
    limit: int = Query(40),
):
    try:
        articles = crawl_news(source=source, limit=min(limit, 100), query=query)
        return {"articles": articles, "count": len(articles)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/api/crawler/sources")
def crawler_sources():
    return {"sources": ["all", *SOURCES.keys()]}
