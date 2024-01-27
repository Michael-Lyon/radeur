from django.urls import include, path
from rest_framework import routers
from accounts.views import UserViewSet, LoginViewSet, ProfileApiView

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r"login", LoginViewSet, basename='login')


app_name = 'accounts'

urlpatterns = [
    path('', include(router.urls)),
    path("profile/", ProfileApiView.as_view(), name="profile"),
]
# urlpatterns = router.urls