from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser, ActivatedAlgorithm
from .utility import AlpacaAccount
from alpaca_trade_api.rest import APIError
from .all_US_assets import all_US_assets
from Backtester.strategy import Strategy
from Backtester.plotting import Plot
import json
from datetime import datetime
from alpaca.data.historical import StockHistoricalDataClient


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
            obj, created = ActivatedAlgorithm.objects.get_or_create(user=request.user, algorithm=request.POST['algorithm'],
                                                                    defaults={'stock_name': request.POST['stock-symbol'],
                                                                              'investment_amount':  request.POST['amount'],
                                                                              'short_moving_avg': request.POST['short-moving-avg'],
                                                                              'long_moving_avg': request.POST['long-moving-avg'],
                                                                              'days_of_moving_avg': request.POST['days-of-moving-avg'],
                                                                              'over_percentage_threshold': request.POST['over-percentage-threshold'],
                                                                              'under_percentage_threshold': request.POST['under-percentage-threshold'],
                                                                              'standard_deviation': request.POST['standard-deviation']})
            if not created:
                obj.investment_amount =  request.POST['amount']
                obj.short_moving_avg = request.POST['short-moving-avg']
                obj.long_moving_avg = request.POST['long-moving-avg']
                obj.stock_name = request.POST['stock-symbol']
                obj.days_of_moving_avg = request.POST['days-of-moving-avg']
                obj.over_percentage_threshold = request.POST['over-percentage-threshold']
                obj.under_percentage_threshold = request.POST['under-percentage-threshold']
                obj.standard_deviation = request.POST['standard-deviation']
                obj.shares = 0
                obj.save()
        elif request.POST['submit-button'] == 'deactivate':
            try:
                obj = ActivatedAlgorithm.objects.get(user=request.user, algorithm=request.POST['algorithm'])
            except:
                obj = None
            if obj:
                obj.delete()

    ActivatedAlgorithm.objects.filter(user=request.user, algorithm='average-true-range')

    context = {
        'MA': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='moving-average'),
        'ATR': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='average-true-range'),
        'RSI': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='relative-strength-indicator'),
        'FIB': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='MACD-with-fibonacci-levels'),
        'BB': ActivatedAlgorithm.objects.filter(user=request.user, algorithm='billinger-bands'),
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
    return render(request, "user/recommendations.html", {})


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
