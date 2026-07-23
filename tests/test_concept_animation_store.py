from __future__ import annotations

from pathlib import Path

from learnloop.db.repositories import Repository
from learnloop.vault.paths import animation_video_path


def _repo(tmp_path: Path) -> Repository:
    return Repository(tmp_path / "state.sqlite")


def test_concept_animation_row_round_trip(tmp_path):
    repo = _repo(tmp_path)

    animation_id = repo.insert_concept_animation(
        {
            "concept_id": "singular_value_decomposition",
            "prompt_version": "mvp-0.1-concept-animation",
            "quality": "ql",
        }
    )

    row = repo.concept_animation(animation_id)
    assert row is not None
    assert row["status"] == "queued"
    assert row["concept_id"] == "singular_value_decomposition"
    assert row["repair_attempted"] == 0

    assert repo.update_concept_animation(
        animation_id,
        status="completed",
        scene_code="class S(Scene): ...",
        video_hash="sha256:abc123",
        video_file_name="sha256-abc123.mp4",
        completed_at="2026-07-22T00:00:00Z",
    )
    row = repo.concept_animation(animation_id)
    assert row["status"] == "completed"
    assert row["video_file_name"] == "sha256-abc123.mp4"
    # Unknown fields are ignored, not written.
    assert repo.update_concept_animation(animation_id, nonsense="x") is False


def test_pending_lock_and_batch_death(tmp_path):
    repo = _repo(tmp_path)
    first = repo.insert_concept_animation({"concept_id": "c1"})
    repo.insert_concept_animation({"concept_id": "c1", "status": "failed"})
    repo.insert_concept_animation({"concept_id": "c2"})

    pending = repo.pending_concept_animations("c1")
    assert [row["id"] for row in pending] == [first]

    # No batch id -> dead; unknown batch -> dead (reconciliation frees the lock).
    assert repo.concept_animation_batch_dead(None) is True
    assert repo.concept_animation_batch_dead("batch_missing") is True


def test_animations_listing_orders_newest_first(tmp_path):
    repo = _repo(tmp_path)
    from learnloop.clock import FrozenClock
    from datetime import UTC, datetime, timedelta

    base = datetime(2026, 7, 22, 12, 0, 0, tzinfo=UTC)
    old = repo.insert_concept_animation({"concept_id": "c1"}, clock=FrozenClock(base))
    new = repo.insert_concept_animation(
        {"concept_id": "c1"}, clock=FrozenClock(base + timedelta(minutes=5))
    )

    rows = repo.concept_animations_for_concept("c1")
    assert [row["id"] for row in rows] == [new, old]


def test_animation_video_path_is_content_addressed(tmp_path):
    path = animation_video_path(tmp_path, "sha256:deadbeef")
    assert path == tmp_path / "media" / "animations" / "sha256-deadbeef.mp4"
