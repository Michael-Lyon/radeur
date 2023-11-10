from django.contrib import admin
from .models import Network, NetworkRating, Comment


# Register your models here.
admin.site.register(Network)
admin.site.register(NetworkRating)
admin.site.register(Comment)