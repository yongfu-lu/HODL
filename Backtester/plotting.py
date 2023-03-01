from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import strategy as strat
from datetime import datetime

class Plot:
    def __init__(self, inputs, client):
        self.inputs = inputs
        self.client = client

    def candlestick_plot(self, symbol, start, end):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params).df
        in1, in2, in3, in4, in5 = [], [], [], [], []
        for index, row in bars.iterrows():
            in1.append(index[1].date())
            in2.append(row['open'])
            in3.append(row['high'])
            in4.append(row['low'])
            in5.append(row['close'])

        in1 = pd.Series(in1)
        in1 = in1.rename('date')
        in2 = pd.Series(in2)
        in2 = in2.rename('open')
        in3 = pd.Series(in3)
        in3 = in3.rename('high')
        in4 = pd.Series(in4)
        in4 = in4.rename('low')
        in5 = pd.Series(in5)
        in5 = in5.rename('close')

        ret = pd.concat([in1,in2,in3,in4,in5], axis=1)
        fig = go.Figure(data=[go.Candlestick(x=ret['date'],
                open=ret['open'],
                high=ret['high'],
                low=ret['low'],
                close=ret['close'])])
        fig.show()
    
    def plot_strategy(self, title):
        plt.scatter(self.inputs['date'][self.inputs.buy_sell_hold == -1.0], self.inputs['investment'][self.inputs.buy_sell_hold == -1.0], c='r', marker="v")
        plt.scatter(self.inputs['date'][self.inputs.buy_sell_hold == 1.0], self.inputs['investment'][self.inputs.buy_sell_hold == 1.0], c='g', marker="^")
        plt.plot(self.inputs['date'], self.inputs['investment'])
        plt.xlabel('Date')
        plt.ylabel('Investment')
        plt.title(title)
        buy = mlines.Line2D([], [], color='r', marker='v', linestyle='None', markersize=5, label='Sell marker')
        sell = mlines.Line2D([], [], color='g', marker='^', linestyle='None', markersize=5, label='Buy marker')
        plt.legend(handles=[buy, sell])
        plt.show()
        
trading_client = StockHistoricalDataClient('PKV2FZHX6E4RMGFON60X',
                                           'GMKXVZ3W4MqenB6SbcSKM8h9WnvYBZn0qdZ86E6n')

x = datetime(2020, 5, 17)
y = datetime(2022, 5, 17)

test = strat.Strategy(trading_client, 10000, 5)
data = test.execute_ma(x, y, "AAPL", 50, 100)
ptest = Plot(data, trading_client)
ptest.plot_strategy("strategy 1")

#ptest.plot_strategy("50/100 Moving Average")
#ptest.candlestick_plot("AAPL", x, y)
