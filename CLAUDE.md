# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Frontend (React + Vite)
```bash
npm run dev        # dev server on http://localhost:5173
npm run build      # production build → dist/
npm run lint       # ESLint
npm run preview    # preview production build
```

### Backend (FastAPI — active)
```bash
cd backend
pip install -r requirements.txt
# copy .env.example → .env and fill in Supabase credentials
uvicorn main:app --reload --port 8000   # dev server on http://localhost:8000
```

### Tests
```bash
cd backend
python -m pytest tests/ -v             # 47 tests, all routes covered
```

### Environment — `backend/.env`
```
SUPABASE_URL=<your-supabase-project-url>
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_JWT_SECRET=<jwt-secret-from-supabase-dashboard>
NEWS_API_KEY=<newsapi.org key>
```

### ⚠️ Legacy backend (retired)
`src/backend/` contains the old Flask + SQLite prototype. **Do not run it.**
See `src/backend/RETIRED.md` for the full retirement record.

---

## Architecture

### Stack
| Layer | Technology |
|---|---|
| Frontend | React 19 + React Router v7, Chart.js, Bootstrap 5 — served by Vite |
| Backend | **FastAPI** (port 8000) + uvicorn. All logic in `backend/` |
| Database | **Supabase (PostgreSQL + pgvector)**. Schema in `backend/migrations/001_initial_schema.sql` |
| Auth | **Supabase Auth**. JWT issued by Supabase, decoded via `SUPABASE_JWT_SECRET` |
| Market data | `yfinance` |
| News | `news_crawler.py` (RSS/HTML) + NewsAPI (`NEWS_API_KEY`) |

### Frontend API base URL
All frontend fetch calls use:
```js
// src/lib/api.js
export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
```
Set `VITE_API_URL` in `.env` for production. No hardcoded `localhost` URLs remain in source.

### Auth flow
1. `POST /login` or `POST /signup` → Supabase Auth issues a JWT.
2. Frontend stores the token in `localStorage` under the key `"token"`.
3. Protected routes send `Authorization: Bearer <token>`.
4. `backend/services/auth_utils.py::get_current_user` FastAPI dependency decodes the Supabase JWT (`audience="authenticated"`, `HS256`). User ID is in `payload["sub"]`.

### Database schema (`backend/migrations/001_initial_schema.sql`)
| Table | Purpose |
|---|---|
| `profiles` | auto-created by Supabase Auth trigger, mirrors `auth.users` |
| `stocks` | BUY/SELL transaction log (`user_id`, `ticker`, `quantity`, `price`, `action`) with RLS |
| `watchlist` | user-specific NSE ticker list with UNIQUE(user_id, ticker) constraint and RLS |
| `article_chunks` | Phase 3 vector store — `VECTOR(1536)` + HNSW index (not yet populated) |

**RPC functions** (complex aggregations not expressible via supabase-py query builder):
- `get_user_portfolio(p_user_id)` — computes net_quantity + total_cost using `SUM(CASE…)` (correct cost basis)
- `get_ticker_quantity(p_user_id, p_ticker)` — used by sell validation

### `backend/` directory layout
```
backend/
├── main.py                     # FastAPI app, CORS, router registration
├── requirements.txt
├── .env.example
├── migrations/
│   └── 001_initial_schema.sql  # Run once in Supabase SQL editor
├── models/
│   └── schemas.py              # Pydantic request/response models
├── routers/
│   ├── auth.py                 # /login  /signup  /reset-password  /me
│   ├── company.py              # /api/companies  /api/chart  /api/company/*
│   ├── market.py               # /marketwatch
│   ├── news.py                 # /news  /api/crawler/*
│   ├── portfolio.py            # /api/portfolios  (prefix)
│   └── watchlist.py            # /watchlist
├── services/
│   ├── supabase_client.py      # supabase_admin + supabase_anon clients
│   ├── auth_utils.py           # get_current_user FastAPI dependency
│   ├── company_catalog.py      # EQUITY_L.csv → companies.json, normalize_nse_symbol()
│   ├── ticker_data.py          # yfinance chart data, 6h file cache, stale-while-revalidate
│   ├── market_service.py       # market overview, watchlist quotes, company info/devs, NewsAPI
│   ├── news_crawler.py         # RSS/HTML scraper (ET, Mint, RBI, Google News)
│   └── company_data.py         # Phase 2 deep yfinance: financials/analysts/holders/earnings/options/esg
├── data/
│   └── (companies.json cached here; EQUITY_L.csv read from src/backend/ as fallback)
└── tests/
    ├── conftest.py             # fake env vars, supabase mock, TestClient fixture
    └── test_routes.py          # 47 smoke tests covering every route
```

