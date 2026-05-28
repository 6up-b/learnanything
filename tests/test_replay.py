from __future__ import annotations

from dataclasses import asdict

import learnloop.services.attempts as attempt_service
from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    SelfGradeInput,
    apply_attempt,
    complete_self_graded_attempt,
    compute_attempt_application,
    load_attempt_prior_state,
)
from learnloop.services.replay import rebuild_derived_state, replay_learning_object
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, create_basic_vault


def test_learning_object_replay_matches_live_state_and_is_idempotent(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="I do not know.", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=clock,
    )
    live_snapshot = _derived_snapshot(repository, attempt.attempt_id)

    first = replay_learning_object(vault, repository, "lo_svd_definition")
    replay_snapshot = _derived_snapshot(repository, attempt.attempt_id)
    second = replay_learning_object(vault, repository, "lo_svd_definition")
    second_snapshot = _derived_snapshot(repository, attempt.attempt_id)

    assert first.as_dict() == {
        "learning_object_id": "lo_svd_definition",
        "replayed_attempts": 1,
        "attempt_ids": [attempt.attempt_id],
    }
    assert second.as_dict() == first.as_dict()
    assert replay_snapshot == live_snapshot
    assert second_snapshot == replay_snapshot


def test_live_and_replay_drive_shared_apply_attempt_step(tmp_path, monkeypatch):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    calls: list[tuple[str, bool]] = []
    real_apply = attempt_service.apply_attempt

    def spy_apply_attempt(vault, repository, attempt, *, clock=None):
        calls.append((attempt.attempt_id, attempt.replace_existing))
        return real_apply(vault, repository, attempt, clock=clock)

    monkeypatch.setattr(attempt_service, "apply_attempt", spy_apply_attempt)

    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="I do not know.", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=clock,
    )
    replay_learning_object(vault, repository, "lo_svd_definition")

    assert calls == [(attempt.attempt_id, False), (attempt.attempt_id, True)]


def test_compute_attempt_application_materializes_outputs_without_persisting(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    before_mastery = asdict(repository.mastery_state("lo_svd_definition"))

    application = compute_attempt_application(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id="pi_svd_define_001",
                learner_answer_md="I do not know.",
                attempt_type="dont_know",
            ),
            attempt_id="attempt_compute_only",
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0.0},
                evidence_rows=[
                    {
                        "id": "evidence_compute_only",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Self-grade awarded 0/4.",
                        "notes": None,
                        "local_grader_id": "self",
                        "grader_tier": 1,
                        "created_at": "2026-05-25T12:00:00Z",
                    }
                ],
                error_attributions=[GradeAttribution("recall_failure", 0.45)],
                grader_confidence=1.0,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=clock,
    )

    assert application.attempt_record["id"] == "attempt_compute_only"
    assert application.result.attempt_id == "attempt_compute_only"
    assert application.error_events[0]["attempt_id"] == "attempt_compute_only"
    assert application.attempt_debug_payload["effective_coverage"] == 1.0
    assert repository.fetch_practice_attempt("attempt_compute_only") is None
    assert repository.error_events_for_attempt("attempt_compute_only") == []
    assert repository.latest_attempt_surprise("attempt_compute_only") is None
    assert repository.attempt_debug_payload("attempt_compute_only") is None
    assert repository.ability_transition_event("attempt_compute_only") is None
    assert asdict(repository.mastery_state("lo_svd_definition")) == before_mastery


def test_compute_attempt_application_uses_explicit_prior_snapshot(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)
    prior = load_attempt_prior_state(
        vault,
        repository,
        learning_object_id="lo_svd_definition",
        practice_item_id="pi_svd_define_001",
        facets=["recall"],
        now_iso="2026-05-25T12:00:00Z",
    )
    repository.upsert_mastery_state(
        MasteryState(
            "lo_svd_definition",
            5.0,
            0.25,
            100,
            "2026-05-25T12:00:00Z",
            vault.config.algorithms.algorithm_version,
            "2026-05-25T12:00:00Z",
        )
    )

    attempt = ApplyAttemptInput(
        draft=AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="I do not know.",
            attempt_type="dont_know",
        ),
        attempt_id="attempt_snapshot_compute",
        grade=ResolvedGrade(
            rubric_score=0,
            criterion_points={"correctness": 0.0},
            evidence_rows=[],
            error_attributions=[GradeAttribution("recall_failure", 0.45)],
            grader_confidence=1.0,
            confidence=5,
            manual_review_reason=None,
        ),
    )

    from_snapshot = compute_attempt_application(vault, repository, attempt, clock=clock, prior_state=prior)
    from_repository = compute_attempt_application(
        vault,
        repository,
        ApplyAttemptInput(
            draft=attempt.draft,
            attempt_id="attempt_repository_compute",
            grade=attempt.grade,
        ),
        clock=clock,
    )

    snapshot_irt = from_snapshot.attempt_debug_payload["prediction_trace"]["irt_predicted_correctness"]
    repository_irt = from_repository.attempt_debug_payload["prediction_trace"]["irt_predicted_correctness"]
    assert snapshot_irt < 0.75
    assert repository_irt > 0.95
    assert repository.fetch_practice_attempt("attempt_snapshot_compute") is None


