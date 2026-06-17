# StockiNews — Rebuild & Expansion Plan

## Vision

Move from a Flask + SQLite prototype to a production-grade financial intelligence platform.  
The end state is a site that covers the full research loop: market data → news ingestion → AI-powered sentiment and outcome analysis → personalised portfolio insights.

Inspiration: Moneycontrol, Yahoo Finance, Groww.

---

## Stack Decisions (pending confirmation)

| Layer | Current | Target | Notes |
|---|---|---|---|
| Backend framework | Flask | **FastAPI** | Keeps Python ecosystem (yfinance, pandas, BS4). Async, OpenAPI docs, Pydantic validation. |
| Database | SQLite | **Supabase (PostgreSQL)** | Relational data + pgvector extension in one service. Built-in Auth replaces hand-rolled JWT. |
| Vector store | None | **pgvector** (via Supabase) | Avoids separate infra. Use `hnsw` index for ANN search. |
| Embedding model | None | **TBD** — OpenAI `text-embedding-3-small` or local `BAAI/bge-small-en` | Model choice locks in vector dimensions — decide once. |
| AI agent | BERT (legacy) | **Claude API** (Anthropic) | Tool-use for grounded, cited responses. Foundry integration later. |
| Auth | Custom JWT + bcrypt | **Supabase Auth** | Removes hand-rolled token management. |
| Frontend | React 19 + Vite | React 19 + Vite (unchanged) | Only API endpoint URLs and auth flow need updating. |
| Firebase | In package.json, unused | **Remove** | Replace entirely with Supabase Auth. |

> Open questions before Phase 1 starts:
> 1. FastAPI confirmed, or switch to Express?
> 2. Supabase confirmed, or MongoDB + Pinecone?
> 3. Embedding model — OpenAI (API cost) or local (self-hosted)?
> 4. Firebase — remove entirely?

---

## Phases

### Phase 1 — Backend Migration

#### 1a — Supabase schema + FastAPI skeleton (no feature changes)

- Provision Supabase project, enable pgvector extension.
- Migrate schema: `users`, `stocks` (portfolio transactions), `watchlist`, `newscache`.
- Implement Supabase Auth (replaces `auth.py` + JWT middleware).
- FastAPI skeleton with same route surface as current Flask app (`/login`, `/signup`, `/me`, `/portfolio`, `/watchlist`, `/marketwatch`, `/news`, `/api/*`).
- Update frontend: swap `localStorage` token for Supabase session, update base URL.

#### 1b — Migrate all existing endpoints

- Port `portfolios.py`, `get.py`, `ticker_data.py`, `companies.py`, `news_crawler.py` to FastAPI routers.
- Retire legacy `get.py::get_portfolio` (the `AVG`-based one); keep only `portfolios.py` logic.
- Retire `Details.py` BERT sentiment (superseded by Phase 4).
- Retire `/api/details` route.

---

### Phase 2 — Yahoo Finance — Full Data Extraction

Currently using ~20% of what yfinance exposes. Expand the company page into a full research terminal.

#### New data to extract and display

| Data | yfinance call | UI section |
|---|---|---|
| Income statement (annual + quarterly) | `stock.financials`, `stock.quarterly_financials` | Financials tab |
| Balance sheet | `stock.balance_sheet`, `stock.quarterly_balance_sheet` | Financials tab |
| Cash flow | `stock.cashflow`, `stock.quarterly_cashflow` | Financials tab |
| Analyst recommendations (buy/sell/hold) | `stock.recommendations` | Analyst section |
| Upgrades & downgrades history | `stock.upgrades_downgrades` | Analyst section |
| EPS & revenue estimates | `stock.analysis` | Estimates section |
| Major holders + institutional holders | `stock.major_holders`, `stock.institutional_holders` | Shareholding section |
| Insider transactions | `stock.insider_transactions` | Insider Activity section |
| Options chain | `stock.options` | Options tab |
| ESG / sustainability scores | `stock.sustainability` | ESG section |
| Earnings history | `stock.earnings_history` | Earnings tab |
| Dividend history | `stock.dividends` | Dividends chart |

#### New backend routes
```
GET /api/company/financials?ticker=RELIANCE
GET /api/company/analysts?ticker=RELIANCE
GET /api/company/holders?ticker=RELIANCE
GET /api/company/earnings?ticker=RELIANCE
GET /api/company/options?ticker=RELIANCE
GET /api/company/esg?ticker=RELIANCE
```

