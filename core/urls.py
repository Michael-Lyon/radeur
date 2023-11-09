from django.urls import include, path
from rest_framework import routers
from core.views import NetworkRatingViewSet

router = routers.DefaultRouter()
router.register(r'core', NetworkRatingViewSet)

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
]