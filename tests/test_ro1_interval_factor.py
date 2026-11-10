"""Router objective RO1 §5.1-5.2: the surprise interval factor is not applied at mvp-0.46.

At the tag, with ``[scheduler.surprise] remove_interval_factor`` on (the default), ``due_at`` follows
``interval_for_retention(S)``; the FSRS rating, S, D and surprise itself are unchanged, and
``attempt_surprise.fsrs_interval_factor`` records 1.0, what was applied. Below the tag, or with the switch
off, the predecessor's interval, byte for byte. Fakes only (self-graded attempts); no model call.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import (
    FOLLOWUP_SERVE_ALGORITHM_VERSION,
    INTERVAL_FACTOR_ALGORITHM_VERSION,
    INTERVAL_FACTOR_VERSIONS,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.router_objective_switches import interval_factor_removed
from learnloop.scheduling.fsrs import interval_for_retention
from learnloop.params.fitted_params import resolve_fsrs_weights
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_placement_vault

TAG = INTERVAL_FACTOR_ALGORITHM_VERSION
PREDECESSOR = FOLLOWUP_SERVE_ALGORITHM_VERSION
OFF = "[scheduler.surprise]\nremove_interval_factor = false\n"

#: (item, points): a hard item answered right (positive surprise, factor > 1) and an easy one answered
#: badly (negative surprise, factor < 1), then the hard one again a few days later.
HISTORY = (("pi_eig_hard", 4, 0), ("pi_eig_easy", 1, 0), ("pi_eig_hard", 4, 3))


def _vault(tmp_path, version: str, toml: str | None = None):
    paths = create_placement_vault(tmp_path, version=version, placement_toml=toml)
    return paths, Repository(paths.sqlite_path)


def _play(paths, repository):
    """The history, returning per attempt (attempt id, item, observed_at, state, surprise row)."""

    out = []
    for index, (item_id, points, day) in enumerate(HISTORY):
        observed = NOW + timedelta(days=day, minutes=index)
        result = complete_self_graded_attempt(
            load_vault(paths.root),
            repository,
            AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer."),
            SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
            clock=FrozenClock(observed),
        )
        state = repository.practice_item_state(item_id)
        out.append((result.attempt_id, item_id, observed, state, repository.latest_attempt_surprise(result.attempt_id)))
    return out


def _due(observed, days: float) -> str:
    return (observed + timedelta(days=days)).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def test_the_gate_is_the_tag_and_the_switch(tmp_path):
    assert TAG == "mvp-0.46" and TAG in INTERVAL_FACTOR_VERSIONS and PREDECESSOR not in INTERVAL_FACTOR_VERSIONS
    on, _ = _vault(tmp_path / "on", TAG)
    off, _ = _vault(tmp_path / "off", TAG, OFF)
    below, _ = _vault(tmp_path / "below", PREDECESSOR)
    assert interval_factor_removed(load_vault(on.root).config) is True
    assert interval_factor_removed(load_vault(off.root).config) is False
    assert interval_factor_removed(load_vault(below.root).config) is False


def test_at_the_tag_due_at_follows_interval_for_retention_of_stability(tmp_path):
    paths, repository = _vault(tmp_path, TAG)
    weights = resolve_fsrs_weights(repository)
    for _attempt_id, _item_id, observed, state, surprise in _play(paths, repository):
        assert state.due_at == _due(observed, interval_for_retention(state.stability, weights=weights))
        # What was applied: nothing.
        assert surprise["fsrs_interval_factor"] == 1.0


def test_below_the_tag_and_switched_off_the_factor_stretches_the_interval_as_before(tmp_path):
    below_paths, below_repo = _vault(tmp_path / "below", PREDECESSOR)
    off_paths, off_repo = _vault(tmp_path / "off", TAG, OFF)
    below = _play(below_paths, below_repo)
    off = _play(off_paths, off_repo)
    weights = resolve_fsrs_weights(below_repo)
    factors = []
    for (_a, _i, observed, state, surprise), (_b, _j, _o, off_state, off_surprise) in zip(below, off, strict=True):
        factor = surprise["fsrs_interval_factor"]
        factors.append(factor)
        assert state.due_at == _due(observed, interval_for_retention(state.stability, weights=weights) * factor)
        assert (off_state.due_at, off_state.stability, off_state.difficulty) == (
            state.due_at, state.stability, state.difficulty)
        assert off_surprise["fsrs_interval_factor"] == factor
    # The history exercises both directions of the factor.
    assert min(factors) < 1.0 < max(factors)


def test_rating_stability_difficulty_and_surprise_match_the_predecessor(tmp_path):
    below_paths, below_repo = _vault(tmp_path / "below", PREDECESSOR)
    tag_paths, tag_repo = _vault(tmp_path / "tag", TAG)
    below = _play(below_paths, below_repo)
    tag = _play(tag_paths, tag_repo)
    keys = ("predictive_surprise", "bayesian_surprise", "surprise_direction", "predicted_score_dist",
            "observed_joint_bucket", "posterior_delta", "triggered_actions", "suppressed_actions")
    for index, ((_a, _i, _o, before_state, before), (_b, _j, _p, after_state, after)) in enumerate(
            zip(below, tag, strict=True)):
        if index < 2:
            # A first review: the same S and D whatever the earlier interval was.
            assert (after_state.stability, after_state.difficulty) == (before_state.stability, before_state.difficulty)
        assert {key: after[key] for key in keys} == {key: before[key] for key in keys}
        assert after["algorithm_version"] == TAG and before["algorithm_version"] == PREDECESSOR
    # Only the stored due date moved for a first review.
    assert below[0][3].due_at != tag[0][3].due_at
    assert parse_utc(tag[0][3].due_at) < parse_utc(below[0][3].due_at)


@pytest.mark.parametrize("version, toml", [(TAG, None), (TAG, OFF), (PREDECESSOR, None)], ids=["tag", "off", "below"])
def test_a_held_or_ineligible_attempt_leaves_the_schedule_as_it_was(tmp_path, version, toml):
    """A primed retry (not FSRS-eligible) keeps the stored due date at every gate."""

    paths, repository = _vault(tmp_path, version, toml)
    [(_a, item_id, _o, state, _s)] = _play_one(paths, repository, "pi_eig_mid", 4, primed=False)
    [(_b, _i, _p, after, surprise)] = _play_one(paths, repository, "pi_eig_mid", 4, primed=True, day=1)
    assert (after.due_at, after.stability, after.difficulty) == (state.due_at, state.stability, state.difficulty)
    assert surprise is not None


def _play_one(paths, repository, item_id, points, *, primed, day=0):
    observed = NOW + timedelta(days=day)
    result = complete_self_graded_attempt(
        load_vault(paths.root),
        repository,
        AttemptDraft(practice_item_id=item_id, learner_answer_md="An answer.", primed=primed),
        SelfGradeInput(criterion_points={"correctness": points}, confidence=4),
        clock=FrozenClock(observed),
    )
    state = repository.practice_item_state(item_id)
    return [(result.attempt_id, item_id, observed, state, repository.latest_attempt_surprise(result.attempt_id))]
