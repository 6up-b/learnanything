from __future__ import annotations

from tests.structured_ai import StructuredClientFake

from pathlib import Path

import pytest

from learnloop.content.authoring.ai_contracts import ManimAnimation
from learnloop.db.repositories import Repository
from learnloop.content.authoring.concept_animation import (
    ConceptAnimationError,
    RenderResult,
    generate_concept_animation,
    request_concept_animation,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import create_basic_vault
from tests.media_fakes import tiny_mp4

VALID_SCENE = """\
from manim import Scene, Circle, Create


class ExplainSVD(Scene):
    def construct(self):
        self.play(Create(Circle()))
"""

BAD_SCENE = "import os\nfrom manim import Scene\nclass S(Scene):\n    pass\n"


class _FakeAnimationClient(StructuredClientFake):
    provider_name = "openrouter"
    model = "anthropic/claude-sonnet-4.5"

    def __init__(self, *animations: ManimAnimation):
        self._animations = list(animations)
        self.contexts: list = []

    def run_concept_animation(self, context) -> ManimAnimation:
        self.contexts.append(context)
        return self._animations.pop(0)


class _FakeVideoClient:
    """Scripted OpenRouterVideoClient: records requests, serves clips, can fail a shot."""

    provider_name = "openrouter_video"
    model = "google/veo-3.1"

    def __init__(self, *, clips=None, fail_shot: int | None = None, submit_fail_at: int | None = None,
                 cancel_on_checkpoint: bool = False, constraints=None):
        from learnloop.ai.providers.openrouter_video import VideoModelConstraints

        self.clips = clips
        self.fail_shot = fail_shot
        self.submit_fail_at = submit_fail_at
        self.cancel_on_checkpoint = cancel_on_checkpoint
        self.constraints = constraints if constraints is not None else VideoModelConstraints((4, 6, 8), ("720p",), ("16:9",))
        self.requests = []
        self.checkpoints = []
        self.downloaded = []

    def supports(self, capability):
        return capability == "video_generation"

    def model_constraints(self):
        return self.constraints

    def submit(self, request):
        from learnloop.ai.errors import VideoGenerationFailed
        from learnloop.ai.providers.openrouter_video import VideoJob

        if self.submit_fail_at is not None and len(self.requests) + 1 == self.submit_fail_at:
            raise VideoGenerationFailed("OpenRouter video submit failed (HTTP 402): insufficient credits", status="rejected")
        self.requests.append(request)
        return VideoJob(id=f"vid_{len(self.requests)}", status="pending", polling_url=None)

    def wait_all(self, job_ids, *, max_wait_seconds, checkpoint=None):
        from learnloop.ai.errors import VideoGenerationFailed
        from learnloop.ai.providers.openrouter_video import VideoJobStatus

        statuses = [VideoJobStatus(id=job_id, status="in_progress", error=None, cost=None, url_count=0) for job_id in job_ids]
        if checkpoint is not None:
            self.checkpoints.append(list(job_ids))
            checkpoint(statuses, 15.0)
        if self.fail_shot is not None:
            raise VideoGenerationFailed(
                f"shot {self.fail_shot + 1}/{len(job_ids)} failed: content policy",
                status="failed", job_id=job_ids[self.fail_shot], shot_index=self.fail_shot,
            )
        return [VideoJobStatus(id=job_id, status="completed", error=None, cost=0.25, url_count=1) for job_id in job_ids]

    def download(self, job_id, index=0):
        self.downloaded.append(job_id)
        if self.clips is not None:
            return self.clips[int(job_id.split("_")[-1]) - 1]
        return b"mp4-" + job_id.encode()


def _storyboard(shots=3, seconds=6):
    from learnloop.content.authoring.ai_contracts import VideoShot, VideoStoryboard

    return VideoStoryboard(
        title="SVD as stretching",
        narration_md="**Grid.** A grid of dots.",
        shots=[
            VideoShot(
                prompt=f"Shot {index}: a flat grid of glowing blue dots stretches along one axis, then rotates slowly; clean educational animation, dark background.",
                duration_seconds=seconds,
                caption=f"Beat {index}",
            )
            for index in range(1, shots + 1)
        ],
    )


class _FakeStoryboardClient(StructuredClientFake):
    provider_name = "openrouter"
    model = "anthropic/claude-sonnet-4.5"

    def __init__(self, *storyboards):
        self._storyboards = list(storyboards)
        self.contexts: list = []

    def run_video_storyboard(self, context):
        self.contexts.append(context)
        return self._storyboards.pop(0)


def _video_vault(tmp_path, monkeypatch):
    from learnloop.ops.settings_store import apply_config_updates

    vault, repository = _vault(tmp_path)
    apply_config_updates(
        vault.root / "learnloop.toml",
        {
            ("animation", "renderer"): "video_model",
            ("ai", "routing", "video_generation"): "openrouter_video",
            ("ai", "providers", "openrouter_video", "type"): "openrouter",
            ("ai", "providers", "openrouter_video", "model"): "google/veo-3.1",
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-secret")
    vault = load_vault(vault.root)
    return vault, repository


def _ok_renderer(scene_code, scene_class, **kwargs) -> RenderResult:
    return RenderResult(ok=True, video_bytes=b"mp4-bytes", stderr_tail="", returncode=0)


def _vault(tmp_path, *, min_duration_seconds: int = 0):
    from learnloop.ops.settings_store import apply_config_updates

    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    # The fakes below author one-line scenes; the pacing lint would otherwise
    # spend a repair round-trip on every test. Tests that exercise pacing opt in.
    apply_config_updates(
        vault_root / "learnloop.toml", {("animation", "min_duration_seconds"): min_duration_seconds}
    )
    vault = load_vault(vault_root)
    repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return vault, repository


def _animation(code=VALID_SCENE, scene_class="ExplainSVD") -> ManimAnimation:
    return ManimAnimation(
        scene_code=code, scene_class=scene_class, title="SVD, visually", narration_md="Watch the circle."
    )


def test_request_requires_consent_enabled_and_known_concept(tmp_path):
    vault, repository = _vault(tmp_path)

    with pytest.raises(ConceptAnimationError) as no_consent:
        request_concept_animation(vault, repository, concept_id="singular_value_decomposition")
    assert no_consent.value.code == "consent_required"

    with pytest.raises(ConceptAnimationError) as missing:
        request_concept_animation(vault, repository, concept_id="nope", consent=True)
    assert missing.value.code == "concept_not_found"

    vault.config.animation.enabled = False
    with pytest.raises(ConceptAnimationError) as disabled:
        request_concept_animation(
            vault, repository, concept_id="singular_value_decomposition", consent=True
        )
    assert disabled.value.code == "animation_disabled"


def test_request_pending_lock_and_dead_batch_reconciliation(tmp_path):
    vault, repository = _vault(tmp_path)

    first = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    # The queued row has no batch yet -> the batch is "dead" and reconciled,
    # freeing the lock for a fresh request (crash-recovery semantics).
    second = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    reconciled = repository.concept_animation(first["animation_id"])
    assert reconciled["status"] == "failed"
    assert second["animation_id"] != first["animation_id"]


def test_generate_happy_path_stores_content_addressed_mp4(tmp_path):
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    client = _FakeAnimationClient(_animation())

    row = generate_concept_animation(
        vault.root, client, animation_id=requested["animation_id"], repository=repository,
        renderer=_ok_renderer,
    )

    assert row["status"] == "completed"
    assert row["provider"] == "openrouter"
    assert row["model"] == "anthropic/claude-sonnet-4.5"
    assert row["title"] == "SVD, visually"
    assert row["video_file_name"].startswith("sha256-") and row["video_file_name"].endswith(".mp4")
    video = vault.root / "media" / "animations" / row["video_file_name"]
    assert video.read_bytes() == b"mp4-bytes"
    # Placeholder bytes are not a real container: the probe stays quiet.
    assert row["duration_seconds"] is None
    # Context carried concept material.
    assert client.contexts[0].concept_title == "Singular Value Decomposition"

    # Idempotent re-entry: terminal rows return unchanged, no new model call.
    again = generate_concept_animation(
        vault.root, _FakeAnimationClient(), animation_id=requested["animation_id"],
        repository=repository, renderer=_ok_renderer,
    )
    assert again["status"] == "completed"


def test_generate_records_duration_of_a_real_clip(tmp_path):
    clip = tiny_mp4(frames=12, fps=15)
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )

    def real_clip_renderer(scene_code, scene_class, **kwargs) -> RenderResult:
        return RenderResult(ok=True, video_bytes=clip, stderr_tail="", returncode=0)

    row = generate_concept_animation(
        vault.root, _FakeAnimationClient(_animation()), animation_id=requested["animation_id"],
        repository=repository, renderer=real_clip_renderer,
    )

    assert row["status"] == "completed"
    assert row["duration_seconds"] == pytest.approx(0.8, abs=0.05)


def test_generate_stores_faststart_remuxed_bytes_and_hashes_them(tmp_path):
    import hashlib

    from learnloop.content.authoring.animation_media import is_faststart

    clip = tiny_mp4()
    assert is_faststart(clip) is False
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )

    def real_clip_renderer(scene_code, scene_class, **kwargs) -> RenderResult:
        return RenderResult(ok=True, video_bytes=clip, stderr_tail="", returncode=0)

    row = generate_concept_animation(
        vault.root, _FakeAnimationClient(_animation()), animation_id=requested["animation_id"],
        repository=repository, renderer=real_clip_renderer,
    )

    stored = (vault.root / "media" / "animations" / row["video_file_name"]).read_bytes()
    assert is_faststart(stored) is True
    assert row["video_hash"] == "sha256:" + hashlib.sha256(stored).hexdigest()
    assert row["video_file_name"] == "sha256-" + hashlib.sha256(stored).hexdigest() + ".mp4"


def test_generate_short_scene_gets_one_pacing_repair_then_renders(tmp_path):
    vault, repository = _vault(tmp_path, min_duration_seconds=30)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    client = _FakeAnimationClient(_animation(), _animation())

    row = generate_concept_animation(
        vault.root, client, animation_id=requested["animation_id"], repository=repository,
        renderer=_ok_renderer,
    )

    # One pacing round-trip, then the (still short) scene renders: soft gate.
    assert len(client.contexts) == 2
    assert "running time" in client.contexts[1].repair["violations"][0]
    assert client.contexts[1].repair["previous_code"] == VALID_SCENE
    assert client.contexts[0].min_duration_seconds == 30
    assert client.contexts[0].resolution == "1280x720" and client.contexts[0].fps == 30
    assert row["status"] == "completed"


def test_generate_provider_without_method_fails_typed(tmp_path):
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )

    class _NoAnimationClient:
        provider_name = "deepseek_flash"
        model = "deepseek-v4-flash"

        def supports(self, _capability):
            return False

    row = generate_concept_animation(
        vault.root, _NoAnimationClient(), animation_id=requested["animation_id"],
        repository=repository, renderer=_ok_renderer,
    )

    assert row["status"] == "failed"
    assert row["failure_stage"] == "generation"
    assert "does not support animation authoring" in row["failure_reason"]


