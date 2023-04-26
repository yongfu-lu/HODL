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
    path('add-to-watchlist/', views.add_to_watchlist, name='add-to-watchlist'),
    path('remove-from-watchlist/', views.remove_from_watchlist, name='remove-from-watchlist'),
    path('all-positions/', views.all_positions, name='all-positions'),
    path('all-activities/', views.all_activities, name='all-activities'),
    path('get-account/', views.get_account, name='get-account'),
    path('get-history/', views.get_history, name='get-history'),
    path('help/', views.help, name='help'),
    path('trade-logs/', views.trade_logs, name='trade-logs'),
]