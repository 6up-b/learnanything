"""Pilot audit, regrade agreement, and shadow report (spec §13, Checkpoint 4/5)."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.probe_audit import (
    calibration_evidence_report,
    eig_calibration_report,
    grading_confusion_report,
    pilot_report,
    record_probe_regrade_check,
    replay_determinism_report,
    shadow_policy_report,
    time_calibration_report,
)
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    serve_presentation,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item
from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
ITEM_2 = "pi_svd_define_002"
CLOCK = FrozenClock(NOW)


def _add_item(vault_root, item_id: str, *, surface_family: str | None = None) -> None:
    upsert_practice_item(
        vault_root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt", "diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Fresh-surface prompt for {item_id}.",
            "expected_answer": "A matrix factorization into U, Sigma, and V transpose.",
            "surface_family": surface_family,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [{"id": "correctness", "points": 4, "description": "Correct definition."}],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with a different decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _setup(tmp_path, *, extra_item: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    if extra_item:
        _add_item(vault_root, ITEM_2, surface_family="fresh_surface")
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    items = (ITEM_ID, ITEM_2) if extra_item else (ITEM_ID,)
    admit_probe_instrument_card(repository, items=items)
    return loaded, repository


def _grade(score: int, *, error_attributions=None) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=score,
        criterion_points={"correctness": float(score)},
        evidence_rows=[],
        error_attributions=error_attributions or [],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _submit(loaded, repository, *, item_id, presentation_id, score=4, error_attributions=None):
    return apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="answer",
                attempt_type="diagnostic_probe",
                hints_used=0,
                probe_presentation_id=presentation_id,
            ),
            attempt_id=new_ulid(),
            grade=_grade(score, error_attributions=error_attributions),
            grading_source="ai",
        ),
        clock=CLOCK,
    )


def _commit(loaded, repository, episode, *, item_id):
    hypothesis_set = episode_hypothesis_set(repository, episode)
    candidates = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    eligible = next(entry for entry in candidates if entry.item.id == item_id)
    presentation = commit_presentation(
        loaded, repository, episode, eligible, candidates=candidates, clock=CLOCK
    )
    serve_presentation(repository, presentation.id, clock=CLOCK)
    return presentation


def _drive_two_observations(loaded, repository):
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    first = _commit(loaded, repository, episode, item_id=ITEM_ID)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=first.id, score=4)
    episode = repository.probe_episode(episode.id)
    if episode.status != "in_progress":
        return episode
    second = _commit(loaded, repository, episode, item_id=ITEM_2)
    _submit(
        loaded,
        repository,
        item_id=ITEM_2,
        presentation_id=second.id,
        score=1,
        error_attributions=[
            GradeAttribution(error_type="conceptual_slip", severity=0.8, evidence="confused")
        ],
    )
    return repository.probe_episode(episode.id)


# --- EIG calibration and negative realized information (Checkpoint 4.3) --------------


def test_eig_report_matches_stored_observations(tmp_path):
    loaded, repository = _setup(tmp_path)
    _drive_two_observations(loaded, repository)

    report = eig_calibration_report(repository)
    assert report["observations"] >= 1
    assert report["mean_expected_eig"] is not None
    assert report["mean_realized_information"] is not None
    # Signed accounting: the negative-information count equals the number of
    # stored rows whose realized gain is negative — never clamped away.
    episodes = repository.list_probe_episodes()
    rows = [
        row["observation"]
        for episode in episodes
        for row in repository.probe_observations_for_episode(episode.id)
        if row["observation"].eligible_for_completion
    ]
    negative = sum(1 for row in rows if row.realized_information_gain < 0)
    assert report["negative_information_count"] == negative
    for row in rows:
        assert row.realized_information_gain == pytest.approx(
            row.entropy_before - row.entropy_after
        )


def test_time_calibration_uses_served_to_submitted(tmp_path):
    loaded, repository = _setup(tmp_path)
    _drive_two_observations(loaded, repository)

    report = time_calibration_report(repository)
    assert report["observations"] >= 1
    # FrozenClock: served and submitted coincide, so the actual is 0s and the
    # error is minus the instrument's expected seconds (45 for the builtin).
    key = next(iter(report["by_family"]))
    assert report["by_family"][key]["mean_actual_seconds"] == 0.0
    assert report["by_family"][key]["mean_error_seconds"] == pytest.approx(-45.0)


def test_replay_determinism_holds_on_pilot_vault(tmp_path):
    loaded, repository = _setup(tmp_path)
    _drive_two_observations(loaded, repository)

    report = replay_determinism_report(loaded, repository)
    assert report["episodes_checked"] >= 1
    assert report["deterministic"], report["failures"]


def test_evidence_sources_stay_separate(tmp_path):
    loaded, repository = _setup(tmp_path)
    _drive_two_observations(loaded, repository)

    report = calibration_evidence_report(repository)
    families = report["families"]
    assert families
    for entry in families.values():
        # real_learner rows exist from the driven observations; any synthetic
        # rows are listed under their own key, never merged.
        assert set(entry["sources"]) <= {"synthetic_gate", "real_learner", "reviewed_human"}
    real = [e for e in families.values() if "real_learner" in e["sources"]]
    assert real


# --- Regrade agreement and grading confusion (Checkpoint 4.4) -------------------------


def test_regrade_checks_record_agreement_and_confusion(tmp_path):
    loaded, repository = _setup(tmp_path)
    _drive_two_observations(loaded, repository)
    episodes = repository.list_probe_episodes()
    rows = [
        row
        for episode in episodes
        for row in repository.probe_observations_for_episode(episode.id)
    ]
    assert len(rows) >= 2

    # Same grade → agreement; contradictory regrade → disagreement cell.
    first, second = rows[0], rows[1]
    agree = record_probe_regrade_check(
        repository,
        attempt_id=first["observation"].attempt_id,
        regrade_rubric_score=first["rubric_score"],
        regrade_error_types=[first["error_type"]] if first["error_type"] else [],
        clock=CLOCK,
    )
    disagree = record_probe_regrade_check(
        repository,
        attempt_id=second["observation"].attempt_id,
        regrade_rubric_score=4,  # regrade says clean full score
        regrade_error_types=[],
        clock=CLOCK,
    )
    assert agree is not None and agree["original_outcome"] == agree["regrade_outcome"]
    assert disagree is not None and disagree["original_outcome"] != disagree["regrade_outcome"]

    report = grading_confusion_report(repository)
    scope = next(iter(report["scopes"].values()))
    assert scope["checks"] == 2
    assert scope["agreement_rate"] == pytest.approx(0.5)
    assert scope["confusion"][disagree["original_outcome"]][disagree["regrade_outcome"]] == 1


class FakeGradingClient:
    """Regrades every response as a clean full score."""

    provider_name = "fake_grader"
    provider_type = "fake"
    model = "fake-model"

    def run_grading_proposal(self, context):
        from learnloop.codex.schemas import CriterionEvidence, GradingProposal

        return GradingProposal(
            attempt_id=context.attempt_id,
            practice_item_id=context.practice_item_id,
            rubric_score=4,
            criterion_evidence=[
                CriterionEvidence(criterion_id="correctness", points_awarded=4.0, evidence="clean")
            ],
            grader_confidence=0.95,
        )


def test_run_probe_regrade_checks_samples_and_skips_checked(tmp_path):
    from learnloop.services.probe_audit import run_probe_regrade_checks

    loaded, repository = _setup(tmp_path)
    _drive_two_observations(loaded, repository)

    first = run_probe_regrade_checks(loaded, repository, FakeGradingClient(), limit=10, clock=CLOCK)
    assert first["recorded"] >= 1
    assert first["failed"] == 0
    # Idempotent sampling: already-checked attempts are skipped next run.
    second = run_probe_regrade_checks(loaded, repository, FakeGradingClient(), limit=10, clock=CLOCK)
    assert second["attempted"] == 0

    report = grading_confusion_report(repository)
    total_checks = sum(scope["checks"] for scope in report["scopes"].values())
    assert total_checks == first["recorded"]


# --- Shadow-mode policy comparison (Checkpoint 5.1) ------------------------------------


def test_shadow_rankings_are_logged_and_reported(tmp_path):
    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    presentation = _commit(loaded, repository, episode, item_id=ITEM_ID)

    shadow = presentation.selection_components.get("shadow_rankings")
    assert shadow is not None
    assert set(shadow) == {"predictive_rate", "hypothesis_eig", "predictive_eig"}
    for ranking in shadow.values():
        assert ranking and all(isinstance(item_id, str) for item_id in ranking)

    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=presentation.id, score=4)
    report = shadow_policy_report(repository)
    assert report["observations_with_shadow"] == 1
    for policy in report["policies"].values():
        assert policy["observations"] == 1


def test_pilot_report_bundles_all_sections(tmp_path):
    loaded, repository = _setup(tmp_path)
    _drive_two_observations(loaded, repository)

    report = pilot_report(loaded, repository)
    for section in (
        "eig_calibration",
        "time_calibration",
        "cross_surface_replication",
        "downstream_outcomes",
        "grading_confusion",
        "calibration_evidence",
        "shadow_policies",
        "replay_determinism",
    ):
        assert section in report
