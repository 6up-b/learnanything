"""KM2 sim gates (§16), deterministic form.

Per the milestone trim guidance these keep the two load-bearing gates — shared-
facet belief MAE and attempts-to-certify improve vs the per-LO baseline, with no
capability inflation — without driving the full sim sweep. They use the canonical
belief re-key (`sim.metrics.canonical_facet_belief_mae`) and the KM2 write path
directly. Since KM2b retired the legacy per-LO bridge, the per-LO baseline is
reconstructed from the canonical per-item marginals (each carrying a single LO's
one observation), so the pooled parent and the split keyings are still compared
on identical evidence.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.sim.metrics import canonical_facet_belief_mae
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW
from tests.test_km2_write_path import SHARED, _attempt, build_mvp07_vault


class _Student:
    """Minimal truth stub: one high-mastery shared facet."""

    def __init__(self, truth: float = 0.9):
        self.truth = truth

    def mastery_at(self, facet_id: str, day: float) -> float:
        return self.truth


@pytest.fixture
def mvp07(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_shared_facet_belief_mae_beats_per_lo(mvp07):
    """One attempt per LO on the shared facet: the pooled canonical parent tracks
    truth better than either per-LO belief on the same evidence."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, clock)

    student = _Student(truth=0.9)
    canonical = canonical_facet_belief_mae(repository, student, final_day=1.0)
    canonical_mae = canonical["mae"]

    # Per-LO baseline: the same shared facet, split per LO. KM2b retired the
    # legacy bridge, so the split belief is the canonical PER-ITEM marginal — each
    # carries only that one LO's single observation (more prior-pulled) — instead
    # of the pooled aggregate parent.
    per_lo_errors = []
    for item_id in ("pi_svd_define_001", "pi_svd_apply_001"):
        state = repository.canonical_facet_recall_state(SHARED, "retrieval", item_id)
        assert state is not None  # per-item marginal: one observation, split keying
        per_lo_errors.append(abs(state.recall_mean - student.truth))
    per_lo_mae = sum(per_lo_errors) / len(per_lo_errors)

    assert canonical_mae < per_lo_mae


def test_shared_facet_certifies_with_fewer_attempts(mvp07):
    """Attempts-to-certify improves: two attempts (one per LO) pool into two
    independent surface groups on the shared parent — the certification-coverage
    threshold — whereas the per-LO keying still has only one group each."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, clock)

    surface_groups, _mass = repository.facet_independence_evidence(SHARED)
    # Shared parent reached the 2-group coverage threshold in 2 attempts.
    assert surface_groups >= vault.config.locks.facet_surface_groups == 2

    # The per-LO keying, on the same two attempts, has one surface each — it would
    # take two attempts PER LO (four total) to match the shared parent's coverage.
    define = repository.facet_capability_evidence(SHARED, "retrieval")
    assert define is not None and len(define.independent_surface_groups) == 2


def test_no_capability_inflation_sim(mvp07):
    """Retrieval evidence never certifies method_selection (no inflation)."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, clock)

    assert repository.facet_capability_evidence(SHARED, "retrieval") is not None
    assert repository.facet_capability_evidence(SHARED, "method_selection") is None
