from flask import Flask, request, jsonify
import sqlite3

DB_NAME = "src/backend/stockinews.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def get_user(decoded_token):
    user_id = decoded_token["user_id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "User not found"}), 404

    return {"name": row[0], "email": row[1]}

def get_portfolio(decoded_token):
    user_id=decoded_token['user_id']
    # print("User_id for portfolio recieved")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker,quantity,price FROM stocks WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    # print(rows)
    conn.close()
    if not rows:
        return jsonify({"error": "User not found"}), 404

    portfolio = []
    portfolio = []
    for row in rows:
        ticker = row[0]
        quantity = row[1]
        buy_price = row[2]
        current_price = get_price(ticker)  # Fetch live price
        portfolio.append({
            "ticker": ticker,
            "quantity": quantity,
            "buy_price": buy_price,
            "current_price": current_price
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

def get_market_overview():
    import yfinance as yf
    tickers = [
        "^GSPC", "^DJI", "^NSEI",  # indices
        "GC=F", "SI=F"  # commodities
    ]

    data = []
    for symbol in tickers:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            data.append({
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": info.get("regularMarketPrice"),
                "change": info.get("regularMarketChange"),
                "percent_change": info.get("regularMarketChangePercent")
            })
        except Exception as e:
            data.append({
                "symbol": symbol,
                "error": str(e)
            })
    return data



def get_watchlist_data(user_id):
    import yfinance as yf
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT ticker FROM watchlist WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    # print(rows)
    symbols = [row[0] for row in rows]
    conn.close()
    data = []
    tickers = yf.Tickers(" ".join(symbols))
    
    for symbol in symbols:
        ticker = tickers.tickers.get(symbol.upper())
        if ticker is None:
            continue
        
        try:
            info = ticker.info
            data.append({
                "symbol": symbol.upper(),
                "name": info.get("shortName", symbol),
                "price": info.get("regularMarketPrice", None),
                "percent_change": info.get("regularMarketChangePercent", None)
            })

        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            continue
            
    return data

def getnewsdata():
    from dotenv import load_dotenv
    import os
    import requests
    load_dotenv()
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    keyz='Indian Stocks Nifty'
    url = f"https://newsapi.org/v2/everything?q={keyz}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    print(data)
    if 'articles' not in data or len(data['articles']) == 0:
        return [{"title": "No News Available", "url": "", "description": "No news articles were found for this company."}]
    return [
        {
            "title": article['title'][:50],
            "url": article['url'],
            "description": article['description']
        }
        for article in data['articles']
    ]