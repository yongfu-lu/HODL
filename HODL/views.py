from django.shortcuts import render, redirect
from django.http import HttpResponse

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html', {})

    return redirect('/user/dashboard')
