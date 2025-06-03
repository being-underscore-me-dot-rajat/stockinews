from flask import Flask, request, jsonify,send_file
import sqlite3
from io import BytesIO



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

    ticker = data['ticker'].split()[0]+".NS"
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
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    from reportlab.lib.utils import ImageReader
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
    y = height - 80
    logo_path = "public/images/logo.png"  # Ensure this path is correct
    try:
        logo = ImageReader(logo_path)
        pdf.drawImage(logo, 50, y, width=50, height=50, mask='auto')
    except:
        pass  # Fail silently if logo not found

    # Brand Title
    pdf.setFillColor(colors.HexColor("#05AFF2"))  # Cyber Sky
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(110, y + 15, "StockiNews")

    y -= 40
    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.HexColor("#28C947"))  # Lush Lime
    pdf.drawString(50, y, f"Portfolio Transaction History")
    pdf.setFont("Helvetica", 11)
    pdf.setFillColor(colors.HexColor("#f5f5f5"))  # Light text
    pdf.drawString(350, y, f"User ID: {user_id}")
    y -= 20

    # Header line
    pdf.setStrokeColor(colors.HexColor("#353540"))
    pdf.setLineWidth(1)
    pdf.line(50, y, width - 50, y)
    y -= 20

    # Body loop
    pdf.setFont("Helvetica", 10)
    for row in rows:
        ticker, quantity, price, action, timestamp = row
        action_color = "#28C947" if action.lower() == "buy" else "#f87171"
        action_str = f"{action.upper()} {quantity} of {ticker} @ ₹{price}"

        # Timestamp
        pdf.setFillColor(colors.HexColor("#888888"))
        pdf.drawString(50, y, timestamp[:19])

        # Action line
        pdf.setFillColor(colors.HexColor(action_color))
        pdf.drawString(180, y, action_str)

        y -= 18

        # Page break
        if y < 60:
            draw_footer(pdf, width)
            pdf.showPage()
            y = height - 80
            pdf.setFont("Helvetica", 10)

    draw_footer(pdf, width)

    pdf.save()
    pdf_buffer.seek(0)

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name='portfolio_history.pdf',
        mimetype='application/pdf'
    )

def draw_footer(pdf, width):
    # Footer branding
    from reportlab.lib import colors
    pdf.setStrokeColor(colors.HexColor("#2D2D37"))
    pdf.setLineWidth(0.5)
    pdf.line(50, 40, width - 50, 40)

    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColor(colors.HexColor("#05AFF2"))
    pdf.drawString(50, 25, "StockiNews - Powered by Insights, Driven by Data.")
    pdf.setFillColor(colors.HexColor("#888888"))
    pdf.drawRightString(width - 50, 25, "https://stockinews.com")

def portfolio_history(decoded_token):
    from datetime import datetime, timedelta
    import yfinance as yf
    import pandas as pd
    user_id = decoded_token['user_id']
    conn = get_connection()
    cursor = conn.cursor()

    # Get user holdings (ticker and quantity)
    cursor.execute("SELECT ticker, quantity, action FROM stocks WHERE user_id = ? ORDER BY created_at ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    portfolio_df = None

# Loop through each stock
    for symbol, quantity, action in rows:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="6mo", interval="1wk")
        data = data.reset_index()
        data['Date'] = data['Date'].dt.strftime('%d-%m-%Y')
        
        # Calculate value of holdings for this stock
        data[f'{symbol}_value'] = data['Close'] * quantity
        
        # Reduce to only date and value columns
        stock_df = data[['Date', f'{symbol}_value']]
        
        # Merge into the main portfolio DataFrame
        if portfolio_df is None:
            portfolio_df = stock_df
        else:
            portfolio_df = pd.merge(portfolio_df, stock_df, on='Date', how='outer')

# Fill any missing values with 0 and compute total portfolio value
    portfolio_df = portfolio_df.fillna(0)
    portfolio_df['Total_Portfolio_Value'] = portfolio_df.drop(columns='Date').sum(axis=1)

    # Final output with Date and Total Portfolio Value
    final_df = portfolio_df[['Date', 'Total_Portfolio_Value']]
    final_df['Date'] = pd.to_datetime(final_df['Date'], format='%d-%m-%Y')

    # Sort by date
    final_df = final_df.sort_values('Date').reset_index(drop=True)

    # (Optional) Convert back to string format
    final_df['Date'] = final_df['Date'].dt.strftime('%d-%m-%Y')

    return {
    "dates": final_df['Date'].tolist(),
    "values": final_df['Total_Portfolio_Value'].tolist()
    }

