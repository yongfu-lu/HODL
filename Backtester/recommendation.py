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
        self.investment = investment
        self.Strategy = Strategy(client, investment, commission)
        self.data = None
    
    def generate_strategy(self, strat_name, symbol, **kwargs):
        strategy_output = None
        # Add strategies here as developed.
        try:
            self.Strategy.setVal(self.investment)
            self.strategy_df = None
            if strat_name == "control":
                strategy_output = self.Strategy.execute_control(self.start_date,self.end_date,symbol)
            elif strat_name == "moving-average":
                strategy_output = self.Strategy.execute_ma(self.start_date,self.end_date,symbol,kwargs['short'],kwargs['long'])
            elif strat_name == "relative-strength-indicator":
                strategy_output = self.Strategy.execute_rsi(self.start_date,self.end_date,symbol,kwargs['days'],kwargs['over'],kwargs['under'])
            elif strat_name == "bollinger-bands":
                strategy_output = self.Strategy.execute_bb(self.start_date,self.end_date,symbol,kwargs['days'],kwargs['num_std_dev'])
            elif strat_name == "average-true-range":
                strategy_output = self.Strategy.execute_atr(self.start_date,self.end_date,symbol,kwargs['short'],kwargs['long'])
            elif strat_name == "MACD-with-fibonacci-levels":
                strategy_output = self.Strategy.execute_fib(self.start_date,self.end_date,symbol,kwargs['short'],kwargs['long'])
            else:
                raise NameError("No strategy called " + strat_name + "\n")
        except KeyError as e:
            print(e, "An exception occurred. Check the input arguments for the provided strategy.")
        return strategy_output

    def percent_difference(self, strat_result, control_result):
        return (strat_result - control_result)/control_result*100

    def generate_analysis(self, strat_name, symbol, **kwargs):
        try:
            #Compare strategy results with control. 
            #Can change in future to compare strategy results with other strategies. Needs work with input formats, but possible.
            self.ctrl_df = self.generate_strategy("control",symbol)
            control = self.ctrl_df.drop(labels=["buy_sell_hold","position","shares"], axis=1).rename(columns={"investment":"control"})
            self.strategy_df = self.generate_strategy(strat_name, symbol, **kwargs)
            data = self.strategy_df.merge(control, how="left")
            data["%_diff"] = self.percent_difference(data['investment'],data['control'])
            # print(kwargs)
            # print(strat_name)
            # print(df1)
            return data["%_diff"].mean(), data.iloc[-1]['investment'], data.iloc[-1]['control']
        except Exception as e:
            print(e, strat_name, symbol, kwargs)

    def get_strategy(self):
        return self.strategy_df
    
    def get_control(self):
        return self.ctrl_df
    
    # def get_under_dates(self,tolerance):
    #     try:
    #         loss_df = self.data[self.data["%_diff"] < tolerance * -1].copy()
    #         loss_df['grp_date'] = loss_df['date'].diff().dt.days.ne(1).cumsum()
    #         return
    #     except:
    #         return
    
    # def loss_analysis(self, strat_name, symbol, tolerance, **kwargs):
    #     try:
    #         df = self.generate_analysis(strat_name,symbol,**kwargs)
    #         # Retrieve rows where strategy underperforms market by more than tolerance percentage
    #         loss_df = df[df["%_diff"] < tolerance * -1].copy()
    #         #Group by consecutive days
    #         #loss_df['grp_date'] = loss_df['date'].diff().dt.days.ne(1).cumsum()
    #         return loss_df["%_diff"].mean(), df.iloc[-1]['investment'], df.iloc[-1]['control']
    #     except Exception as e:
    #         print(e, "Unable to analyze")
    #         return -1,-1,-1   