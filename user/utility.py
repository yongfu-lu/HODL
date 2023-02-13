from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class AlpacaAccount:
    def __init__(self, api_key, secret_key):
        self.account_linked = None
        self.client = None

        if api_key == '' or secret_key == '':
            print('User does not have api-key or secret-key')
            self.account_linked = False
            return

        self.client = TradingClient(api_key, secret_key, paper=True)
        try:
            self.client.get_account()
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