#### Frontend
- Tabbed layout on the company page: Overview · Financials · Analysts · Holders · Earnings · News · Options
- Charts for financials (quarterly revenue/profit bars), dividend yield trend, earnings beat/miss history.

---

### Phase 3 — News Ingestion Pipeline

A server-side pipeline that continuously harvests, cleans, and stores news into a vector DB.

#### Pipeline stages

```
Crawl → Clean → Chunk → Embed → Store
```

**1. Crawl**  
Extend `news_crawler.py` with source adapters:
- `economic_times_adapter.py` — RSS (already partially done)
- `moneycontrol_adapter.py` — HTML listing scraper
- `mint_adapter.py` — HTML listing scraper (partially done)
- `rbi_adapter.py` — RSS (already partially done)
- `bse_adapter.py` — BSE corporate announcements XML feed
- `nse_adapter.py` — NSE circulars RSS

Each adapter emits a normalized article object:
```json
{
  "title": "",
  "source": "",
  "published_at": "",
  "companies": [],
  "sector": "",
  "url": "",
  "article_text": "",
  "summary": "",
  "embedding": []
}
```

**2. Clean**  
- Strip HTML, remove boilerplate (ads, nav, cookie banners)
- Deduplicate by URL hash and fuzzy title similarity
- Language detection (keep `en` only)
- Normalize timestamps to UTC ISO 8601

**3. Chunk**  
- Split article text into ~512-token overlapping chunks (overlap: ~64 tokens)
- Each chunk carries parent article metadata (ticker list, source, published_at, url)

**4. Embed**  
- Generate dense vectors per chunk using the chosen embedding model
- Vector dimensions must match pgvector column definition

**5. Store**  
pgvector table schema:
```sql
CREATE TABLE article_chunks (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id  uuid NOT NULL,
    tickers     text[],
    sector      text,
    source      text,
    published_at timestamptz,
    url         text,
    chunk_text  text,
    embedding   vector(1536),   -- adjust dim to match embedding model
    created_at  timestamptz DEFAULT now()
);

CREATE INDEX ON article_chunks USING hnsw (embedding vector_cosine_ops);
```

**Scheduler**  
APScheduler (or a FastAPI lifespan background task) runs the pipeline every 3–6 hours.  
Tracks seen URLs in a `crawled_urls` table to avoid reprocessing.

---

### Phase 4 — AI Agent (RAG + Claude)

Once vectors are populated, the agent answers user queries grounded in real articles and live market data.

#### Request flow

```
User query
    → embed query
    → pgvector cosine-similarity search (filter by ticker + recency)
    → top-k chunks retrieved
    → Claude API call with tool use
    → structured response
```

#### Claude tools
- `get_stock_info(ticker)` — calls `/api/company/info`
- `get_financials(ticker)` — calls `/api/company/financials`
- `search_news(query, ticker, limit)` — vector similarity search
- `get_portfolio(user_id)` — user's current holdings

#### Response format
```json
{
  "sentiment": "Bullish | Bearish | Neutral",
  "confidence": 0.82,
  "key_themes": ["earnings beat", "FII outflow", "margin expansion"],
  "directional_impact": "Likely upward pressure on price in near term",
  "sources": [
    { "title": "...", "source": "Economic Times", "url": "...", "published_at": "..." }
  ],
  "summary": "..."
}
```

#### New endpoints
```
POST /api/agent/query        — { ticker, question }
POST /api/agent/portfolio    — { question } (uses user's portfolio as context)
GET  /api/agent/briefing     — daily market briefing for user's watchlist
```

#### Frontend
- Chat-style panel on the company page and portfolio page
- Daily briefing card on the dashboard
- Source citations rendered inline

---

## Execution Order

| Phase | Depends on | Estimated scope |
|---|---|---|
| 1a — Supabase + FastAPI skeleton | Nothing | Large |
| 1b — Migrate all routes | 1a | Medium |
| 2 — Yahoo Finance expansion | 1b | Medium |
| 3 — News pipeline + pgvector | 1a | Large |
| 4 — Agent + RAG | 2 + 3 | Large |

---

## What Gets Retired

| Current file/feature | Replaced by |
|---|---|
| `src/backend/app.py` (Flask) | FastAPI routers |
| `src/backend/auth.py` + JWT middleware | Supabase Auth |
| `src/backend/models/` (SQLite) | Supabase PostgreSQL |
| `src/backend/Details.py` (BERT) | Phase 4 Claude agent |
| `/api/details` route | `/api/agent/query` |
| `get.py::get_portfolio` (legacy) | Already superseded by `portfolios.py` |
| Firebase (`package.json`) | Supabase Auth |
