from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
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
    
    def line_plot(self, title):
        ax = self.inputs.plot(x='date', y='investment', kind='line')
        ax.set_xlabel('date')
        ax.set_ylabel('investment')
        ax.set_title(title)
        plt.show()
