
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from yt.fetcher.views import SubscriptionImportView, SubscriptionFetchView, SubscriptionListView, FavChannelsLatestVideosView, ImportFavChannelVideosView, DownloadUnwatchedVideosView, DownloadedVideosView, DeleteDownloadedVideoView, HomePageView, MarkSubscriptionFavView, FetchAndDownloadFavVideosView, RewatchableVideosView, UpdateRewatchableFlagView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomePageView.as_view(), name='home'),
    path('import-subscriptions/', SubscriptionImportView.as_view(), name='import-subscriptions'),
    path('fetch-subscriptions/', SubscriptionFetchView.as_view(), name='fetch-subscriptions'),
    path('subscriptions/', SubscriptionListView.as_view(), name='subscriptions'),
    path('mark-subscription-fav/', MarkSubscriptionFavView.as_view(), name='mark-subscription-fav'),
    path('fetch-download-fav-videos/', FetchAndDownloadFavVideosView.as_view(), name='fetch-download-fav-videos'),
    path('fav-channels-latest-videos/', FavChannelsLatestVideosView.as_view(), name='fav-channels-latest-videos'),
    path('import-fav-channel-videos/', ImportFavChannelVideosView.as_view(), name='import-fav-channel-videos'),
    path('download-unwatched-videos/', DownloadUnwatchedVideosView.as_view(), name='download-unwatched-videos'),
    path('downloaded-videos/', DownloadedVideosView.as_view(), name='downloaded-videos'),
    path('downloaded-videos/delete/', DeleteDownloadedVideoView.as_view(), name='delete-downloaded-video'),
    path('rewatchable-videos/', RewatchableVideosView.as_view(), name='rewatchable-videos'),
    path('update-rewatchable-flag/', UpdateRewatchableFlagView.as_view(), name='update-rewatchable-flag'),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)