from rest_framework import serializers
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import Network, NetworkDevice, NetworkRating, Comment

class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Network
        fields = '__all__'


class NetworkDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkDevice
        fields = '__all__'

class NetworkRatingSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    network =serializers.SerializerMethodField()
    device = NetworkDeviceSerializer(read_only=True)
    network_id = serializers.PrimaryKeyRelatedField(
        queryset=Network.objects.filter(status=True), 
        source='network', 
        write_only=True,
        help_text="ID of the network being rated"
    )
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=NetworkDevice.objects.all(), 
        source='device', 
        write_only=True,
        required=False,
        help_text="ID of the device used (optional)"
    )
    rating = serializers.DecimalField(
        max_digits=3, 
        decimal_places=1,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text="Rating between 1.0 and 5.0"
    )
    review = serializers.CharField(
        max_length=1000,
        min_length=10,
        help_text="Detailed review (minimum 10 characters)"
    )

    class Meta:
        model = NetworkRating
        fields = ['id', 'user', 'network', 'device', 'network_id', 'device_id', 'rating', 'address', 'created_at', 'review', 'comments']
        extra_kwargs = {
            'user': {'read_only': True},
            'created_at': {'read_only': True},
        }

    def validate_rating(self, value):
        """Custom validation for rating"""
        if value < 1.0 or value > 5.0:
            raise serializers.ValidationError("Rating must be between 1.0 and 5.0")
        return value

    def validate_review(self, value):
        """Custom validation for review"""
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Review must be at least 10 characters long")
        return value.strip()

    def validate_network_id(self, value):
        """Validate that the network is active"""
        if not value.status:
            raise serializers.ValidationError("Cannot rate an inactive network")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        # Check if user already rated this network (optional business rule)
        user = self.context['request'].user if 'request' in self.context else None
        network = attrs.get('network')
        
        if user and network and self.instance is None:  # Only for creation
            existing_rating = NetworkRating.objects.filter(user=user, network=network).first()
            if existing_rating:
                raise serializers.ValidationError("You have already rated this network. You can edit your existing rating.")
        
        return attrs

    def get_comments(self, obj):
        comments = obj.comments.filter(parent=None).order_by('-created_at')
        return CommentSerializer(comments, many=True, context=self.context).data

    def get_network(self, obj):
        network = obj.network
        return NetworkSerializer(network, context=self.context).data if network else None

    def create(self, validated_data):
        # Set user from request context
        validated_data['user'] = self.context['request'].user
        return NetworkRating.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Don't allow changing the network or user
        validated_data.pop('network', None)
        validated_data.pop('user', None)
        return super().update(instance, validated_data)


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    num_likes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    content = serializers.CharField(
        max_length=500,
        min_length=1,
        help_text="Comment content (1-500 characters)"
    )

    class Meta:
        model = Comment
        fields = ['id', 'user', 'username', 'content', 'network_rating', 'created_at', 'updated_at', 'parent', 'num_likes', 'liked', 'replies']
        extra_kwargs = {
            'user': {'read_only': True},
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }

    def validate_content(self, value):
        """Custom validation for comment content"""
        if not value or len(value.strip()) < 1:
            raise serializers.ValidationError("Comment cannot be empty")
        if len(value.strip()) > 500:
            raise serializers.ValidationError("Comment cannot exceed 500 characters")
        return value.strip()

    def validate(self, attrs):
        """Cross-field validation"""
        # Validate parent comment exists and belongs to same rating
        parent = attrs.get('parent')
        network_rating = attrs.get('network_rating')
        
        if parent and network_rating and parent.network_rating != network_rating:
            raise serializers.ValidationError("Parent comment must belong to the same rating")
        
        # Don't allow nested replies (only one level deep)
        if parent and parent.parent is not None:
            raise serializers.ValidationError("Cannot reply to a reply. Please reply to the original comment.")
        
        return attrs

    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.all().order_by('created_at')
            return CommentSerializer(replies, many=True, context=self.context).data
        return []

    def get_num_likes(self, obj):
        return obj.total_likes

    def get_liked(self, obj):
        user = self.context.get('request').user if 'request' in self.context else None
        if user and user.is_authenticated:
            return obj.likes.filter(id=user.id).exists()
        return False

    def create(self, validated_data):
        # Set user from request context
        validated_data['user'] = self.context['request'].user
        return Comment.objects.create(**validated_data)
