"""
News crawler — ported from src/backend/news_crawler.py.
Only change: imports updated for the new package structure.
"""
import hashlib
import html
import json
import logging
import re
import time
import xml.etree.ElementTree as ET

log = logging.getLogger(__name__)
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .company_catalog import load_companies

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / ".cache" / "company_news"
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 8
MAX_ARTICLE_CHARS = 12000

_NOISE_PATTERN = re.compile(
    r"ad[s\-_]?(?:unit|box|slot|widget)?|advertisement|sponsor(?:ed)?"
    r"|promo(?:tion)?|sidebar|widget|related[-_]?(?:articles?|news|stories|posts?)"
    r"|social[-_]?(?:share|media|links?)|share[-_]?button"
    r"|newsletter|subscription|popup|modal|cookie[-_]?(?:banner|notice)?"
    r"|outbrain|taboola|mgid|revcontent|sticky[-_]?(?:ad|bar)?",
    re.I,
)


@dataclass(frozen=True)
class Source:
    name: str
    kind: str
    urls: tuple[str, ...]


SOURCES = {
    "economic_times": Source(
        name="Economic Times", kind="rss",
        urls=(
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
            "https://economictimes.indiatimes.com/news/economy/rssfeeds/1373380680.cms",
            "https://economictimes.indiatimes.com/news/company/rssfeeds/2143429.cms",
            "https://economictimes.indiatimes.com/news/defence/rssfeeds/49847392.cms",
            "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
            "https://economictimes.indiatimes.com/markets/commodities/rssfeeds/1808152121.cms",
        ),
    ),
    "rbi": Source(
        name="Reserve Bank of India", kind="rss",
        urls=(
            "https://rbi.org.in/pressreleases_rss.xml",
            "https://rbi.org.in/notifications_rss.xml",
            "https://rbi.org.in/speeches_rss.xml",
        ),
    ),
    "google_news": Source(
        name="Google News", kind="rss",
        urls=(
            # Market overview
            "https://news.google.com/rss/search?q=india+stock+market+nse+bse&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+quarterly+results+earnings+profit&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+ipo+fundraise+investment+2025&hl=en-IN&gl=IN&ceid=IN:en",
            # Corporate actions — the layer that catches MAZDOCK-type stories
            "https://news.google.com/rss/search?q=india+merger+acquisition+corporate+deal&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+psu+disinvestment+government+stake+nse&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+company+contract+order+win+billion&hl=en-IN&gl=IN&ceid=IN:en",
            # Sectors
            "https://news.google.com/rss/search?q=india+defence+shipbuilding+aerospace+naval&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+infrastructure+capex+railway+port+road&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+banking+nbfc+rbi+rate+credit&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+pharma+biotech+drug+approval&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+it+software+technology+export+deal&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+steel+metals+mining+commodity&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=india+fmcg+consumer+retail+ecommerce&hl=en-IN&gl=IN&ceid=IN:en",
            # Proxy for Business Standard and Moneycontrol (both block direct RSS)
            "https://news.google.com/rss/search?q=site:business-standard.com+india+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=site:moneycontrol.com+india+stock+nse&hl=en-IN&gl=IN&ceid=IN:en",
        ),
    ),
    "mint": Source(
        name="Mint", kind="listing",
        urls=(
            "https://www.livemint.com/market",
            "https://www.livemint.com/companies",
            "https://www.livemint.com/economy",
            "https://www.livemint.com/industry",
            "https://www.livemint.com/politics",
        ),
    ),
}

SECTOR_KEYWORDS = {
    "Banking": ("bank", "nbfc", "loan", "credit", "deposit", "rbi", "lender"),
    "Information Technology": ("software", "it services", "technology", "ai", "cloud", "semiconductor"),
    "Pharma": ("pharma", "drug", "medicine", "vaccine", "healthcare", "hospital"),
    "Auto": ("auto", "vehicle", "ev", "car", "two-wheeler", "automobile"),
    "Energy": ("oil", "gas", "power", "renewable", "solar", "energy", "coal"),
    "Telecom": ("telecom", "5g", "spectrum", "broadband"),
    "Metals": ("steel", "metal", "aluminium", "copper", "mining"),
    "Real Estate": ("real estate", "housing", "property", "reit"),
    "FMCG": ("fmcg", "consumer", "retail", "qsr"),
    "Capital Markets": ("nifty", "sensex", "equity", "ipo", "stock", "market", "shares"),
    "Defence & Aerospace": ("defence", "defense", "military", "shipbuilding", "shipyard", "naval",
                            "drdo", "hal", "beml", "mazagon", "mazdock", "bharat", "ordnance",
                            "aerospace", "missile", "warship", "frigate", "submarine"),
    "Infrastructure": ("infrastructure", "railway", "port", "airport", "highway", "road", "bridge",
                       "capex", "project", "tender", "construction", "epc", "l1 bid"),
}

