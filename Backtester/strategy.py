from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass,  AssetStatus
from datetime import datetime
from .Indicator import Indicator
import pandas as pd
import numpy as np

class Strategy:
    def __init__(self, client, investment, commission):
        self.investment = investment
        self.commission = commission
        self.client = client

    def get_stock_price(self, start, end, symbol):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')
        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = self.investment / bars['close'][0]
        pos = 'cash'
        prevpos = 'cash'
        
        for index, row in bars.iterrows():
            in1.append(index.date())
            in2.append(row['close'])
        
        ret = pd.DataFrame({'date': in1, 'stock_price': in2})
        return ret

    def execute_control(self, start, end, symbol):
        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')
        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = self.investment / bars['close'][0]
        pos = 'cash'
        prevpos = 'cash'
        
        for index, row in bars.iterrows():
            in1.append(index.date())
            in2.append(row['close'] * shares)
            in3.append(0)
            in4.append('long')
            in5.append(shares)
        in3[0] = 1
        
        ret = pd.DataFrame({'date': in1, 'investment': in2, 'buy_sell_hold': in3, 'position': in4, 'shares': in5})
        return ret

    def execute_roc(self, start, end, symbol, window, over, under):
        rocI = Indicator(self.client, symbol)
        roc = rocI.roc(start, end, window)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
        df = pd.concat([roc, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = 0

        for index, row in df.iterrows():
            if(row['ROC']<=under) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif (row['ROC']>=over) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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

    def execute_stochastic(self, start, end, symbol, window, over, under):
        stoI = Indicator(self.client, symbol)
        sto = stoI.stochastic_oscillator(start, end, window)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
        df = pd.concat([sto, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = 0

        for index, row in df.iterrows():
            if(row['k percent']<=under) and (row['d percent']<=under) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif (row['k percent']>=over) and (row['d percent']>=over) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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

    def execute_tsi(self, start, end, symbol, window1, window2, over, under):
        tsiI = Indicator(self.client, symbol)
        tsi = tsiI.tsi(start, end, window1, window2)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
        df = pd.concat([tsi, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = 0

        for index, row in df.iterrows():
            if(row['tsi']<=under) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif (row['tsi']>=over) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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

    def execute_uo(self, start, end, symbol, window, over, under):
        uoI = Indicator(self.client, symbol)
        uo = uoI.ultimate_oscillator(start, end, window)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
        df = pd.concat([uo, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = 0

        for index, row in df.iterrows():
            if(row['UO']<=under) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif (row['UO']>=over) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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

    def execute_emv(self, start, end, symbol, window1, window2, over, under):
        emvI = Indicator(self.client, symbol)
        emv = emvI.emv(start, end,  window1)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        emv['emv signal'] = emv['emv'].rolling(window2).mean()
        emv['diff'] = emv['emv'] - emv['emv signal']
        emv['sign'] = emv['diff'].apply(lambda x: '+' if x > 0 else '-')
        emv['cross'] = emv['sign'] != emv['sign'].shift()

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
        df = pd.concat([emv, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = 0
        
        for index, row in df.iterrows():
            if(row['emv']<=under) and (row['cross']) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif (row['emv']>=over) and (row['cross']) and (position == 'long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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

    def execute_aroon(self, start, end, symbol, window):
        aroonI = Indicator(self.client, symbol)
        aroon = aroonI.aroon(start, end, window)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = end,
                                          adjustment='all')

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
        aroon['diff'] = aroon['aroon up'] - aroon['aroon down']
        aroon['sign'] = aroon['diff'].apply(lambda x: '+' if x > 0 else '-')
        aroon['cross'] = aroon['sign'] != aroon['sign'].shift()
        
        df = pd.concat([aroon, data], axis=1)
        in1, in2, in3, in4, in5 = [], [], [], [], []
        shares = 0

        for index, row in df.iterrows():
            if(row['aroon up']>row['aroon down']) and (row['cross']) and (position=='cash'):
                shares = self.investment / row['close']
                self.investment = 0
                prevpos = position
                position = 'long'
            elif(row['aroon down']>row['aroon up']) and (row['cross']) and (position=='long'):
                self.investment = shares * row['close'] - self.commission
                shares = 0
                prevpos = position
                position = 'cash'
            else:
                prevpos = position
            if position == 'long':
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
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
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))
        
        res = Indicator(self.client, symbol)
        rsi = res.RSI(start, end, days)
        signals = pd.DataFrame()
        signals['rsi'] = rsi['RSI']
        signals['long'] = np.where(rsi['RSI'] > over, 1, 0)
        signals['short'] = np.where(rsi['RSI'] < under, -1, 0)
        signals['signal'] = signals['long'] + signals['short']

        in1 = []
        for index, row in bars.iterrows():
            in1.append(index.date())
        
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
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))
        
        bb = Indicator(self.client, symbol)
        bands = bb.bollinger_bands(start, end, ma_days, num_std_devs)
        signals = pd.DataFrame()
        signals['ma'] = bars['close'].rolling(window=ma_days).mean()
        signals['signal'] = 0.0
        in1 = []
        for index, row in bars.iterrows():
            in1.append(index.date())

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

        bars = self.client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))
        
        data = bars['close']

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
                in1.append(index.date())
                in2.append((row['close'] * shares))
            else:
                in1.append(index.date())
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

        bars = self.client.get_stock_bars(request_params).df
        
        data = bars['close']
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

    def setVal(self, amount):
        self.investment = amount

    def test_parameters(self, s, e, symbol, algorithm, investment, client, window = 0, rsi_over = 0, rsi_under = 0, short = 0, long = 0, std_dev = 0, window2 = 0):
        if(investment <= 0):
            return ("Investment must be positive.")
        if(s.year < 2016 or e.year < 2016):
            return ("Please input data ranges post-2016 for Alpaca compatibility.")
        if(datetime.now() < s):
            return ("Start date must be before the current day.")
        if(datetime.now() < e):
            return ("End date must be before the current day.")
        if(e < s):
            return ("End date must be chronologically after start date.")
        if(algorithm == 'RSI'):
            if(window <= 1):
                return ("The moving average window must be greater than 1.")
            if(rsi_over > 100 or rsi_over < 0):
                return ("RSI over and under must be between 0 to 100")
            if(rsi_under > 100 or rsi_under < 0):
                return ("RSI over and under must be between 0 to 100")
            if(rsi_under > rsi_over or rsi_under==rsi_over):
                return ("RSI over must be greater than RSI under.")
        if(algorithm=='STO' or algorithm =='UO' or algorithm =='TSI' or algorithm =='ROC' or algorithm=='EMV'):
            if(window <= 1):
                return ("The window must be greater than 1.")
            if(rsi_under > rsi_over or rsi_under==rsi_over):
                return ("Over threshold must be greater than under threshold.")
            if(algorithm=='TSI' or algorithm=='EMV'):
                if(window2 <= 1):
                    return ("The second window must be greater than 1.")
        if(algorithm =="ARN"):
            if(window <= 1):
                return ("The window must be greater than 1.")
        if(algorithm == 'MA' or algorithm == 'ATR' or algorithm == 'FIB'):
            if(short <= 0 or long <= 0):
                return ("Short and long periods must be greater than 0")
            if(short > long):
                return ("Long period must be greater than short period.")
        if(algorithm == 'BB'):
            if(window <= 1):
                return ("The moving average window must be greater than 1.")
            if(std_dev <= 0):
                return ("Standard deviation must be greater than 0.")

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
