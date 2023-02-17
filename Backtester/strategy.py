from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import Indicator as ind
import pandas as pd
import numpy as np

class Strategy:
    def __init__(self, client, investment, commission):
        self.investment = investment
        self.commission = commission
        self.client = client

    def execute_rsi(self, start, end, symbol, days, over, under):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')
        bars = self.client.get_stock_bars(request_params).df
        res = ind.Indicator(self.client, symbol)
        rsi = res.RSI(start, end, days)
        signals = pd.DataFrame()
        signals['rsi'] = rsi['RSI']
        signals['long'] = np.where(rsi['RSI'] > over, 1, 0)
        signals['short'] = np.where(rsi['RSI'] < under, -1, 0)
        signals['signal'] = signals['long'] + signals['short']

        in1 = []
        for index, row in bars.iterrows():
            in1.append(index[1].date())
        
        positions = signals.signal.values.tolist()
        shares = 0
        temp = []
        pos = 'cash'

        for i in range(len(positions)):
            if positions[i] == 1 and (pos=='cash'):
                shares = self.investment / bars['close'][i]
                self.investment = 0
                pos = 'long'
            elif positions[i] == -1 and (pos=='long'):
                self.investment = shares * bars['close'][i]
                shares = 0
                pos = 'cash'
            temp.append(self.investment if shares == 0 else shares*bars['close'][i])

        ret = pd.DataFrame({'date': in1, 'investment': temp})
        
        return ret

    def execute_bb(self, start, end, symbol, ma_days, num_std_devs):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')
        bars = self.client.get_stock_bars(request_params).df
        bb = ind.Indicator(self.client, symbol)
        bands = bb.bollinger_bands(start, end, ma_days, num_std_devs)
        signals = pd.DataFrame()
        signals['ma'] = bars['close'].rolling(window=ma_days).mean()
        signals['signal'] = 0.0
        in1 = []
        for index, row in bars.iterrows():
            in1.append(index[1].date())

        signals['signal'][ma_days:] = np.where(bars['close'][ma_days:] > bands['upper band'][ma_days:], -1.0, 0.0)
        signals['signal'][ma_days:] = np.where(bars['close'][ma_days:] < bands['lower band'][ma_days:], 1.0, signals['signal'][ma_days:])
        signals['positions'] = signals['signal'].diff()

        positions = signals.positions.values.tolist()
        shares = 0
        temp = []
        pos = 'cash'

        for i in range(len(positions)):
            if positions[i] == 1.0 and (pos=='cash'):
                shares = self.investment / bars['close'][i]
                self.investment = 0
                pos = 'long'
            elif positions[i] == -1.0 and (pos=='long'):
                self.investment = shares * bars['close'][i]
                shares = 0
                pos = 'cash'
            temp.append(self.investment if shares == 0 else shares*bars['close'][i])

        
        ret = pd.DataFrame({'date': in1, 'investment': temp})
        return ret

    def execute_ma(self, start, end, symbol, short, long):
        ma = ind.Indicator(self.client, symbol)
        ma_short = ma.moving_average(start, end, short)
        ma_short.rename(columns = {'moving average':'short'}, inplace = True)
        ma_long = ma.moving_average(start, end, long)
        ma_long.rename(columns = {'moving average':'long'}, inplace = True)
        position = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']
        df = pd.concat([ma_short, ma_long, data], axis=1)
        in1, in2 = [], []

        for index, row in df.iterrows():
            if(row['short'] > row['long']) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                position = 'long'
            elif (row['short'] < row['long']) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                position = 'cash'
            if position == 'long':
                in1.append(index[1].date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index[1].date())
                in2.append(self.investment)
        in1 = pd.Series(in1)
        in1 = in1.rename('date')
        in2 = pd.Series(in2)
        in2 = in2.rename('investment')
        ret = pd.concat([in1,in2], axis=1)
        return ret

    def execute_atr(self, start, end, symbol, short, long):
        atr = ind.Indicator(self.client, symbol)
        atr_short = atr.ATR(start, end, short)
        atr_short.rename(columns = {'ATR':'short'}, inplace = True)
        atr_long = atr.ATR(start, end, long)
        atr_long.rename(columns = {'ATR':'long'}, inplace = True)
        position = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment = 'all')

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']

        df = pd.concat([atr_short, atr_long, data], axis=1)
        in1, in2 = [], []

        prev_close = 0

        for index, row in df.iterrows():
            if (prev_close != 0) and (row['long'] + row['close'] > prev_close) and (position == 'cash'):
                shares = self.investment / row['close']
                self.investment = 0
                position = 'long'
            elif (prev_close != 0) and (row['long'] + row['close'] < prev_close) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                position = 'cash'
            if position == 'long':
                in1.append(index[1].date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index[1].date())
                in2.append(self.investment)

            prev_close = row['close']

        in1 = pd.Series(in1)
        in1 = in1.rename('date')
        in2 = pd.Series(in2)
        in2 = in2.rename('investment')
        ret = pd.concat([in1,in2], axis=1)
        return ret

    def execute_fib(self, start, end, symbol, short, long):
        fib = ind.Indicator(self.client, symbol)
        fib_signals = fib.MACD(start, end, short, long)
        fib_levels = fib.FibLevels(start, end)

        def get_level(price):
            if price >= fib_levels[1]:
                return fib_levels[0], fib_levels[1]
            elif price >= fib_levels[2]:
                return fib_levels[1], fib_levels[2]
            elif price >= fib_levels[3]:
                return fib_levels[2], fib_levels[3]
            elif price >= fib_levels[4]:
                return fib_levels[3], fib_levels[4]
            else:
                return fib_levels[4], fib_levels[5]

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment = 'all')

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']
        df2 = data.to_frame()

        df = pd.concat([fib_signals, data], axis=1)
        in1, in2 = [], []

        position = 'cash'
        hi_level, lo_level = None, None
        buy_price = 0

        for index, row in df.iterrows():
            price = row['close']
            if (hi_level == None or lo_level == None):
                hi_level, lo_level = get_level(price)
                continue
            elif(price >= hi_level) or (price <= lo_level): ## Enter new level
                if (row['signal'] > row['MACD']) and (position == 'cash'): # buy
                    shares = self.investment / row['close']
                    self.investment = 0
                    position = 'long'
                    buy_price = price
                elif (row['signal'] < row['MACD']) and (position == 'long') and price > buy_price: # sell
                    self.investment = shares * row['close'] - self.commission
                    shares = 0
                    position = 'cash'
                    buy_price = 0
            if position == 'long':
                in1.append(index[1].date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index[1].date())
                in2.append(self.investment)

            hi_level, lo_level = get_level(price)

        in1 = pd.Series(in1)
        in1 = in1.rename('date')
        in2 = pd.Series(in2)
        in2 = in2.rename('investment')
        ret = pd.concat([in1,in2], axis=1)
        return ret


    def getVal(self):
        return self.investment
