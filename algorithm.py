from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.common.exceptions import APIError

from datetime import datetime
import Indicator as Indicator
import pandas as pd
import numpy as np

import psycopg2

class Algorithm:
    def __init__(self, api_key, h_client, t_client, investment, commission):
        self.api_key = api_key
        self.h_client = h_client
        self.t_client = t_client
        self.investment = investment
        self.commission = commission
        
        # connect to the DB
        self.conn = psycopg2.connect(
                        host="",
                        database="",
                        user="",
                        password=""
                        )
                       
        self.cur = self.conn.cursor()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cur.close()
        self.conn.close()
    
    
    def execute_ma(self, start, symbol, short, long):
        today = datetime.now()

        ma = Indicator.Indicator(self.h_client, symbol)
        ma_short = ma.moving_average(start, today, short)
        ma_short.rename(columns = {'moving average':'short'}, inplace = True)
        ma_long = ma.moving_average(start, today, long)
        ma_long.rename(columns = {'moving average':'long'}, inplace = True)
        position = 'cash'
        prevpos = 'cash'

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = today,
                                          adjustment='all')

        bars = self.h_client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))

        data = bars['close']
        df = pd.concat([ma_short, ma_long, data], axis=1)
        shares = 0
        prev_close = 0

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

            prev_close = row['close']

        # retrieving user_id from DB
        user_id_query = """SELECT id 
                            FROM user_customuser 
                            WHERE api_key='{key}' """.format(key = self.api_key)
        self.cur.execute(user_id_query)
        print("Selecting user_id...")
        fetched0 = self.cur.fetchall()
        print(fetched0)
        user_id = fetched0[0][0]
        print(user_id)

        # retrieving number of currently owned stocks of the symbol from DB
        stocks_query = """SELECT shares
                            FROM user_activatedalgorithm 
                            WHERE algorithm='moving-average' 
                                AND stock_name='{stock_name}' 
                                AND user_id={id}""".format(stock_name = symbol, id = user_id)
        self.cur.execute(stocks_query)
        print("Selecting shares...")
        fetched1 = self.cur.fetchall()
        print(fetched1)
        current_shares = fetched1[0][0]
        print(current_shares)

        print(position)
        print(shares)
        print(prev_close)

        # Testing Selling
        # position = 'cash'
        # current_shares = 5
        # Testing Buying
        # position = 'long'
        # shares = 5

        try:
            # gets the currently available shares in case if the user manually sold stocks
            updated_shares = min(float(self.t_client.get_open_position(symbol).qty), current_shares)
            print(updated_shares)
        except:
            updated_shares = 0

        if (position == 'cash'):
            if (updated_shares > 0):
                # sell order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=updated_shares,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )

                update_query = """UPDATE user_activatedalgorithm
                                    SET shares=0
                                    WHERE algorithm='moving-average'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'sell', 'Moving Average', symbol, updated_shares, prev_close, user_id))

                print("SOLD %f STOCKS" % updated_shares)

            else:
                print("NO %s STOCKS OF MA ALGO TO SELL" % symbol)

        if (position == 'long'):
            if (current_shares == 0):
                # buy order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=shares,
                                        side=OrderSide.BUY,
                                        time_in_force=TimeInForce.DAY
                                    )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares={qty}
                                    WHERE algorithm='moving-average'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(qty=shares, stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'buy', 'Moving Average', symbol, shares, prev_close, user_id))

                print("BOUGHT %f STOCKS" % shares)
            else:
                print("CONTINUE HOLDING ONTO %f of %s STOCKS OF MA ALGO TO SELL" % (current_shares, symbol))

        self.conn.commit()

        ret = "\nEND OF MA FUNCTION TESTING\n"
        return ret
    
    def execute_rsi(self, start, symbol, days, over, under):
        today = datetime.now()

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = today,
                                          adjustment='all')
        bars = self.h_client.get_stock_bars(request_params).df
        res = Indicator.Indicator(self.h_client, symbol)
        rsi = res.RSI(start, today, days)
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
        # temp, bsh, sh, p = [], [], [], []
        prevpos = 'cash'
        pos = 'cash'
        prev_close = 0

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
            prev_close = bars['close'][i]

        # retrieving user_id from DB
        user_id_query = """SELECT id 
                            FROM user_customuser 
                            WHERE api_key='{key}' """.format(key = self.api_key)
        self.cur.execute(user_id_query)
        print("Selecting user_id...")
        fetched0 = self.cur.fetchall()
        print(fetched0)
        user_id = fetched0[0][0]
        print(user_id)

        # retrieving number of currently owned stocks of the symbol from DB
        stocks_query = """SELECT shares
                            FROM user_activatedalgorithm 
                            WHERE algorithm='relative-strength-indicator' 
                                AND stock_name='{stock_name}' 
                                AND user_id={id}""".format(stock_name = symbol, id = user_id)
        self.cur.execute(stocks_query)
        print("Selecting shares...")
        fetched1 = self.cur.fetchall()
        print(fetched1)
        current_shares = fetched1[0][0]
        print(current_shares)

        print(pos)
        print(shares)

        # Testing Selling
        # current_shares = 5
        # Testing Buying
        # position = 'long'
        # shares = 5

        try:
            # gets the currently available shares in case if the user manually sold stocks
            updated_shares = min(float(self.t_client.get_open_position(symbol).qty), current_shares)
            print(updated_shares)
        except:
            updated_shares = 0

        if (pos == 'cash'):
            if (updated_shares > 0):
                # sell order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=updated_shares,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares=0
                                    WHERE algorithm='relative-strength-indicator'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'sell', 'RSI', symbol, updated_shares, prev_close, user_id))

                print("SOLD %f STOCKS" % updated_shares)
            else:
                print("NO %s STOCKS OF RSI ALGO TO SELL" % symbol)
        if (pos == 'long'):
            if (current_shares == 0):
                # buy order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=shares,
                                        side=OrderSide.BUY,
                                        time_in_force=TimeInForce.DAY
                                    )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares={qty}
                                    WHERE algorithm='relative-strength-indicator'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(qty=shares, stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'buy', 'RSI', symbol, shares, prev_close, user_id))

                print("BOUGHT %f STOCKS" % shares)
            else:
                print("CONTINUE HOLDING ONTO %f of %s STOCKS OF RSI ALGO TO SELL" % (current_shares, symbol))

        self.conn.commit()

        ret = "\nEND OF RSI FUNCTION TESTING\n"
        # ret = pd.DataFrame({'date': in1, 'investment': temp, 'buy_sell_hold': bsh, 'position': p, 'shares': sh})
        return ret

    def execute_bb(self, start, symbol, ma_days, num_std_devs):
        today = datetime.now()

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = today,
                                          adjustment='all')
        bars = self.h_client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))
        
        bb = Indicator.Indicator(self.h_client, symbol)
        bands = bb.bollinger_bands(start, today, ma_days, num_std_devs)
        signals = pd.DataFrame()
        signals['ma'] = bars['close'].rolling(window=ma_days).mean()
        signals['signal'] = 0.0

        signals['signal'][ma_days:] = np.where(bars['close'][ma_days:] > bands['upper band'][ma_days:], -1.0, 0.0)
        signals['signal'][ma_days:] = np.where(bars['close'][ma_days:] < bands['lower band'][ma_days:], 1.0, signals['signal'][ma_days:])
        signals['positions'] = signals['signal'].diff()

        positions = signals.positions.values.tolist()
        shares = 0
        prevpos = 'cash'
        pos = 'cash'
        prev_close = 0

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
            prev_close = bars['close'][i]
        
        # retrieving user_id from DB
        user_id_query = """SELECT id 
                            FROM user_customuser 
                            WHERE api_key='{key}' """.format(key = self.api_key)
        self.cur.execute(user_id_query)
        print("Selecting user_id...")
        fetched0 = self.cur.fetchall()
        print(fetched0)
        user_id = fetched0[0][0]
        print(user_id)

        # retrieving number of currently owned stocks of the symbol from DB
        stocks_query = """SELECT shares
                            FROM user_activatedalgorithm 
                            WHERE algorithm='bollinger-bands' 
                                AND stock_name='{stock_name}' 
                                AND user_id={id}""".format(stock_name = symbol, id = user_id)
        self.cur.execute(stocks_query)
        print("Selecting shares...")
        fetched1 = self.cur.fetchall()
        print(fetched1)
        current_shares = fetched1[0][0]
        print(current_shares)

        print(pos)
        print(shares)

        # Testing Selling
        # current_shares = 5
        # Testing Buying
        # position = 'long'
        # shares = 5

        try:
            # gets the currently available shares in case if the user manually sold stocks
            updated_shares = min(float(self.t_client.get_open_position(symbol).qty), current_shares)
            print(updated_shares)
        except:
            updated_shares = 0

        if (pos == 'cash'):
            if (updated_shares > 0):
                # sell order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=updated_shares,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares=0
                                    WHERE algorithm='bollinger-bands'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'sell', 'Bollinger Bands', symbol, updated_shares, prev_close, user_id))

                print("SOLD %f STOCKS" % updated_shares)
            else:
                print("NO %s STOCKS OF BB ALGO TO SELL" % symbol)
        if (pos == 'long'):
            if (current_shares == 0):
                # buy order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=shares,
                                        side=OrderSide.BUY,
                                        time_in_force=TimeInForce.DAY
                                    )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares={qty}
                                    WHERE algorithm='bollinger-bands'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(qty=shares, stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'buy', 'Bollinger Bands', symbol, shares, prev_close, user_id))

                print("BOUGHT %f STOCKS" % shares)
            else:
                print("CONTINUE HOLDING ONTO %f of %s STOCKS OF BB ALGO TO SELL" % (current_shares, symbol))

        self.conn.commit()
        
        ret = "\nEND OF BB FUNCTION TESTING\n"
        return ret

    def execute_atr(self, start, symbol, short, long):
        today = datetime.now()

        atr = Indicator.Indicator(self.h_client, symbol)
        atr_short = atr.ATR(start, today, short)
        atr_short.rename(columns = {'ATR':'short'}, inplace = True)
        atr_long = atr.ATR(start, today, long)
        atr_long.rename(columns = {'ATR':'long'}, inplace = True)
        position = 'cash'
        prevpos = 'cash'
        shares = 0
        prev_close = 0

        request_params = StockBarsRequest(symbol_or_symbols=[symbol],
                                          timeframe = TimeFrame.Day,
                                          start = start,
                                          end = today,
                                          adjustment = 'all')

        bars = self.h_client.get_stock_bars(request_params).df
        bars = bars.reset_index()
        del bars["symbol"]
        bars = bars.set_index('timestamp')
        bars = bars.truncate(before=pd.Timestamp(start, tz='US/Pacific'))
        
        data = bars['close']

        df = pd.concat([atr_short, atr_long, data], axis=1)

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

            prev_close = row['close']

        # retrieving user_id from DB
        user_id_query = """SELECT id 
                            FROM user_customuser 
                            WHERE api_key='{key}' """.format(key = self.api_key)
        self.cur.execute(user_id_query)
        print("Selecting user_id...")
        fetched0 = self.cur.fetchall()
        print(fetched0)
        user_id = fetched0[0][0]
        print(user_id)

        # retrieving number of currently owned stocks of the symbol from DB
        stocks_query = """SELECT shares
                            FROM user_activatedalgorithm 
                            WHERE algorithm='average-true-range' 
                                AND stock_name='{stock_name}' 
                                AND user_id={id}""".format(stock_name = symbol, id = user_id)
        self.cur.execute(stocks_query)
        print("Selecting shares...")
        fetched1 = self.cur.fetchall()
        print(fetched1)
        current_shares = fetched1[0][0]
        print(current_shares)

        print(position)
        print(shares)

        # Testing Selling
        # current_shares = 5
        # Testing Buying
        # position = 'long'
        # shares = 5

        try:
            # gets the currently available shares in case if the user manually sold stocks
            updated_shares = min(float(self.t_client.get_open_position(symbol).qty), current_shares)
            # deals with negative shares
            if (updated_shares < 0):
                updated_shares = 0
            print(updated_shares)
        except:
            updated_shares = 0

        if (position == 'cash'):
            if (updated_shares > 0):
                # sell order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=updated_shares,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares=0
                                    WHERE algorithm='average-true-range'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'sell', 'Average True Range', symbol, updated_shares, prev_close, user_id))

                print("SOLD %f STOCKS" % updated_shares)
            else:
                print("NO %s STOCKS OF ATR ALGO TO SELL" % symbol)
        if (position == 'long'):
            if (current_shares == 0):
                # buy order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=shares,
                                        side=OrderSide.BUY,
                                        time_in_force=TimeInForce.DAY
                                    )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares={qty}
                                    WHERE algorithm='average-true-range'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(qty=shares, stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'buy', 'Average True Range', symbol, shares, prev_close, user_id))

                print("BOUGHT %f STOCKS" % shares)
            else:
                print("CONTINUE HOLDING ONTO %f of %s STOCKS OF ATR ALGO TO SELL" % (current_shares, symbol))

        self.conn.commit()
        
        ret = "\nEND OF ATR FUNCTION TESTING\n"
        return ret

    def execute_fib(self, start, symbol, short, long):
        today = datetime.now()

        fib = Indicator.Indicator(self.h_client, symbol)
        fib_signals = fib.MACD(start, today, short, long)
        fib_levels = fib.FibLevels(start, today)

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
                                          end = today,
                                          adjustment = 'all')

        bars = self.h_client.get_stock_bars(request_params)
        data = bars.df['close']
        df2 = data.to_frame()

        df = pd.concat([fib_signals, data], axis=1)

        position = 'cash'
        prevpos = 'cash'
        shares = 0
        hi_level, lo_level = None, None
        buy_price = 0
        prev_close = 0

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

            hi_level, lo_level = get_level(price)

            prev_close = row['close']

        # retrieving user_id from DB
        user_id_query = """SELECT id 
                            FROM user_customuser 
                            WHERE api_key='{key}' """.format(key = self.api_key)
        self.cur.execute(user_id_query)
        print("Selecting user_id...")
        fetched0 = self.cur.fetchall()
        print(fetched0)
        user_id = fetched0[0][0]
        print(user_id)

        # retrieving number of currently owned stocks of the symbol from DB
        stocks_query = """SELECT shares
                            FROM user_activatedalgorithm 
                            WHERE algorithm='MACD-with-fibonacci-levels' 
                                AND stock_name='{stock_name}' 
                                AND user_id={id}""".format(stock_name = symbol, id = user_id)
        self.cur.execute(stocks_query)
        print("Selecting shares...")
        fetched1 = self.cur.fetchall()
        print(fetched1)
        current_shares = fetched1[0][0]
        print(current_shares)

        print(position)
        print(shares)

        # Testing Selling
        # current_shares = 5
        # Testing Buying
        # position = 'long'
        # shares = 5

        try:
            # gets the currently available shares in case if the user manually sold stocks
            updated_shares = min(float(self.t_client.get_open_position(symbol).qty), current_shares)
            print(updated_shares)
        except:
            updated_shares = 0

        if (position == 'cash'):
            if (updated_shares > 0):
                # sell order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=updated_shares,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY
                )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares=0
                                    WHERE algorithm='MACD-with-fibonacci-levels'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'sell', 'MACD with Fibonacci levels', symbol, updated_shares, prev_close, user_id))

                print("SOLD %f STOCKS" % updated_shares)
            else:
                print("NO %s STOCKS OF FIB ALGO TO SELL" % symbol)
        if (position == 'long'):
            if (current_shares == 0):
                # buy order
                market_order_data = MarketOrderRequest(
                                        symbol=symbol,
                                        qty=shares,
                                        side=OrderSide.BUY,
                                        time_in_force=TimeInForce.DAY
                                    )
                market_order = self.t_client.submit_order(
                                    order_data=market_order_data
                                )
                update_query = """UPDATE user_activatedalgorithm
                                    SET shares={qty}
                                    WHERE algorithm='MACD-with-fibonacci-levels'
                                    AND stock_name='{stock_name}'
                                    AND user_id={id}""".format(qty=shares, stock_name = symbol, id = user_id)
                self.cur.execute(update_query)

                log_query = """INSERT INTO user_tradelog (trade_time, trade_type, algorithm_name, stock_name, shares, avg_price, user_id)
                                VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                self.cur.execute(log_query, (today, 'buy', 'MACD with Fibonacci levels', symbol, shares, prev_close, user_id))

                print("BOUGHT %f STOCKS" % shares)
            else:
                print("CONTINUE HOLDING ONTO %f of %s STOCKS OF FIB ALGO TO SELL" % (current_shares, symbol))

        self.conn.commit()
        
        ret = "\nEND OF FIB FUNCTION TESTING\n"
        return ret

    def getVal(self):
        return self.investment
    
    def checkDB(self):
        # testing DB functions
        print("TABLES IN DB:\n")
        self.cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ")
        table_names = [row[0] for row in self.cur.fetchall()]
        print(table_names)
        print('\n')

        print("ENTRIES IN TRADELOG:\n")
        self.cur.execute("SELECT * FROM user_tradelog")
        # extract column names from the cursor description
        col_names = [desc[0] for desc in self.cur.description]
        #print colums name
        print(col_names)
        print('\n')
        # print all rows
        rows = self.cur.fetchall()
        for row in rows:
            print(row)
        print('\n')

        print("USERS AND API KEYS IN USER TABLE:\n")
        self.cur.execute("SELECT username, api_key, secret_key FROM user_customuser WHERE id=1")
        rows = self.cur.fetchall()
        for row in rows:
            print(row)
        print('\n')
        # END OF TESTING FOR DB FUNCTIONS

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TESTING FUNCTIONS:

x = datetime(2020, 5, 17)
y = datetime(2022, 5, 17)

# TESTING USING API KEY AND SECRET KEY:
h_client = StockHistoricalDataClient('',
                                           '')
t_client = TradingClient('',
                         '',
                         paper=True)


# INSERT API KEY TO TEST:
test = Algorithm("", h_client, t_client, 10000, 5)

#print(test.execute_ma(y, "AAPL", 50, 100))
#print(test.execute_rsi(y, "SPY", 20, 70, 30))
#print(test.execute_bb(y, "AAPL", 50, 2))
#print(test.execute_atr(y, "MSFT", 50, 100)) # negative quantity of stock causing problem. see error msg from running this: https://alpaca.markets/support/insufficient-quantity-available
#print(test.execute_fib(y, "AAPL", 50, 100))

#test.checkDB()