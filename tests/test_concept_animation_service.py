from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.codex.schemas import ManimAnimation
from learnloop.db.repositories import Repository
from learnloop.services.concept_animation import (
    ConceptAnimationError,
    RenderResult,
    generate_concept_animation,
    request_concept_animation,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import create_basic_vault

VALID_SCENE = """\
from manim import Scene, Circle, Create


class ExplainSVD(Scene):
    def construct(self):
        self.play(Create(Circle()))
"""

BAD_SCENE = "import os\nfrom manim import Scene\nclass S(Scene):\n    pass\n"


class _FakeAnimationClient:
    provider_name = "openrouter"
    model = "anthropic/claude-sonnet-4.5"

    def __init__(self, *animations: ManimAnimation):
        self._animations = list(animations)
        self.contexts: list = []

    def run_concept_animation(self, context) -> ManimAnimation:
        self.contexts.append(context)
        return self._animations.pop(0)


def _ok_renderer(scene_code, scene_class, **kwargs) -> RenderResult:
    return RenderResult(ok=True, video_bytes=b"mp4-bytes", stderr_tail="", returncode=0)


def _vault(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
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
    # Context carried concept material.
    assert client.contexts[0].concept_title == "Singular Value Decomposition"

    # Idempotent re-entry: terminal rows return unchanged, no new model call.
    again = generate_concept_animation(
        vault.root, _FakeAnimationClient(), animation_id=requested["animation_id"],
        repository=repository, renderer=_ok_renderer,
    )
    assert again["status"] == "completed"


def test_generate_provider_without_method_fails_typed(tmp_path):
    vault, repository = _vault(tmp_path)
    requested = request_concept_animation(
        vault, repository, concept_id="singular_value_decomposition", consent=True
    )

    class _NoAnimationClient:
        provider_name = "deepseek_flash"
        model = "deepseek-v4-flash"

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

    class _ExplodingClient:
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
    from learnloop.services.ingest_runner import IngestRunner, JobSpec, RunnerServices

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
