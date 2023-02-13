from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser
from .utility import AlpacaAccount

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
    is_account_linked = alpaca_account.link_account()
    context = {
        "is_account_linked": is_account_linked,
    }
    if is_account_linked:
        context["equity"] = "{:.2f}".format(float(alpaca_account.account.equity))
        context["change_of_today"] = "{:.2f}".format(float(alpaca_account.account.equity) - float(alpaca_account.account.last_equity))
        context["per_change_of_today"] = "{:.2f}".format((float(alpaca_account.account.equity) - float(alpaca_account.account.last_equity)) / float(alpaca_account.account.last_equity))
        context["positions"] = alpaca_account.positions
        for position in context["positions"]:
            position.change_today = "{:.2f}".format(float(position.change_today)*100)

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
        api_key = request.POST['api-key']
        secret_key = request.POST['secret-key']
        user.api_key = api_key
        user.secret_key = secret_key
        user.save()
        messages.success(request, "API key updated successfully")

    return render(request, "user/user-api.html", {"api_key": user.api_key, "secret_key":user.secret_key})
