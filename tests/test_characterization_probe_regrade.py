"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior; these tests document reality, not desired behavior. When P0.x intentionally changes behavior, update these tests in the same commit and note the change."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.probe_audit import record_probe_regrade_check
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    episode_posterior,
    serve_presentation,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, admit_probe_instrument_card, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
CLOCK = FrozenClock(NOW)


def _setup_probe_observation(tmp_path):
    """Enter an episode, serve one committed diagnostic probe, and record a
    full-score observation. Returns (loaded, repository, episode, attempt_id)."""

    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    loaded = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    admit_probe_instrument_card(repository, card_id="card_svd_contrast", items=(ITEM_ID,))

    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)
    eligible = next(
        entry
        for entry in eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
        if entry.item.id == ITEM_ID
    )
    presentation = commit_presentation(loaded, repository, episode, eligible, clock=CLOCK)
    serve_presentation(repository, presentation.id, clock=CLOCK)

    attempt_id = new_ulid()
    apply_attempt(
        loaded,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=ITEM_ID,
                learner_answer_md="answer",
                attempt_type="diagnostic_probe",
                probe_presentation_id=presentation.id,
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4.0},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=1.0,
                confidence=4,
                manual_review_reason=None,
            ),
            grading_source="ai",
        ),
        clock=CLOCK,
    )
    return loaded, repository, episode, attempt_id


# --- Regrade agreement recording (§7.6) --------------------------------------------


def test_regrade_records_original_vs_regrade_grader_outputs(tmp_path):
    """Pin the recorded regrade comparison. Both `original_outcome` and
    `regrade_outcome` are grader classifications through the observation's own
    persisted card snapshot -- neither is an adjudicated true class. Agreement is
    the equality of the two grader labels, not correctness against ground truth."""

    _loaded, repository, _episode, attempt_id = _setup_probe_observation(tmp_path)

    # A disagreeing regrade (fresh grader now returns a low/misconception outcome).
    result = record_probe_regrade_check(
        repository,
        attempt_id=attempt_id,
        regrade_rubric_score=0,
        regrade_error_types=["conceptual_slip"],
        attempt_type="diagnostic_probe",
        clock=CLOCK,
    )
    assert result == {
        "original_outcome": "correct_target_reason",
        "regrade_outcome": "confusable_signature",
    }

    checks = repository.probe_regrade_checks()
    assert len(checks) == 1
    check = checks[0]
    assert set(check.keys()) == {
        "id",
        "attempt_id",
        "probe_family_template_id",
        "probe_family_template_version",
        "grader_version",
        "original_outcome",
        "regrade_outcome",
        "agreement",
        "created_at",
    }
    assert check["attempt_id"] == attempt_id
    assert check["probe_family_template_id"] == "contrast_confusable"
    assert check["probe_family_template_version"] == 1
    assert check["grader_version"] == "diagnostic_microprobe_v1"
    # Both stored labels are grader outputs; agreement is grader-vs-grader.
    assert check["original_outcome"] == "correct_target_reason"
    assert check["regrade_outcome"] == "confusable_signature"
    assert check["agreement"] == 0

    # An agreeing regrade (same outcome) records agreement == 1.
    agreeing = record_probe_regrade_check(
        repository,
        attempt_id=attempt_id,
        regrade_rubric_score=4,
        attempt_type="diagnostic_probe",
        clock=CLOCK,
    )
    assert agreeing == {
        "original_outcome": "correct_target_reason",
        "regrade_outcome": "correct_target_reason",
    }
    assert repository.probe_regrade_checks()[-1]["agreement"] == 1


# --- Deferred grade-summary rewrite does not propagate to the posterior -----------


def test_deferred_regrade_rewrites_summary_but_posterior_does_not_follow(tmp_path):
    """Pin the known deficiency: a deferred regrade rewrites the grade-summary
    columns on `practice_attempts` (rubric_score / correctness / grader_confidence)
    in place, but the probe posterior is replayed from the persisted observation's
    grader channel, which is NOT rewritten. The posterior therefore does NOT
    follow the correction."""

    loaded, repository, episode, attempt_id = _setup_probe_observation(tmp_path)

    before_attempt = repository.fetch_practice_attempt(attempt_id)
    assert before_attempt["rubric_score"] == 4
    before_posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id)).posterior

    # Deferred regrade: rewrite the attempt's grade summary in place (the same
    # rubric_score / correctness / grader_confidence columns the deferred
    # self-grade path rewrites via record_deferred_regrade).
    repository.record_deferred_regrade(
        attempt_id=attempt_id,
        new_evidence_rows=[],
        superseded_by_evidence_id=new_ulid(),
        mastery_state=MasteryState(
            learning_object_id=LO_ID,
            logit_mean=-2.0,
            logit_variance=1.0,
            evidence_count=1,
            last_evidence_at=NOW_ISO,
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        ),
        attempt_update={
            "rubric_score": 0,
            "correctness": 0.0,
            "grader_confidence": 1.0,
            "manual_review": False,
            "manual_review_reason": None,
            "error_type": "conceptual_slip",
        },
        clock=CLOCK,
    )

    # The summary columns were rewritten in place.
    after_attempt = repository.fetch_practice_attempt(attempt_id)
    assert after_attempt["rubric_score"] == 0
    assert after_attempt["correctness"] == pytest.approx(0.0)
    assert after_attempt["error_type"] == "conceptual_slip"

    # But the persisted observation's grader channel is untouched...
    observation = repository.probe_observation_for_attempt(attempt_id)
    assert observation.grader_channel["observed_outcome"] == "correct_target_reason"

    # ...so the replayed posterior is byte-for-byte identical to before the
    # rewrite. This is the deficiency being pinned: the correction does not
    # propagate to the diagnostic posterior.
    after_posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id)).posterior
    assert after_posterior == pytest.approx(before_posterior)
    assert after_posterior["robust_initial_grasp"] == pytest.approx(0.911239569370203)
