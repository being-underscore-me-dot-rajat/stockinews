# StockiNews

A full-stack Indian stock market intelligence platform. Combines live NSE/BSE market data, a continuously updated news knowledge base, and an AI research agent into a single interface.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + React Router v7, Chart.js, Bootstrap 5 — served by Vite |
| Backend | FastAPI + uvicorn (Python 3.12) |
| Database | Supabase (PostgreSQL + pgvector) |
| Auth | Supabase Auth (JWT) |
| Market data | yfinance |
| Embeddings | Azure AI Foundry — `text-embedding-3-small` (1536 dims) |
| AI Agent | Azure AI Foundry — `gpt-4.1-mini` with tool use |
| News | RSS crawlers (ET, Business Standard, Moneycontrol, RBI) + Google News + yfinance live headlines |

---

## Features

### Dashboard
- **Portfolio panel** — real-time P&L, pie chart by holding weight
- **Market Watch** — global indices (Nifty, S&P 500, DAX, Nikkei…) and commodities (Gold, Crude, Silver…)
- **Watchlist** — NSE stocks with live open prices
- **News feed** — aggregated headlines from Indian financial sources
- **AI Briefing** — on-demand GPT-powered market summary for your watchlist

### Company Page (9 tabs)
| Tab | Data |
|---|---|
| Overview | Price chart (7d/1m/6m/1y/max), key metrics, corporate actions |
| News | Crawled articles from ET, Mint, BS, Moneycontrol |
| AI Analyst | Ask any question — agent searches knowledge base + live yfinance headlines |
| Financials | Income statement, balance sheet, cash flow — annual & quarterly |
| Analysts | Ratings, price targets, consensus estimates |
| Holders | Major, institutional, MF holders, insiders |
| Earnings | EPS history, dividend history, earnings dates |
| ESG | Environmental, Social & Governance scores |
| Options | Nearest-expiry call/put options chain |

### Portfolio Page
- Full transaction history (BUY/SELL)
- 6-month portfolio value chart
- PDF export
- AI chat — ask questions about your holdings

### News Pipeline (background)
- Crawls 7 source families, 300+ articles per run
- Ticker-specific crawl for 37 tracked NSE stocks
- Chunks, embeds (Azure), stores in Supabase pgvector
- Runs every 2 hours automatically via APScheduler

### AI Agent (RAG)
- Embeds user query → pgvector cosine similarity search
- `get_live_news` tool — real-time yfinance headlines for breaking news
- `search_news` tool — knowledge base vector search
- `get_stock_info` tool — live price and fundamentals
- Returns structured JSON: sentiment, confidence, key themes, directional impact, sources, summary

---

## Project Structure

```
stockinews/
├── backend/                    # FastAPI application
│   ├── main.py                 # App entry point, CORS, router registration
│   ├── requirements.txt
│   ├── .env.example            # Copy to .env and fill in credentials
│   ├── migrations/
│   │   ├── 001_initial_schema.sql   # Run once in Supabase SQL Editor
│   │   ├── 002_crawled_urls.sql     # Run once in Supabase SQL Editor
│   │   └── 003_match_chunks_fn.sql  # Run once in Supabase SQL Editor
│   ├── models/
│   │   └── schemas.py
│   ├── routers/
│   │   ├── agent.py            # /api/agent/*
│   │   ├── auth.py             # /login  /signup  /reset-password  /me
│   │   ├── company.py          # /api/companies  /api/chart  /api/company/*
│   │   ├── market.py           # /marketwatch
│   │   ├── news.py             # /news  /api/crawler/*
│   │   ├── pipeline.py         # /api/pipeline/run  /api/pipeline/status
│   │   ├── portfolio.py        # /api/portfolios  (CRUD + PDF + history chart)
│   │   └── watchlist.py        # /watchlist
│   ├── services/
│   │   ├── agent_service.py    # GPT-4.1-mini tool-use loop
│   │   ├── auth_utils.py       # FastAPI dependency — verifies Supabase JWT
│   │   ├── company_catalog.py  # EQUITY_L.csv → companies.json, normalize_nse_symbol()
│   │   ├── company_data.py     # Deep yfinance: financials/analysts/holders/earnings/options/esg
│   │   ├── embedder.py         # Azure text-embedding-3-small
│   │   ├── market_service.py   # Market overview, watchlist quotes, company info, NewsAPI
│   │   ├── news_crawler.py     # RSS/HTML/yfinance crawlers
│   │   ├── pipeline.py         # Crawl → Chunk → Embed → Store pipeline
│   │   ├── rag.py              # pgvector similarity search
│   │   ├── supabase_client.py  # supabase_admin + supabase_anon clients
│   │   └── ticker_data.py      # yfinance OHLCV chart data, 6h file cache
│   ├── data/                   # companies.json cache
│   ├── .cache/                 # File-based cache (charts, company data, watchlist)
│   └── tests/
│       ├── conftest.py
│       └── test_routes.py
│
└── src/                        # React frontend
    ├── App.jsx
    ├── lib/
    │   ├── api.js              # API_BASE — reads VITE_API_URL env var
    │   ├── AgentChat.jsx       # Shared AI chat panel component
    │   └── Tip.jsx             # CSS-only tooltip component
    ├── Login/
    ├── dashboard/
    │   └── components/
    │       ├── briefing/       # AI Briefing card
    │       ├── marketwatch/
    │       ├── news/
    │       ├── portfolio/
    │       └── watchlist/
    ├── Stock/                  # Company page (9 tabs)
    ├── Portfolio/              # Portfolio page
    └── home/
```

