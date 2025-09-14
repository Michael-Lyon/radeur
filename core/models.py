from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
# from django.contrib.gis.db import models as gis_models

User = get_user_model()

class Network(models.Model):
    """
    Represents network providers/ISPs.

    Fields:
        name: The name of the ISP.
        image: An image representing the ISP.
        status: Boolean status to indicate if the ISP is active.
        slug: A slug for URL representation, unique for each network.
    """
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='uploads/')
    status = models.BooleanField()
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Network, self).save(*args, **kwargs)

class NetworkDevice(models.Model):
    """
    Represents devices used with ISPs such as phones, Wi-Fi devices, etc.

    Fields:
        name: The name of the device.
        slug: A slug for URL representation.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(NetworkDevice, self).save(*args, **kwargs)

class NetworkRating(models.Model):
    """
    Represents ratings given by users for networks.

    Fields:
        user: The user who gave the rating.
        network: The network being rated.
        device: The name of the device used.
        rating: The rating given by the user.
        latitude: Latitude for geolocation (optional).
        longitude: Longitude for geolocation (optional).
        created_at: The date and time when the rating was created.
        review: The user's review text.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    network = models.ForeignKey(Network, on_delete=models.CASCADE, blank=True, null=True)
    device = models.ForeignKey(NetworkDevice, on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Rating between 1.0 and 5.0"
    )
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(-90.0), MaxValueValidator(90.0)],
        help_text="Latitude coordinate (-90 to 90)"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        validators=[MinValueValidator(-180.0), MaxValueValidator(180.0)],
        help_text="Longitude coordinate (-180 to 180)"
    )
    # location = gis_models.PointField(null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True, help_text="User's location address")
    created_at = models.DateTimeField(auto_now_add=True)
    # objects = gis_models.Manager()
    review = models.TextField(max_length=1000, help_text="User's detailed review of the network")

    def clean(self):
        """Validate the model instance"""
        super().clean()
        
        # Validate rating
        if self.rating and (self.rating < 1.0 or self.rating > 5.0):
            raise ValidationError({'rating': 'Rating must be between 1.0 and 5.0'})
        
        # Validate coordinates if provided
        if self.latitude is not None and (self.latitude < -90 or self.latitude > 90):
            raise ValidationError({'latitude': 'Latitude must be between -90 and 90'})
        
        if self.longitude is not None and (self.longitude < -180 or self.longitude > 180):
            raise ValidationError({'longitude': 'Longitude must be between -180 and 180'})
        
        # Ensure both coordinates are provided together or both are None
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError('Both latitude and longitude must be provided together')
        
        # Validate review length
        if self.review and len(self.review.strip()) < 10:
            raise ValidationError({'review': 'Review must be at least 10 characters long'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.network.name} Rating by {self.user.username}' if self.network else f'Rating by {self.user.username}'

class Comment(models.Model):
    """
    Model for managing user comments and likes on network ratings.

    Fields:
        user: The user who wrote the comment.
        content: The content of the comment.
        network_rating: The rating the comment is associated with.
        created_at: The date and time when the comment was created.
        updated_at: The date and time when the comment was last updated.
        parent: Reference to another comment if this is a reply.
        likes: Users who liked the comment.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    network_rating = models.ForeignKey(NetworkRating, related_name="comments", on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_comments', blank=True)

    def __str__(self):
        return f'Comment by {self.user} on {self.created_at}'

    @property
    def is_reply(self):
        return self.parent is not None

    @property
    def is_liked(self):
        return self.likes.filter(username=self.user.username).exists()

    @property
    def total_likes(self):
        return self.likes.count()
