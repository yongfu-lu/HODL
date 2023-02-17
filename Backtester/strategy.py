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
                self.investment = shares * row['close'] - commission
                shares = 0
                position = 'cash'
            if position == 'long':
                self.portfolio = shares * row['close']
            else:
                self.portfolio = self.investment

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
