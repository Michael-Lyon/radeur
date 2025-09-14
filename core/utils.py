import requests
import os
from dotenv import load_dotenv
from geopy.distance import geodesic
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import NetworkRating, Network
from typing import List, Dict, Optional

load_dotenv()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_location_from_ip(ip_address):
    API_KEY = os.getenv("IPKEY")
    BASE_URL = os.getenv("IPSTACK_BASE_URL", "https://api.ipstack.com")  # Default value if not set
    url = f'{BASE_URL}/{ip_address}?access_key={API_KEY}'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
        return response.json()
    except requests.RequestException as e:
        # Handle network-related errors here
        print(f"Error fetching location data: {e}")
    except ValueError:
        # Handle JSON decoding error
        print("Error decoding the response JSON")
    return None

def get_location_data(request):
    ip = get_client_ip(request)
    if ip:
        location = get_location_from_ip(ip)
        if location and "city" in location and "country_name" in location:
            addy = f"{location['city']}, {location['country_name']}"
            longitude = location['longitude']
            latitude = location['latitude']
            return addy, longitude, latitude
    return None


# MEASURE DISTANCE
def get_nearby_ratings(user_latitude, user_longitude, radius_km=5):
    nearby_ratings = []
    all_ratings =  NetworkRating.objects.filter(
            latitude__isnull=False,
            longitude__isnull=False
        ).order_by("rating")

    for rating in all_ratings:
        rating_location = (rating.latitude, rating.longitude)
        user_location = (user_latitude, user_longitude)
        distance = geodesic(rating_location, user_location).km
        if distance <= radius_km:
            nearby_ratings.append(rating)

    return nearby_ratings


# RATING CALCULATION UTILITIES

def calculate_network_average_rating(network_id: int) -> Dict[str, float]:
    """
    Calculate average rating and statistics for a specific network.
    
    Args:
        network_id: ID of the network
        
    Returns:
        Dictionary with rating statistics
    """
    ratings = NetworkRating.objects.filter(network_id=network_id)
    
    if not ratings.exists():
        return {
            'average_rating': 0.0,
            'total_ratings': 0,
            'rating_distribution': {str(i): 0 for i in range(1, 6)},
            'recent_average': 0.0
        }
    
    # Calculate basic stats
    stats = ratings.aggregate(
        avg_rating=Avg('rating'),
        total_ratings=Count('id')
    )
    
    # Rating distribution
    rating_distribution = {}
    for i in range(1, 6):
        count = ratings.filter(rating=i).count()
        rating_distribution[str(i)] = count
    
    # Recent average (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_ratings = ratings.filter(created_at__gte=thirty_days_ago)
    recent_avg = recent_ratings.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0
    
    return {
        'average_rating': round(stats['avg_rating'], 2) if stats['avg_rating'] else 0.0,
        'total_ratings': stats['total_ratings'],
        'rating_distribution': rating_distribution,
        'recent_average': round(recent_avg, 2)
    }


def get_top_rated_networks(limit: int = 10, min_ratings: int = 5) -> List[Dict]:
    """
    Get top-rated networks with minimum number of ratings.
    
    Args:
        limit: Maximum number of networks to return
        min_ratings: Minimum number of ratings required
        
    Returns:
        List of network dictionaries with rating info
    """
    networks = Network.objects.filter(
        status=True
    ).annotate(
        avg_rating=Avg('networkrating__rating'),
        total_ratings=Count('networkrating')
    ).filter(
        total_ratings__gte=min_ratings
    ).order_by('-avg_rating')[:limit]
    
    return [
        {
            'id': network.id,
            'name': network.name,
            'slug': network.slug,
            'average_rating': round(network.avg_rating, 2) if network.avg_rating else 0.0,
            'total_ratings': network.total_ratings
        }
        for network in networks
    ]


def get_location_based_network_rankings(latitude: float, longitude: float, 
                                       radius_km: float = 10) -> List[Dict]:
    """
    Get network rankings based on ratings within a specific location.
    
    Args:
        latitude: User's latitude
        longitude: User's longitude
        radius_km: Search radius in kilometers
        
    Returns:
        List of networks ranked by average rating in the area
    """
    nearby_ratings = get_nearby_ratings(latitude, longitude, radius_km)
    
    if not nearby_ratings:
        return []
    
    # Group ratings by network
    network_stats = {}
    for rating in nearby_ratings:
        if rating.network:
            net_id = rating.network.id
            if net_id not in network_stats:
                network_stats[net_id] = {
                    'network': rating.network,
                    'ratings': [],
                    'total_rating': 0
                }
            network_stats[net_id]['ratings'].append(rating.rating)
            network_stats[net_id]['total_rating'] += float(rating.rating)
    
    # Calculate averages and sort
    rankings = []
    for net_id, stats in network_stats.items():
        avg_rating = stats['total_rating'] / len(stats['ratings'])
        rankings.append({
            'id': stats['network'].id,
            'name': stats['network'].name,
            'slug': stats['network'].slug,
            'average_rating': round(avg_rating, 2),
            'total_ratings': len(stats['ratings']),
            'location_based': True
        })
    
    return sorted(rankings, key=lambda x: x['average_rating'], reverse=True)


