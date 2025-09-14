from django.urls import include, path
from core import views


app_name = 'core'

urlpatterns = [
    path('ratings/', views.NetworkRatingListCreate.as_view(), name="network_rating_list_create"),
    path('ratings/<int:pk>', views.NetworkRatingDetail.as_view(), name="network_rating_detail"),

    path('comments/', views.CommentView.as_view(), name='add_comment'),
    path('comments/<int:comment_id>/', views.CommentView.as_view(), name='comment-detail'),
    path('comments/<int:comment_id>/like/', views.CommentView.as_view(), name='like_comment'),

    path("devices/", views.DevicesView.as_view(), name="device_view"),
    path("isp-providers/", views.NetworkView.as_view(), name="networks_list_view"),
    
    # New endpoints for statistics and recommendations
    path("statistics/", views.NetworkStatisticsView.as_view(), name="network_statistics"),
    path("statistics/<int:network_id>/", views.NetworkDetailStatsView.as_view(), name="network_detail_stats"),
    path("recommendations/", views.LocationBasedRecommendationsView.as_view(), name="location_recommendations"),
]