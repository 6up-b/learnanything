"""System-authored Review changelog entries (§4.9) and the persisted regrade
marker on the feedback bundle (§2.1).

Covers:
  - out-of-session (deferred) regrades surface as their own `regrade` entries;
  - in-session regrades stay folded into the session diff's `corrections`
    count and are NOT re-listed as top-level entries (no double-listing);
  - an algorithm_version bump collapses to exactly ONE `recalibration` entry,
    regardless of how many learning objects/facets it recomputed;
  - the feedback bundle carries a `regrade` marker after a persisted regrade
    and lacks it otherwise.

All deterministic under FrozenClock.
"""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.codex.client import GradingContext
from learnloop.codex.runtime import CodexRuntimeReport
from learnloop.codex.schemas import CriterionEvidence, ErrorAttribution, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.services.learner_review_feed import build_learner_review_feed
from learnloop.services.regrade import run_deferred_regrades
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers.serializers import feedback_bundle

from tests.helpers import NOW, create_basic_vault


class _RegradeClient:
    def __init__(self, *, score: int, points: float):
        self.score = score
        self.points = points
        self.error_attributions: list[ErrorAttribution] = []

    def run_grading_proposal(self, context: GradingContext) -> GradingProposal:
        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=self.score,
            criterion_evidence=[
                CriterionEvidence(
                    criterion_id="correctness",
                    points_awarded=self.points,
                    evidence="Codex regrade evidence.",
                )
            ],
            error_attributions=[],
            grader_confidence=0.9,
        )


def _ready_runtime() -> CodexRuntimeReport:
    return CodexRuntimeReport(
        status="ready",
        checkout_path="codex",
        configured_revision="abc",
        actual_revision="abc",
    )


def _seeded(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _record(vault, repository, *, at, points, answer="SVD is U Sigma V^T."):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md=answer),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=3),
        clock=FrozenClock(at),
    )


def _regrade(vault, repository, *, at, score, points):
    return run_deferred_regrades(
        vault,
        repository,
        runtime=_ready_runtime(),
        codex_client=_RegradeClient(score=score, points=points),
        clock=FrozenClock(at),
    )


def _changelog(vault, repository) -> list[dict]:
    return build_learner_review_feed(vault, repository)["changelog"]


# ── Task 1: system-authored changelog entries ──────────────────────────────


