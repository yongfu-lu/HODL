from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    api_key = models.CharField(max_length=255, blank=True)
    secret_key = models.CharField(max_length=255, blank=True)

class ActivatedAlgorithm(models.Model):
    id = models.AutoField(primary_key=True)
    algorithm = models.CharField(max_length=100)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    stock_name = models.CharField(max_length=100)
    investment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shares = models.PositiveIntegerField(default=0)
    short_moving_avg = models.PositiveIntegerField(default=0)
    long_moving_avg = models.PositiveIntegerField(default=0)
    days_of_moving_avg = models.PositiveIntegerField(default=0)
    over_percentage_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    under_percentage_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    standard_deviation = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user}  {self.algorithm}  {self.stock_name}"

