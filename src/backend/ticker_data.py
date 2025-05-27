import yfinance as yf
import pandas as pd

def getdata(ticker,period="7d"):
    interval={"7d":"1m","max":"1d","1mo":"1d","6mo":"1d","1y":"1d"}
    inter=interval[period]
    data = yf.Ticker(ticker).history(period=period, interval=inter) 
    print("gathering data for", ticker, period)
    data=pd.DataFrame(data)
    data_json = data[['Close']].reset_index().to_json(orient='records', date_format='iso')

    import json
    return json.loads(data_json)