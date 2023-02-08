from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import numpy as np
import pandas as pd

class Indicator:
    def __init__(self, api, symbol):
        self.api = api
        self.symbol = symbol

    def moving_average(self, s, e, ma_days):
        # Get historical data for the symbol
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = s,
                                          end = e)
        bars = self.api.get_stock_bars(request_params)
        data = bars.df['close'].rolling(window=ma_days).mean()
        data = data.rename('moving average')
        df = data.to_frame()
        return df

    def bollinger_bands(self, s, e, ma_days, num_std_devs):
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = s,
                                          end = e)
        bars = self.api.get_stock_bars(request_params)
        ma = bars.df['close'].rolling(window=ma_days).mean()
        # Calculate the standard deviation
        std = bars.df['close'].rolling(window=ma_days).std()
        # Calculate the upper and lower bands
        upper = ma + (std * num_std_devs)
        lower = ma - (std * num_std_devs)
        upper = upper.rename('upper band')
        lower = lower.rename('lower band')
        df = pd.concat([upper,lower], axis = 1)
        return (df)

    def RSI(self, s, e, days):
        # Get historical data for the symbol
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = s,
                                          end = e)
        bars = self.api.get_stock_bars(request_params)
        data = bars.df['close'].diff()
        # Calculate the gain and loss for each day
        gain = data.where(data > 0, 0)
        loss = abs(data.where(data < 0, 0))

        avg_gain = gain.rolling(window=days).mean()
        avg_loss = loss.rolling(window=days).mean()

        rs = avg_gain/avg_loss
        
        RSI = 100 - (100/(1+rs))
        RSI = RSI.rename('RSI')
        df = RSI.to_frame()

        return df
