import requests
import os
from dotenv import load_dotenv
from geopy.distance import geodesic
from .models import NetworkRating

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
