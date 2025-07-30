import json
import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
import socket

import yt_dlp

def db_updater():
    """Placeholder for database update logic."""
    import json
    from fetcher.models import Subscription

    with open('subscriptions_combined.json') as f:
        data = json.load(f)
        for item in data:
            Subscription.objects.update_or_create(
                id=item['id'],
                defaults={
                    'kind': item['kind'],
                    'etag': item['etag'],
                    'snippet': item['snippet'],
                }
            )

# Scopes for read-only YouTube access
SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

# Folder to store intermediate responses
RAW_DATA_DIR = "raw_responses"
FINAL_FILE = "subscriptions_combined.json"

def ensure_dir(path):
    """Ensure the directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)

def get_authenticated_service():
    """
    Authenticate the user with OAuth and return the API client.
    Uses token.json for persistent authentication, avoiding repeated browser logins.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = None
    # Load credentials from token.json if it exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If no (valid) credentials available, let user log in via browser ONCE
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)
    return youtube

def fetch_and_save_responses(youtube):
    """Fetch all pages of subscriptions and save each page as raw JSON."""
    ensure_dir(RAW_DATA_DIR)
    all_items = []
    page = 1

    try:
        request = youtube.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50
        )

        while request is not None:
            response = request.execute()
            items = response.get("items", [])
            all_items.extend(items)

            # Save raw page response
            filename = os.path.join(RAW_DATA_DIR, f"subscriptions_page_{page}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(response, f, indent=4, ensure_ascii=False)
            print(f"✅ Saved page {page} with {len(items)} subscriptions to '{filename}'")

            page += 1
            request = youtube.subscriptions().list_next(request, response)

        return all_items

    except HttpError as e:
        # Save whatever data was fetched so far
        save_combined_items(all_items)
        if e.resp.status == 403:
            print("❌ API quota exceeded or access forbidden.")
        elif e.resp.status == 401:
            print("❌ Unauthorized. Token might be expired.")
        else:
            print(f"❌ API Error: {e}")
        sys.exit(1)

    except socket.gaierror:
        save_combined_items(all_items)
        print("❌ Network error while accessing API.")
        sys.exit(1)

    except Exception as e:
        save_combined_items(all_items)
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def save_combined_items(items, filename=FINAL_FILE):
    """Save all combined items to a final JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
        print(f"💾 Final combined JSON saved to '{filename}' with {len(items)} subscriptions.")
        # Delete all files in RAW_DATA_DIR starting with 'subscriptions_page'
        # try:
        #     for fname in os.listdir(RAW_DATA_DIR):
        #         if fname.startswith("subscriptions_page"):
        #             fpath = os.path.join(RAW_DATA_DIR, fname)
        #             if os.path.isfile(fpath):
        #                 os.remove(fpath)
        #     print(f"🧹 Deleted all intermediate 'subscriptions_page' files in '{RAW_DATA_DIR}'.")
        # except Exception as cleanup_err:
        #     print(f"⚠️ Error cleaning up raw response files: {cleanup_err}")
    except Exception as e:
        print(f"❌ Error saving final combined file: {e}")

def get_latest_videos(channel_id, max_results=5):
    youtube = get_authenticated_service()

    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=max_results,
        order="date",
        type="video"
    )

    response = request.execute()

    all_data = []

    for item in response.get("items", []):
        title = item["snippet"]["title"]
        video_id = item["id"]["videoId"]
        published_at = item["snippet"]["publishedAt"]
        snippet = item["snippet"]
        all_data.append({
            "title": title,
            "video_id": video_id,
            "published_at": published_at,
            "snippet": snippet
        })
    return all_data




def download_video(video_id, download_dir="downloaded_videos"):
    """
    Download a YouTube video using yt-dlp in the best available resolution.
    The file will be named as videoid_title.mp4 in the specified download_dir.
    """
    try:
        # Ensure the download directory exists
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
        url = f"https://www.youtube.com/watch?v={video_id}"

        # Use yt-dlp to extract video info first (to get the title)
        ydl_opts_info = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            # Clean title for filename
            safe_title = ''.join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in title).strip().replace(' ', '_')
            filename = f"{video_id}_{safe_title}.mp4"

        # Download the best video+audio as mp4
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f"{download_dir}/{video_id}_{safe_title}.%(ext)s",
            'merge_output_format': 'mp4',
            'quiet': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"⬇️ Downloading {title} as {filename} in best available resolution...")
            ydl.download([url])
            print("✅ Download completed successfully!")

    except Exception as e:
        print(f"❌ Error downloading video: {e}")


if __name__ == "__main__":
    # print("🔐 Starting authentication...")
    # youtube = get_authenticated_service()

    # print("📡 Fetching subscriptions with intermediate saves...")
    # all_subs = fetch_and_save_responses(youtube)

    # print("📦 Saving final combined file...")
    # save_combined_items(all_subs)

    download_video("Z3e7w8XId1c")