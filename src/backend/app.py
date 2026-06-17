from flask import Flask, jsonify,request,render_template
from flask_cors import CORS
import jwt
import datetime
import bcrypt
from functools import wraps
import os
import ticker_data
from companies import Companies, Symbols
from auth import login_user, signup, reset_password
import get
import add
import delete
import portfolios
import news_crawler
from dotenv import load_dotenv
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")


app = Flask(__name__,template_folder='../Templates')
CORS(app, origins=[
    "http://localhost:5173",
    "http://localhost:5174",
], supports_credentials=True)


@app.route('/api/companies', methods=['GET'])
def get_symb():
    return jsonify({"Symbols": Symbols, "companies": Companies})

@app.route('/api/details', methods=['GET'])
def get_company_details():
    import Details
    print("Company details called for")
    company = request.args.get('company')
    print(company)
    print(f"Fetching details for: {company}")

    news_articles = Details.get_news(company)
    analyzed_data = []

    for article in news_articles:
        sentiment = Details.analyze_sentiment_bert(article['description'])
        article['sentiment_score'] = sentiment['polarity']
        article['sentiment']=sentiment['label']
        analyzed_data.append(article)
    # print(analyzed_data)
    return jsonify(analyzed_data)

@app.route('/api/chart')
def genchart():
    ticker = request.args.get('ticker').split(":")[0]
    period=request.args.get('period') or "7d"
    # print("Ticker and Period",ticker,period)
    data = ticker_data.getdata(ticker,period)
    ticker_data.warm_cache(ticker)
    # print(data)
    return jsonify(data)

@app.route('/login', methods=['POST'])
def login_route():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    result, status = login_user(email, password)
    return jsonify(result), status

@app.route('/signup', methods=['POST'])
def newuser():
    data = request.get_json()
    return signup(data.get("name"), data.get("email"), data.get("password"))

@app.route('/reset-password', methods=['POST'])
def reset_password_route():
    data = request.get_json()
    return reset_password(data.get("email"), data.get("password"))

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            # decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            # print("Raw token received:", token)  # LOGGING
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            # print("Decoded JWT:", decoded)  # LOGGING
            # request.user = decoded
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(decoded, *args, **kwargs)
    return wrapper

@app.route('/me', methods=['GET'])
@token_required
def getuser(decoded_token):
    user = get.get_user(decoded_token)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user})

@app.route('/portfolio', methods=['GET'])
@token_required
def portfolio(decoded_token):
    return get.get_portfolio(decoded_token)

@app.route('/marketwatch', methods=['GET'])
@token_required
def market_watch(decoded_token):
    overview = get.get_market_overview()
    # print('market overview sent to the frontend')
    return jsonify({"market": overview})

@app.route("/watchlist", methods=["GET"])
@token_required
def get_watchlist(decoded_token):
    user_id=decoded_token['user_id']
    # print(get.get_watchlist_data(user_id))
    return get.get_watchlist_data(user_id)

@app.route("/watchlist", methods=["POST"])
@token_required
def add_watchlist(decoded_token):
    user_id=decoded_token['user_id']
    return add.add_watchlist(user_id)

@app.route("/watchlist/<symbol>", methods=["DELETE"])
@token_required
def delete_watchlist(decoded_token, symbol):
    user_id=decoded_token['user_id']
    return delete.delete_watchlist(user_id,symbol)

@app.route("/news", methods=["GET"])
def get_news():
    try:
        news = get.getnewsdata()
        return jsonify({"news": news})
    except Exception as e:
        print("Error fetching news:", e)
        return jsonify({"news": [], "error": "Could not fetch news"}), 500

@app.route("/api/crawler/news", methods=["GET"])
def crawl_news_route():
    try:
        source = request.args.get("source", "all")
        query = request.args.get("query")
        limit = min(int(request.args.get("limit", 40)), 100)
        articles = news_crawler.crawl_news(source=source, limit=limit, query=query)
        return jsonify({"articles": articles, "count": len(articles)})
    except ValueError as e:
        return jsonify({"articles": [], "error": str(e)}), 400
    except Exception as e:
        print("Error crawling news:", e)
        return jsonify({"articles": [], "error": "Could not crawl news"}), 500

@app.route("/api/crawler/sources", methods=["GET"])
def crawler_sources_route():
    return jsonify({"sources": ["all", *news_crawler.SOURCES.keys()]})

@app.route("/api/company/news", methods=["GET"])
def company_news():
    try:
        ticker = request.args.get("ticker", "").strip().upper()
        if not ticker:
            return jsonify({"error": "ticker parameter is required"}), 400
        limit = min(int(request.args.get("limit", 15)), 50)
        articles = news_crawler.crawl_news_for_ticker_cached(ticker=ticker, limit=limit)
        return jsonify({"ticker": ticker, "articles": articles, "count": len(articles)})
    except Exception as e:
        print(f"Error fetching company news for {request.args.get('ticker')}: {e}")
        return jsonify({"articles": [], "error": "Could not fetch company news"}), 500

@app.route("/api/company/info", methods=["GET"])
def company_info():
    try:
        ticker = request.args.get("ticker", "").strip().upper()
        if not ticker:
            return jsonify({"error": "ticker parameter is required"}), 400
        info = get.get_company_info(ticker)
        return jsonify(info)
    except Exception as e:
        print(f"Error fetching company info for {request.args.get('ticker')}: {e}")
        return jsonify({"error": "Could not fetch company info"}), 500

@app.route("/api/company/developments", methods=["GET"])
def company_developments():
    try:
        ticker = request.args.get("ticker", "").strip().upper()
        if not ticker:
            return jsonify({"error": "ticker parameter is required"}), 400
        data = get.get_company_developments(ticker)
        return jsonify(data)
    except Exception as e:
        print(f"Error fetching developments for {request.args.get('ticker')}: {e}")
        return jsonify({"error": "Could not fetch company developments"}), 500
    
@app.route("/api/portfolios", methods=["GET"])
@token_required
def fetch_portfolio(decoded_token):
    return portfolios.get_portfolio(decoded_token)

@app.route("/api/portfolios/add", methods=["POST"])
@token_required
def add_stock(decoded_token):
    return portfolios.add_stock(decoded_token)

@app.route("/api/portfolios/sell", methods=["POST"])
@token_required
def sell_stock(decoded_token):
    return portfolios.sell_stock(decoded_token)

@app.route('/api/portfolios/history', methods=['GET'])
@token_required
def download_portfolio_history(decoded_token):
    
    return portfolios.download_portfolio_history(decoded_token)

@app.route('/api/portfolios/histories', methods=['GET'])
@token_required
def portfolio_history(decoded_token):
    return portfolios.portfolio_history(decoded_token)

if __name__ == '__main__':
    app.run(debug=True)

