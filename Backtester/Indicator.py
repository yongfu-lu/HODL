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

    def FibLevels(self, s , e):
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = s,
                                          end = e)
        bars = self.api.get_stock_bars(request_params)
        swing_max = bars.df['close'].max()
        swing_min = bars.df['close'].min()

        diff = swing_max - swing_min
        level1 = swing_max - diff*0.236
        level2 = swing_max - diff*0.382
        level3 = swing_max - diff*0.5
        level4 = swing_max - diff*0.618
        return [swing_max, level1, level2, level3, level4, swing_min]
    
    def MACD(self, s , e, short, long):
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = s,
                                          end = e)
        bars = self.api.get_stock_bars(request_params)
        short_EMA = bars.df['close'].ewm(span=short, adjust=False).mean()
        long_EMA = bars.df['close'].ewm(span=long, adjust=False).mean()
        MACD = short_EMA - long_EMA
        signal = MACD.ewm(span=9, adjust=False).mean()
        MACD = MACD.rename("MACD")
        signal = signal.rename("signal")
        df = MACD.to_frame().join(signal.to_frame())
        return df




trading_client = StockHistoricalDataClient('PKV2FZHX6E4RMGFON60X',
                                           'GMKXVZ3W4MqenB6SbcSKM8h9WnvYBZn0qdZ86E6n')

ind = Indicator(trading_client, "AAPL")

x = datetime(2020, 5, 7)
y = datetime(2021, 5, 7)

#s1 = (ind.MACD(x, y, 12, 9)).to_string()
#s2 = (ind2.bollinger_bands(x, y, 20, 2)).to_string()
#s3 = (ind3.RSI(x, y, 20)).to_string()

#print(s1)
#print(s2)
#print(s3)