### NSE ticker normalisation
`backend/services/company_catalog.py::normalize_nse_symbol(value)` accepts symbol strings,
`"SYMBOL : Company Name"` display strings, and bare names, and always returns a `.NS`-suffixed
symbol for yfinance (e.g. `RELIANCE.NS`). All tickers stored in Supabase and sent to yfinance
must go through this function.

The CSV (`EQUITY_L.csv`) is searched first in `backend/data/`, then falls back to
`src/backend/EQUITY_L.csv` so we don't need to duplicate the large file.

### Caching layers

**Backend file cache** (`backend/.cache/`):
| Cache | File pattern | TTL |
|---|---|---|
| Chart data | `charts/{CACHE_VERSION}_{ticker}_{period}.json` | 6 h (stale-while-revalidate) |
| Company news | `company_news/{ticker}_{limit}.json` | 7 days |
| Watchlist quotes | `watchlist_quotes.json` | 8 h (24 h stale fallback) |
| Market overview | in-memory `_market_cache` dict | 8 h |
| Financials / analysts / holders / earnings / options / ESG | `company_data/{ticker}_{key}.json` | 1–48 h per key |

**Frontend localStorage** (`src/Stock/stock.jsx`):
- Chart data: `stock-chart:v3:{ticker}:{range}` — 6 h TTL, prefetches all ranges in background.
- Watchlist: `dashboard-watchlist-open-v5:{token_suffix}` — 8 h TTL.
- Market: `dashboard-market-open-v1` — 8 h TTL.

### Route surface (FastAPI)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/login` | — | Supabase sign-in, returns JWT |
| POST | `/signup` | — | Create user via Supabase admin API |
| POST | `/reset-password` | — | Update password via admin API |
| GET | `/me` | ✓ | Return current user profile |
| GET | `/marketwatch` | ✓ | Global indices + commodities |
| GET | `/watchlist` | ✓ | User watchlist with live open prices |
| POST | `/watchlist` | ✓ | Add ticker to watchlist |
| DELETE | `/watchlist/{symbol}` | ✓ | Remove ticker |
| GET | `/news` | — | NewsAPI headlines |
| GET | `/api/companies` | — | Full NSE company list |
| GET | `/api/chart` | — | OHLCV data for price chart |
| GET | `/api/company/info` | — | Key fundamentals |
| GET | `/api/company/developments` | — | Corporate actions, calendar, Yahoo news |
| GET | `/api/company/news` | — | Crawled news articles for a ticker |
| GET | `/api/company/financials` | — | Income statement, balance sheet, cash flow |
| GET | `/api/company/analysts` | — | Recommendations, price targets, estimates |
| GET | `/api/company/holders` | — | Major, institutional, MF holders, insiders |
| GET | `/api/company/earnings` | — | EPS history, earnings dates, dividends |
| GET | `/api/company/options` | — | Nearest-expiry options chain |
| GET | `/api/company/esg` | — | ESG/sustainability scores |
| GET | `/api/portfolios` | ✓ | User portfolio with live prices + P&L |
| POST | `/api/portfolios/add` | ✓ | Record BUY transaction |
| POST | `/api/portfolios/sell` | ✓ | Record SELL transaction (validates quantity) |
| GET | `/api/portfolios/history` | ✓ | Download transaction history as PDF |
| GET | `/api/portfolios/histories` | ✓ | 6-month portfolio value time series |
| GET | `/api/crawler/news` | — | Crawl news from a specific source |
| GET | `/api/crawler/sources` | — | List available crawler sources |

