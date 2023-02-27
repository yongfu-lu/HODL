from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser, ActivatedAlgorithm
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
                obj.save()
        elif request.POST['submit-button'] == 'deactivate':
            try:
                obj = ActivatedAlgorithm.objects.get(user=request.user, algorithm=request.POST['algorithm'])
            except:
                obj = None
            if obj:
                obj.delete()

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