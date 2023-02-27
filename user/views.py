from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import *
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from .models import CustomUser
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
    return render(request, "user/dashboard.html", {})


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
    
    data = {
        'Strategy': ['Strategy A', 'Strategy B', 'Strategy C'],
        'Percent_Difference': ['5%', '10%', '15%'],
        'Period': ['2/4/23-Present', '1/14/23-Present', '2/21/23-Present']
    }
    df = pd.DataFrame(data)
    context = {'df': df}
    return render(request, 'user/recommendations.html', context)
    
    


def userAPI(request):
    if not request.user.is_authenticated:
        return redirect('/user/login')

    user = CustomUser.objects.filter(id=request.user.id)[0]
    current_api_key = user.api_key
    if request.method == 'POST':
        api_key = request.POST['api-key']
        user.api_key = api_key
        user.save()
        current_api_key = api_key
        messages.success(request, "API key updated successfully")

    return render(request, "user/user-api.html", {"api_key": current_api_key})