---

## Setup

### 1. Clone and install frontend dependencies

```bash
git clone <repo-url>
cd stockinews
npm install
```

### 2. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Enable the **pgvector** extension: Dashboard → Database → Extensions → search `vector` → Enable
3. Open the **SQL Editor** and run the three migration files in order:
   - `backend/migrations/001_initial_schema.sql`
   - `backend/migrations/002_crawled_urls.sql`
   - `backend/migrations/003_match_chunks_fn.sql`
4. From Project Settings → API, copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon / public key** → `SUPABASE_ANON_KEY`
   - **service_role key** → `SUPABASE_SERVICE_ROLE_KEY`

### 3. Set up Azure AI Foundry

You need two model deployments in the same Azure AI Foundry project:

| Deployment | Model | Purpose |
|---|---|---|
| `text-embedding-3-small` | text-embedding-3-small | Embedding articles and queries |
| `gpt-41-mini` (or your name) | gpt-4.1-mini | AI agent chat |

From your Azure AI Foundry project:
- **Endpoint**: `https://<your-project>.services.ai.azure.com`
- **API Key**: Project Settings → Keys

> Deploy as **standard model deployments** (not agent deployments).

### 4. Configure backend environment

```bash
cd backend
cp .env.example .env
```

Fill in `backend/.env`:

```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_ANON_KEY=sb_publishable_...
SUPABASE_SERVICE_ROLE_KEY=sb_secret_...

NEWS_API_KEY=<newsapi.org key>

AZURE_OPENAI_ENDPOINT=https://<your-project>.services.ai.azure.com
AZURE_OPENAI_API_KEY=<your-azure-key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-41-mini
AZURE_OPENAI_API_VERSION=2024-02-01

# For production — comma-separated list of allowed frontend origins
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174
```

### 5. Install backend dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

---

## Running the Project

Open two terminals.

**Terminal 1 — Backend**
```bash
cd backend
uvicorn main:app --reload --port 8000
```
API is available at `http://localhost:8000`
Interactive API docs at `http://localhost:8000/docs`

**Terminal 2 — Frontend**
```bash
npm run dev
```
App is available at `http://localhost:5173`

---

## News Pipeline

The pipeline crawls news, chunks articles, embeds them with Azure, and stores vectors in Supabase. It runs automatically every **2 hours** when the backend is running.

### Run manually

**Option A — Swagger UI (easiest)**

Open `http://localhost:8000/docs` in a browser → find `POST /api/pipeline/run` → click **Try it out** → **Execute**.

**Option B — PowerShell**

```powershell
# Trigger a run
Invoke-RestMethod -Method POST http://localhost:8000/api/pipeline/run

# Check status
Invoke-RestMethod http://localhost:8000/api/pipeline/status
```

**Option C — Windows curl (note the .exe suffix to bypass the PowerShell alias)**

```powershell
curl.exe -X POST http://localhost:8000/api/pipeline/run
curl.exe http://localhost:8000/api/pipeline/status
```

**Option D — bash / macOS / Linux**

```bash
curl -X POST http://localhost:8000/api/pipeline/run
curl http://localhost:8000/api/pipeline/status
```

### Pipeline modes

Set `PIPELINE_MODE` in `backend/.env`:

| Mode | `PIPELINE_MODE` | Runtime | Articles | Tickers | Article fetch |
|---|---|---|---|---|---|
| Development | `dev` (default) | ~5 min | 120 broad + 3/ticker × 15 tickers | 15 | Uses RSS summary if ≥ 200 chars — skips full page fetch |
| Production | `prod` | 30–60 min | 300 broad + 5/ticker × 37 tickers | 37 | Always fetches full article page for richer embeddings |

