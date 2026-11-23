"""YouTube helpers the live import and the Reader share: a video's id from any common URL form, and its
title and channel from YouTube's public oEmbed endpoint."""

from __future__ import annotations

import json
import re
import urllib.request
from urllib.parse import parse_qs, urlparse

from learnloop.ingest.models import SourceFetchError, UnsupportedSourceError

_USER_AGENT = "learnloop-ingest/0.1 (+https://github.com/learnloop)"


def youtube_video_id(source: str) -> str:
    """Extract the 11-character video id from any common YouTube URL form."""

    candidate = source.strip()
    parsed = urlparse(candidate)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host in {"youtu.be", "www.youtu.be"}:
        video = parsed.path.lstrip("/").split("/", 1)[0]
        if video:
            return video
    if "v" in parse_qs(parsed.query):
        return parse_qs(parsed.query)["v"][0]
    match = re.search(r"/(?:embed|shorts|live|v)/([^/?#]+)", parsed.path)
    if match:
        return match.group(1)
    raise UnsupportedSourceError(f"Could not extract a YouTube video id from {source!r}")


def _http_get_text(url: str, *, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (a fixed https URL)
            return response.read().decode("utf-8", errors="replace")
    except OSError as exc:
        raise SourceFetchError(f"Failed to fetch {url}: {exc}") from exc


def youtube_oembed_metadata(video_id: str) -> tuple[str | None, str | None]:
    """Best-effort (title, author) from YouTube's public oEmbed endpoint.

    No API key: ``https://www.youtube.com/oembed`` returns the video title and
    the uploading channel as ``author_name``. Any failure (offline, private
    video, malformed JSON) returns ``(None, None)`` so callers degrade to a URL
    title rather than failing the import.
    """

    url = (
        "https://www.youtube.com/oembed?format=json&url="
        f"https://www.youtube.com/watch?v={video_id}"
    )
    try:
        data = json.loads(_http_get_text(url, timeout=10))
        title = (data.get("title") or "").strip() or None
        author = (data.get("author_name") or "").strip() or None
        return title, author
    except Exception:  # pragma: no cover - metadata is best-effort
        return None, None


__all__ = ["youtube_oembed_metadata", "youtube_video_id"]
