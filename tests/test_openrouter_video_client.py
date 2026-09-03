from __future__ import annotations

import pytest

from learnloop.ai.client import make_video_generation_client
from learnloop.ai.errors import AIProviderUnavailable, VideoGenerationFailed, VideoGenerationTimeout
from learnloop.ai.providers.openrouter_video import (
    OpenRouterVideoClient,
    VideoGenerationRequest,
    VideoModelConstraints,
    clamp_duration,
    clamp_resolution,
)
from learnloop.ai.transport import VIDEO_GENERATION
from learnloop.config.schema import LearnLoopConfig
from tests.video_fakes import FakeVideoHttp


def _profile(model="google/veo-3.1"):
    config = LearnLoopConfig.model_validate(
        {"ai": {"providers": {"openrouter_video": {"type": "openrouter", "model": model}}}}
    )
    return config, config.ai.providers["openrouter_video"]


def _client(monkeypatch, http, **kwargs):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    _config, profile = _profile()
    sleeps: list[float] = []
    ticks = iter(range(0, 100000, 10))
    client = OpenRouterVideoClient(
        "openrouter_video", profile, http=http, sleep=sleeps.append, clock=lambda: float(next(ticks)), **kwargs
    )
    return client, sleeps


def test_submit_posts_model_prompt_and_options_with_bearer(monkeypatch):
    http = FakeVideoHttp()
    client, _ = _client(monkeypatch, http)

    job = client.submit(VideoGenerationRequest(prompt="a grid of dots", duration_seconds=6, resolution="720p", aspect_ratio="16:9"))

    assert job.id == "vid_1" and job.status == "pending"
    method, path, payload = http.calls[-1]
    assert (method, path) == ("POST", "/api/v1/videos")
    assert payload == {
        "model": "google/veo-3.1",
        "prompt": "a grid of dots",
        "duration": 6,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "generate_audio": False,
    }
    assert client.supports(VIDEO_GENERATION) and not client.supports("structured_completion")


def test_submit_rejection_is_typed_and_never_retried(monkeypatch):
    http = FakeVideoHttp(submit_status=402, submit_error={"message": "insufficient credits"})
    client, _ = _client(monkeypatch, http)

    with pytest.raises(VideoGenerationFailed, match="insufficient credits"):
        client.submit(VideoGenerationRequest(prompt="x"))
    assert http.submitted == 1


def test_wait_all_polls_every_pending_job_and_checkpoints_each_round(monkeypatch):
    http = FakeVideoHttp(
        polls={
            "vid_1": [{"status": "in_progress"}, {"status": "completed"}],
            "vid_2": [{"status": "pending"}, {"status": "in_progress"}, {"status": "completed"}],
        }
    )
    client, sleeps = _client(monkeypatch, http)
    rounds: list[tuple[list[str], float]] = []

    statuses = client.wait_all(
        ["vid_1", "vid_2"],
        max_wait_seconds=600,
        checkpoint=lambda snapshot, elapsed: rounds.append(([s.status for s in snapshot], elapsed)),
    )

    assert [s.status for s in statuses] == ["completed", "completed"]
    assert statuses[0].cost == 0.25 and statuses[0].url_count == 1
    assert sleeps == [15.0, 30.0, 30.0]
    assert [statuses_ for statuses_, _ in rounds] == [
        ["in_progress", "pending"],
        ["completed", "in_progress"],
        ["completed", "completed"],
    ]
    # Completed jobs are not polled again.
    polled = [path for method, path, _ in http.calls if method == "GET" and "/videos/vid_" in path]
    assert polled.count("/api/v1/videos/vid_1") == 2
    assert polled.count("/api/v1/videos/vid_2") == 3


def test_wait_all_failure_carries_the_shot_index(monkeypatch):
    http = FakeVideoHttp(polls={"vid_1": [{"status": "completed"}], "vid_2": [{"status": "failed", "error": {"message": "nsfw"}}]})
    client, _ = _client(monkeypatch, http)

    with pytest.raises(VideoGenerationFailed) as excinfo:
        client.wait_all(["vid_1", "vid_2"], max_wait_seconds=600)
    assert excinfo.value.shot_index == 1 and excinfo.value.status == "failed"
    assert "shot 2/2 failed: nsfw" in str(excinfo.value)


