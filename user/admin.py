from django.contrib import admin
from .models import CustomUser, ActivatedAlgorithm, TradeLog

# Register your models here.
admin.site.register(CustomUser)


class ActivatedAlgorithmAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'algorithm', 'stock_name', 'investment_amount', 'shares')


class TradeLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'trade_time', 'trade_type', 'algorithm_name')


admin.site.register(ActivatedAlgorithm, ActivatedAlgorithmAdmin)
admin.site.register(TradeLog, TradeLogAdmin)
