from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

class Indicator:
    def __init__(self, api, symbol):
        self.api = api
        self.symbol = symbol

    def moving_average(self, s, e, ma_days):
        # Get historical data for the symbol
        modS = s - timedelta(days = ma_days*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        data = bars.df['close'].rolling(window=ma_days).mean()
        data = data.rename('moving average')
        df = data.to_frame()
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df

    def bollinger_bands(self, s, e, ma_days, num_std_devs):
        modS = s - timedelta(days = ma_days*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
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
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return (df)

    def RSI(self, s, e, days):
        # Get historical data for the symbol
        modS = s - timedelta(days = days*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
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
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df

    def ATR(self, s, e, days):
        # Get historical data for the symbol
        modS = s - timedelta(days = days*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)

        # Calculate the true range for each day
        high_low = bars.df['high'] - bars.df['low']
        high_close = abs(bars.df['high'] - bars.df['close'].shift())
        low_close = abs(bars.df['low'] - bars.df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis = 1)
        true_range = np.max(ranges, axis = 1)

        ATR = true_range.rolling(window=days).mean() # standard number of periods is 14
        ATR = ATR.rename('ATR')
        df = ATR.to_frame()
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
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
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        short_EMA = bars.df['close'].ewm(span=short, adjust=False).mean()
        long_EMA = bars.df['close'].ewm(span=long, adjust=False).mean()
        MACD = short_EMA - long_EMA
        signal = MACD.ewm(span=9, adjust=False).mean()
        MACD = MACD.rename("MACD")
        signal = signal.rename("signal")
        df = MACD.to_frame().join(signal.to_frame())
        return df