IGNORED_SYMBOL_WORDS = {"TOTAL", "RETAIL", "NEXT", "THE", "AND", "FOR", "BANKINDIA"}


def _resolve_item(item: dict, min_summary_len: int = 0) -> tuple[dict, str]:
    """
    Return (article_data, resolved_url).
    If min_summary_len > 0 and the RSS description is already that long, skip the
    full HTTP fetch and use the feed text directly (dev mode optimisation).
    In prod mode (min_summary_len=0) the full article is always fetched.
    """
    url = _canonical_url(item.get("url", ""))
    summary = _clean_text(item.get("summary", ""))
    if min_summary_len > 0 and len(summary) >= min_summary_len:
        return {
            "title": _clean_text(item.get("title", "")),
            "source": item.get("source") or _source_from_url(url),
            "published_at": _normalize_datetime(item.get("published_at")),
            "article_text": summary,
            "resolved_url": url,
        }, url
    fetched = _fetch_article(url)
    resolved = _canonical_url(fetched.get("resolved_url", "")) or url
    return fetched, resolved


def crawl_news(
    source: str = "all",
    limit: int = 40,
    query: str | None = None,
    min_summary_len: int = 0,
) -> list[dict]:
    selected = _select_sources(source)
    companies = _load_companies()
    discovered = []
    for src in selected:
        if src.kind == "rss":
            discovered.extend(_discover_from_rss(src, limit))
        else:
            discovered.extend(_discover_from_listing(src, limit))

    articles, seen_urls = [], set()
    for item in discovered:
        url = _canonical_url(item.get("url", ""))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        title = _clean_text(item.get("title", ""))
        article, resolved_url = _resolve_item(item, min_summary_len)
        if resolved_url != url:
            if resolved_url in seen_urls:
                continue
            seen_urls.add(resolved_url)
        article_text = article.get("article_text") or _clean_text(item.get("summary", ""))
        combined = " ".join([title, article_text, _clean_text(item.get("summary", ""))])
        if query and query.lower() not in combined.lower():
            continue
        source_name = item.get("source") or article.get("source") or _source_from_url(resolved_url)
        articles.append({
            "title": title or article.get("title", ""),
            "source": source_name,
            "published_at": _normalize_datetime(item.get("published_at") or article.get("published_at")),
            "companies": _detect_companies(title, article_text, companies),
            "sector": _detect_sector(combined),
            "url": resolved_url,
            "article_text": article_text[:MAX_ARTICLE_CHARS],
            "summary": _summarize(article_text or item.get("summary", "")),
        })
        if len(articles) >= limit:
            break
        time.sleep(0.05)
    return articles


