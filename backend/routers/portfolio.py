from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from pathlib import Path

import yfinance as yf
import pandas as pd

from models.schemas import StockTransaction, SellRequest
from services.auth_utils import get_current_user
from services.supabase_client import supabase_admin
from services.company_catalog import normalize_nse_symbol

router = APIRouter(prefix="/api/portfolios")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_price(ticker: str):
    try:
        price = yf.Ticker(ticker).info.get("regularMarketPrice")
        return round(price, 2) if price is not None else None
    except Exception:
        return None


@router.get("")
def get_portfolio(user=Depends(get_current_user)):
    user_id = user["sub"]
    rows = supabase_admin.rpc("get_user_portfolio", {"p_user_id": user_id}).execute().data or []
    if not rows:
        return {"portfolio": []}
    portfolio = []
    for row in rows:
        ticker = row["ticker"]
        net_qty = int(row["net_quantity"])
        avg_price = round(float(row["total_cost"]) / net_qty, 2) if net_qty else 0
        current_price = _get_price(ticker)
        if current_price is None:
            continue
        portfolio.append({
            "ticker": ticker,
            "quantity": net_qty,
            "avg_price": avg_price,
            "current_price": current_price,
            "market_value": round(net_qty * current_price, 2),
            "profit_loss": round((current_price - avg_price) * net_qty, 2),
        })
    return {"portfolio": portfolio}


@router.post("/add")
def add_stock(body: StockTransaction, user=Depends(get_current_user)):
    user_id = user["sub"]
    ticker = normalize_nse_symbol(body.ticker)
    if not ticker:
        raise HTTPException(status_code=400, detail="Invalid ticker")
    action = body.action.strip().upper()
    if action not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="Action must be BUY or SELL")
    if body.quantity <= 0 or body.price <= 0:
        raise HTTPException(status_code=400, detail="Quantity and price must be positive")
    supabase_admin.table("stocks").insert({
        "user_id": user_id, "ticker": ticker,
        "quantity": body.quantity, "price": body.price, "action": action,
    }).execute()
    return {"message": "Transaction recorded successfully."}


@router.post("/sell")
def sell_stock(body: SellRequest, user=Depends(get_current_user)):
    user_id = user["sub"]
    ticker = normalize_nse_symbol(body.ticker)
    if not ticker or body.quantity <= 0 or body.price <= 0:
        raise HTTPException(status_code=400, detail="Invalid ticker, quantity, or price")
    qty_row = supabase_admin.rpc("get_ticker_quantity", {"p_user_id": user_id, "p_ticker": ticker}).execute().data
    owned = int((qty_row or [{}])[0].get("quantity", 0) or 0)
    if owned < body.quantity:
        raise HTTPException(status_code=400, detail="Not enough shares to sell")
    supabase_admin.table("stocks").insert({
        "user_id": user_id, "ticker": ticker,
        "quantity": body.quantity, "price": body.price, "action": "SELL",
    }).execute()
    return {"message": "Sell transaction recorded successfully."}


@router.get("/history")
def download_history(user=Depends(get_current_user)):
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader

    user_id = user["sub"]
    rows = (supabase_admin.table("stocks").select("ticker, quantity, price, action, created_at")
            .eq("user_id", user_id).order("created_at").execute().data or [])
    if not rows:
        raise HTTPException(status_code=404, detail="No transaction history found")

    buf = BytesIO()
    pdf = pdf_canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 80
    try:
        logo = REPO_ROOT / "public" / "images" / "logo.png"
        pdf.drawImage(ImageReader(str(logo)), 50, y, width=50, height=50, mask="auto")
    except Exception:
        pass

    pdf.setFillColor(colors.HexColor("#05AFF2"))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(110, y + 15, "StockiNews")
    y -= 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.HexColor("#28C947"))
    pdf.drawString(50, y, "Portfolio Transaction History")
    y -= 20
    pdf.setStrokeColor(colors.HexColor("#353540"))
    pdf.line(50, y, width - 50, y)
    y -= 20

    pdf.setFont("Helvetica", 10)
    for row in rows:
        action_color = "#28C947" if row["action"].lower() == "buy" else "#f87171"
        pdf.setFillColor(colors.HexColor("#888888"))
        pdf.drawString(50, y, row["created_at"][:19])
        pdf.setFillColor(colors.HexColor(action_color))
        pdf.drawString(180, y, f"{row['action'].upper()} {row['quantity']} of {row['ticker']} @ ₹{row['price']}")
        y -= 18
        if y < 60:
            _draw_footer(pdf, width)
            pdf.showPage()
            y = height - 80
            pdf.setFont("Helvetica", 10)

    _draw_footer(pdf, width)
    pdf.save()
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition": "attachment; filename=portfolio_history.pdf"})


def _draw_footer(pdf, width):
    from reportlab.lib import colors
    pdf.setStrokeColor(colors.HexColor("#2D2D37"))
    pdf.setLineWidth(0.5)
    pdf.line(50, 40, width - 50, 40)
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColor(colors.HexColor("#05AFF2"))
    pdf.drawString(50, 25, "StockiNews - Powered by Insights, Driven by Data.")
    pdf.setFillColor(colors.HexColor("#888888"))
    pdf.drawRightString(width - 50, 25, "stockinews.com")


@router.get("/histories")
def portfolio_history(user=Depends(get_current_user)):
    import gc
    user_id = user["sub"]

    # Use the RPC to get net positions (same as /api/portfolios) to correctly handle BUY/SELL netting
    rows = supabase_admin.rpc("get_user_portfolio", {"p_user_id": user_id}).execute().data or []
    holdings = {r["ticker"]: int(r["net_quantity"]) for r in rows if int(r.get("net_quantity", 0)) > 0}
    if not holdings:
        raise HTTPException(status_code=404, detail="No holdings found")

    portfolio_df = None
    for ticker, net_qty in holdings.items():
        try:
            data = yf.Ticker(ticker).history(period="6mo", interval="1wk").reset_index()
            if data.empty:
                continue
            data["Date"] = data["Date"].dt.strftime("%d-%m-%Y")
            col = f"{ticker}_value"
            data[col] = data["Close"] * net_qty
            stock_df = data[["Date", col]].copy()
            del data
            portfolio_df = stock_df if portfolio_df is None else pd.merge(portfolio_df, stock_df, on="Date", how="outer")
            del stock_df
            gc.collect()
        except Exception:
            continue

    if portfolio_df is None:
        raise HTTPException(status_code=404, detail="No price data available")

    portfolio_df = portfolio_df.fillna(0)
    portfolio_df["Total_Portfolio_Value"] = portfolio_df.drop(columns="Date").sum(axis=1)
    final_df = portfolio_df[["Date", "Total_Portfolio_Value"]].copy()
    del portfolio_df
    gc.collect()
    final_df["Date"] = pd.to_datetime(final_df["Date"], format="%d-%m-%Y")
    final_df = final_df.sort_values("Date").reset_index(drop=True)
    final_df["Date"] = final_df["Date"].dt.strftime("%d-%m-%Y")
    return {"dates": final_df["Date"].tolist(), "values": final_df["Total_Portfolio_Value"].tolist()}