def test_generate_validator_violation_gets_one_repair_then_fails(tmp_path):
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    client = _FakeAnimationClient(_animation(code=BAD_SCENE, scene_class="S"), _animation(code=BAD_SCENE, scene_class="S"))

    row = generate_concept_animation(
        vault.root, client, animation_id=requested["animation_id"], repository=repository,
        renderer=_ok_renderer,
    )

    assert row["status"] == "failed"
    assert row["failure_stage"] == "validation"
    assert "import of 'os'" in row["failure_reason"]
    # The corrective round-trip carried the violations back to the model.
    assert client.contexts[1].repair is not None
    assert "violations" in client.contexts[1].repair
    # The failing code is retained for debugging.
    assert row["scene_code"] == BAD_SCENE


def test_generate_render_failure_gets_stderr_repair_then_fails(tmp_path):
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    client = _FakeAnimationClient(_animation(), _animation())

    def failing_renderer(scene_code, scene_class, **kwargs) -> RenderResult:
        return RenderResult(ok=False, video_bytes=None, stderr_tail="LaTeX error: tex not found", returncode=1)

    row = generate_concept_animation(
        vault.root, client, animation_id=requested["animation_id"], repository=repository,
        renderer=failing_renderer,
    )

    assert row["status"] == "failed"
    assert row["failure_stage"] == "render"
    assert row["repair_attempted"] == 1
    assert "tex not found" in row["render_stderr"]
    assert client.contexts[1].repair["render_stderr"].startswith("LaTeX error")


