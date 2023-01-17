from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout', views.logout, name='logout'),
    path('algorithms/', views.algorithms, name='algorithms'),
    path('data-analysis/', views.dataAnalysis, name='dataAnalysis'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('user-api/', views.userAPI, name='userAPI'),
]