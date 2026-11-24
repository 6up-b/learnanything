"""Episode posterior arithmetic on a locked set and literal evidence."""

from math import log

import pytest

from learnloop.diagnosis import probe_episodes
from learnloop.diagnosis.probes import Hypothesis, HypothesisSet


def test_fold_uses_the_running_posterior_to_discount_the_next_likelihood():
    locked = HypothesisSet("topic", [Hypothesis("a"), Hypothesis("b")], {"a": 0.5, "b": 0.5})
    evidence = probe_episodes.EpisodeEvidence(
        hypothesis_set=locked,
        weighted_likelihoods=(({"a": 0.75, "b": 0.25}, 1.0), ({"a": 0.25, "b": 0.75}, 0.5)),
        total_observations=3,
        completion_candidates=("clean", "held"),
        held_attempt_ids=frozenset({"held"}),
    )
    result = probe_episodes.fold_posterior(evidence)

    assert result.hypothesis_set is locked
    assert result.prior == {"a": 0.5, "b": 0.5}
    assert result.posterior == {"a": 0.625, "b": 0.375}
    assert result.entropy == pytest.approx(-0.625 * log(0.625) - 0.375 * log(0.375))
    assert result.qualifying_observations == 1
    assert result.total_observations == 3


def test_fold_with_no_updates_returns_the_prior_and_counts_the_inert_observation():
    locked = HypothesisSet("topic", [Hypothesis("a"), Hypothesis("b")], {"a": 0.75, "b": 0.25})
    evidence = probe_episodes.EpisodeEvidence(
        hypothesis_set=locked,
        weighted_likelihoods=(),
        total_observations=1,
        completion_candidates=(),
        held_attempt_ids=frozenset(),
    )
    result = probe_episodes.fold_posterior(evidence)

    assert result.posterior == result.prior == locked.prior
    assert result.qualifying_observations == 0
    assert result.total_observations == 1
