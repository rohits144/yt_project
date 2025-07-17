import datetime
import json
import logging
import os
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.http import HttpResponse

from yt.fetcher.serializers import VideoSerializer
from .utils import get_latest_videos
from .models import Subscription, Video

# Import the fetch logic from utils.py
from .utils import get_authenticated_service, fetch_and_save_responses, save_combined_items

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class SubscriptionImportView(View):
    def get(self, request):
        file_path = settings.BASE_DIR / 'subscriptions_combined.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read JSON file: {e}")
            return JsonResponse({'error': 'Failed to read JSON file.'}, status=500)

        created, skipped = 0, 0
        for item in data:
            try:
                # Skip if required fields are missing
                if not item.get('id') or not item.get('snippet'):
                    continue
                snippet = item['snippet']
                obj, created_flag = Subscription.objects.get_or_create(
                    id=item['id'],
                    defaults={
                        'kind': item.get('kind', ''),
                        'etag': item.get('etag', ''),
                        'published_at': snippet.get('publishedAt'),
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'channel_id': snippet.get('channelId', ''),
                        'resource_channel_id': snippet.get('resourceId', {}).get('channelId', ''),
                        'thumbnails': snippet.get('thumbnails', {}),
                    }
                )
                if created_flag:
                    created += 1
                else:
                    skipped += 1
                    logger.info(f"Subscription with id={item['id']} already exists. Skipping insert.")
            except Exception as e:
                logger.error(f"Error processing subscription id={item.get('id')}: {e}")
        # Delete the file after import if it exists
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
        return JsonResponse({
            'created': created,
            'skipped': skipped,
            'message': 'Import completed.'
        })

class SubscriptionFetchView(View):
    def post(self, request):
        try:
            youtube = get_authenticated_service()
            all_subs = fetch_and_save_responses(youtube)
            save_combined_items(all_subs, filename=str(settings.BASE_DIR / 'subscriptions_combined.json'))
            logger.info(f"Fetched and saved {len(all_subs)} subscriptions from YouTube API.")
            return JsonResponse({'status': 'success', 'fetched': len(all_subs)})
        except Exception as e:
            logger.error(f"Failed to fetch subscriptions from YouTube API: {e}")
            return JsonResponse({'error': str(e)}, status=500)


class SubscriptionListView(View):
    def get(self, request):
        subscriptions = Subscription.objects.all().order_by('title')
        return render(request, 'fetcher/subscription_list.html', {'subscriptions': subscriptions})
        
@method_decorator(csrf_exempt, name='dispatch')
class FavChannelsLatestVideosView(View):
    def get(self, request):
        # Get all favorite subscriptions
        fav_subs = Subscription.objects.filter(is_fav=True)

        result = {}
        for sub in fav_subs:
            channel_id = sub.resource_channel_id
            if channel_id:
                try:
                    videos = get_latest_videos(channel_id)
                    result[channel_id] = videos
                except Exception as e:
                    result[channel_id] = {'error': str(e)}

        # Only write the file if there is data in result
        if not result:
            return JsonResponse({'status': 'no_data', 'message': 'No favorite channels or no videos found.'})

        # Create a filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"fav_channels_latest_videos_{timestamp}.json"
        file_dir = settings.BASE_DIR / 'raw_responses'
        if not os.path.exists(file_dir):
            os.makedirs(file_dir, exist_ok=True)
        file_path = str(file_dir / filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save latest videos JSON: {e}")
            return JsonResponse({'error': 'Failed to save file', 'details': str(e)}, status=500)

        return JsonResponse({'status': 'success', 'file': filename, 'channels': len(result)})

@method_decorator(csrf_exempt, name='dispatch')
class ImportFavChannelVideosView(View):
    def get(self, request):
        import glob
        file_dir = settings.BASE_DIR / 'raw_responses'
        pattern = str(file_dir / 'fav_channels_latest_videos*.json')
        files = glob.glob(pattern)
        if not files:
            return JsonResponse({'status': 'no_files', 'message': 'No matching files found.'}, status=404)

        imported, errors = 0, []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                errors.append({'file': file_path, 'error': str(e)})
                continue

            for channel_id, videos in data.items():
                try:
                    sub = Subscription.objects.filter(resource_channel_id=channel_id).first()
                    if not sub:
                        errors.append({'channel_id': channel_id, 'error': 'Subscription not found'})
                        continue
                    for video in videos:
                        video_data = {
                            'subscription': sub.id,
                            'channel_id': channel_id,
                            'video_id': video.get('video_id'),
                            'title': video.get('title'),
                            'published_at': video.get('published_at'),
                            'is_watched': False
                        }
                        serializer = VideoSerializer(data=video_data)
                        if serializer.is_valid():
                            serializer.save()
                            imported += 1
                        else:
                            errors.append({'video_id': video.get('video_id'), 'errors': serializer.errors})
                except Exception as e:
                    errors.append({'channel_id': channel_id, 'error': str(e)})

        return JsonResponse({'imported': imported, 'errors': errors})
    
from .utils import download_video
@method_decorator(csrf_exempt, name='dispatch')
class DownloadUnwatchedVideosView(View):
    def get(self, request):
        unwatched_videos = Video.objects.filter(is_watched=False)
        downloaded, errors = 0, []
        for video in unwatched_videos:
            try:
                download_video(video.video_id)
                downloaded += 1
            except Exception as e:
                errors.append({'video_id': video.video_id, 'error': str(e)})
        return JsonResponse({'downloaded': downloaded, 'errors': errors})