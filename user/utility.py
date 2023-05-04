from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
import alpaca_trade_api as tradeapi
import datetime
import pytz


class AlpacaAccount:
    def __init__(self, api_key, secret_key):
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
            self.account_linked = False
        else:
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

        try:
            watchlist_id = self.API.get_watchlists()[0].id
            watchlist = self.API.get_watchlist(watchlist_id)
            symbols = [asset['symbol'] for asset in watchlist.assets]
            current_time = datetime.datetime.now(tz=pytz.timezone('US/Eastern'))
        except:
            return None

        # create list of stock dictionary, each dictionary contains symbol, current price, last market close price
        assets = []
        for i in range(len(symbols)):
            try:
                current_price = self.API.get_latest_bar(symbols[i]).c
                last_market_close_price =self.API.get_bars(symbol=symbols[i],
                                     timeframe=TimeFrame(1, TimeFrameUnit('Day')),
                                     start=(current_time - datetime.timedelta(days=7)).isoformat(),
                                     end=(current_time - datetime.timedelta(hours=1)).isoformat(),
                                     limit=7)[-2].c

                assets.append(
                    {"symbol": symbols[i],
                     "current_price": current_price,
                     "last_close_price": last_market_close_price,
                     "price_change": current_price - last_market_close_price,
                     "price_change_perc": (current_price - last_market_close_price) / last_market_close_price * 100})

            except:
                pass

        return {"id": watchlist_id, "assets": assets}

    def add_to_watchlist(self, watchlist_id: str, symbol: str):
        if not self.account_linked:
            return
        self.API.add_to_watchlist(watchlist_id, symbol)

    def remove_from_watchlist(self, watchlist_id: str, symbol: str):
        if not self.account_linked:
            return
        self.API.delete_from_watchlist(watchlist_id, symbol)

    def get_all_assets(self):
        search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        assets = self.client.get_all_assets(search_params)
        return [asset.symbol for asset in assets]

    def is_crypto(self, symbol):
        try:
            asset = self.API.get_asset(symbol)
        except:
            return False
        else:
            return not getattr(asset,'class') == 'us_equity'

    def get_history(self, period='7D'):
        if not self.account_linked:
            return
        return self.API.get_portfolio_history(period=period, timeframe='1D')