def test_out_of_session_regrade_surfaces_as_system_entry(tmp_path):
    vault, repository = _seeded(tmp_path)
    _record(vault, repository, at=NOW, points=0)
    # Regrade later than the original grade so it lands in a distinct grading
    # epoch (same-timestamp legacy epochs collapse). No session exists.
    result = _regrade(vault, repository, at=NOW + timedelta(hours=2), score=4, points=4)
    assert result.regraded == 1

    changelog = _changelog(vault, repository)
    regrades = [entry for entry in changelog if entry["kind"] == "regrade"]
    assert len(regrades) == 1
    entry = regrades[0]
    assert entry["direction"] == "up"
    assert entry["old_score"] == 0.0
    assert entry["new_score"] == 4.0
    assert entry["at"] == (NOW + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    # Facet reference for the drawer; belief-change fields are zeroed.
    assert "recall" in entry["facet_ids"]
    assert entry["corrections"] == 0
    assert entry["predictions_moved"] == {"up": 0, "down": 0}
    assert entry["misconceptions_touched"] == {"resolved": 0, "returned": 0}


def test_downgrade_direction_is_annotated(tmp_path):
    vault, repository = _seeded(tmp_path)
    _record(vault, repository, at=NOW, points=4)
    _regrade(vault, repository, at=NOW + timedelta(hours=2), score=1, points=1)

    regrades = [entry for entry in _changelog(vault, repository) if entry["kind"] == "regrade"]
    assert len(regrades) == 1
    assert regrades[0]["direction"] == "down"
    assert regrades[0]["old_score"] == 4.0
    assert regrades[0]["new_score"] == 1.0


def test_in_session_regrade_is_not_double_listed(tmp_path):
    vault, repository = _seeded(tmp_path)
    session_id = repository.create_session(clock=FrozenClock(NOW))
    _record(vault, repository, at=NOW, points=0)
    # Regrade inside the session window (started NOW, ends NOW+1h).
    _regrade(vault, repository, at=NOW + timedelta(minutes=30), score=4, points=4)
    repository.end_session(session_id, clock=FrozenClock(NOW + timedelta(hours=1)))

    changelog = _changelog(vault, repository)
    # The regrade lives inside the session — it is counted once, as the session
    # entry's `corrections`, and never as a separate top-level regrade entry.
    assert [entry["kind"] for entry in changelog] == ["session"]
    session_entry = changelog[0]
    assert session_entry["corrections"] == 1
    assert all(entry["kind"] != "regrade" for entry in changelog)


def test_algorithm_version_bump_yields_exactly_one_recalibration_entry(tmp_path):
    vault, repository = _seeded(tmp_path)
    # Two rebuilds under the same version → no recalibration; a third under a
    # new version → exactly one entry, regardless of the LO/facet fan-out.
    repository.record_derived_state_rebuild(
        scope="full",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version="mvp-0.6",
        rebuilt_learning_objects=1,
        replayed_attempts=3,
        clock=FrozenClock(NOW),
    )
    repository.record_derived_state_rebuild(
        scope="full",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version="mvp-0.6",
        rebuilt_learning_objects=1,
        replayed_attempts=3,
        clock=FrozenClock(NOW + timedelta(hours=1)),
    )
    repository.record_derived_state_rebuild(
        scope="full",
        # Many learning objects recomputed — must still be ONE entry.
        learning_object_ids=[f"lo_{i}" for i in range(20)],
        algorithm_version="mvp-0.7",
        rebuilt_learning_objects=20,
        replayed_attempts=40,
        clock=FrozenClock(NOW + timedelta(hours=2)),
    )

    changelog = _changelog(vault, repository)
    recalibrations = [entry for entry in changelog if entry["kind"] == "recalibration"]
    assert len(recalibrations) == 1
    entry = recalibrations[0]
    assert entry["algorithm_version"] == "mvp-0.7"
    assert entry["previous_algorithm_version"] == "mvp-0.6"
    assert entry["at"] == (NOW + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
    assert entry["facet_ids"] == []


def test_no_recalibration_without_version_change(tmp_path):
    vault, repository = _seeded(tmp_path)
    for offset in (0, 1, 2):
        repository.record_derived_state_rebuild(
            scope="full",
            learning_object_ids=["lo_svd_definition"],
            algorithm_version="mvp-0.7",
            rebuilt_learning_objects=1,
            replayed_attempts=1,
            clock=FrozenClock(NOW + timedelta(hours=offset)),
        )
    assert [entry for entry in _changelog(vault, repository) if entry["kind"] == "recalibration"] == []


def test_entries_are_interleaved_reverse_chronologically(tmp_path):
    vault, repository = _seeded(tmp_path)
    _record(vault, repository, at=NOW, points=0)
    _regrade(vault, repository, at=NOW + timedelta(hours=1), score=4, points=4)
    repository.record_derived_state_rebuild(
        scope="full",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version="mvp-0.6",
        rebuilt_learning_objects=1,
        replayed_attempts=1,
        clock=FrozenClock(NOW - timedelta(hours=1)),
    )
    repository.record_derived_state_rebuild(
        scope="full",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version="mvp-0.7",
        rebuilt_learning_objects=1,
        replayed_attempts=1,
        clock=FrozenClock(NOW + timedelta(hours=3)),
    )

    changelog = _changelog(vault, repository)
    kinds = [entry["kind"] for entry in changelog]
    # recalibration at NOW+3h, then regrade at NOW+1h.
    assert kinds[0] == "recalibration"
    assert "regrade" in kinds
    ats = [entry["at"] for entry in changelog]
    assert ats == sorted(ats, reverse=True)


# ── Task 2: persisted regrade marker on the feedback bundle ────────────────


def test_feedback_bundle_lacks_regrade_marker_without_regrade(tmp_path):
    vault, repository = _seeded(tmp_path)
    attempt = _record(vault, repository, at=NOW, points=3)
    bundle = feedback_bundle(vault, repository, attempt.attempt_id)
    assert bundle["regrade"] is None


def test_feedback_bundle_carries_regrade_marker_after_regrade(tmp_path):
    vault, repository = _seeded(tmp_path)
    attempt = _record(vault, repository, at=NOW, points=0)
    _regrade(vault, repository, at=NOW + timedelta(hours=2), score=4, points=4)

    bundle = feedback_bundle(vault, repository, attempt.attempt_id)
    marker = bundle["regrade"]
    assert marker is not None
    # versioned() camelizes the payload recursively.
    assert marker["oldScore"] == 0.0
    assert marker["newScore"] == 4.0
    assert marker["direction"] == "up"
    assert marker["maxPoints"] == bundle["maxPoints"]
    assert marker["regradedAt"] == (NOW + timedelta(hours=2)).isoformat().replace("+00:00", "Z")