Switch to prod before deploying: add `PIPELINE_MODE=prod` to your server's environment variables.

### What it crawls

| Source | Type | Coverage |
|---|---|---|
| Economic Times | RSS (7 feeds) | Markets, stocks, economy, companies, defence, industry, commodities |
| Financial Express | RSS (3 feeds) | Markets, economy, industry |
| Reserve Bank of India | RSS (3 feeds) | Press releases, notifications, speeches |
| Google News | RSS (15 targeted queries) | M&A, PSU, IPO, defence, infra, banking, pharma, IT, metals, FMCG + proxies for Business Standard and Moneycontrol |
| Mint | HTML listing (5 pages) | Market, companies, economy, industry |
| Ticker-specific | Google News per ticker | 37 tracked NSE stocks including MAZDOCK, HAL, BEML, RELIANCE, TCS, etc. |

### How the AI stays current between runs

Even when an article hasn't been crawled yet, the **AI Analyst** tab calls `get_live_news` which fetches real-time headlines from Yahoo Finance for the specific stock you're asking about.

### Pipeline status fields

```json
{
  "running": false,
  "last_run_at": "2026-06-01T10:00:00+00:00",
  "last_run_status": "ok",
  "articles_processed": 312,
  "chunks_stored": 489,
  "last_error": null
}
```

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key (never expose to frontend) |
| `NEWS_API_KEY` | No | newsapi.org key for `/news` headline feed |
| `AZURE_OPENAI_ENDPOINT` | Yes (pipeline + agent) | Azure AI Foundry project endpoint |
| `AZURE_OPENAI_API_KEY` | Yes (pipeline + agent) | Azure AI Foundry API key |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Yes (pipeline + agent) | Deployment name for text-embedding-3-small |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | Yes (agent) | Deployment name for gpt-4.1-mini |
| `AZURE_OPENAI_API_VERSION` | No | API version, default `2024-02-01` |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins, default `localhost:5173,5174` |
| `VITE_API_URL` | No | Frontend API base URL, default `http://localhost:8000` |

---

## API Routes

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/login` | — | Sign in, returns JWT |
| POST | `/signup` | — | Create account |
| POST | `/reset-password` | — | Reset password |
| GET | `/me` | JWT | Current user profile |
| GET | `/marketwatch` | JWT | Global indices and commodities |
| GET | `/watchlist` | JWT | User watchlist with live prices |
| POST | `/watchlist` | JWT | Add ticker to watchlist |
| DELETE | `/watchlist/{symbol}` | JWT | Remove ticker |
| GET | `/news` | — | NewsAPI headlines |
| GET | `/api/companies` | — | Full NSE company list |
| GET | `/api/chart` | — | OHLCV chart data |
| GET | `/api/company/info` | — | Key fundamentals |
| GET | `/api/company/developments` | — | Corporate actions and calendar |
| GET | `/api/company/news` | — | Crawled news for a ticker |
| GET | `/api/company/financials` | — | Income statement, balance sheet, cash flow |
| GET | `/api/company/analysts` | — | Analyst ratings and estimates |
| GET | `/api/company/holders` | — | Institutional, MF, and insider holders |
| GET | `/api/company/earnings` | — | EPS history, dividends |
| GET | `/api/company/options` | — | Nearest-expiry options chain |
| GET | `/api/company/esg` | — | ESG scores |
| GET | `/api/portfolios` | JWT | Portfolio with live P&L |
| POST | `/api/portfolios/add` | JWT | Record BUY transaction |
| POST | `/api/portfolios/sell` | JWT | Record SELL (validates quantity) |
| GET | `/api/portfolios/history` | JWT | Download transaction PDF |
| GET | `/api/portfolios/histories` | JWT | 6-month portfolio value chart |
| POST | `/api/agent/query` | JWT | AI analysis for a stock |
| POST | `/api/agent/portfolio` | JWT | AI analysis of user's portfolio |
| GET | `/api/agent/briefing` | JWT | Daily AI briefing for watchlist |
| POST | `/api/pipeline/run` | — | Trigger news pipeline manually |
| GET | `/api/pipeline/status` | — | Pipeline status and last-run stats |

---

## Notes

- `src/backend/` is the retired Flask + SQLite prototype. Do not run it. See `src/backend/RETIRED.md`.
- The backend validates `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` at startup and exits with a clear message if any are missing.
- Pipeline memory usage is capped at ~12 GB (75% of 16 GB). If exceeded, the run is aborted cleanly and the error is recorded in the status endpoint.
- Chart data and company fundamentals are file-cached in `backend/.cache/` to reduce yfinance API calls.
