"""Redundancy penalty and sequential selection on the observed posterior."""

from __future__ import annotations

import pytest

from learnloop.ids import new_ulid
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.diagnosis.probe_episodes import (
    eligible_instruments,
    enter_episode,
    episode_hypothesis_set,
    episode_posterior,
)
from learnloop.diagnosis.probe_presentations import (
    commit_presentation,
    serve_presentation,
)
from tests.probe_policy_helpers import CLOCK, ITEM_ID, LO_ID, _setup

def _grade(score: int) -> ResolvedGrade:
    return ResolvedGrade(
        rubric_score=score,
        criterion_points={"correctness": float(score)},
        evidence_rows=[],
        error_attributions=[],
        grader_confidence=1.0,
        confidence=4,
        manual_review_reason=None,
    )


def _submit(loaded, repository, *, item_id, presentation_id, score=4):
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
            grade=_grade(score),
            grading_source="ai",
        ),
        clock=CLOCK,
    )


# --- Redundancy penalty (Checkpoint 5.2) -----------------------------------------------


def test_family_redundancy_penalty_after_observation_below_mvp_077(tmp_path):
    """mvp-0.76's ranking (G2-R33 retired it at mvp-0.77): the retired field's remembered value multiplies."""

    from learnloop.config.retired import retired_value
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    from tests.helpers import set_algorithm_version

    loaded, repository = _setup(tmp_path)
    set_algorithm_version(VaultPaths(loaded.root, loaded.config), "mvp-0.76")
    loaded = load_vault(loaded.root)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)

    before = eligible_instruments(loaded, repository, episode)
    assert all(entry.redundancy_penalty == 1.0 for entry in before)

    hypothesis_set = episode_hypothesis_set(repository, episode)
    first = next(entry for entry in before if entry.item.id == ITEM_ID)
    presentation = commit_presentation(loaded, repository, episode, first, clock=CLOCK)
    serve_presentation(repository, presentation.id, vault=loaded, clock=CLOCK)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=presentation.id)

    episode = repository.probe_episode(episode.id)
    if episode.status != "in_progress":
        pytest.skip("episode completed after one observation; penalty unobservable")
    after = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    # The remaining candidate shares the observed family: penalized once, and
    # the penalty is a separate component — the EIG value itself is unpenalized.
    penalty = retired_value(loaded.config.probe.block, "family_redundancy_penalty")
    assert penalty == 0.6
    for entry in after:
        assert entry.redundancy_penalty == pytest.approx(penalty)
        assert entry.selection_components()["redundancy_penalty"] == pytest.approx(penalty)


def test_sequential_selection_conditions_on_observed_posterior(tmp_path):
    """§16 test 29: outside a precommitted block, selection is sequential and
    conditions on the observed posterior — the live ranking reflects the first
    observation instead of the entry prior."""

    loaded, repository = _setup(tmp_path)
    episode = enter_episode(loaded, repository, LO_ID, clock=CLOCK)
    hypothesis_set = episode_hypothesis_set(repository, episode)

    entry_prior_ranked = eligible_instruments(
        loaded, repository, episode, hypothesis_set=hypothesis_set, posterior=hypothesis_set.prior
    )
    first = next(entry for entry in entry_prior_ranked if entry.item.id == ITEM_ID)
    presentation = commit_presentation(loaded, repository, episode, first, clock=CLOCK)
    serve_presentation(repository, presentation.id, vault=loaded, clock=CLOCK)
    _submit(loaded, repository, item_id=ITEM_ID, presentation_id=presentation.id)

    episode = repository.probe_episode(episode.id)
    if episode.status != "in_progress":
        pytest.skip("episode completed after one observation")
    live = episode_posterior(loaded, repository, episode)
    sequential = eligible_instruments(loaded, repository, episode, hypothesis_set=hypothesis_set)
    conditioned = eligible_instruments(
        loaded, repository, episode, hypothesis_set=hypothesis_set, posterior=live.posterior
    )
    # The default path equals explicit conditioning on the live posterior.
    assert [entry.item.id for entry in sequential] == [entry.item.id for entry in conditioned]
    assert [entry.expected_information_gain for entry in sequential] == [
        entry.expected_information_gain for entry in conditioned
    ]
