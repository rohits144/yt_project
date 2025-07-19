# YouTube Subscription & Video Manager

A Django web application to manage your YouTube subscriptions, download videos, and view them in a local gallery. Features include favorite channels, bulk video download, AJAX actions, and a modern UI.

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/rohits144/yt_project.git
cd yt_project
```

### 2. Install dependencies (Recommended: [uv](https://github.com/astral-sh/uv))
```bash
uv sync
```

### 3. Set up the database
```bash
uv run python manage.py migrate
```

### 4. Generate and add your Google API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project (or select an existing one)
3. Enable the YouTube Data API v3 for your project
4. Go to "Credentials" and click "Create Credentials" > "OAuth client ID"
5. Choose "Desktop app" as the application type
6. Download the `client_secret.json` file and place it in your project root
7. On first run, the app will prompt you to authenticate in your browser and generate `token.json` automatically

### 5. Run the development server
```bash
uv run python manage.py runserver
```

### 6. Access the app
Open [http://localhost:8000/](http://localhost:8000/) in your browser.

---

## Usage

1. **Import Subscriptions:**
   - Use the homepage to fetch subscriptions from YouTube or import from JSON.
2. **Mark Favorites:**
   - Go to Subscriptions, mark favorite channels.
3. **Fetch & Download Videos:**
   - Click the button to fetch and download latest videos from favorites.
   - Progress and notifications are shown.
4. **View Downloaded Videos:**
   - Go to the Downloaded Videos gallery.
   - Play videos in a modal, seek using the timeline.
   - Select and delete multiple videos at once.

---

## Project Structure
- `yt/` - Django app
- `downloaded_videos/` - Folder for downloaded video files
- `raw_responses/` - API response dumps
- `client_secret.json` - Google API credentials
- `token.json` - OAuth token (auto-generated)
- `README.md` - This file

---

## Notes
- For production, serve videos via Nginx or a proper static server.
- Never commit secrets (`token.json`, `client_secret.json`) to git.
- For best results, use Chrome/Firefox and properly encoded MP4 files.
- All Python commands and dependency management are recommended to be run via [uv](https://github.com/astral-sh/uv) for speed and reliability.

---

## License
MIT

---

## Author
Rohit Ranjan
GitHub: [rohits144](https://github.com/rohits144)
