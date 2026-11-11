"""KM5 §4.2 lazy capability-residual activation (DEFAULT OFF).

A planted capability-divergent learner (strong retrieval, weak method_selection
on ONE shared facet) drives real attempts. With the feature enabled the
projection activates a learner-specific residual per diverging (facet,
capability): the capability-sliced residual belief tracks the planted truth
better than the pooled shared parent, without inflating that parent. Activation
is derived in the projection fold, so a rebuild reproduces it byte-identically.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.substrate.replay import rebuild_derived_state

from tests.helpers import NOW
from tests.capability_residual_helpers import _build_vault, _drive

def _by_capability(repository) -> dict[str, dict]:
    return {row["capability"]: row for row in repository.capability_residual_states()}


def test_residual_activation_default_off_writes_nothing(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=False)
    _, repository = _drive(paths)
    assert repository.capability_residual_states() == []


def test_residual_activation_tracks_capability_truth_without_inflating_parent(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=True)
    _, repository = _drive(paths)
    rows = _by_capability(repository)
    assert "retrieval" in rows and "method_selection" in rows
    assert all(row["active"] for row in rows.values())

    truth = {"retrieval": 1.0, "method_selection": 0.0}
    parent_mean = rows["retrieval"]["parent_mean"]
    # The pooled parent is shared, so both cells report the same parent belief.
    assert parent_mean == pytest.approx(rows["method_selection"]["parent_mean"])

    residual_mae = sum(abs(rows[c]["residual_mean"] - truth[c]) for c in truth) / len(truth)
    parent_mae = sum(abs(parent_mean - truth[c]) for c in truth) / len(truth)
    assert residual_mae < parent_mae

    # The shared parent is not inflated toward the strong capability: it sits
    # between the two capability-sliced residual beliefs.
    assert rows["method_selection"]["residual_mean"] < parent_mean < rows["retrieval"]["residual_mean"]


def test_residual_activation_replay_deterministic(tmp_path):
    paths = _build_vault(tmp_path / "vault", enable=True)
    vault, repository = _drive(paths)

    def snapshot():
        return {
            (r["facet_id"], r["capability"]): (
                r["active"],
                r["activation_reason"],
                round(r["residual_mean"], 9),
                round(r["parent_mean"], 9),
                round(r["divergence"], 9),
                r["independent_groups"],
            )
            for r in repository.capability_residual_states()
        }

    live = snapshot()
    assert live  # activation actually happened
    rebuild_derived_state(vault, repository, clock=FrozenClock(NOW))
    once = snapshot()
    rebuild_derived_state(vault, repository, clock=FrozenClock(NOW))
    twice = snapshot()
    assert live == once == twice
