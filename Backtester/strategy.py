from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
#import Indicator as ind
from .Indicator import Indicator
import pandas as pd
import numpy as np

class Strategy:
    def __init__(self, client, investment, commission):
        self.investment = investment
        self.commission = commission
        self.client = client

    def execute_control(self, start, end, symbol):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')
        bars = self.client.get_stock_bars(request_params).df

        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = self.investment / bars['close'][0]
        pos = 'cash'
        prevpos = 'cash'
        
        for index, row in bars.iterrows():
            in1.append(index[1].date())
            in2.append(row['close'] * shares)
            in3.append(0)
            in4.append('long')
            in5.append(shares)
        in3[0] = 1
        
        ret = pd.DataFrame({'date': in1, 'investment': in2, 'buy_sell_hold': in3, 'position': in4, 'shares': in5})
        return ret
        
    def execute_ma(self, start, end, symbol, short, long):
        ma = Indicator(self.client, symbol)
        ma_short = ma.moving_average(start, end, short)
        ma_short.rename(columns = {'moving average':'short'}, inplace = True)
        ma_long = ma.moving_average(start, end, long)
        ma_long.rename(columns = {'moving average':'long'}, inplace = True)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']
        df = pd.concat([ma_short, ma_long, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = 0

        for index, row in df.iterrows():
            if(row['short'] > row['long']) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif (row['short'] < row['long']) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index[1].date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index[1].date())
                in2.append(self.investment)

            if(prevpos == position):
                in3.append(0)
            else:
                if(position=='cash'):
                    in3.append(-1)
                else:
                    in3.append(1)
            in4.append(position)
            in5.append(shares)

        ret = pd.DataFrame({'date': in1, 'investment': in2, 'buy_sell_hold': in3, 'position': in4, 'shares': in5})
        return ret
    
    def execute_rsi(self, start, end, symbol, days, over, under):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')
        bars = self.client.get_stock_bars(request_params).df
        res = Indicator(self.client, symbol)
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
        temp, bsh, sh, p = [], [], [], []
        prevpos = 'cash'
        pos = 'cash'

        for i in range(len(positions)):
            if positions[i] == 1 and (pos=='cash'):
                shares = self.investment / bars['close'][i]
                self.investment = 0
                prevpos = pos
                pos = 'long'
            elif positions[i] == -1 and (pos=='long'):
                self.investment = shares * bars['close'][i]
                shares = 0
                prevpos = pos
                pos = 'cash'
            else:
                prevpos = pos
            temp.append(self.investment if shares == 0 else shares*bars['close'][i])
            sh.append(shares)
            p.append(pos)
            if(prevpos == pos):
                bsh.append(0)
            else:
                if(pos=='cash'):
                    bsh.append(-1)
                else:
                    bsh.append(1)
                    
        ret = pd.DataFrame({'date': in1, 'investment': temp, 'buy_sell_hold': bsh, 'position': p, 'shares': sh})
        return ret

    def execute_bb(self, start, end, symbol, ma_days, num_std_devs):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')
        bars = self.client.get_stock_bars(request_params).df
        bb = Indicator(self.client, symbol)
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
        temp, bsh, sh, p = [], [], [], []
        prevpos = 'cash'
        pos = 'cash'

        for i in range(len(positions)):
            if positions[i] == 1.0 and (pos=='cash'):
                shares = self.investment / bars['close'][i]
                self.investment = 0
                prevpos = pos
                pos = 'long'
            elif positions[i] == -1.0 and (pos=='long'):
                self.investment = shares * bars['close'][i]
                shares = 0
                prevpos = pos
                pos = 'cash'
            else:
                prevpos = pos
            temp.append(self.investment if shares == 0 else shares*bars['close'][i])
            sh.append(shares)
            p.append(pos)
            if(prevpos == pos):
                bsh.append(0)
            else:
                if(pos=='cash'):
                    bsh.append(-1)
                else:
                    bsh.append(1)

        
        ret = pd.DataFrame({'date': in1, 'investment': temp, 'buy_sell_hold': bsh, 'position': p, 'shares': sh})
        return ret

    def execute_atr(self, start, end, symbol, short, long):
        atr = Indicator(self.client, symbol)
        atr_short = atr.ATR(start, end, short)
        atr_short.rename(columns = {'ATR':'short'}, inplace = True)
        atr_long = atr.ATR(start, end, long)
        atr_long.rename(columns = {'ATR':'long'}, inplace = True)
        position = 'cash'
        prevpos = 'cash'
        shares = 0

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment = 'all')

        bars = self.client.get_stock_bars(request_params)
        data = bars.df['close']

        df = pd.concat([atr_short, atr_long, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []

        prev_close = 0

        for index, row in df.iterrows():
            if (prev_close != 0) and (row['long'] + row['close'] > prev_close) and (position == 'cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif (prev_close != 0) and (row['long'] + row['close'] < prev_close) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index[1].date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index[1].date())
                in2.append(self.investment)
            if(prevpos == position):
                in3.append(0)
            else:
                if(position=='cash'):
                    in3.append(-1)
                else:
                    in3.append(1)
            in4.append(position)
            in5.append(shares)

            prev_close = row['close']

        ret = pd.DataFrame({'date': in1, 'investment': in2, 'buy_sell_hold': in3, 'position': in4, 'shares': in5})
        return ret

    def execute_fib(self, start, end, symbol, short, long):
        fib = Indicator(self.client, symbol)
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
        in1, in2, in3, in4, in5 = [], [], [], [], []

        position = 'cash'
        prevpos = 'cash'
        shares = 0
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
                    prevpos = position
                    position = 'long'
                    buy_price = price
                elif (row['signal'] < row['MACD']) and (position == 'long') and price > buy_price: # sell
                    self.investment = shares * row['close'] - self.commission
                    shares = 0
                    prevpos = position
                    position = 'cash'
                    buy_price = 0
                else:
                    prevpos = position

            if(prevpos == position):
                in3.append(0)
            else:
                if(position=='cash'):
                    in3.append(-1)
                else:
                    in3.append(1)
            in4.append(position)
            in5.append(shares)
            
            if position == 'long':
                in1.append(index[1].date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index[1].date())
                in2.append(self.investment)

            hi_level, lo_level = get_level(price)

        ret = pd.DataFrame({'date': in1, 'investment': in2, 'buy_sell_hold': in3, 'position': in4, 'shares': in5})
        return ret

    def getVal(self):
        return self.investment

trading_client = StockHistoricalDataClient('PKV2FZHX6E4RMGFON60X',
                                           'GMKXVZ3W4MqenB6SbcSKM8h9WnvYBZn0qdZ86E6n')

x = datetime(2020, 5, 17)
y = datetime(2022, 5, 17)

test = Strategy(trading_client, 10000, 5)
#print(test.execute_control(x, y, "AAPL").to_string())
#print(test.execute_atr(x, y, "AAPL", 50, 100).to_string())
#print(test.execute_fib(x, y, "AAPL", 50, 100).to_string())
#print(test.execute_bb(x, y, "AAPL", 50, 2).to_string())
#print(test.execute_ma(x, y, "AAPL", 50, 100).to_string())
#print(test.execute_rsi(x, y, "AAPL", 20, 70, 30).to_string())



