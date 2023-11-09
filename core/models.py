from django.db import models

# Create your models here.
from django.shortcuts import render
from django.db import models
from django.contrib.auth import get_user_model
# Create your views here.

User = get_user_model()

class NetworkRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    network_name = models.CharField(max_length=255)
    device = models.CharField(max_length=255)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    review = models.CharField(max_length=225)

    def __str__(self):
        return self.network_name
