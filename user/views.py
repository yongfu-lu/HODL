from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser
from .models import ActivatedAlgorithm
from .utility import AlpacaAccount
from .all_US_assets import all_US_assets
from Backtester.recommendation import Recommendation
from Backtester.strategy import Strategy
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime
import pandas as pd


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
    context = {
        "is_account_linked": alpaca_account.account_linked,
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
    return render(request, "user/algorithms.html", {})


def dataAnalysis(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')
    return render(request, "user/data-analysis.html", {})


def recommendations(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')
    
    
    # activated_algorithm = ActivatedAlgorithm.objects.get(user=request.user)
    activated_algorithm = ActivatedAlgorithm.objects.all()
    df = pd.DataFrame(list(activated_algorithm.values()))
    algorithm = activated_algorithm[0].algorithm
    stock_name = activated_algorithm[0].stock_name
    investment_amount = activated_algorithm[0].investment_amount
    short_moving_avg = activated_algorithm[0].short_moving_avg
    long_moving_avg = activated_algorithm[0].long_moving_avg
    
    trading_client = StockHistoricalDataClient('PKV2FZHX6E4RMGFON60X',
                                           'GMKXVZ3W4MqenB6SbcSKM8h9WnvYBZn0qdZ86E6n')

    x = datetime(2020, 5, 17)
    y = datetime(2022, 5, 17)

    test = Recommendation(trading_client, x, y)
    # df1 = test.generate_analysis(strat_name=algorithm, symbol=stock_name, short=short_moving_avg, long=long_moving_avg)
    # df1 = test.generate_analysis('atr','APPL', short = 50, long= 100)
    # df['loss_analysis'] = test.loss_analysis(df1, 5)
    context = {'df': df}
    return render(request, 'user/recommendations.html', context)


    # data = {
    #     'Strategy': ['Strategy A', 'Strategy B', 'Strategy C'],
    #     'Percent_Difference': ['5%', '10%', '15%'],
    #     'Period': ['2/4/23-Present', '1/14/23-Present', '2/21/23-Present']
    # }
    # df = pd.DataFrame(data)
    # context = {'df': df}
    # return render(request, 'user/recommendations.html', context)
    
    


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
        if symbol not in all_US_assets:
            messages.error(request, "The asset you tried to add to watch list is not found!")
        else:
            try:
                alpaca_account.add_to_watchlist(request.POST['watchlist-id'], symbol)
            except:
                messages.warning(request, "The stock you just entered already in your watchlist")
            else:
                messages.success(request, "Watch list updated!")

    return redirect("/user/dashboard")


def remove_from_watchlist(request):
    if request.method == "POST":
        alpaca_account = AlpacaAccount(request.user.api_key, request.user.secret_key)
        alpaca_account.remove_from_watchlist(request.POST['watchlist-id'], request.POST["stock-symbol"])
        messages.success(request, "Watch list updated!")

    return redirect("/user/dashboard")
