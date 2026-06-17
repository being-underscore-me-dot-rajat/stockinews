# ⚠️ RETIRED — Legacy Flask Backend

This directory (`src/backend/`) is the **original Flask + SQLite prototype**.
It has been superseded by the new **FastAPI + Supabase** backend in [`backend/`](../../backend/).

**Do not run or modify files in this directory.**

---

## What was retired and why

| File / route | Status | Replaced by |
|---|---|---|
| `app.py` (Flask entry point, port 5000) | Retired | `backend/main.py` (FastAPI, port 8000) |
| `auth.py` (bcrypt + hand-rolled JWT) | Retired | Supabase Auth (`backend/routers/auth.py`) |
| `models/` (SQLite schema) | Retired | Supabase PostgreSQL (`backend/migrations/001_initial_schema.sql`) |
| `get.py::get_portfolio` (`/portfolio` route) | **Retired** — used `AVG` which gives wrong cost basis | `backend/routers/portfolio.py` using `SUM(CASE…)` via Supabase RPC |
| `Details.py` + `/api/details` (BERT sentiment) | Retired | Superseded by Phase 4 Claude RAG agent (`/api/agent/query`) |
| `get.py`, `add.py`, `delete.py`, `portfolios.py` | Retired | `backend/routers/` + `backend/services/` |
| `ticker_data.py` | Retired | `backend/services/ticker_data.py` |
| `news_crawler.py` | Retired | `backend/services/news_crawler.py` |
| `company_catalog.py` | Retired | `backend/services/company_catalog.py` (reads same `EQUITY_L.csv`) |
| `companies.py` | Retired | `backend/services/company_catalog.py` |

## Why the directory is kept (not deleted)

- `EQUITY_L.csv` — NSE equity list referenced by new backend as fallback path
- `stockinews.db` — SQLite DB retained for local reference / data migration if needed
- `companies.json` — cached company catalogue, read by new backend

## How to run the new backend

```bash
cd backend
pip install -r requirements.txt
# copy .env.example → .env and fill in Supabase credentials
uvicorn main:app --reload --port 8000
```
