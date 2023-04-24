from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from plotly.offline import plot
from plotly.graph_objs import Scatter
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

class Plot:
    def __init__(self, inputs, control, client):
        self.inputs = inputs
        self.control = control
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
        pd.options.plotting.backend = "plotly"
        
        fig = px.line(self.inputs, x=self.inputs['date'], y=self.inputs['investment'])

        fig.add_trace(go.Scatter(x=self.control['date'],
                                 y=self.control['investment'],
                                 mode='lines',
                                 name='Control',
                                 line=dict(color="#FF9912",
                                           dash="dot")))
        
        fig.add_trace(go.Scatter(x=self.inputs['date'][self.inputs.buy_sell_hold == -1.0],
                                 y=self.inputs['investment'][self.inputs.buy_sell_hold == -1.0],
                                 mode='markers',
                                 marker=dict(
                                     symbol="triangle-down",
                                     size=10,
                                     color="indianred",
                                     ),
                                 name='Sell'))

        fig.add_trace(go.Scatter(x=self.inputs['date'][self.inputs.buy_sell_hold == 1.0],
                                 y=self.inputs['investment'][self.inputs.buy_sell_hold == 1.0],
                                 mode='markers',
                                 marker=dict(
                                     symbol="triangle-up",
                                     size=10,
                                     color="forestgreen",
                                     ),
                                 name='Buy'))
        
        plt_div = plot(fig, output_type='div')
        return(plt_div)

    def plot_indicator(self, title):
        pd.options.plotting.backend = "plotly"
        fig = px.line()
        
        for column_name, column_data in df.items():
            fig.add_trace(go.Scatter(x=column_data.index,
                                 y=column_data.values,
                                 name=column_name,
                                 mode='lines'))
            
        fig.update_layout(title=title)
        plt_div = plot(fig, output_type='div')
        return(plt_div)
