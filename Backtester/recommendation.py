from Backtester import strategy
from .strategy import Strategy
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime

import pandas as pd
import numpy as np

class Recommendation:
    def __init__(self, client, start_date, end_date, investment=10000, commission=5):
        self.start_date = start_date
        self.end_date = end_date
        self.Strategy = Strategy(client, investment, commission)
    
    def generate_strategy(self, strat_name, symbol, **kwargs):
        strategy_output = None
        # Add strategies here as developed.
        try:
            if strat_name == "control":
                strategy_output = self.Strategy.execute_control(self.start_date,self.end_date,symbol)
            elif strat_name == "ma":
                strategy_output = self.Strategy.execute_ma(self.start_date,self.end_date,symbol,kwargs['short'],kwargs['long'])
            elif strat_name == "rsi":
                strategy_output = self.Strategy.execute_rsi(self.start_date,self.end_date,symbol,kwargs['days'],kwargs['over'],kwargs['under'])
            elif strat_name == "bb":
                strategy_output = self.Strategy.execute_bb(self.start_date,self.end_date,symbol,kwargs['ma_days'],kwargs['num_std_devs'])
            elif strat_name == "atr":
                strategy_output = self.Strategy.execute_atr(self.start_date,self.end_date,symbol,kwargs['short'],kwargs['long'])
            elif strat_name == "fib":
                strategy_output = self.Strategy.execute_fib(self.start_date,self.end_date,symbol,kwargs['short'],kwargs['long'])
            else:
                raise NameError("No strategy called " + strat_name + "\n")
        except KeyError:
            print("An exception occurred. Check the input arguments for the provided strategy.")
        return strategy_output

    def percent_difference(self, strat_result, control_result):
        return (strat_result - control_result)/control_result*100

    def generate_analysis(self, strat_name, symbol, **kwargs):
        #Compare strategy results with control. 
        #Can change in future to compare strategy results with other strategies. Needs work with input formats, but possible.
        control = self.generate_strategy("control",symbol).drop(labels=["buy_sell_hold","position","shares"], axis=1).rename(columns={"investment":"control"})
        strategy = self.generate_strategy(strat_name, symbol, **kwargs)
        df1 = strategy.merge(control, how="left")
        df1["%_diff"] = self.percent_difference(df1['investment'],df1['control'])
        return df1

    def loss_analysis(self, df, tolerance):
        # Retrieve rows where strategy underperforms market by more than tolerance percentage
        loss_df = df[df["%_diff"] < tolerance * -1].copy()
        #Group by consecutive days
        loss_df['grp_date'] = loss_df['date'].diff().dt.days.ne(1).cumsum()
        #print(loss_df)    
        #plt.scatter(df['date'][df.buy_sell_hold == -1.0], df['investment'][df.buy_sell_hold == -1.0], c='r', marker="v")
        #plt.scatter(df['date'][df.buy_sell_hold == 1.0], df['investment'][df.buy_sell_hold == 1.0], c='g', marker="^")
        #plt.plot(df['date'], df['investment'])
        #plt.plot(df['date'], df['control'])
        #plt.xlabel('Date')
        #plt.ylabel('Investment')
        #plt.title("Investment")
        #buy = mlines.Line2D([], [], color='r', marker='v', linestyle='None', markersize=5, label='Sell marker')
        #sell = mlines.Line2D([], [], color='g', marker='^', linestyle='None', markersize=5, label='Buy marker')
        #plt.legend(handles=[buy, sell])
        return loss_df["%_diff"].mean()
    

    
trading_client = StockHistoricalDataClient('PKV2FZHX6E4RMGFON60X',
                                           'GMKXVZ3W4MqenB6SbcSKM8h9WnvYBZn0qdZ86E6n')

x = datetime(2020, 5, 17)
y = datetime(2022, 5, 17)

test = Recommendation(trading_client, x, y)
#df = test.generate_analysis("rsi","AAPL",days=20,over=70,under=30)
#print(test.loss_analysis(df, 5))

df = test.generate_analysis("atr","AAPL",short=50,long=100)
print(test.loss_analysis(df, 5))