def get_user_rating_summary(user_id: int) -> Dict:
    """
    Get summary of a user's rating activity.
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with user rating statistics
    """
    ratings = NetworkRating.objects.filter(user_id=user_id)
    
    if not ratings.exists():
        return {
            'total_ratings': 0,
            'average_rating_given': 0.0,
            'networks_rated': 0,
            'recent_activity': 0,
            'favorite_rating': None
        }
    
    stats = ratings.aggregate(
        total_ratings=Count('id'),
        avg_rating_given=Avg('rating'),
        networks_rated=Count('network', distinct=True)
    )
    
    # Recent activity (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_activity = ratings.filter(created_at__gte=seven_days_ago).count()
    
    # Most frequently given rating
    rating_counts = {}
    for rating in ratings:
        r = str(rating.rating)
        rating_counts[r] = rating_counts.get(r, 0) + 1
    
    favorite_rating = max(rating_counts.items(), key=lambda x: x[1])[0] if rating_counts else None
    
    return {
        'total_ratings': stats['total_ratings'],
        'average_rating_given': round(stats['avg_rating_given'], 2) if stats['avg_rating_given'] else 0.0,
        'networks_rated': stats['networks_rated'],
        'recent_activity': recent_activity,
        'favorite_rating': favorite_rating
    }


def calculate_network_trend(network_id: int, days: int = 30) -> Dict:
    """
    Calculate rating trend for a network over time.
    
    Args:
        network_id: ID of the network
        days: Number of days to analyze
        
    Returns:
        Dictionary with trend information
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    ratings = NetworkRating.objects.filter(
        network_id=network_id,
        created_at__gte=start_date
    ).order_by('created_at')
    
    if not ratings.exists():
        return {
            'trend': 'no_data',
            'change': 0.0,
            'recent_ratings_count': 0,
            'period_days': days
        }
    
    # Split into two halves
    mid_point = start_date + timedelta(days=days//2)
    
    first_half = ratings.filter(created_at__lt=mid_point)
    second_half = ratings.filter(created_at__gte=mid_point)
    
    first_avg = first_half.aggregate(avg=Avg('rating'))['avg'] or 0.0
    second_avg = second_half.aggregate(avg=Avg('rating'))['avg'] or 0.0
    
    change = second_avg - first_avg
    
    if abs(change) < 0.1:
        trend = 'stable'
    elif change > 0:
        trend = 'improving'
    else:
        trend = 'declining'
    
    return {
        'trend': trend,
        'change': round(change, 2),
        'recent_ratings_count': ratings.count(),
        'period_days': days,
        'first_half_avg': round(first_avg, 2),
        'second_half_avg': round(second_avg, 2)
    }


def get_network_performance_insights(network_id: int) -> Dict:
    """
    Get comprehensive performance insights for a network.
    
    Args:
        network_id: ID of the network
        
    Returns:
        Dictionary with comprehensive insights
    """
    basic_stats = calculate_network_average_rating(network_id)
    trend = calculate_network_trend(network_id)
    
    ratings = NetworkRating.objects.filter(network_id=network_id)
    
    # Device analysis
    device_stats = ratings.values(
        'device__name'
    ).annotate(
        avg_rating=Avg('rating'),
        count=Count('id')
    ).order_by('-avg_rating')
    
    # Time-based analysis
    recent_ratings = ratings.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    
    return {
        **basic_stats,
        'trend_analysis': trend,
        'device_performance': list(device_stats),
        'recent_activity': recent_ratings,
        'performance_grade': _calculate_performance_grade(basic_stats['average_rating'], basic_stats['total_ratings'])
    }


def _calculate_performance_grade(avg_rating: float, total_ratings: int) -> str:
    """
    Calculate performance grade based on average rating and sample size.
    
    Args:
        avg_rating: Average rating
        total_ratings: Total number of ratings
        
    Returns:
        Performance grade (A+, A, B+, B, C+, C, D, F)
    """
    if total_ratings < 5:
        return 'Insufficient Data'
    
    # Adjust grade based on sample size
    confidence_factor = min(total_ratings / 50, 1.0)  # Max confidence at 50+ ratings
    adjusted_rating = avg_rating * confidence_factor
    
    if adjusted_rating >= 4.5:
        return 'A+'
    elif adjusted_rating >= 4.0:
        return 'A'
    elif adjusted_rating >= 3.5:
        return 'B+'
    elif adjusted_rating >= 3.0:
        return 'B'
    elif adjusted_rating >= 2.5:
        return 'C+'
    elif adjusted_rating >= 2.0:
        return 'C'
    elif adjusted_rating >= 1.5:
        return 'D'
    else:
        return 'F'
