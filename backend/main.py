import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

_REQUIRED_ENV = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
_missing = [k for k in _REQUIRED_ENV if not os.getenv(k)]
if _missing:
    sys.exit(f"Missing required environment variables: {', '.join(_missing)}\nCopy backend/.env.example to backend/.env and fill in the values.")

from routers import agent, auth, company, education, market, news, pipeline, portfolio, watchlist


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from services.pipeline import run_pipeline
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_pipeline, "interval", hours=2, id="news_pipeline", misfire_grace_time=300)
        scheduler.start()
        app.state.scheduler = scheduler
        yield
        scheduler.shutdown(wait=False)
    except ImportError:
        yield  # APScheduler not installed — pipeline runs on-demand only via /api/pipeline/run


app = FastAPI(title="StockiNews API", version="3.0.0", lifespan=lifespan)

# ALLOWED_ORIGINS accepts a comma-separated list; falls back to localhost for development
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent.router)
app.include_router(auth.router)
app.include_router(company.router)
app.include_router(education.router)
app.include_router(market.router)
app.include_router(news.router)
app.include_router(pipeline.router)
app.include_router(portfolio.router)
app.include_router(watchlist.router)
