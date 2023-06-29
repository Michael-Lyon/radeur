from django.urls import include, path
from rest_framework import routers
from core.views import UserViewSet

router = routers.DefaultRouter()
router.register(r'core', UserViewSet)

app_name = 'core'

urlpatterns = [
    path('', include(router.urls)),
]