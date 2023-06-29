
from rest_framework import serializers
from core.models import NetworkRating
from django.contrib.auth import get_user_model

User = get_user_model()




class NetworkRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkRating
        exclude = ['latitude', 'longitude']