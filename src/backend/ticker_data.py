import yfinance as yf
import pandas as pd

def getdata(ticker,period="7d"):
    interval={"7d":"1d","max":"1d","1mo":"1d","6mo":"1d","1y":"1d"}
    inter=interval[period]
    data = yf.Ticker(ticker).history(period=period, interval=inter) 
    data = pd.DataFrame(data).reset_index()
    data.head()
    # Format the datetime column
    data['Datetime'] = data['Date'].dt.strftime('%d-%m-%y')  # <-- formatted here
    data = data[['Datetime', 'Close']]

    import json 
    data_json = data.to_json(orient='records')

    return json.loads(data_json)