from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser, ActivatedAlgorithm
from .utility import AlpacaAccount
from alpaca_trade_api.rest import APIError
from .all_US_assets import all_US_assets
from .all_tradable_stocks import all_tradable_stocks
from Backtester.recommendation import Recommendation
from Backtester.strategy import Strategy
from Backtester.plotting import Plot
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime, timedelta


import pandas as pd
import json

# Create your views here.
def register(request):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/user/login')

    context = {'form': form}
    return render(request, "user/register.html", context)


def login(request):
    message = None
    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user)
                return redirect('/user/dashboard')
            else:
                message = "Incorrect username or password."

    form = LoginForm()
    context = {'form': form, 'msg': message}
    return render(request, "user/login.html", context)


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    alpaca_account = AlpacaAccount(request.user.api_key, request.user.secret_key)
    activated_algorithms = ActivatedAlgorithm.objects.filter(user=request.user)
    context = {
        "is_account_linked": alpaca_account.account_linked,
        "activated_algorithms": activated_algorithms
    }
    if alpaca_account.account_linked:
        context["account"] = alpaca_account.get_account()
        context["positions"] = alpaca_account.get_positions()
        context["activities"] = alpaca_account.get_activities()
        context["watchlist"] = alpaca_account.get_stocks_in_watchlist()

    return render(request, "user/dashboard.html", context)


def logout(request):
    auth_logout(request)
    return redirect('/')


def algorithms(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    if request.method == 'POST':
        if request.POST['submit-button'] == 'activate':
            stock = request.POST['stock-symbol'].upper()
            if stock not in all_tradable_stocks:
                messages.warning(request, "The stock you just entered is not found")
            elif float(request.POST['over-percentage-threshold']) < float(request.POST['under-percentage-threshold']):
                messages.warning(request, "Over percentage threshold must be greater than under percentage threshold")
            elif float(request.POST['short-moving-avg']) > float(request.POST['long-moving-avg']):
                messages.warning(request, "Short moving average must be smaller then long moving average")
            else:
                obj, created = ActivatedAlgorithm.objects.get_or_create(user=request.user, algorithm=request.POST['algorithm'], stock_name=stock,
                                                                        defaults={
                                                                                  'investment_amount':  request.POST['amount'],
                                                                                  'short_moving_avg': request.POST['short-moving-avg'],
                                                                                  'long_moving_avg': request.POST['long-moving-avg'],
                                                                                  'days_of_moving_avg': request.POST['days-of-moving-avg'],
                                                                                  'over_percentage_threshold': request.POST['over-percentage-threshold'],
                                                                                  'under_percentage_threshold': request.POST['under-percentage-threshold'],
                                                                                  'standard_deviation': request.POST['standard-deviation']})
                if not created:
                    obj.investment_amount = request.POST['amount']
                    obj.short_moving_avg = request.POST['short-moving-avg']
                    obj.long_moving_avg = request.POST['long-moving-avg']
                    obj.days_of_moving_avg = request.POST['days-of-moving-avg']
                    obj.over_percentage_threshold = request.POST['over-percentage-threshold']
                    obj.under_percentage_threshold = request.POST['under-percentage-threshold']
                    obj.standard_deviation = request.POST['standard-deviation']
                    obj.shares = 0
                    obj.save()
                messages.success(request, "You've successfully applied the strategy to stock")
        elif request.POST['submit-button'] == 'deactivate':
            try:
                obj = ActivatedAlgorithm.objects.get(id=request.POST['id'])
            except:
                obj = None
            if obj:
                obj.delete()
                messages.success(request, "You've successfully de-activate strategy to your stock.")

    #ActivatedAlgorithm.objects.filter(user=request.user, algorithm='average-true-range')

    context = {
        'MA': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='moving-average'),
        'ATR': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='average-true-range'),
        'RSI': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='relative-strength-indicator'),
        'FIB': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='MACD-with-fibonacci-levels'),
        'BB': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='bollinger-bands'),
    }

    return render(request, "user/algorithms.html", context)


