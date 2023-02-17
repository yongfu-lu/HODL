from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import Indicator as ind
import pandas as pd

class Strategy:
    def __init__(self, client, portfolio, investment, commission):
        self.portfolio = portfolio
        self.investment = investment
        self.commission = commission
        self.client = client

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
                                          end = end)

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']
        df2 = data.to_frame()

        df = pd.concat([ma_short, ma_long, data], axis=1)

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
                self.portfolio = shares * row['close']
            else:
                self.portfolio = self.investment

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
                                          end = end)

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']
        df2 = data.to_frame()

        df = pd.concat([fib_signals, data], axis=1)

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
                self.portfolio = shares * row['close']
            else:
                self.portfolio = self.investment
            hi_level, lo_level = get_level(price)

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
                                          end = end) # type: ignore

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']

        df = pd.concat([atr_short, atr_long, data], axis=1)

        prev_close = 0

        for index, row in df.iterrows():
            if (prev_close != 0) and (row['long'] + row['close'] > prev_close) and (position == 'cash'):
                shares = self.investment / row['close']
                self.investment = 0
                position = 'long'
            elif (prev_close != 0) and (row['long'] + row['close'] < prev_close) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission # type: ignore
                shares = 0
                position = 'cash'
            if position == 'long':
                self.portfolio = shares * row['close'] # type: ignore
            else:
                self.portfolio = self.investment
                
            prev_close = row['close']    

    def getVal(self):
        return self.portfolio