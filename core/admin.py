from django.contrib import admin
from .models import Network, NetworkDevice, NetworkRating, Comment

@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'status')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(NetworkDevice)
class NetworkDeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(NetworkRating)
class NetworkRatingAdmin(admin.ModelAdmin):
    list_display = ('network', 'user', 'rating', 'created_at')
    search_fields = ('network__name', 'user__username')
    list_filter = ('network', 'rating')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at', 'is_reply')
    search_fields = ('user__username', 'content')
    list_filter = ('created_at', 'user')
