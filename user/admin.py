from django.contrib import admin
from .models import CustomUser, ActivatedAlgorithm

# Register your models here.
admin.site.register(CustomUser)


class ActivatedAlgorithmAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'algorithm', 'stock_name', 'investment_amount', 'shares')


admin.site.register(ActivatedAlgorithm, ActivatedAlgorithmAdmin)