### Retired routes (not in new backend)
| Old route | Reason retired |
|---|---|
| `GET /portfolio` | Used incorrect `AVG` cost basis; replaced by `/api/portfolios` with `SUM(CASE…)` |
| `GET /api/details` | BERT sentiment — superseded by Phase 4 Claude RAG agent (`/api/agent/query`) |

### Frontend page structure
| Route | Entry component | Tabs / data fetched |
|---|---|---|
| `/` | `Login/Login.jsx` | `/login`, `/signup`, `/reset-password` |
| `/dashboard` | `dashboard/dashboard.jsx` | `/me`, portfolio widget, marketwatch, watchlist, news |
| `/company-page?company=TICKER:Name` | `Stock/stock.jsx` | 8 tabs: Overview, News, Financials, Analysts, Holders, Earnings, ESG, Options |
| `/portfolio` | `Portfolio/Portfoliopage.jsx` | `/api/portfolios`, `/api/portfolios/histories` |

`/company-page` reads the `company` query param and splits on `:` to extract the bare ticker.
Company page tabs are **lazy-loaded** — each tab fetches its data only when first activated.

### Phase roadmap (from PLAN.md)
| Phase | Status |
|---|---|
| 1a — FastAPI skeleton + Supabase schema | ✅ Complete |
| 1b — Retire Flask backend, port all routes | ✅ Complete |
| 2 — Yahoo Finance full data extraction (6 new endpoints + company page tabs) | ✅ Complete |
| 3 — News ingestion pipeline (crawl → clean → chunk → embed → pgvector) | ✅ Complete |
| 4 — Claude RAG agent (`/api/agent/*`) | 🔲 Next |

---

## Memory Safety Rules

This project runs on a 16 GB RAM system. Previous versions caused Windows memory exhaustion (>45 GB commit), system lag, audio freezes, and crashes. All code in this repo **must** follow these rules.

### Never
- Load entire datasets, article lists, or files into memory at once
- Accumulate unbounded Python lists or dicts
- Cache embeddings or API responses indefinitely in RAM
- Use infinite append patterns without cleanup
- Store large API responses in global state
- Process huge batches by default
- Use recursion for large data pipelines
- Create memory leaks through async tasks, queues, or retries

### Always prefer
- **Generators and iterators** over loading full lists
- **Chunked / streaming pipelines** — process one article at a time, not all at once
- **Configurable batch sizes** defaulting to 4–16 for AI/embedding operations
- **`del` + `gc.collect()`** after embeddings, dataframe ops, vector ops, large API responses
- **Capped queues / rolling buffers** (`collections.deque(maxlen=N)`) instead of unbounded lists
- **Disk-backed caching** over in-memory caching for anything larger than a few KB
- **Lazy loading** — never preload all DB records or embeddings into RAM

### Batch size rule
```python
BATCH_SIZE = 8  # default; always configurable
```
All embedding, summarisation, and AI inference calls must use this pattern.

### Mandatory cleanup after heavy operations
```python
import gc
del large_object
gc.collect()
```
Required after: embeddings, dataframe transforms, vector ops, large API responses, document parsing.

### Hard memory limit
```python
import psutil
MAX_MEMORY_MB = 12_000  # ~75% of 16 GB
process = psutil.Process()
if process.memory_info().rss / 1024 / 1024 > MAX_MEMORY_MB:
    # warn and throttle — do not crash silently
```

### Before writing any new code, check
1. Could this create unbounded memory growth?
2. Could this accumulate objects indefinitely?
3. Are batch sizes capped?
4. Is cleanup performed after heavy operations?
5. Is streaming possible instead of full loading?
6. Could concurrency multiply memory usage?
7. Will this stay stable after running for many hours?

If the answer to any risk question is "yes", redesign before implementing.
