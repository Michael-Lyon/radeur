from rest_framework import viewsets
from rest_framework.response import Response
from geopy.geocoders import Nominatim
from core.models import NetworkRating
from core.serializers import  NetworkRatingSerializer
from django.contrib.gis.measure import Distance


class NetworkRatingViewSet(viewsets.ModelViewSet):
    queryset = NetworkRating.objects.all()
    serializer_class = NetworkRatingSerializer

    def perform_create(self, serializer):
        user = self.request.user
        geolocator = Nominatim(user_agent='network_rating_app')
        location = geolocator.geocode(user.profile.location)
        serializer.save(user=user, latitude=location.latitude, longitude=location.longitude)


    def list(self, request, *args, **kwargs):
        user = request.user
        geolocator = Nominatim(user_agent='network_rating_app')
        location = geolocator.geocode(user.profile.location)

        queryset = NetworkRating.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).order_by(
            Distance('latitude', 'longitude', location.latitude, location.longitude)
        )[:100]

        network_name = request.query_params.get('network_name')
        device = request.query_params.get('device')
        rating = request.query_params.get('rating')

        if network_name:
            queryset = queryset.filter(network_name__icontains=network_name)
        if device:
            queryset = queryset.filter(device__icontains=device)
        if rating:
            queryset = queryset.filter(rating=float(rating))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    


