from flask import Flask, jsonify,request,render_template
from flask_cors import CORS
import jwt
import datetime
import bcrypt
from functools import wraps
import os
from Details import get_news,analyze_sentiment_bert
import ticker_data
from companies import Symbols
from auth import login_user,signup
import get
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

if __name__ == '__main__':
    app.run(debug=True)

