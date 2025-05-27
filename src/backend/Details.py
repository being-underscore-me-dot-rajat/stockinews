import requests
from transformers import pipeline
from dotenv import load_dotenv
import os
load_dotenv()

# Fetch the API key securely
NEWS_API_KEY = os.getenv('NEWS_API_KEY')


def get_news(company):
    keyz=company+" Share"
    url = f"https://newsapi.org/v2/everything?q={keyz}&apiKey={NEWS_API_KEY}"
    # print(keyz)
    response = requests.get(url)
    data = response.json()
    # print(data)
    if 'articles' not in data or len(data['articles']) == 0:
        return [{"title": "No News Available", "url": "", "description": "No news articles were found for this company."}]
    return [
        {
            "title": article['title'][:50],
            "url": article['url'],
            "description": article['description']
        }
        for article in data['articles'][:5]
    ]

sentiment_pipeline = pipeline("sentiment-analysis")

def analyze_sentiment_bert(text):
    if not text or text.strip() == "":
        return {"label": "NEUTRAL", "polarity":0}  
    result = sentiment_pipeline(text)[0]
    polarity = result['score'] if result['label'] == 'POSITIVE' else -result['score']
    return {
        "label": result['label'],
        "polarity": polarity
    }
