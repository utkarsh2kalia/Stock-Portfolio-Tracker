import yfinance as yf

# Get the data
data = yf.download(tickers="MSFT", period="5d", interval="1m")

import numpy as np
from datetime import datetime
import smtplib
import time
from selenium import webdriver
#For Prediction
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing,svm
from sklearn.model_selection import cross_validate
#For Stock Data
from iexfinance.stocks import Stock
from iexfinance.stocks import get_historical_data
from iexfinance.stocks import get_historical_intraday
import os
# from iexfinance.refdata import get_symbols
from sklearn.model_selection import train_test_split
import pandas_datareader as web

def get_prediction(stock, days):


    # try:
    #     api_key = os.environ.get("API_KEY")
    #     response1 = requests.get(f"https://cloud-sse.iexapis.com/stable/stock/{urllib.parse.quote_plus(stock)}/quote?token={api_key}")
    #     response1.raise_for_status()
    #     except requests.RequestException:
    #         return None
    # print(get_symbols(output_format='pandas', token="sk_eff2d35f7bf842ee8a9c077f24d903d4"))
    start = datetime(2020, 1, 1)
    end = datetime.now()
    # print(start, end)
    # a = Stock("amzn", token = "pk_6b58fdbbf705461aa6c78e7b882e2f90")
    # stock = "NFLX"
    # # print(a.get_quote())
    # date = datetime(2018, 11, 27)
    # get_historical_intraday("AAPL", date)
    # df = yf.download(tickers="AAPL", period="5d", interval="1m")
    df = web.DataReader(stock, 'yahoo', start, end);
    # print(df.tail())
    # df = get_historical_data("amzn", token="pk_6b58fdbbf705461aa6c78e7b882e2f90", start=start1, end = end1)
    # IEX_TOKEN  = os.environ.get("IEX_TOKEN")
    # stock = Stock("NFLX", token = "pk_6b58fdbbf705461aa6c78e7b882e2f90")
    # print(stock)
    # start = datetime(2017, 1, 1)
    # end = datetime(2017, 5, 24)
    # print(stock.get_price());
    #Outputting the Historical data into a .csv for later use
    # df = get_historical_data(stock,token="IEX_TOKEN", start=start, end=end, output_format='pandas')
    # csv_name = (stock + '_Export.csv')
    # df.to_csv(csv_name)
    # print(df)

    df['prediction'] = df['Close'].shift(-1)
    df.dropna(inplace=True)
    forecast_time = int(days)
    X = np.array(df.drop(['prediction'], 1))

    Y = np.array(df['prediction'])
    # print(X,Y)
    X = preprocessing.scale(X)
    X_prediction = X[-forecast_time:]
    # print(X_prediction)
    X_train, X_test, Y_train, Y_test =train_test_split(X, Y, test_size=0.5)
    clf = LinearRegression()
    clf.fit(X_train, Y_train)
    prediction = (clf.predict(X_prediction))
    print(prediction)
    return prediction
get_prediction("aapl", 5)