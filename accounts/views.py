from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import viewsets

from core.models import NetworkRating
from core.serializers import NetworkRatingSerializer
from .serializers import LoginSerializer, UserSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from .models import UserProfile
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated

User = get_user_model()
# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        # location = request.data.get('location')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Create UserProfile with the user and store the location
        UserProfile.objects.create(user=user)
        data = serializer.data
        data['id'] = user.id

        return Response(data, status=status.HTTP_201_CREATED)


class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    def create(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if username is None or password is None:
            return Response({'error': 'Please provide both username and password.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            return Response({'error': 'Invalid credentials'},
                            status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({'access_token': access_token})


class ProfileApiView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user
        ratings = NetworkRating.objects.filter(user=user)
        return Response({'user': {"username": user.username, "email": user.email, "first_name": user.first_name, "last_name": user.last_name}, "ratings": NetworkRatingSerializer(ratings, many=True).data})