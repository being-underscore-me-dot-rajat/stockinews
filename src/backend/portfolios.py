from flask import Flask, request, jsonify,send_file
import sqlite3
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


DB_NAME = "src/backend/stockinews.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_portfolio(decoded_token):
    user_id = decoded_token['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            ticker,
            SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END) AS net_quantity,
            SUM(CASE WHEN action = 'BUY' THEN quantity * price ELSE 0 END) AS total_cost
        FROM stocks
        WHERE user_id = ?
        GROUP BY ticker
        HAVING net_quantity > 0;
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({"portfolio": []}), 200

    portfolio = []

    for row in rows:
        ticker, net_quantity, total_cost = row
        net_quantity = int(net_quantity)
        avg_price = round(total_cost / net_quantity, 2) if net_quantity else 0
        current_price = get_price(ticker)
        if current_price is None:
            continue  # skip if current price failed

        market_value = round(net_quantity * current_price, 2)
        pl = round((current_price - avg_price) * net_quantity, 2)

        portfolio.append({
            "ticker": ticker,
            "quantity": net_quantity,
            "avg_price": avg_price,
            "current_price": current_price,
            "market_value": market_value,
            "profit_loss": pl
        })
    # print(portfolio)

    return jsonify({"portfolio": portfolio}), 200

def get_price(ticker):
    import yfinance as yf
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get("regularMarketPrice")
        if price is None:
            raise ValueError(f"No market price found for {ticker}")
        return round(price, 2)
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None 
    
def add_stock(decoded_token):
    data = request.get_json()
    required_fields = ['ticker', 'quantity', 'price', 'action']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    ticker = data['ticker'].strip().upper()+".NS"
    quantity = int(data['quantity'])
    price = float(data['price'])
    action = data['action'].strip().upper()
    user_id = decoded_token['user_id']

    if action not in ['BUY', 'SELL']:
        return jsonify({"error": "Invalid action. Must be 'BUY' or 'SELL'."}), 400

    if quantity <= 0 or price <= 0:
        return jsonify({"error": "Quantity and price must be positive."}), 400

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO stocks (ticker, user_id, quantity, price, action) VALUES (?, ?, ?, ?, ?)",
            (ticker, user_id, quantity, price, action)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

    return jsonify({"message": "Transaction recorded successfully."}), 200

def sell_stock(decoded_token):
    data = request.get_json()
    user_id = decoded_token['user_id']

    ticker = data.get("ticker", "").strip().upper()
    quantity = int(data.get("quantity", 0))
    price = float(data.get("price", 0))

    if not ticker or quantity <= 0 or price <= 0:
        return jsonify({"error": "Invalid ticker, quantity, or price"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    # Step 1: Check if user owns enough quantity
    cursor.execute("""
        SELECT SUM(CASE WHEN action = 'BUY' THEN quantity ELSE -quantity END)
        FROM stocks WHERE user_id = ? AND ticker = ?
    """, (user_id, ticker))
    total_quantity = cursor.fetchone()[0] or 0

    if total_quantity < quantity:
        return jsonify({"error": "Not enough shares to sell"}), 400

    # Step 2: Record the SELL transaction
    try:
        cursor.execute("""
            INSERT INTO stocks (ticker, user_id, quantity, price, action)
            VALUES (?, ?, ?, ?, 'SELL')
        """, (ticker, user_id, quantity, price))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

    return jsonify({"message": "Sell transaction recorded successfully."}), 200

def download_portfolio_history(decoded_token):
    user_id = decoded_token['user_id']

    conn = get_connection()
    cursor = conn.cursor()

    # Fetching all stock transactions for this user
    cursor.execute("""
        SELECT ticker, quantity, price, action, created_at
        FROM stocks
        WHERE user_id = ?
        ORDER BY created_at ASC
    """, (user_id,))
    
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return jsonify({"error": "No transaction history found"}), 404

    # Start PDF generation
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    y = height - 40

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, f"Portfolio Transaction History (User ID: {user_id})")
    y -= 30

    pdf.setFont("Helvetica", 12)
    for row in rows:
        ticker, quantity, price, action, timestamp = row
        line = f"{timestamp[:19]} | {action.upper()} {quantity} of {ticker} @ ₹{price}"
        pdf.drawString(50, y, line)
        y -= 20

        if y < 40:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 12)

    pdf.save()
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name='portfolio_history.pdf',
        mimetype='application/pdf'
    )

def portfolio_history(decoded_token):
    from datetime import datetime, timedelta
    import yfinance as yf
    import pandas as pd
    user_id = decoded_token['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    # Get user holdings (ticker and quantity)
    cursor.execute("SELECT ticker, quantity FROM stocks WHERE user_id = ?", (user_id,))
    holdings = cursor.fetchall()
    conn.close()

    if not holdings:
        return jsonify({'error': 'No stocks found in portfolio'}), 404

    start_date = datetime.now() - timedelta(days=9)
    end_date = datetime.now()

    portfolio_values = {}

    for ticker, qty in holdings:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(start=start_date, end=end_date)

            if hist.empty:
                print(f"No data for {ticker}")
                continue

            for date, row in hist.iterrows():
                date_str = date.strftime('%Y-%m-%d')
                value = row['Close'] * qty
                portfolio_values[date_str] = portfolio_values.get(date_str, 0) + value

        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            continue

    # Sort dates and prepare JSON-serializable output
    sorted_dates = sorted(portfolio_values.keys())
    values = [round(portfolio_values[date], 2) for date in sorted_dates]
    print(sorted_dates,values)
    return {
        "dates": sorted_dates,
        "values": values
    }