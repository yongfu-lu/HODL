from Backtester import strategy
from .strategy import Strategy
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime

import pandas as pd
import numpy as np
import pygad as pg
import random

class Recommendation:
    def __init__(self, client, start_date, end_date, investment=10000, commission=5, optimal_params={}):
        self.start_date = start_date
        self.end_date = end_date
        self.investment = investment
        self.Strategy = Strategy(client, investment, commission)
        self.data = None
        self.optimal_params = optimal_params
    
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
        except Exception as e:
            print("Generate Strategy Error: ", e)
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
            self.data = data
            # print(kwargs)
            # print(strat_name)
            return data["%_diff"].mean(), data.iloc[-1]['investment'], data.iloc[-1]['control']
        except Exception as e:
            print("Generate Analysis Error: ", e, strat_name, symbol, kwargs)
            #return -1,-1,-1

    def get_strategy(self):
        return self.strategy_df
    
    def get_control(self):
        return self.ctrl_df
    
    def optimize_params(self, strat_name, symbol, num_people=5, num_generations=3):
        def fitness(ga, solution, solution_idx):
            x, y, z = solution
            try:
                if strat_name == "moving-average" or strat_name == "average-true-range" or strat_name == 'MACD-with-fibonacci-levels':
                    if x >= y:
                        # Return a high penalty for invalid solutions
                        return -99999999
                    result = self.generate_analysis(strat_name, symbol, short=int(x), long=int(y))
                elif strat_name == "relative-strength-indicator":
                    if z >= y:
                        # Return a high penalty for invalid solutions
                        return -99999999
                    result = self.generate_analysis(strat_name, symbol, days=int(x), over=int(y), under=int(z))
                elif strat_name == "bollinger-bands":
                    result = self.generate_analysis(strat_name, symbol, days=int(x), num_std_dev=int(y))
                #print(result)
                return result[0]
            except Exception as e:
                print(e)
                return -99999999

        def print_generation(ga_instance):
            print("Generation = ", ga_instance.generations_completed)
        
        #num_genes = 2
        gene_space = [(1,100),(0,100),(0,100)] if strat_name == 'relative-strength-indicator' else [(1, 100), (1, 100)]

        # Define the initial population
        if (strat_name, symbol) in self.optimal_params:
            initial_population = [self.optimal_params[(strat_name,symbol)]]
        else:
            initial_population = []
        num_individuals = num_people - len(initial_population)

        for j in range(num_individuals):
            if strat_name == "moving-average" or strat_name == "average-true-range" or strat_name == 'MACD-with-fibonacci-levels':
                init_x = 9999999
                init_y = -9999999
                while(init_x >= init_y):
                    init_x =  random.uniform(gene_space[0][0], gene_space[0][1])
                    init_y =  random.uniform(gene_space[1][0], gene_space[1][1])
                initial_population.append([init_x,init_y,-1])
            elif strat_name == "relative-strength-indicator":
                init_y = -9999999
                init_z = 9999999
                while(init_z >= init_y):
                    init_x =  random.uniform(gene_space[0][0], gene_space[0][1])
                    init_y =  random.uniform(gene_space[1][0], gene_space[1][1])
                    init_z =  random.uniform(gene_space[2][0], gene_space[2][1])
                initial_population.append([init_x,init_y,init_z])
            elif strat_name == "bollinger-bands":
                init_x =  random.uniform(gene_space[0][0], gene_space[0][1])
                init_y =  random.uniform(gene_space[1][0], gene_space[1][1])
                initial_population.append([init_x,init_y,-1])
        
        #print(len(initial_population))

        ga_instance = pg.GA(num_generations=num_generations, 
                            num_parents_mating=3,
                            initial_population=initial_population, 
                            #parent_selection_type="tournament",
                            fitness_func=fitness,
                            mutation_type="Adaptive",
                            mutation_probability=[1.0, 0.5],
                            on_generation=print_generation)

        # Run the GA optimization
        print("starting optimization")
        ga_instance.run()
        print("optimization complete")

        solution, solution_fitness, solution_idx = ga_instance.best_solution()
        #print("Parameters of the best solution : ", solution)
        #print("Fitness value of the best solution : ", solution_fitness)
        return solution, solution_fitness
    
    def update_dates(self, start, end):
        if (end > start):
            self.start_date = start
            self.end_date = end
    
    def get_loss_dates(self,tolerance=0,days_under=5):
        try:
            loss_dict = {}
            loss_df = self.data[self.data["%_diff"] < tolerance * -1].copy()
            loss_df['grp_date'] = pd.to_datetime(loss_df['date']).diff().dt.days.ge(5).cumsum()
            if (len(loss_df) == 0):
                return loss_dict
            #print(loss_df)
            num_periods = loss_df['grp_date'].iloc[-1]
            #print("Numperiods: ", num_periods)
            for i in range(num_periods+1):
                period_df = loss_df[loss_df.grp_date == i]
                #print (period_df.shape[0])
                if period_df.shape[0] >= days_under:
                    start = pd.to_datetime(period_df['date']).iloc[0]
                    end = pd.to_datetime(period_df['date']).iloc[-1]
                    loss_dict[(start,end)] = period_df.drop(['grp_date'], axis=1)
            print(len(loss_dict))
            return loss_dict
        except Exception as e:
            print("Get Loss Dates Error: ", e )
            print(e)