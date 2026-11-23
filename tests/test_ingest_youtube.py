from __future__ import annotations

import pytest

from learnloop.ingest.models import UnsupportedSourceError
from learnloop.ingest.youtube import youtube_video_id


@pytest.mark.parametrize(
    "source",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
    ],
)
def test_youtube_video_id(source):
    assert youtube_video_id(source) == "dQw4w9WgXcQ"


def test_youtube_video_id_rejects_bad_url():
    with pytest.raises(UnsupportedSourceError):
        youtube_video_id("https://www.youtube.com/feed/subscriptions")
