from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
import alpaca_trade_api as tradeapi
import datetime
import pytz


class AlpacaAccount:
    def __init__(self, api_key, secret_key):
        # self.account_linked = None
        # self.client = None
        self.base_url = "https://paper-api.alpaca.markets"

        if api_key == '' or secret_key == '':
            print('User does not have api-key or secret-key')
            self.account_linked = False
            return

        self.client = TradingClient(api_key, secret_key, paper=True)
        try:
            self.client.get_account()
            self.API = tradeapi.REST(api_key, secret_key, api_version="v2", base_url=self.base_url)
        except:
            print("account is not found")
            self.account_linked = False
        else:
            print("account is found")
            self.account_linked = True

    def get_account(self):
        if not self.account_linked:
            return None
        return self.client.get_account()

    def get_positions(self):
        if not self.account_linked:
            return None
        return self.client.get_all_positions()

    def get_activities(self):
        if not self.account_linked:
            return None
        return self.API.get_activities()

    def get_stocks_in_watchlist(self):
        if not self.account_linked:
            return None

        watchlist_id = self.API.get_watchlists()[0].id
        watchlist = self.API.get_watchlist(watchlist_id)
        symbols = [asset['symbol'] for asset in watchlist.assets]

        # create list of stock dictionary, each dictionary contains symbol, current price, last market close price
        data = []
        for i in range(len(symbols)):
            current_price = self.API.get_latest_bar(symbols[i]).c
            close_time = datetime.datetime.now(tz=pytz.timezone('US/Eastern')) \
                             .replace(hour=16, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)

            last_market_close_price = self.API.get_bars([symbols[i]], timeframe=TimeFrame(1, TimeFrameUnit('Hour')),
                                                        start=(close_time - datetime.timedelta(minutes=1)).isoformat(),
                                                        end=close_time.isoformat())[0].c
            data.append(
                {"symbol": symbols[i],
                 "current_price": current_price,
                 "last_close_price": last_market_close_price,
                 "price_change": current_price - last_market_close_price,
                 "price_change_perc": (current_price - last_market_close_price) / last_market_close_price * 100})

        return data
