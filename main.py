import json
import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
import socket
import datetime

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
    """Authenticate the user with OAuth and return the API client."""
    try:
        flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
        credentials = flow.run_local_server(port=0)
        youtube = build("youtube", "v3", credentials=credentials)
        return youtube
    except FileNotFoundError:
        print("❌ Error: 'client_secret.json' not found.")
        sys.exit(1)
    except socket.gaierror:
        print("❌ Network error. Check your internet connection.")
        sys.exit(1)
    except RefreshError:
        print("❌ Error: Authentication failed. Try again.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected authentication error: {e}")
        sys.exit(1)

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
    except Exception as e:
        print(f"❌ Error saving final combined file: {e}")

if __name__ == "__main__":
    print("🔐 Starting authentication...")
    youtube = get_authenticated_service()

    print("📡 Fetching subscriptions with intermediate saves...")
    all_subs = fetch_and_save_responses(youtube)

    print("📦 Saving final combined file...")
    save_combined_items(all_subs)
