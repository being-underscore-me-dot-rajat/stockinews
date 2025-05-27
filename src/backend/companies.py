import pandas as pd

df=pd.read_csv('src/backend/EQUITY_L.csv')
df['Symbols']=df['SYMBOL']+" : "+df['NAME OF COMPANY']
Symbols=df['Symbols'].to_list()