def test_wait_all_times_out_and_checkpoint_exceptions_stop_polling(monkeypatch):
    http = FakeVideoHttp(polls={"vid_1": [{"status": "in_progress"}]})
    client, _ = _client(monkeypatch, http)
    with pytest.raises(VideoGenerationTimeout):
        client.wait_all(["vid_1"], max_wait_seconds=25)

    class Cancelled(Exception):
        pass

    def cancel(_statuses, _elapsed):
        raise Cancelled()

    http2 = FakeVideoHttp(polls={"vid_1": [{"status": "in_progress"}]})
    client2, sleeps = _client(monkeypatch, http2)
    with pytest.raises(Cancelled):
        client2.wait_all(["vid_1"], max_wait_seconds=600, checkpoint=cancel)
    assert sleeps == [15.0]


def test_poll_retries_once_on_5xx_then_surfaces_errors(monkeypatch):
    http = FakeVideoHttp(polls={"vid_1": [{"status": "completed"}]}, poll_http_errors={"vid_1": [503]})
    client, _ = _client(monkeypatch, http)
    assert client.poll("vid_1").status == "completed"

    http2 = FakeVideoHttp(poll_http_errors={"vid_9": [404, 404]})
    client2, _ = _client(monkeypatch, http2)
    with pytest.raises(AIProviderUnavailable, match="HTTP 404"):
        client2.poll("vid_9")


def test_download_returns_bytes_with_index_query(monkeypatch):
    http = FakeVideoHttp(contents={"vid_1": b"real-mp4"})
    client, _ = _client(monkeypatch, http)
    assert client.download("vid_1") == b"real-mp4"
    assert http.calls[-1][1] == "/api/v1/videos/vid_1/content?index=0"


def test_model_constraints_parse_and_cache(monkeypatch):
    http = FakeVideoHttp()
    client, _ = _client(monkeypatch, http)
    constraints = client.model_constraints()
    assert constraints == VideoModelConstraints((4, 6, 8), ("720p", "1080p"), ("16:9",))
    assert client.model_constraints() is constraints
    assert sum(1 for _, path, _ in http.calls if path.endswith("/videos/models")) == 1

    unknown, _ = _client(monkeypatch, FakeVideoHttp(models=[]))
    assert unknown.model_constraints() is None


def test_clamp_helpers():
    constraints = VideoModelConstraints((4, 6, 8), ("720p", "1080p"), ("16:9",))
    assert clamp_duration(7, max_seconds=60, constraints=constraints) == 6
    assert clamp_duration(20, max_seconds=60, constraints=constraints) == 8
    assert clamp_duration(2, max_seconds=60, constraints=constraints) == 4
    assert clamp_duration(None, max_seconds=5, constraints=constraints) == 4
    assert clamp_duration(9, max_seconds=60, constraints=None) == 9
    assert clamp_duration(None, max_seconds=12, constraints=None) == 12
    assert clamp_resolution("1080p", constraints) == "1080p"
    assert clamp_resolution("4K", constraints) == "720p"
    assert clamp_resolution("720p", None) == "720p"
    assert clamp_resolution(None, constraints) is None


def test_missing_key_and_model_are_typed(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _config, profile = _profile()
    with pytest.raises(AIProviderUnavailable, match="OPENROUTER_API_KEY"):
        OpenRouterVideoClient("openrouter_video", profile, http=FakeVideoHttp())
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    _config, blank = _profile(model=None)
    with pytest.raises(AIProviderUnavailable, match="model slug"):
        OpenRouterVideoClient("openrouter_video", blank, http=FakeVideoHttp())


def test_factory_requires_an_openrouter_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    config, _profile_ = _profile()
    client = make_video_generation_client(config, tmp_path, provider_name="openrouter_video", http=FakeVideoHttp())
    assert isinstance(client, OpenRouterVideoClient)
    with pytest.raises(AIProviderUnavailable, match="OpenRouter profile"):
        make_video_generation_client(config, tmp_path, provider_name="codex")
    with pytest.raises(AIProviderUnavailable, match="not configured"):
        make_video_generation_client(config, tmp_path, provider_name="ghost")
