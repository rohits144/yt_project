# YouTube Subscription & Video Manager

A Django web application to manage your YouTube subscriptions, download videos, and view them in a local gallery. Features include favorite channels, bulk video download, AJAX actions, and a modern UI.

---


## Deployment with Docker Compose

### 1. Clone the repository
```powershell
git clone https://github.com/rohits144/yt_project.git
cd yt_project
```

### 2. Add Google API credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create/select a project, enable YouTube Data API v3
3. Create OAuth client ID (Desktop app)
4. Download `client_secret.json` and place in project root

### 3. Build and start containers
```powershell
docker compose build
docker compose up -d
```

### 4. Set up the database (inside Django container)
```powershell
docker compose exec django python manage.py migrate
```

### 5. Access the app
Open [http://localhost](http://localhost) in your browser.

---

## Auto-start containers on system reboot

To ensure all containers/services start automatically after a system reboot:

1. Install Docker Compose and Docker as a service (Windows: Docker Desktop, Linux: systemd).
2. Use Docker's restart policy in `docker-compose.yml`:

```
services:
   django:
      ...
      restart: always
   nginx:
      ...
      restart: always
```

3. (Linux) Enable Docker to start on boot:
```bash
sudo systemctl enable docker
```

4. (Optional) Use scheduled tasks or systemd to run `docker compose up -d` on startup if needed.

---

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
- Videos are served via Nginx (`/media/`) for best performance.
- All requests go through Nginx; Django is not exposed directly.
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
