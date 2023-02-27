from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    api_key = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)

class ActivatedAlgorithm(models.Model):
    algorithm = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    stock_name = models.CharField(max_length=100)
    investment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    short_moving_avg = models.DecimalField(max_digits=10, decimal_places=2,  blank=True, null=True)
    long_moving_avg = models.DecimalField(max_digits=10, decimal_places=2,  blank=True, null=True)
    days_of_moving_avg = models.PositiveIntegerField( blank=True, null=True)
    over_percentage_threshold = models.DecimalField(max_digits=5, decimal_places=2,  blank=True, null=True)
    under_percentage_threshold = models.DecimalField(max_digits=5, decimal_places=2,  blank=True, null=True)
    standard_deviation = models.DecimalField(max_digits=10, decimal_places=2,  blank=True, null=True)

    def __str__(self):
        return f"{self.user}  {self.algorithm}  {self.stock_name}"

