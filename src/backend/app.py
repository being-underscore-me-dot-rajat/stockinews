from flask import Flask, jsonify,request,render_template
from flask_cors import CORS
import jwt
import datetime
import bcrypt
from functools import wraps
import os
import ticker_data
from companies import Symbols
from auth import login_user,signup
import get
import add
import delete
import portfolios
from dotenv import load_dotenv
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")


app = Flask(__name__,template_folder='../Templates')
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)


@app.route('/api/companies', methods=['GET'])
def get_symb():
    return jsonify({"Symbols": Symbols})

@app.route('/api/details', methods=['GET'])
def get_company_details():
    from Details import get_news
    from Details import analyze_sentiment_bert
    company = request.args.get('company')
    company = company.split(': ')[1]
    print(f"Fetching details for: {company}")

    news_articles = get_news(company)
    analyzed_data = []

    for article in news_articles:
        sentiment = analyze_sentiment_bert(article['description'])
        article['sentiment_score'] = sentiment['polarity']
        article['sentiment']=sentiment['label']
        analyzed_data.append(article)
    # print(analyzed_data)
    return jsonify(analyzed_data)

@app.route('/api/chart')
def genchart():
    ticker = request.args.get('ticker').split(":")[0]+'.NS'
    period=request.args.get('period')
    print("Ticker and Period",ticker,period)
    data = ticker_data.getdata(ticker,period)
    print(data)
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

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
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
    
@app.route("/api/portfolio", methods=["GET"])
@token_required
def fetch_portfolio(decoded_token):
    return portfolios.get_portfolio(decoded_token)

@app.route("/api/portfolio/add", methods=["POST"])
@token_required
def add_stock(decoded_token):
    return portfolios.add_stock(decoded_token)

@app.route("/api/portfolio/sell", methods=["POST"])
@token_required
def sell_stock(decoded_token):
    return portfolios.sell_stock(decoded_token)

@app.route('/api/portfolio/history', methods=['GET'])
@token_required
def download_portfolio_history(decoded_token):
    return portfolios.download_portfolio_history(decoded_token)

@app.route('/api/portfolio/histories', methods=['GET'])
@token_required
def portfolio_history(decoded_token):
    return portfolios.portfolio_history(decoded_token)

if __name__ == '__main__':
    app.run(debug=True)