def test_generate_render_repair_recovers(tmp_path):
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    client = _FakeAnimationClient(_animation(), _animation())
    calls = {"n": 0}

    def flaky_renderer(scene_code, scene_class, **kwargs) -> RenderResult:
        calls["n"] += 1
        if calls["n"] == 1:
            return RenderResult(ok=False, video_bytes=None, stderr_tail="transient", returncode=1)
        return RenderResult(ok=True, video_bytes=b"fixed-mp4", stderr_tail="", returncode=0)

    row = generate_concept_animation(
        vault.root, client, animation_id=requested["animation_id"], repository=repository,
        renderer=flaky_renderer,
    )

    assert row["status"] == "completed"
    assert row["repair_attempted"] == 1


def test_generate_unexpected_exception_never_wedges_the_row(tmp_path):
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )

    class _ExplodingClient(StructuredClientFake):
        provider_name = "openrouter"
        model = "x"

        def run_concept_animation(self, context):
            raise RuntimeError("provider exploded")

    with pytest.raises(RuntimeError):
        generate_concept_animation(
            vault.root, _ExplodingClient(), animation_id=requested["animation_id"],
            repository=repository, renderer=_ok_renderer,
        )

    row = repository.concept_animation(requested["animation_id"])
    assert row["status"] == "failed"
    assert "provider exploded" in row["failure_reason"]


