from django.urls import include, path
from rest_framework import routers
from accounts.views import UserViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

app_name = 'accounts'

urlpatterns = [
    path('', include(router.urls)),
]