def dataAnalysis(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d')
            end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d')
            stock_symbol = request.POST.get('stock_symbol').upper()
            algorithm = request.POST.get('algorithm')
            investment = int(request.POST.get('investment'))
        except:
            return render(request, "user/data-analysis.html", {"e": "Please input all values"})

        try:
            user = CustomUser.objects.filter(id=request.user.id)[0]
            client = StockHistoricalDataClient(user.api_key, user.secret_key)
            temp = Strategy(client, investment, 5)
        except:
            return render(request, "user/data-analysis.html", {"e": "Please connect your API key before you utilize data analysis."})

        if algorithm == 'RSI':
            try:
                rsi_days = int(request.POST.get('rsi_days'))
                rsi_over = int(request.POST.get('rsi_over'))
                rsi_under = int(request.POST.get('rsi_under'))
            except:
                return render(request, "user/data-analysis.html", {"e": "Please input all values"})
            e = temp.test_parameters(start_date, end_date, stock_symbol, algorithm, investment, client, window = rsi_days, rsi_over = rsi_over, rsi_under = rsi_under)
            if(e != "Valid"):
                return render(request, "user/data-analysis.html", {"e": e})
            d = temp.execute_rsi(start_date, end_date, stock_symbol, rsi_days, rsi_over, rsi_under)
            temp.setVal(investment)
            control = temp.execute_control(start_date, end_date, stock_symbol)
            data = json.loads(d.reset_index().to_json(orient = 'records', date_format='iso'))
            plt = Plot(d, control, client)
            p = plt.plot_strategy("RSI Strategy")
            return render(request, "user/data-analysis.html", {"d": data, 'p': p})
        elif algorithm == 'MA':
            try:
                ma_short = int(request.POST.get('ma_short'))
                ma_long = int(request.POST.get('ma_long'))
            except:
                return render(request, "user/data-analysis.html", {"e": "Please input all values"})
            e = temp.test_parameters(start_date, end_date, stock_symbol, algorithm, investment, client, short = ma_short, long = ma_long)
            if(e != "Valid"):
                return render(request, "user/data-analysis.html", {"e": e})
            d = temp.execute_ma(start_date, end_date, stock_symbol, ma_short, ma_long)
            temp.setVal(investment)
            control = temp.execute_control(start_date, end_date, stock_symbol)
            data = json.loads(d.reset_index().to_json(orient = 'records', date_format='iso'))
            plt = Plot(d, control, client)
            p = plt.plot_strategy("Moving Average Strategy")
            return render(request, "user/data-analysis.html", {"d": data, 'p': p})
        elif algorithm == 'ATR':
            try:
                atr_short = int(request.POST.get('atr_short'))
                atr_long = int(request.POST.get('atr_long'))
            except:
                return render(request, "user/data-analysis.html", {"e": "Please input all values"})
            e = temp.test_parameters(start_date, end_date, stock_symbol, algorithm, investment, client, short = atr_short, long = atr_long)
            if(e != "Valid"):
                return render(request, "user/data-analysis.html", {"e": e})
            d = temp.execute_atr(start_date, end_date, stock_symbol, atr_short, atr_long)
            temp.setVal(investment)
            control = temp.execute_control(start_date, end_date, stock_symbol)
            data = json.loads(d.reset_index().to_json(orient = 'records', date_format='iso'))
            plt = Plot(d, control, client)
            p = plt.plot_strategy("Average True Range Strategy")
            return render(request, "user/data-analysis.html", {"d": data, 'p': p})
        elif algorithm == 'FIB':
            try:
                fib_short = int(request.POST.get('fib_short'))
                fib_long = int(request.POST.get('fib_long'))
            except:
                return render(request, "user/data-analysis.html", {"e": "Please input all values"})
            e = temp.test_parameters(start_date, end_date, stock_symbol, algorithm, investment, client, short = fib_short, long = fib_long)
            if(e != "Valid"):
                return render(request, "user/data-analysis.html", {"e": e})
            d = temp.execute_fib(start_date, end_date, stock_symbol, fib_short, fib_long)
            temp.setVal(investment)
            control = temp.execute_control(start_date, end_date, stock_symbol)
            data = json.loads(d.reset_index().to_json(orient = 'records', date_format='iso'))
            plt = Plot(d, control, client)
            p = plt.plot_strategy("Fibonacci Strategy")
            return render(request, "user/data-analysis.html", {"d": data, 'p': p})
        elif algorithm == 'BB':
            try:
                bb_ma_days = int(request.POST.get('bb_ma_days'))
                bb_num_std = int(request.POST.get('bb_num_std'))
            except:
                return render(request, "user/data-analysis.html", {"e": "Please input all values"})
            e = temp.test_parameters(start_date, end_date, stock_symbol, algorithm, investment, client, window=bb_ma_days, std_dev=bb_num_std)
            if(e != "Valid"):
                return render(request, "user/data-analysis.html", {"e": e})
            d = temp.execute_bb(start_date, end_date, stock_symbol, bb_ma_days, bb_num_std)
            temp.setVal(investment)
            control = temp.execute_control(start_date, end_date, stock_symbol)
            data = json.loads(d.reset_index().to_json(orient = 'records', date_format='iso'))
            plt = Plot(d, control, client)
            p = plt.plot_strategy("Fibonacci Strategy")
            return render(request, "user/data-analysis.html", {"d": data, 'p': p})
            
    return render(request, "user/data-analysis.html", {})


def recommendations(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')
    periods = [[datetime(2019, 12, 1),datetime(2022, 12, 31)],
               [datetime(2015, 11, 1),datetime(2020, 12, 31)],
               [datetime(2010, 1, 1),datetime(2016, 12, 31)],
               [datetime(2016,1,1), datetime.today() - timedelta(days=1)]]
    
    select_algorithm = request.POST.get('select_algorithm')
    activated_algorithm = ActivatedAlgorithm.objects.filter(user=request.user)
    activated_algorithm_list = []
    for algo in activated_algorithm:
        algo_dict = {
            'id': algo.id,
            'algorithm': algo.algorithm,
            'stock_name': algo.stock_name,
        }
        activated_algorithm_list.append(algo_dict)
    
    try:
        if select_algorithm is not None and select_algorithm != "":
            id, algorithm, stock_name = select_algorithm.split('|')
        
        if select_algorithm == None:
            return render(request, 'user/recommendations.html', {'activated_algorithm_list': activated_algorithm_list})
      
    except Exception as e:
        print(e)
        return render(request, 'user/recommendations.html')
    
    
    # id, algorithm, stock_name = select_algorithm.split('|')
    user = CustomUser.objects.filter(id=request.user.id)[0]
    trading_client = StockHistoricalDataClient(user.api_key, user.secret_key)
     
    try:
        loss_analysis=[]
        potential = []
        current = []
        plots = []
        act_algo = ActivatedAlgorithm.objects.filter(user=request.user, id=id)
        act_algo = list(act_algo.values())[0]
        
        for i in periods:
            x = i[0]
            y = i[1]
            test = Recommendation(trading_client, x, y)
            print("looping through periods")
            try:
                l,c,p= test.generate_analysis(algorithm, stock_name, short=int(act_algo["short_moving_avg"]),long=int(act_algo["long_moving_avg"]),days=int(act_algo["days_of_moving_avg"]),
                                                    over=int(act_algo["over_percentage_threshold"]),under=int(act_algo["under_percentage_threshold"]),num_std_dev=int(act_algo["standard_deviation"]))
               
            except Exception as e:
                l=c=p= -1
                print(e)
            loss_analysis.append(l)
            potential.append(p)
            current.append(c)

            d = test.get_strategy()
            control = test.get_control()
            plt = Plot(d, control, trading_client)
            p = plt.plot_strategy("Plot")
            plots.append(p)
        
        for i, period in enumerate(periods):
            start_time = period[0].strftime("%m/%d/%Y")
            end_time = period[1].strftime("%m/%d/%Y")
            periods[i] = [start_time, end_time]

        print(periods)
        df = pd.DataFrame(periods, columns =['start', 'end'])
        
        df['Percent_Difference'] = loss_analysis
        df['plots'] = plots
        df['potential'] = potential
        df['current'] = current
        
        print("done")
        print(df)

        return render(request, 'user/recommendations.html', {'df': df, 'activated_algorithm_list': activated_algorithm_list})
            
    
    except:
        return render(request, "user/recommendations.html" , {"e": "Error. please try again."})

def userAPI(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    user = CustomUser.objects.filter(id=request.user.id)[0]

    if request.method == 'POST':
        user.api_key = request.POST['api-key']
        user.secret_key = request.POST['secret-key']
        user.save()
        messages.success(request, "API key updated successfully")

    return render(request, "user/user-api.html", {"api_key": user.api_key, "secret_key": user.secret_key})

def add_to_watchlist(request):
    if request.method == "POST":
        alpaca_account = AlpacaAccount(request.user.api_key, request.user.secret_key)
        symbol = request.POST["stock-symbol"]
        if alpaca_account.is_crypto(symbol):
            messages.warning(request, "We currently do not support crypto")
        else:
            try:
                alpaca_account.add_to_watchlist(request.POST['watchlist-id'], symbol)
            except APIError as e:
                if "asset not found" in e.args[0]:
                    messages.warning(request, "The stock you just entered is not found")
                if "duplicate symbol" in e.args[0]:
                    messages.warning(request, "The stock you just entered is already in the watch list")
            else:
                messages.success(request, "Watch list updated!")

    return redirect("/user/dashboard")


def remove_from_watchlist(request):
    if request.method == "POST":
        alpaca_account = AlpacaAccount(request.user.api_key, request.user.secret_key)
        alpaca_account.remove_from_watchlist(request.POST['watchlist-id'], request.POST["stock-symbol"])
        messages.success(request, "Watch list updated!")

    return redirect("/user/dashboard")