def test_runner_handler_drives_generation_through_the_queue(tmp_path):
    from learnloop.clock import FrozenClock
    from datetime import UTC, datetime
    from learnloop.content.pipeline.runner import IngestRunner, JobSpec, RunnerServices

    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )
    client = _FakeAnimationClient(_animation())
    runner = IngestRunner(
        repository,
        vault_root=vault.root,
        worker_id="w1",
        clock=FrozenClock(datetime(2026, 7, 22, 12, 0, 0, tzinfo=UTC)),
        services=RunnerServices(
            animation_client_factory=lambda ctx: client,
            animation_renderer=_ok_renderer,
        ),
    )

    batch_id = runner.enqueue_batch(
        "concept_animation", [JobSpec("concept_animation", {"animation_id": requested["animation_id"]})]
    )
    runner.drain()

    job = runner.repo.ingest_jobs_for_batch(batch_id)[0]
    assert job["status"] == "completed"
    assert job["result"]["status"] == "completed"
    assert job["result"]["videoFileName" if "videoFileName" in job["result"] else "video_file_name"]
    row = repository.concept_animation(requested["animation_id"])
    assert row["status"] == "completed"


# ---------------------------------------------------------------------------
# Video-model renderer (storyboard -> OpenRouter jobs -> stitched clip)
# ---------------------------------------------------------------------------


def test_request_video_model_requires_a_ready_route(tmp_path, monkeypatch):
    from learnloop.ops.settings_store import apply_config_updates

    vault, repository = _vault(tmp_path)
    apply_config_updates(vault.root / "learnloop.toml", {("animation", "renderer"): "video_model"})
    vault = load_vault(vault.root)

    with pytest.raises(ConceptAnimationError) as excinfo:
        request_concept_animation(vault, repository, concept_id="singular_value_decomposition", consent=True)
    assert excinfo.value.code == "video_model_unconfigured"
    assert "no video model chosen" in str(excinfo.value)

    vault, repository = _video_vault(tmp_path, monkeypatch)
    monkeypatch.delenv("OPENROUTER_API_KEY")
    with pytest.raises(ConceptAnimationError) as excinfo:
        request_concept_animation(vault, repository, concept_id="singular_value_decomposition", consent=True)
    assert excinfo.value.code == "video_model_unconfigured"
    assert "OPENROUTER_API_KEY" in str(excinfo.value)


