import requests
from dotenv import load_dotenv
import os
load_dotenv()

# Fetch the API key securely
NEWS_API_KEY = os.getenv('NEWS_API_KEY')


def get_news(company):
    company=company[:-3]
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

from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
# nltk.download('vader_lexicon')

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment_bert(text):
    if not text or text.strip() == "":
        return {"label": "NEUTRAL", "polarity": 0}
    
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    label = 'POSITIVE' if compound > 0.05 else 'NEGATIVE' if compound < -0.05 else 'NEUTRAL'
    return {"label": label, "polarity": compound}