def test_replay_preserves_targeted_error_attribution_facets(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    item = read_yaml(item_path)
    item["evidence_facets"] = ["concept", "numeric"]
    item["evidence_weights"] = {"concept": 0.5, "numeric": 0.5}
    item["criterion_facet_weights"] = {"correctness": {"concept": 1.0}}
    write_yaml(item_path, item)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    attempt = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft("pi_svd_define_001", "Correct concept, arithmetic slip."),
            attempt_id="attempt_targeted_numeric_replay",
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4.0},
                evidence_rows=[
                    {
                        "id": "evidence_targeted_numeric_replay",
                        "criterion_id": "correctness",
                        "points_awarded": 4.0,
                        "evidence": "Correct concept; numeric issue captured in attribution.",
                        "notes": None,
                        "local_grader_id": "self",
                        "grader_tier": 1,
                        "created_at": "2026-05-19T12:00:00Z",
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        "conceptual_slip",
                        0.6,
                        evidence="Arithmetic slip in otherwise correct concept.",
                        target_evidence_families=["numeric"],
                    )
                ],
                grader_confidence=1.0,
                confidence=5,
                manual_review_reason=None,
            ),
        ),
        clock=clock,
    )
    live_snapshot = _targeted_replay_snapshot(repository, attempt.attempt_id)

    replay_learning_object(vault, repository, "lo_svd_definition")
    replay_snapshot = _targeted_replay_snapshot(repository, attempt.attempt_id)

    assert live_snapshot["debug"]["facet_outcomes"] == {"concept": 1.0, "numeric": 0.0}
    assert live_snapshot["error_events"][0]["repair_plan"]["target_evidence_families"] == ["numeric"]
    assert replay_snapshot == live_snapshot


def test_rebuild_derived_state_replays_attempt_logs(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    clock = FrozenClock(NOW)
    sync_vault_state(vault, repository, clock=clock)

    attempt = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="I do not know.", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4),
        clock=clock,
    )
    live_snapshot = _derived_snapshot(repository, attempt.attempt_id)

    result = rebuild_derived_state(vault, repository)
    rebuilt_snapshot = _derived_snapshot(repository, attempt.attempt_id)

    assert result.marker_id is not None
    payload = result.as_dict()
    assert payload.pop("marker_id") == result.marker_id
    assert payload == {
        "algorithm_version": vault.config.algorithms.algorithm_version,
        "rebuilt_learning_objects": 1,
        "replayed_attempts": 1,
        "learning_object_ids": ["lo_svd_definition"],
    }
    marker = repository.latest_derived_state_rebuild()
    assert marker is not None
    assert marker["id"] == result.marker_id
    assert marker["scope"] == "all"
    assert marker["algorithm_version"] == vault.config.algorithms.algorithm_version
    assert marker["learning_object_ids"] == ["lo_svd_definition"]
    assert marker["rebuilt_learning_objects"] == 1
    assert marker["replayed_attempts"] == 1
    assert rebuilt_snapshot == live_snapshot


def _derived_snapshot(repository: Repository, attempt_id: str) -> dict:
    mastery = repository.mastery_state("lo_svd_definition")
    aggregate = repository.facet_recall_state("lo_svd_definition", "recall")
    item_local = repository.facet_recall_state("lo_svd_definition", "recall", "pi_svd_define_001")
    quality = repository.practice_item_quality_state("pi_svd_define_001")
    surprise = repository.latest_attempt_surprise(attempt_id)
    return {
        "attempt": _attempt_fields(repository.fetch_practice_attempt(attempt_id)),
        "mastery": asdict(mastery) if mastery is not None else None,
        "aggregate_facet": _facet_fields(aggregate),
        "item_facet": _facet_fields(item_local),
        "quality": asdict(quality) if quality is not None else None,
        "error_events": repository.error_events_for_attempt(attempt_id),
        "ability_transition": repository.ability_transition_event(attempt_id),
        "surprise": surprise,
        "debug": repository.attempt_debug_payload(attempt_id),
    }


def _targeted_replay_snapshot(repository: Repository, attempt_id: str) -> dict:
    return {
        "error_events": repository.error_events_for_attempt(attempt_id),
        "concept_facet": _facet_fields(repository.facet_recall_state("lo_svd_definition", "concept", "pi_svd_define_001")),
        "numeric_facet": _facet_fields(repository.facet_recall_state("lo_svd_definition", "numeric", "pi_svd_define_001")),
        "debug": repository.attempt_debug_payload(attempt_id),
    }


def _attempt_fields(attempt: dict | None) -> dict | None:
    if attempt is None:
        return None
    return {
        key: attempt[key]
        for key in (
            "id",
            "rubric_score",
            "correctness",
            "error_type",
            "grader_confidence",
            "manual_review",
            "manual_review_reason",
            "updated_at",
        )
    }


def _facet_fields(state) -> dict | None:
    if state is None:
        return None
    payload = asdict(state)
    payload.pop("id", None)
    return payload
