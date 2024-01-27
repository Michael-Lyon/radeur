from rest_framework import serializers
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
        queryset=Network.objects.all(), source='network', write_only=True
    )
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=NetworkDevice.objects.all(), source='device', write_only=True
    )

    class Meta:
        model = NetworkRating
        fields = ['id', 'user', 'network', 'device', 'network_id', 'device_id', 'rating', 'address', 'created_at', 'review', 'comments']
        extra_kwargs = {
            'user': {'required': False, },
        }

    def get_comments(self, obj):
        comments = obj.comments.all()
        return CommentSerializer(comments, many=True).data

    def get_network(self, obj):
        network = obj.network
        return NetworkSerializer(network, context=self.context).data

    def create(self, validated_data):
        # Implement custom create logic if necessary
        return NetworkRating.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Implement custom update logic if necessary
        instance = super().update(instance, validated_data)
        return instance


class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    num_likes = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'network_rating', 'created_at', 'updated_at', 'parent', 'num_likes', 'liked', 'replies']
        extra_kwargs = {
            'user': {'required': False, },
        }

    def get_replies(self, obj):
        # If the comment is a parent comment, serialize its replies
        if obj.parent is None:
            replies = obj.replies.all()
            return CommentSerializer(replies, many=True, context=self.context).data
        return []

    def get_num_likes(self, obj):
        # If the comment is a parent comment, serialize its replies
        if obj.parent is None:
            numbers = obj.total_likes
            return numbers
    def get_liked(self, obj):
        # If the comment is a parent comment, serialize its replies
        return obj.is_liked
