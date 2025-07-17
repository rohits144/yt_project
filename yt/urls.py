
from django.contrib import admin
from django.urls import path

from yt.fetcher.views import SubscriptionImportView, SubscriptionFetchView, SubscriptionListView, FavChannelsLatestVideosView, ImportFavChannelVideosView, DownloadUnwatchedVideosView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('subscriptions-import/', SubscriptionImportView.as_view(), name='subscription-import'),
    path('subscriptions-fetch/', SubscriptionFetchView.as_view(), name='subscription-fetch'),
    path('subscriptions/', SubscriptionListView.as_view(), name='subscription-list'),
    path('fav-channels-latest-videos/', FavChannelsLatestVideosView.as_view(), name='fav-channels-latest-videos'),
    path('import-fav-channel-videos/', ImportFavChannelVideosView.as_view(), name='import-fav-channel-videos'),
    path('download-unwatched-videos/', DownloadUnwatchedVideosView.as_view(), name='download-unwatched-videos'),
]