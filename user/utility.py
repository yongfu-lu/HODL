from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class AlpacaAccount:
    def __init__(self, api_key, secret_key):
        self.account = None
        self.positions = []
        self.api_key = api_key
        self.secret_key = secret_key

    def link_account(self):
        if self.api_key == '' or self.secret_key == '':
            print('account is not found')
            return False

        trading_client = TradingClient(self.api_key, self.secret_key, paper=True)
        try:
            self.account = trading_client.get_account()
            self.positions = trading_client.get_all_positions()
        except:
            print("account is not found")
            return False
        else:
            print("account is found")
            return True
