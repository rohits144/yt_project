from rest_framework import serializers
from .models import Subscription, Video

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = [
            'id', 'kind', 'etag', 'published_at', 'title',
            'description', 'channel_id', 'resource_channel_id', 'thumbnails'
        ]


# Serializer for Video model
class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['subscription', 'channel_id', 'video_id', 'title', 'published_at', 'is_watched']