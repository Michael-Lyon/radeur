from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import viewsets


User = get_user_model()
# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer