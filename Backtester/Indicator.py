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

    def roc(self, s, e, n):
        modS = s - timedelta(days = n*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        data = (bars.df['close'] - bars.df['close'].shift(n)) / bars.df['close'].shift(n) * 100
        data = data.rename('ROC')
        df = data.to_frame()
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df

    def aroon(self, s, e, n):
        modS = s - timedelta(days = n*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        high_period = bars.df['high'].rolling(n).apply(lambda x: x.argmax(), raw=True)
        low_period = bars.df['low'].rolling(n).apply(lambda x: x.argmin(), raw=True)
        aroon_up = (n - high_period) / n * 100
        aroon_up = aroon_up.rename('aroon up')
        aroon_down = (n - low_period) / n * 100
        aroon_down = aroon_down.rename('aroon down')
        df = pd.concat([aroon_up, aroon_down], axis = 1)
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df
    
    def stochastic_oscillator(self, s, e, n):
        modS = s - timedelta(days = n*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        lowest_low = bars.df['low'].rolling(window=n).min()
        highest_high = bars.df['high'].rolling(window=n).max()
        k_percent = 100 * ((bars.df['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=3).mean()
        k_percent = k_percent.rename('k percent')
        d_percent = d_percent.rename('d percent')
        df = pd.concat([k_percent, d_percent], axis = 1)
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df

    def tsi(self, s, e, n1, n2):
        temp = 0
        if(n1>n2):
            temp = n1
        else:
            temp = n2
        modS = s - timedelta(days = 2*n1+n2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        diff = bars.df['close'].diff(1)
        abs_diff = abs(bars.df['close'].diff(1))

        # First smoothing
        ema1 = diff.ewm(span=n1, min_periods=n1).mean()
        ema_abs_diff1 = abs_diff.ewm(span=n1, min_periods=n1).mean()
        tsi1 = 100 * (ema1 / ema_abs_diff1)
        
        # Second smoothing
        ema2 = tsi1.ewm(span=n2, min_periods=n2).mean()

        ema2 = ema2.rename('tsi')
        df = ema2.to_frame()
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df

    def ultimate_oscillator(self, s, e, n):
        n2 = n * 2
        n3 = n* 4
        modS = s - timedelta(days = n3*3)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        periods = [n, n2, n3]
        df = pd.DataFrame()
        for period in periods:
            min_low = bars.df['low'].rolling(window=period, min_periods=period).min()
            max_high = bars.df['high'].rolling(window=period, min_periods=period).max()
            bp = bars.df['close'] - min_low
            tr = max_high - min_low
            avg = bp.rolling(window=period, min_periods=period).sum() / tr.rolling(window=period, min_periods=period).sum()
            df['avg'+str(period)] = avg

        df['UO'] = ((4 * df['avg'+str(n)] + 2 * df['avg'+str(n2)] + df['avg'+str(n3)]) / 7) *  100
        
        df = df['UO'].to_frame()
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df

    def emv(self, s, e, n):
        modS = s - timedelta(days = n*2)
        request_params = StockBarsRequest(symbol_or_symbols=[self.symbol],
                                          timeframe = TimeFrame.Day,
                                          start = modS,
                                          end = e,
                                          adjustment='all')
        bars = self.api.get_stock_bars(request_params)
        dm = ((bars.df['high'] + bars.df['low']) / 2) - ((bars.df['high'].shift(1) + bars.df['low'].shift(1)) / 2)
        br = (bars.df['volume']/100000000) / ((bars.df['high'] - bars.df['low']))
        emv = dm / br

        emv_ma = emv.rolling(n).mean()
        
        emv_ma = emv_ma.rename('emv')
        df = emv_ma.to_frame()
        df = df.reset_index()
        del df["symbol"]
        df = df.set_index('timestamp')
        df = df.truncate(before=pd.Timestamp(s, tz='US/Pacific'))
        return df

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
                                          end = e,
                                          adjustment='all')
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

    def test_parameters(self, s, e, symbol, client, algorithm = None, w=0, w1=0, w2=0, w3=0, stdev=0):
        if(s.year < 2016 or e.year < 2016):
            return ("Please input data ranges post-2016 for Alpaca compatibility.")
        if(datetime.now() < s):
            return ("Start date must be before the current day.")
        if(datetime.now() < e):
            return ("End date must be before the current day.")
        if(e < s):
            return ("End date must be chronologically after start date.")
        if algorithm:
            if( algorithm == 'MA' or algorithm == 'ATR' or algorithm == 'RSI' or
                 algorithm == 'ROC' or algorithm == 'ARN' or algorithm == 'UO' or
                 algorithm =='STO'):
                if(w <= 1):
                    return ("The window must be greater than 1.")
            if(algorithm =='TSI'):
                if(w1 <= 1):
                    return ("The first window must be greater than 1.")
                if(w2 <= 1):
                    return ("The second window must be greater than 1.")
            if(algorithm=='BB'):
                if(w3 <=1):
                    return ("The window must be greater than 1.")
                if(stdev<=0):
                    return("Standard deviation must be greater than 0.")
        try:
            request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = s,
                                          end = e,
                                          adjustment = 'all')
            bars = client.get_stock_bars(request_params).df
        except:
            return ("Please input a correct ticker symbol.")

        return("Valid")

    def normalize_df(self, df1, df2):
        if len(df1.columns) == 1:
            col_min_df1 = df1.min()[0]
            col_max_df1 = df1.max()[0]
        else:
            col_min_df1 = df1.min()
            col_max_df1 = df1.max()
            
        df2_normalized = df2.copy()
        for i in range(len(df2.columns)):
            col_min = col_min_df1 if np.ndim(col_min_df1) == 0 else col_min_df1[i]
            col_max = col_max_df1 if np.ndim(col_max_df1) == 0 else col_max_df1[i]
            normalization_factor = col_max / df2.iloc[:, i].max()
            df2_normalized.iloc[:, i] = ((df2_normalized.iloc[:, i] * normalization_factor - col_min) / (col_max - col_min)) * (col_max - col_min) + col_min
                
        return df2_normalized

    def normalize_df2(self, df1, df2):
        max_val = df1.values.max()
        min_val = df1.values.min()
        normalized_df2 = (df2 - df2.min()) / (df2.max() - df2.min())
        normalized_df2 = (normalized_df2 * (max_val - min_val)) + min_val
        return normalized_df2
