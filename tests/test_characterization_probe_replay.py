"""Characterization tests (P0.0, spec_p0_measurement_correctness.md §2): pin current behavior; these tests document reality, not desired behavior. When P0.x intentionally changes behavior, update these tests in the same commit and note the change."""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services import probe_families
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.probe_episodes import (
    commit_presentation,
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    episode_posterior,
    serve_presentation,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, admit_probe_instrument_card, create_basic_vault

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


def test_replay_pins_exact_posterior_under_current_default_policy(tmp_path):
    """Pin the exact replayed posterior for a simple constructed episode under
    the current default grader policy (`diagnostic_microprobe_v1`, reliability
    0.90). One full-score diagnostic probe concentrates mass on the robust
    hypothesis."""

    loaded, repository, episode, attempt_id = _setup_probe_observation(tmp_path)

    # The observation persists the classified grader outcome (the true class the
    # grader observed), NOT the recomposed likelihoods it will be replayed with.
    observation = repository.probe_observation_for_attempt(attempt_id)
    assert observation.grader_channel["grader_policy"] == "diagnostic_microprobe_v1"
    assert observation.grader_channel["observed_outcome"] == "correct_target_reason"

    posterior = episode_posterior(loaded, repository, repository.probe_episode(episode.id))
    assert posterior.qualifying_observations == 1
    assert posterior.total_observations == 1
    assert posterior.posterior == pytest.approx(
        {
            "robust_initial_grasp": 0.911239569370203,
            "unfamiliar": 0.04762127693036372,
            "recall_without_mechanism": 0.02776892874711746,
            "other_or_unknown": 0.013370224952315815,
        }
    )
    assert posterior.entropy == pytest.approx(0.3868892008615352)


def test_replay_rebuilds_from_current_grader_policy_not_a_pinned_snapshot(tmp_path, monkeypatch):
    """Pin the known non-pinning: replay recomposes observation likelihoods from
    the CURRENT `GRADER_CHANNEL_RELIABILITY` for the policy name, not from any
    channel snapshot frozen at observation time. Mutating the live reliability
    changes the replayed posterior of the same historical observation."""

    loaded, repository, episode, _ = _setup_probe_observation(tmp_path)

    baseline = episode_posterior(loaded, repository, repository.probe_episode(episode.id))

    # Same persisted observation, different current default policy reliability.
    monkeypatch.setitem(probe_families.GRADER_CHANNEL_RELIABILITY, "diagnostic_microprobe_v1", 0.55)
    replayed = episode_posterior(loaded, repository, repository.probe_episode(episode.id))

    # No pinning: the replayed posterior moved because the channel was rebuilt.
    assert replayed.posterior != pytest.approx(baseline.posterior)
    assert replayed.posterior == pytest.approx(
        {
            "robust_initial_grasp": 0.7116379707782198,
            "unfamiliar": 0.1530700178923866,
            "recall_without_mechanism": 0.09132210764734065,
            "other_or_unknown": 0.04396990368205292,
        }
    )
    # A lower grader reliability dilutes the same success toward the prior.
    assert replayed.posterior["robust_initial_grasp"] < baseline.posterior["robust_initial_grasp"]
