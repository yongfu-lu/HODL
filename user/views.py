from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser, ActivatedAlgorithm
from .utility import AlpacaAccount
from alpaca_trade_api.rest import APIError
from .all_tradable_stocks import all_tradable_stocks, all_tradable_stocks_alphabet
from Backtester.recommendation import Recommendation
from Backtester.strategy import Strategy
from Backtester.plotting import Plot
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime
import pandas as pd
import json
from django.core.paginator import Paginator


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
        "activated_algorithms": activated_algorithms[:5]
    }
    if alpaca_account.account_linked:
        context["account"] = alpaca_account.get_account()
        context["positions"] = alpaca_account.get_positions()[:5]
        context["activities"] = alpaca_account.get_activities()[:5]
        context["watchlist"] = alpaca_account.get_stocks_in_watchlist()
        context['all_stocks_alphabet'] = all_tradable_stocks_alphabet

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

    context = {
        'MA': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='moving-average'),
        'ATR': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='average-true-range'),
        'RSI': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='relative-strength-indicator'),
        'FIB': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='MACD-with-fibonacci-levels'),
        'BB': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='bollinger-bands'),
        'all_stocks_alphabet': all_tradable_stocks_alphabet,
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
    
    try:
        user = CustomUser.objects.filter(id=request.user.id)[0]
        trading_client = StockHistoricalDataClient(user.api_key, user.secret_key)
        x = datetime(2020, 5, 17)
        y = datetime(2022, 5, 17)
        test = Recommendation(trading_client, x, y)
    except:
        return render(request, 'user/recommendations.html', {"e": "Please connect your API key before you utilize recommendations."})

    try:
        loss_analysis=[]
        potential = []
        current = []
        activated_algorithm = ActivatedAlgorithm.objects.filter(user=request.user)
    
        for i in activated_algorithm:
            l,c,p= test.loss_analysis(i.algorithm,i.stock_name,5, short=int(i.short_moving_avg),long=int(i.long_moving_avg),days=int(i.days_of_moving_avg),
                                                over=int(i.over_percentage_threshold),under=int(i.under_percentage_threshold),num_std_dev=int(i.standard_deviation))
            loss_analysis.append(l)
            potential.append(p)
            current.append(c)
        
        

    #raise ValueError("activated_algorithm " + activated_algorithm[0].stock_name)
        df = pd.DataFrame(list(activated_algorithm.values()))
    
    
        df['Percent_Difference'] = loss_analysis
        df['potential'] = potential
        df['current'] = current
    
        d = test.generate_strategy("rsi","AAPL",days=20,over=70,under=30)
        control = test.generate_strategy("control","AAPL")
    

        plt = Plot(d, control, trading_client)
        p = plt.plot_strategy("Strat Name")
        return render(request, 'user/recommendations.html', {'df': df, 'p': p})
    
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


def all_positions(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    alpaca_account = AlpacaAccount(request.user.api_key, request.user.secret_key)
    context = {
        "is_account_linked": alpaca_account.account_linked,
    }

    if alpaca_account.account_linked:
        all_positions = alpaca_account.get_positions()
        paginator = Paginator(all_positions, 10)  # 10 activities per page
        page = request.GET.get('page')
        context["positions"] = paginator.get_page(page)

    return render(request, "user/all-positions.html", context)


def all_activities(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    alpaca_account = AlpacaAccount(request.user.api_key, request.user.secret_key)
    context = {
        "is_account_linked": alpaca_account.account_linked,
    }

    if alpaca_account.account_linked:
        all_activities = alpaca_account.get_activities()
        paginator = Paginator(all_activities, 10)  # 10 activities per page
        page = request.GET.get('page')
        context["activities"] = paginator.get_page(page)

    return render(request, "user/all-activities.html", context)


def get_account(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    alpaca_account = AlpacaAccount(request.user.api_key, request.user.secret_key)
    data = {
        "is_account_linked": alpaca_account.account_linked,
    }
    if alpaca_account.account_linked:
        account = {
            'equity': round(float(alpaca_account.get_account().equity), 2),
            'change_of_today': round(float(alpaca_account.get_account().equity) - float(alpaca_account.get_account().last_equity),2),
            'perc_change_of_today': round((float(alpaca_account.get_account().equity) - float(alpaca_account.get_account().last_equity)) / float(alpaca_account.get_account().last_equity) * 100, 2)
        }
        watchlist = alpaca_account.get_stocks_in_watchlist()
        positions_info = alpaca_account.get_positions()[:5]
        positions = []
        for position_info in positions_info:
            positions.append({
                'symbol': position_info.symbol,
                'qty': position_info.qty,
                'current_price': position_info.current_price,
                'change_today': position_info.change_today,
                'cost_basis': round(float(position_info.cost_basis), 2),
                'market_value': round(float(position_info.market_value), 2),
                'earning': round(float(position_info.market_value) - float(position_info.cost_basis), 2)
            })
        data["account"] = account
        data["watchlist"] = watchlist
        data['positions'] = positions
    return JsonResponse(data)


def help(request):
    return render(request, "user/help.html", {})
