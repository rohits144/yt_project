
import datetime
import json
import logging
import os
from django.conf import settings
from django.http import JsonResponse, HttpResponseRedirect
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
@method_decorator(csrf_exempt, name='dispatch')
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
    
@method_decorator(csrf_exempt, name='dispatch')
class DownloadedVideosView(View):
    def get(self, request):
        # Assume videos are downloaded in 'downloaded_videos' directory
        video_dir = settings.BASE_DIR / 'downloaded_videos'
        videos = []
        if os.path.exists(video_dir):
            for video_obj in Video.objects.all():
                # Find the actual file for this video
                # The filename format is videoid_title.mp4
                safe_title = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in video_obj.title).strip().replace(' ', '_')
                filename = f"{video_obj.video_id}_{safe_title}.mp4"
                file_path = video_dir / filename
                if os.path.exists(file_path):
                    videos.append({
                        'title': video_obj.title,
                        'video_id': video_obj.video_id,
                        'file_url': f"/downloaded_videos/{filename}",
                    })
        return render(request, 'fetcher/downloaded_videos.html', {'videos': videos})
    
@method_decorator(csrf_exempt, name='dispatch')
class DeleteDownloadedVideoView(View):
    def post(self, request):
        video_id = request.POST.get('video_id')
        if not video_id:
            return JsonResponse({'error': 'Missing video_id'}, status=400)
        try:
            video_obj = Video.objects.filter(video_id=video_id).first()
            if not video_obj:
                return JsonResponse({'error': 'Video not found'}, status=404)
            # Build filename
            safe_title = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in video_obj.title).strip().replace(' ', '_')
            filename = f"{video_obj.video_id}_{safe_title}.mp4"
            video_dir = settings.BASE_DIR / 'downloaded_videos'
            file_path = video_dir / filename
            if os.path.exists(file_path):
                os.remove(file_path)
            video_obj.is_watched = True
            video_obj.save()
            # Redirect to gallery with success message
            from django.urls import reverse
            response = HttpResponseRedirect(reverse('downloaded-videos') + '?deleted=1')
            return response
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
class HomePageView(View):
    def get(self, request):
        return render(request, 'fetcher/home.html')

@method_decorator(csrf_exempt, name='dispatch')
class MarkSubscriptionFavView(View):
    def post(self, request):
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
            sub_id = data.get('id')
            is_fav = data.get('is_fav')
            if sub_id is None or is_fav is None:
                return JsonResponse({'success': False, 'error': 'Missing id or is_fav'})
            sub = Subscription.objects.filter(id=sub_id).first()
            if not sub:
                return JsonResponse({'success': False, 'error': 'Subscription not found'})
            sub.is_fav = bool(is_fav)
            sub.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
@method_decorator(csrf_exempt, name='dispatch')
class FetchAndDownloadFavVideosView(View):
    def post(self, request):
        from .utils import get_latest_videos, download_video
        fav_subs = Subscription.objects.filter(is_fav=True)
        new_videos = 0
        downloaded = 0
        errors = []
        for sub in fav_subs:
            channel_id = sub.resource_channel_id
            if not channel_id:
                continue
            try:
                videos = get_latest_videos(channel_id)
            except Exception as e:
                errors.append({'channel_id': channel_id, 'error': str(e)})
                continue
            for video in videos:
                video_id = video.get('video_id')
                if not video_id:
                    continue
                # Check if video already exists in Video model
                if Video.objects.filter(video_id=video_id).exists():
                    continue
                # Create Video object
                try:
                    Video.objects.create(
                        subscription=sub,
                        channel_id=channel_id,
                        video_id=video_id,
                        title=video.get('title', ''),
                        published_at=video.get('published_at'),
                        is_watched=False
                    )
                    new_videos += 1
                except Exception as e:
                    errors.append({'video_id': video_id, 'error': str(e)})
                    continue
                # Download video
                try:
                    download_video(video_id)
                    downloaded += 1
                except Exception as e:
                    errors.append({'video_id': video_id, 'error': str(e)})
        return JsonResponse({'new_videos': new_videos, 'downloaded': downloaded, 'errors': errors})