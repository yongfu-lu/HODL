from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser
from .utility import AlpacaAccount
from .all_US_assets import all_US_assets

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







    def backtesting(request):
        if request.method == 'POST':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            stock_symbol = request.POST.get('stock_symbol')
            algorithm = request.POST.get('algorithm')

            if algorithm == 'RSI':
                rsi_days = request.POST.get('rsi_days')
                rsi_over = request.POST.get('rsi_over')
                rsi_under = request.POST.get('rsi_under')
                result = RSI(start_date, end_date, stock_symbol, rsi_days, rsi_over, rsi_under)
            elif algorithm == 'MA':
                ma_short = request.POST.get('ma_short')
                ma_long = request.POST.get('ma_long')
                result = moving_average(start_date, end_date, stock_symbol, ma_short, ma_long)
            elif algorithm == 'ATR':
                atr_short = request.POST.get('atr_short')
                atr_long = request.POST.get('atr_long')
                result = ATR(start_date, end_date, stock_symbol, atr_short, atr_long)
            elif algorithm == 'FIB':
                fib_short = request.POST.get('fib_short')
                fib_long = request.POST.get('fib_long')
                result = FibLevels(start_date, end_date, stock_symbol, fib_short, fib_long)
            elif algorithm == 'BB':
                bb_ma_days = request.POST.get('bb_ma_days')
                bb_num_std = request.POST.get('bb_num_std')
                result = bollinger_bands(start_date, end_date, stock_symbol, bb_ma_days, bb_num_std)

        return render(request, 'backtesting_results.html', {'result': result})

        return render(request, 'backtesting.html')