def test_generate_video_model_path_stores_stitched_clip_and_provenance(tmp_path, monkeypatch):
    import json

    from learnloop.content.authoring.animation_media import is_faststart

    vault, repository = _video_vault(tmp_path, monkeypatch)
    requested = request_concept_animation(vault, repository, concept_id="singular_value_decomposition", consent=True)
    assert repository.concept_animation(requested["animation_id"])["renderer"] == "video_model"
    clips = [tiny_mp4(frames=6, fps=15) for _ in range(3)]
    video = _FakeVideoClient(clips=clips)
    client = _FakeStoryboardClient(_storyboard(shots=3, seconds=7))
    phases: list[tuple[str, str]] = []

    row = generate_concept_animation(
        vault.root, client, animation_id=requested["animation_id"], repository=repository,
        renderer=_ok_renderer, video_client=video, report=lambda phase, message: phases.append((phase, message)),
    )

    assert row["status"] == "completed"
    assert row["renderer"] == "video_model"
    assert row["provider"] == "openrouter_video" and row["model"] == "google/veo-3.1"
    assert row["title"] == "SVD as stretching"
    assert json.loads(row["video_job_ids"]) == ["vid_1", "vid_2", "vid_3"]
    plan = json.loads(row["storyboard_json"])
    assert [shot["caption"] for shot in plan["shots"]] == ["Beat 1", "Beat 2", "Beat 3"]
    # 7 s requested -> clamped to the largest supported duration under it.
    assert [request.duration_seconds for request in video.requests] == [6, 6, 6]
    assert all(request.resolution == "720p" for request in video.requests)
    assert plan["total_cost"] == pytest.approx(0.75)
    assert video.downloaded == ["vid_1", "vid_2", "vid_3"]
    stored = (vault.root / "media" / "animations" / row["video_file_name"]).read_bytes()
    assert is_faststart(stored) is True
    assert row["duration_seconds"] == pytest.approx(1.2, abs=0.15)
    # Progress reached the job lease per polling round.
    assert any("shots 0/3 complete" in message for _phase, message in phases)
    assert client.contexts[0].shot_durations == [4, 6, 8]
    assert client.contexts[0].video_model == "google/veo-3.1"


def test_generate_video_model_storyboard_gets_one_repair_then_fails_typed(tmp_path, monkeypatch):
    vault, repository = _video_vault(tmp_path, monkeypatch)
    requested = request_concept_animation(vault, repository, concept_id="singular_value_decomposition", consent=True)
    video = _FakeVideoClient()
    client = _FakeStoryboardClient(_storyboard(shots=1), _storyboard(shots=9))

    row = generate_concept_animation(
        vault.root, client, animation_id=requested["animation_id"], repository=repository,
        renderer=_ok_renderer, video_client=video,
    )

    assert row["status"] == "failed"
    assert row["failure_stage"] == "validation"
    assert "between 2 and 4" in row["failure_reason"]
    assert client.contexts[1].repair["violations"]
    assert video.requests == []  # nothing was billed


def test_generate_video_model_shot_failure_and_submit_rejection_are_typed(tmp_path, monkeypatch):
    import json

    vault, repository = _video_vault(tmp_path, monkeypatch)
    requested = request_concept_animation(vault, repository, concept_id="singular_value_decomposition", consent=True)
    video = _FakeVideoClient(fail_shot=1)
    row = generate_concept_animation(
        vault.root, _FakeStoryboardClient(_storyboard()), animation_id=requested["animation_id"],
        repository=repository, renderer=_ok_renderer, video_client=video,
    )
    assert row["status"] == "failed" and row["failure_stage"] == "video_model"
    assert "shot 2/3 failed" in row["failure_reason"]
    assert json.loads(row["video_job_ids"]) == ["vid_1", "vid_2", "vid_3"]

    requested = request_concept_animation(vault, repository, concept_id="singular_value_decomposition", consent=True)
    video = _FakeVideoClient(submit_fail_at=2)
    row = generate_concept_animation(
        vault.root, _FakeStoryboardClient(_storyboard()), animation_id=requested["animation_id"],
        repository=repository, renderer=_ok_renderer, video_client=video,
    )
    assert row["status"] == "failed" and row["failure_stage"] == "video_model"
    assert "insufficient credits" in row["failure_reason"]
    # Submission stopped at the rejection: only the first job was billed.
    assert json.loads(row["video_job_ids"]) == ["vid_1"]


def test_generate_video_model_without_client_fails_typed(tmp_path, monkeypatch):
    vault, repository = _video_vault(tmp_path, monkeypatch)
    requested = request_concept_animation(vault, repository, concept_id="singular_value_decomposition", consent=True)

    row = generate_concept_animation(
        vault.root, _FakeStoryboardClient(_storyboard()), animation_id=requested["animation_id"],
        repository=repository, renderer=_ok_renderer, video_client=None,
    )

    assert row["status"] == "failed"
    assert row["failure_stage"] == "video_model"
    assert "no video-generation provider" in row["failure_reason"]
