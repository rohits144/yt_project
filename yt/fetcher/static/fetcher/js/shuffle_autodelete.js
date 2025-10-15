// shuffle_autodelete.js
// Netflix-style shuffle play with auto-delete for downloaded videos

document.addEventListener('DOMContentLoaded', function() {
    const shuffleAutoBtn = document.getElementById('shuffleAutoDeleteBtn');
    if (!shuffleAutoBtn) return;

    let videoList = Array.from(document.querySelectorAll('.tile'));
    let played = new Set();
    let isPlaying = false;
    let modal = document.getElementById('videoModal');
    let videoPlayer = document.getElementById('modalVideo');

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    function getUnplayedVideos() {
        return videoList.filter(tile => !played.has(tile.dataset.videoId));
    }

    function playRandomVideo() {
        let remaining = getUnplayedVideos();
        if (remaining.length === 0) {
            alert('No more videos!');
            isPlaying = false;
            return;
        }
        let randomTile = remaining[Math.floor(Math.random() * remaining.length)];
        let videoId = randomTile.dataset.videoId;
        let videoUrl = randomTile.dataset.videoUrl;
        let title = randomTile.dataset.videoTitle;
        played.add(videoId);
        // Show modal and play
        document.getElementById('modalTitle').textContent = title;
        videoPlayer.src = videoUrl;
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        setTimeout(() => videoPlayer.play(), 100);
        // Listen for end
        videoPlayer.onended = function() {
            // Delete video via AJAX
            fetch('/downloaded-videos/delete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ video_ids: [videoId] })
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    // Remove tile from DOM
                    randomTile.remove();
                    // Play next
                    playRandomVideo();
                } else {
                    alert('Failed to delete video.');
                    isPlaying = false;
                }
            });
        };
    }

    shuffleAutoBtn.addEventListener('click', function() {
        if (isPlaying) return;
        // Refresh video list and played set
        videoList = Array.from(document.querySelectorAll('.tile'));
        played = new Set();
        isPlaying = true;
        playRandomVideo();
    });

    // If modal is closed, stop playing
    document.querySelector('.modal-close').addEventListener('click', function() {
        isPlaying = false;
        videoPlayer.onended = null;
    });
});
