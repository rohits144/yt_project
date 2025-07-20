from django.db import models


class Subscription(models.Model):
    id = models.CharField(primary_key=True, max_length=100)  # Unique subscription ID from JSON
    kind = models.CharField(max_length=50)
    etag = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    channel_id = models.CharField(max_length=100)
    resource_channel_id = models.CharField(max_length=100)
    thumbnails = models.JSONField()
    is_fav = models.BooleanField(default=False)

    class Meta:
        unique_together = ('channel_id', 'resource_channel_id')  # Prevent duplicate subscriptions

    def __str__(self):
        return self.title
    

class Video(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='videos')
    channel_id = models.CharField(max_length=100)
    video_id = models.CharField(max_length=32, unique=True)
    title = models.CharField(max_length=512)
    published_at = models.DateTimeField()
    snippet = models.JSONField(default=dict, blank=True)
    is_watched = models.BooleanField(default=False)
    is_rewatchable = models.BooleanField(default=False)

    def __str__(self):
        return self.title