def crawl_news_for_ticker(ticker: str, limit: int = 20, min_summary_len: int = 0) -> list[dict]:
    companies = _load_companies()
    ticker_upper = ticker.upper().replace(".NS", "")
    entry = next((c for c in companies if c["symbol"].upper() == ticker_upper), None)
    company_name = entry["name"] if entry else ticker_upper
    short_name = _company_short_name(_normalize_for_match(company_name)).title()
    search_term = short_name if len(short_name) >= 4 else company_name

    from urllib.parse import urlencode
    encoded_q = urlencode({"q": f"{search_term} NSE India", "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
    src = Source(name="Google News", kind="rss", urls=(f"https://news.google.com/rss/search?{encoded_q}",))
    discovered = _discover_from_rss(src, limit * 2)

    articles, seen_urls = [], set()
    for item in discovered:
        url = _canonical_url(item.get("url", ""))
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        title = _clean_text(item.get("title", ""))
        article, resolved_url = _resolve_item(item, min_summary_len)
        if resolved_url != url:
            if resolved_url in seen_urls:
                continue
            seen_urls.add(resolved_url)
        article_text = article.get("article_text") or _clean_text(item.get("summary", ""))
        articles.append({
            "title": title or article.get("title", ""),
            "source": item.get("source") or article.get("source") or _source_from_url(resolved_url),
            "published_at": _normalize_datetime(item.get("published_at") or article.get("published_at")),
            "ticker": ticker_upper,
            "sector": _detect_sector(article_text),
            "url": resolved_url,
            "article_text": article_text[:MAX_ARTICLE_CHARS],
            "summary": _summarize(article_text or item.get("summary", "")),
        })
        if len(articles) >= limit:
            break
        time.sleep(0.05)
    return articles


def crawl_news_for_ticker_cached(ticker: str, limit: int = 20) -> list[dict]:
    ticker_upper = ticker.upper().replace(".NS", "")
    cache_path = _company_news_cache_path(ticker_upper, limit)
    cached = _read_json_cache(cache_path)
    if cached is not None:
        return cached
    articles = crawl_news_for_ticker(ticker=ticker_upper, limit=limit)
    _write_json_cache(cache_path, articles)
    _delete_expired_cache_files(CACHE_DIR)
    return articles


def _company_news_cache_path(ticker: str, limit: int) -> Path:
    safe = re.sub(r"[^A-Z0-9._-]", "_", ticker.upper())
    return CACHE_DIR / f"{safe}_{limit}.json"


def _read_json_cache(path: Path):
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > CACHE_TTL_SECONDS:
        try:
            path.unlink()
        except OSError:
            pass
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_json_cache(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _delete_expired_cache_files(cache_dir: Path) -> None:
    if not cache_dir.exists():
        return
    cutoff = time.time() - CACHE_TTL_SECONDS
    for path in cache_dir.glob("*.json"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            pass


def _select_sources(source: str) -> list[Source]:
    if not source or source == "all":
        return list(SOURCES.values())
    key = source.strip().lower()
    if key not in SOURCES:
        raise ValueError(f"Unknown source '{source}'. Use: all, {', '.join(SOURCES)}")
    return [SOURCES[key]]


def _load_companies() -> list[dict]:
    return [{"symbol": c["symbol"], "name": c["name"]} for c in load_companies()]


def _discover_from_rss(source: Source, limit: int) -> list[dict]:
    items = []
    for feed_url in source.urls:
        try:
            root = ET.fromstring(_get(feed_url).content)
            for entry in root.findall(".//item"):
                url = _xml_text(entry, "link") or _xml_text(entry, "guid")
                source_el = entry.find("source")
                source_name = (_clean_text(source_el.text)
                               if source_el is not None and source_el.text else source.name)
                items.append({
                    "title": _xml_text(entry, "title"), "url": url,
                    "summary": _xml_text(entry, "description"),
                    "published_at": _xml_text(entry, "pubDate"), "source": source_name,
                })
                if len(items) >= limit:
                    return items
        except Exception as exc:
            log.warning("RSS failed %s: %s", feed_url, exc)
    return items


def _discover_from_listing(source: Source, limit: int) -> list[dict]:
    items = []
    for listing_url in source.urls:
        try:
            soup = BeautifulSoup(_get(listing_url).text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = urljoin(listing_url, link["href"])
                if not _looks_like_article_url(href):
                    continue
                title = _clean_text(link.get_text(" "))
                if len(title) < 12:
                    title = _clean_text(link.get("title", ""))
                if len(title) < 12:
                    continue
                items.append({"title": title, "url": href, "source": source.name})
                if len(items) >= limit:
                    return _dedupe(items)
        except Exception as exc:
            log.warning("Listing failed %s: %s", listing_url, exc)
    return _dedupe(items)


def _fetch_article(url: str) -> dict:
    try:
        response = _get(url)
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as exc:
        log.warning("Article fetch failed %s: %s", url, exc)
        return {}
    _remove_noise(soup)
    title = _meta_content(soup, "og:title") or (_clean_text(soup.title.get_text(" ")) if soup.title else "")
    published_at = (_meta_content(soup, "article:published_time")
                    or _meta_content(soup, "pubdate") or _meta_content(soup, "publish-date"))
    source = _meta_content(soup, "og:site_name") or _source_from_url(url)
    node = (soup.find("article") or soup.find("main")
            or soup.find("div", class_=re.compile(r"article|story|content", re.I)))
    return {
        "title": _clean_text(title), "source": _clean_text(source),
        "published_at": _normalize_datetime(published_at),
        "article_text": _paragraph_text(node or soup),
        "resolved_url": _canonical_url(response.url) or url,
    }


def _remove_noise(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "form", "nav", "footer", "header", "aside"]):
        tag.decompose()
    for tag in soup.find_all(True, attrs={"class": _NOISE_PATTERN}):
        tag.decompose()
    for tag in soup.find_all(True, attrs={"id": _NOISE_PATTERN}):
        tag.decompose()
    for tag in soup.find_all(True, attrs={"aria-label": re.compile(r"advertisement|sponsored", re.I)}):
        tag.decompose()


def _paragraph_text(node) -> str:
    paragraphs = []
    for p in node.find_all(["p", "li"]):
        text = _clean_text(p.get_text(" "))
        if len(text) >= 40 and not _is_boilerplate(text):
            paragraphs.append(text)
    return "\n\n".join(paragraphs)[:MAX_ARTICLE_CHARS]


def _detect_companies(title, body, companies, max_matches=5):
    clean_title = re.sub(r"\bReserve Bank of India\b|\bRBI\b", " ", title, flags=re.I)
    clean_body = re.sub(r"\bReserve Bank of India\b|\bRBI\b", " ", body, flags=re.I)
    norm_title = f" {_normalize_for_match(clean_title)} "
    norm_body = f" {_normalize_for_match(clean_body)} "
    matches = []
    for c in companies:
        name = _normalize_for_match(c["name"])
        short = _company_short_name(name)
        sym = c["symbol"]
        in_title = (_contains_token(norm_title, name) or _symbol_in_text(clean_title, sym)
                    or (len(short) >= 4 and _contains_token(norm_title, short)))
        body_hits = sum([_contains_token(norm_body, name), bool(_symbol_in_text(clean_body, sym)),
                         int(len(short) >= 4 and _contains_token(norm_body, short))])
        if in_title or body_hits >= 2:
            matches.append(sym)
        if len(matches) >= max_matches:
            break
    return matches


def _detect_sector(text: str) -> str:
    lowered = text.lower()
    scores = {s: sum(1 for kw in kws if kw in lowered) for s, kws in SECTOR_KEYWORDS.items()}
    sector, score = max(scores.items(), key=lambda x: x[1])
    return sector if score else ""


def _summarize(text: str, max_sentences: int = 2) -> str:
    cleaned = _clean_text(text)
    if not cleaned:
        return ""
    return " ".join(re.split(r"(?<=[.!?])\s+", cleaned)[:max_sentences]).strip()[:700]


def _normalize_datetime(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except (TypeError, ValueError):
        return _clean_text(value)


def _xml_text(entry: ET.Element, tag_name: str) -> str:
    node = entry.find(tag_name)
    if node is None or node.text is None:
        return ""
    raw = html.unescape(node.text)
    text = BeautifulSoup(raw, "html.parser").get_text(" ") if "<" in raw else raw
    return _clean_text(text)


def _meta_content(soup: BeautifulSoup, key: str) -> str:
    tag = soup.find("meta", property=key) or soup.find("meta", attrs={"name": key})
    return _clean_text(tag.get("content", "")) if tag else ""


def _get(url: str) -> requests.Response:
    r = requests.get(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
    }, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r


def _dedupe(items: Iterable[dict]) -> list[dict]:
    deduped, seen = [], set()
    for item in items:
        url = _canonical_url(item.get("url", ""))
        if not url or url in seen:
            continue
        seen.add(url)
        deduped.append(item)
    return deduped


def _canonical_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return ""
    if parsed.netloc.lower() == "www.rbi.org.in":
        parsed = parsed._replace(scheme="https", netloc="rbi.org.in")
    filtered_q = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                  if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}]
    return parsed._replace(fragment="", query=urlencode(filtered_q)).geturl()


def _looks_like_article_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    path = parsed.path.lower()
    if any(s in path for s in ("/video", "/photos", "/web-stories", "/podcast", "/login",
                                "/tag/", "/author/", "/search", "/rss", "/feed")):
        return False
    return (path.endswith(".html") or "/news/" in path or "/market/" in path
            or "/companies/" in path or "/economy/" in path or "/industry/" in path
            or "/article/" in path or "/story/" in path or "/stocks/" in path
            or "/business/" in path or "/finance/" in path)


def _source_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    return {
        "economictimes.indiatimes.com": "Economic Times",
        "moneycontrol.com": "Moneycontrol",
        "livemint.com": "Mint",
        "rbi.org.in": "Reserve Bank of India",
        "news.google.com": "Google News",
        "business-standard.com": "Business Standard",
        "ndtvprofit.com": "NDTV Profit",
        "thehindubusinessline.com": "BusinessLine",
        "financialexpress.com": "Financial Express",
        "thehindu.com": "The Hindu",
        "reuters.com": "Reuters",
        "bloombergquint.com": "BQ Prime",
        "bqprime.com": "BQ Prime",
    }.get(host, host)


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", html.unescape(str(value))).strip()


def _normalize_for_match(value: str) -> str:
    value = value.lower()
    value = re.sub(r"&", " and ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _company_short_name(name: str) -> str:
    removable = (" limited", " ltd", " private", " india", " corporation", " company", " co ")
    short = f" {name} "
    for word in removable:
        short = short.replace(word, " ")
    return re.sub(r"\s+", " ", short).strip()


def _contains_token(haystack: str, needle: str) -> bool:
    return bool(needle) and f" {needle} " in haystack


def _symbol_in_text(text: str, symbol: str) -> bool:
    if len(symbol) < 3 or symbol.upper() in IGNORED_SYMBOL_WORDS:
        return False
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(symbol)}(?![A-Za-z0-9])", text) is not None


def _is_boilerplate(text: str) -> bool:
    lowered = text.lower()
    return any(w in lowered for w in ("subscribe", "advertisement", "download app",
                                      "follow us", "log in", "sign up", "read more", "terms of use"))
