from rest_framework import viewsets
from rest_framework.response import Response
from geopy.geocoders import Nominatim
from core.models import Comment, Network, NetworkDevice, NetworkRating
from core.serializers import  CommentSerializer, NetworkDeviceSerializer, NetworkRatingSerializer, NetworkSerializer
from django.contrib.gis.measure import Distance
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import models
from django.db.models import Avg, Count

from core.utils import get_location_data, get_nearby_ratings

class NetworkRatingListCreate(APIView):
    serializer_class = NetworkRatingSerializer

    """
    List all network ratings, or create a new network rating.
    """
    def get(self, request):
        try:
            # Get query parameters for filtering
            network_id = request.GET.get('network_id')
            device_id = request.GET.get('device_id')
            min_rating = request.GET.get('min_rating')
            search = request.GET.get('search')
            nearby = request.GET.get('nearby', 'true').lower() == 'true'
            radius = float(request.GET.get('radius', 5))
            
            # Start with all ratings
            ratings = NetworkRating.objects.all()
            
            # Apply filters
            if network_id:
                ratings = ratings.filter(network_id=network_id)
            if device_id:
                ratings = ratings.filter(device_id=device_id)
            if min_rating:
                ratings = ratings.filter(rating__gte=float(min_rating))
            if search:
                ratings = ratings.filter(
                    models.Q(review__icontains=search) |
                    models.Q(network__name__icontains=search) |
                    models.Q(address__icontains=search)
                )
            
            # Location-based filtering
            if nearby:
                loca_data = get_location_data(request)
                if loca_data:
                    _, longitude, latitude = loca_data
                    ratings_list = list(ratings)
                    nearby_ratings = get_nearby_ratings(latitude, longitude, radius)
                    # Filter to only include nearby ratings
                    ratings = [r for r in ratings_list if r in nearby_ratings]
                else:
                    ratings = ratings.all()
            else:
                ratings = ratings.all()
            
            # Order by creation date (newest first)
            if hasattr(ratings, 'order_by'):
                ratings = ratings.order_by('-created_at')
            
            serializer = NetworkRatingSerializer(ratings, many=True, context={"request": request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching ratings", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            return None

    def get(self, request, pk, format=None):
        try:
            rating = self.get_object(pk)
            if rating is None:
                return Response(
                    {"error": "Rating not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = NetworkRatingSerializer(rating)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching the rating", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk, format=None):
        try:
            rating = self.get_object(pk)
            if rating is None:
                return Response(
                    {"error": "Rating not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user owns the rating or is admin
            if rating.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to edit this rating"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = NetworkRatingSerializer(rating, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "An error occurred while updating the rating", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, pk, format=None):
        try:
            rating = self.get_object(pk)
            if rating is None:
                return Response(
                    {"error": "Rating not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if user owns the rating or is admin
            if rating.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to delete this rating"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            rating.delete()
            return Response({"message": "Rating deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {"error": "An error occurred while deleting the rating", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CommentView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):
        try:
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "An error occurred while creating the comment", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def patch(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(pk=comment_id)
            if request.user in comment.likes.all():
                comment.likes.remove(request.user)
                liked = False
            else:
                comment.likes.add(request.user)
                liked = True
            return Response({
                'status': 'like status changed',
                'liked': liked,
                'total_likes': comment.likes.count()
            }, status=status.HTTP_200_OK)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "An error occurred while updating the like status", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, comment_id, format=None):
        try:
            comment = Comment.objects.get(pk=comment_id)
            
            # Check if user owns the comment or is admin
            if comment.user != request.user and not request.user.is_staff:
                return Response(
                    {"error": "You don't have permission to edit this comment"}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = CommentSerializer(comment, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "An error occurred while updating the comment", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DevicesView(APIView):
    serializer_class = NetworkDeviceSerializer

    def get(self, request):
        try:
            devices = NetworkDevice.objects.all()
            serializer = NetworkDeviceSerializer(devices, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching devices", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class NetworkView(APIView):
    serializer_class = NetworkSerializer

    def get(self, request):
        try:
            search = request.GET.get('search')
            active_only = request.GET.get('active_only', 'false').lower() == 'true'
            
            networks = Network.objects.all()
            
            if active_only:
                networks = networks.filter(status=True)
            
            if search:
                networks = networks.filter(name__icontains=search)
            
            networks = networks.order_by('name')
            serializer = NetworkSerializer(networks, many=True, context={"request": request})
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching networks", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NetworkStatisticsView(APIView):
    """
    Get aggregated statistics for networks including average ratings and review counts.
    """
    
    def get(self, request):
        try:
            # Get statistics for all networks
            networks_stats = Network.objects.annotate(
                avg_rating=Avg('networkrating__rating'),
                review_count=Count('networkrating'),
                total_comments=Count('networkrating__comments')
            ).values(
                'id', 'name', 'slug', 'status',
                'avg_rating', 'review_count', 'total_comments'
            )
            
            # Format the response
            formatted_stats = []
            for network in networks_stats:
                formatted_stats.append({
                    'id': network['id'],
                    'name': network['name'],
                    'slug': network['slug'],
                    'status': network['status'],
                    'average_rating': round(network['avg_rating'], 1) if network['avg_rating'] else 0,
                    'total_reviews': network['review_count'],
                    'total_comments': network['total_comments'],
                })
            
            return Response({
                'networks': formatted_stats,
                'total_networks': len(formatted_stats)
            })
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching network statistics", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NetworkDetailStatsView(APIView):
    """
    Get detailed statistics for a specific network including rating distribution.
    """
    
    def get(self, request, network_id):
        try:
            network = Network.objects.get(id=network_id)
            ratings = NetworkRating.objects.filter(network=network)
            
            if not ratings.exists():
                return Response({
                    'network': {
                        'id': network.id,
                        'name': network.name,
                        'slug': network.slug
                    },
                    'statistics': {
                        'total_reviews': 0,
                        'average_rating': 0,
                        'rating_distribution': {str(i): 0 for i in range(1, 6)},
                        'recent_reviews': []
                    }
                })
            
            # Calculate statistics
            stats = ratings.aggregate(
                avg_rating=Avg('rating'),
                total_reviews=Count('id')
            )
            
            # Rating distribution
            rating_distribution = {}
            for i in range(1, 6):
                count = ratings.filter(rating=i).count()
                rating_distribution[str(i)] = count
            
            # Get recent reviews (last 5)
            recent_reviews = ratings.order_by('-created_at')[:5]
            recent_serialized = NetworkRatingSerializer(recent_reviews, many=True, context={"request": request}).data
            
            return Response({
                'network': {
                    'id': network.id,
                    'name': network.name,
                    'slug': network.slug
                },
                'statistics': {
                    'total_reviews': stats['total_reviews'],
                    'average_rating': round(stats['avg_rating'], 1) if stats['avg_rating'] else 0,
                    'rating_distribution': rating_distribution,
                    'recent_reviews': recent_serialized
                }
            })
        except Network.DoesNotExist:
            return Response(
                {"error": "Network not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": "An error occurred while fetching network details", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LocationBasedRecommendationsView(APIView):
    """
    Get network recommendations based on user's location.
    """
    
    def get(self, request):
        try:
            radius = float(request.GET.get('radius', 10))
            min_reviews = int(request.GET.get('min_reviews', 1))
            
            loca_data = get_location_data(request)
            if not loca_data:
                return Response(
                    {"error": "Could not determine your location"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            address, longitude, latitude = loca_data
            
            # Get nearby ratings
            nearby_ratings = get_nearby_ratings(latitude, longitude, radius)
            
            if not nearby_ratings:
                return Response({
                    'location': {'address': address, 'latitude': latitude, 'longitude': longitude},
                    'recommendations': [],
                    'message': f'No ratings found within {radius}km of your location'
                })
            
            # Group by network and calculate stats
            network_stats = {}
            for rating in nearby_ratings:
                if rating.network:
                    net_id = rating.network.id
                    if net_id not in network_stats:
                        network_stats[net_id] = {
                            'network': rating.network,
                            'ratings': [],
                            'total_rating': 0,
                            'count': 0
                        }
                    network_stats[net_id]['ratings'].append(rating)
                    network_stats[net_id]['total_rating'] += float(rating.rating)
                    network_stats[net_id]['count'] += 1
            
            # Calculate averages and filter by minimum reviews
            recommendations = []
            for net_id, stats in network_stats.items():
                if stats['count'] >= min_reviews:
                    avg_rating = stats['total_rating'] / stats['count']
                    recommendations.append({
                        'network': NetworkSerializer(stats['network']).data,
                        'average_rating': round(avg_rating, 1),
                        'review_count': stats['count'],
                        'recent_reviews': NetworkRatingSerializer(
                            stats['ratings'][:3], many=True, context={"request": request}
                        ).data
                    })
            
            # Sort by average rating (descending)
            recommendations.sort(key=lambda x: x['average_rating'], reverse=True)
            
            return Response({
                'location': {'address': address, 'latitude': latitude, 'longitude': longitude},
                'search_radius_km': radius,
                'recommendations': recommendations[:10]  # Top 10 recommendations
            })
            
        except Exception as e:
            return Response(
                {"error": "An error occurred while generating recommendations", "details": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )