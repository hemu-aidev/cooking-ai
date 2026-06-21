"""
youtube_service.py
-------------------
Pulls relevant cooking videos for a recipe title.

IMPORTANT: This uses a server-side API key against the public YouTube Data
API v3 search endpoint. No user sign-in / OAuth is needed or used — public
video search doesn't touch anyone's personal YouTube account. OAuth would
only be relevant if you needed a *user's own* playlists/history, which this
product doesn't.
"""
from typing import List, Dict, Optional

from . import config

try:
    from googleapiclient.discovery import build
except ImportError:
    build = None


class YouTubeService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.YOUTUBE_API_KEY
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if build is None:
                raise RuntimeError("Run: pip install google-api-python-client")
            if not self.api_key:
                raise RuntimeError("YOUTUBE_API_KEY not set")
            self._client = build("youtube", "v3", developerKey=self.api_key)
        return self._client

    def search_videos(self, query: str, max_results: Optional[int] = None) -> List[Dict]:
        """Returns a list of {video_id, title, channel, thumbnail, url}.
        Fails gracefully (returns an error payload instead of raising) so a
        YouTube outage or quota limit never takes down recipe search."""
        max_results = max_results or config.DEFAULT_VIDEO_COUNT
        try:
            response = self.client.search().list(
                q=f"{query} recipe",
                part="snippet",
                type="video",
                maxResults=max_results,
                relevanceLanguage="en",
                safeSearch="strict",
            ).execute()
        except Exception as e:
            return [{"error": str(e)}]

        videos = []
        for item in response.get("items", []):
            vid = item["id"]["videoId"]
            snippet = item["snippet"]
            videos.append({
                "video_id": vid,
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "thumbnail": snippet["thumbnails"]["medium"]["url"],
                "url": f"https://www.youtube.com/watch?v={vid}",
            })
        return videos
