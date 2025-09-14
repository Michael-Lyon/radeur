# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Radeur is a Django REST API for an ISP rating system that allows users to evaluate their network experience based on location and device usage. Users can rate networks, discover the best networks in their area, and engage with the community through comments and replies.

## Development Commands

### Environment Setup
- **Development Server**: `python manage.py runserver`
- **Database Migrations**: `python manage.py makemigrations && python manage.py migrate`
- **Create Superuser**: `python manage.py createsuperuser`
- **Collect Static Files**: `python manage.py collectstatic`

### Testing and Deployment
- **Production Deployment**: Uses Gunicorn as defined in Procfile: `python manage.py makemigrations && python manage.py migrate && gunicorn radarr.wsgi`
- **Database**: SQLite3 for local development (ENV=LOCAL), PostgreSQL for production using `dj_database_url`

## Architecture Overview

### Project Structure
- **`radarr/`**: Django project root containing settings, URLs, and WSGI configuration
- **`core/`**: Main app handling network ratings, comments, and network/device management
- **`accounts/`**: User authentication and profile management
- **`templates/`**: Django templates
- **`static/` & `staticfiles/`**: Static assets and collected static files
- **`media/`**: User-uploaded media files

### Key Models (`core/models.py`)
- **`Network`**: ISP/network providers with name, image, status, and slug
- **`NetworkDevice`**: Devices used with ISPs (phones, Wi-Fi devices, etc.)
- **`NetworkRating`**: User ratings for networks with geolocation, device info, and reviews
- **`Comment`**: Comments and replies on network ratings with like functionality

### Authentication & Permissions
- Uses Django REST Framework with JWT authentication (`rest_framework_simplejwt`)
- JWT tokens have 60-hour access token lifetime and 12-week refresh token lifetime
- API endpoints use `JWTAuthentication` and `IsAuthenticated` permissions where needed
- CORS is configured to allow all origins for development

### API Structure
- **Base URL Pattern**: `/api/network/` for core functionality, `/api/accounts/` for user management
- **Authentication**: `/api/token/` for JWT token obtain/refresh
- **Documentation**: Swagger UI at `/doc/`, ReDoc at `/redoc/`
- Uses `drf-yasg` for OpenAPI documentation generation

### Key Features
- **Geolocation Support**: Uses `geopy` for location services and stores latitude/longitude
- **Image Handling**: Pillow for image processing, uploads to `media/uploads/`
- **Location-based Recommendations**: Utility functions in `core/utils.py` for nearby ratings
- **Comment System**: Hierarchical comments with replies and like functionality

### Database Configuration
- **Local Development**: SQLite3 database (`db.sqlite3`)
- **Production**: PostgreSQL via `dj_database_url` with `DB_URL` environment variable
- Environment switching controlled by `ENV` variable

### Static Files & Media
- Static files collected to `staticfiles/` directory
- Media uploads stored in `media/` directory
- Configured for both development and production serving

### Third-party Dependencies
- **Core**: Django 4.2.2, Django REST Framework, JWT authentication
- **Database**: PostgreSQL support via `psycopg2`, `dj-database-url`
- **Location Services**: `geopy`, `geographiclib`
- **Documentation**: `drf-yasg` for Swagger/OpenAPI
- **Production**: Gunicorn WSGI server, whitenoise-style static serving
- **CORS**: `django-cors-headers` for cross-origin requests

### New API Endpoints (Added Improvements)

- **Statistics & Analytics**:
  - `GET /api/network/statistics/` - Get aggregated statistics for all networks
  - `GET /api/network/statistics/{id}/` - Get detailed stats for specific network
  - `GET /api/network/recommendations/` - Get location-based network recommendations

- **Enhanced Filtering** (Query Parameters):
  - `GET /api/network/ratings/?network_id=1&device_id=2&min_rating=3.0&search=fast&nearby=true&radius=10`
  - `GET /api/network/isp-providers/?search=MTN&active_only=true`

### Utility Functions (`core/utils.py`)

- **Rating Calculations**: `calculate_network_average_rating()`, `get_top_rated_networks()`
- **Location Analysis**: `get_location_based_network_rankings()`, `get_nearby_ratings()`
- **User Analytics**: `get_user_rating_summary()`, `calculate_network_trend()`
- **Performance Insights**: `get_network_performance_insights()`, performance grading system

### Data Validation & Constraints

- **Model-level validation**: Rating range (1.0-5.0), coordinate validation, review length
- **Serializer validation**: Comprehensive field validation, cross-field validation
- **Business rules**: One rating per user per network, nested comment restrictions
- **Input sanitization**: Content trimming, empty value checks

### Enhanced Features

- **Smart Recommendations**: Location-based network suggestions with rating aggregation
- **Rating Analytics**: Trend analysis, performance grading, device-specific ratings
- **Advanced Search**: Multi-field search across reviews, networks, and addresses
- **Error Handling**: Comprehensive try-catch blocks with detailed error messages
- **Permission Checks**: Owner-based editing/deletion for ratings and comments

## Important Notes

- The project is deployed on Railway (`radeur.up.railway.app`)
- Secret key is hardcoded in settings (should be moved to environment variables for production)
- Debug mode is currently enabled (should be disabled in production)
- CORS is configured to allow all origins (should be restricted for production)
- Location-based features now fully functional with distance calculation utilities
- All major gaps identified in initial analysis have been addressed