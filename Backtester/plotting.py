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

    def plot_stock(self, title):
        pd.options.plotting.backend = "plotly"
        
        fig = px.line(self.inputs, x=self.inputs['date'], y=self.inputs['stock_price'])
        fig.update_layout(title=title)
        
        plt_div = plot(fig, output_type='div')
        return(plt_div)

    def plot_indicator(self, title, df, df2, df3):
        pd.options.plotting.backend = "plotly"
        fig = px.line(self.inputs, x=df2.index, y=df2.iloc[:, 0])
        
        for column_name, column_data in df.items():
            fig.add_trace(go.Scatter(x=column_data.index,
                                 y=column_data.values,
                                 name=column_name,
                                 mode='lines'))
            
        for column_name, column_data in df3.items():
            fig.update_traces(text=column_data.values, selector=dict(name=column_name))
            
        fig.update_layout(title=title)
        plt_div = plot(fig, output_type='div')
        return(plt_div)

    def plot_indicator2(self, title, df, df2):
        pd.options.plotting.backend = "plotly"
        fig = px.line(self.inputs, x=df2.index, y=df2['stock_price'])
        
        for column_name, column_data in df.items():
            fig.add_trace(go.Scatter(x=column_data.index,
                                 y=column_data.values,
                                 name=column_name,
                                 mode='lines'))
            
        fig.update_layout(title=title)
        plt_div = plot(fig, output_type='div')
        return(plt_div)
