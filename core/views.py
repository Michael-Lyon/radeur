from rest_framework import viewsets
from rest_framework.response import Response
from geopy.geocoders import Nominatim
from core.models import Comment, NetworkDevice, NetworkRating
from core.serializers import  CommentSerializer, NetworkDeviceSerializer, NetworkRatingSerializer, NetworkSerializer
from django.contrib.gis.measure import Distance
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated

from core.utils import get_location_data, get_nearby_ratings

class NetworkRatingListCreate(APIView):
    serializer_class = NetworkRatingSerializer

    """
    List all network ratings, or create a new network rating.
    """
    def get(self, request):
        loca_data = get_location_data(request)
        if loca_data:
            _, longitude, latitude = loca_data
        ratings = NetworkRating.objects.all()
        # ratings = get_nearby_ratings(longitude, latitude)
        serializer = NetworkRatingSerializer(ratings, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        authentication_classes = (JWTAuthentication,)
        permission_classes = (IsAuthenticated,)

        # Apply authentication and permission checks
        self.authentication_classes = authentication_classes
        self.permission_classes = permission_classes
        self.check_permissions(request)
        self.perform_authentication(request)

        serializer = NetworkRatingSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            address = serializer.validated_data.get("address")
            loca_data = get_location_data(request)
            if loca_data:
                addy, longitude, latitude = loca_data
                address = f"{address}, {addy}"
                serializer.validated_data["latitude"] = latitude
                serializer.validated_data["longitude"] = longitude
                serializer.validated_data["address"] = address
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class NetworkRatingDetail(APIView):
    serializer_class = NetworkRatingSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    """
    Retrieve, update, or delete a network rating instance.
    """
    def get_object(self, pk):
        try:
            return NetworkRating.objects.get(pk=pk)
        except NetworkRating.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def get(self, request, pk, format=None):
        rating = self.get_object(pk)
        serializer = NetworkRatingSerializer(rating)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        rating = self.get_object(pk)
        serializer = NetworkRatingSerializer(rating, data=request.data)
        if serializer.is_valid():
            # Custom handling of data before saving
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        rating = self.get_object(pk)
        rating.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, format=None):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Assuming the user is authenticated
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, comment_id, format=None):
        comment = Comment.objects.get(pk=comment_id)
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)  # Unlike the comment
        else:
            comment.likes.add(request.user)  # Like the comment
        return Response({'status': 'like status changed'}, status=status.HTTP_200_OK)


class DevicesView(APIView):
    serializer_class = NetworkDeviceSerializer

    def get(self, request):
        devices = NetworkDevice.objects.all()
        serializer = NetworkDeviceSerializer(devices, many=True)
        return Response(serializer.data)

class Network(APIView):
    serializer_class = NetworkSerializer

    def get(self, request):
        network = Network.objects.all()
        serializer = NetworkSerializer(network, many=True, contect={"request": request})
        return Response(serializer.data)