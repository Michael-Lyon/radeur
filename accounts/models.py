from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    location = models.CharField(max_length=255)
    # Other fields to store the accurate user location

    def __str__(self):
        return str(self.user)