"""KM2b — consumer re-key: mvp-0.7 consumers read canonical shared facet state,
and the legacy per-LO write bridge is retired.

Drives real attempts through the write path on the shared hand-authored mvp-0.7
fixture (two LOs sharing one canonical facet) and asserts the thirteen-reader
surfaces (scheduler view, goal projection, prior-state read) observe the pooled
canonical parent — while the legacy `evidence_facet_recall_state` table stays
empty and refuses any mvp-0.7-keyed write.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.facet_state_reader import facet_states_by_lo
from learnloop.services.goal_projection import goal_report
from learnloop.services.replay import rebuild_derived_state
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import Goal, GoalFacetScope

from tests.helpers import NOW, NOW_ISO
from tests.test_km2_write_path import SHARED, _attempt, build_mvp07_vault

DEFINE_LO = "lo_svd_definition"
APPLY_LO = "lo_svd_application"


@pytest.fixture
def mvp07(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def test_two_los_share_one_facet_parent_in_scheduler_view(mvp07):
    """The scheduler's per-LO facet-state view (its `facet_states_by_lo` source)
    shows both LOs seeing ONE pooled canonical parent, moved by both attempts."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, clock)

    by_lo = facet_states_by_lo(vault, repository)

    def shared_aggregate(lo_id):
        rows = [
            s
            for s in by_lo[lo_id]
            if s.facet_id == SHARED and s.practice_item_id is None
        ]
        assert len(rows) == 1, f"{lo_id} should see exactly one shared parent"
        return rows[0]

    define_view = shared_aggregate(DEFINE_LO)
    apply_view = shared_aggregate(APPLY_LO)

    # Both LOs read the SAME pooled parent: two positive observations (alpha past
    # the 2.0 single-observation value) and an identical belief, not two split
    # per-LO beliefs on one observation each.
    assert define_view.recall_alpha > 2.0
    assert define_view.recall_mean == pytest.approx(apply_view.recall_mean)
    assert define_view.recall_alpha == pytest.approx(apply_view.recall_alpha)
    assert define_view.independent_evidence_mass == pytest.approx(
        apply_view.independent_evidence_mass
    )


def test_goal_projection_reads_canonical_state(mvp07):
    """A goal report's facet projection reads the canonical pooled recall mean,
    not a per-LO split value."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, clock)

    goal = Goal(
        schema_version=2,
        id="goal_svd",
        title="Master SVD",
        target_recall=0.5,
        facet_scope=GoalFacetScope(concepts=["singular_value_decomposition"]),
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    report = goal_report(vault, repository, goal, clock=clock)

    shared_projections = [f for f in report.facets if f.facet_id == SHARED]
    assert shared_projections, "shared facet must be in the goal scope"
    pooled = repository.canonical_facet_recall_state(SHARED, "retrieval", None)
    assert pooled is not None
    # Every LO's projection of the shared facet shows the one pooled belief.
    for projection in shared_projections:
        assert projection.current_recall == pytest.approx(pooled.recall_mean)
        assert projection.current_recall > 0.6  # pooled positive evidence


def test_mvp07_vault_refuses_legacy_facet_state_write(mvp07):
    """The legacy per-LO table stays empty under mvp-0.7, and any mvp-0.7-keyed
    legacy write is a hard error (KM2b item 9 hard-stop flipped)."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 3}, clock)

    # Real attempts drove the canonical projection but wrote NO legacy rows.
    assert repository.facet_recall_states() == []
    assert repository.canonical_facet_recall_states(), "canonical state was written"

    # The write-path guard refuses an mvp-0.7-keyed legacy row outright.
    with pytest.raises(AssertionError):
        with repository.connection() as connection:
            repository._upsert_facet_recall_state(
                connection, {"algorithm_version": "mvp-0.7"}
            )
    with pytest.raises(AssertionError):
        with repository.connection() as connection:
            repository._upsert_facet_uncertainty_state(
                connection, {"algorithm_version": "mvp-0.7"}
            )


def test_exam_attempt_moves_shared_parent_across_los(mvp07):
    """Evidence recorded against ONE LO's item moves the shared parent that the
    OTHER LO reads — the whole point of the vault-level re-key."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)

    # Before any attempt, the apply LO sees no shared-facet evidence.
    before = facet_states_by_lo(vault, repository)
    assert not any(
        s.facet_id == SHARED and s.practice_item_id is None for s in before[APPLY_LO]
    )

    # One graded attempt on the DEFINITION LO's item.
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)

    after = facet_states_by_lo(vault, repository)
    apply_view = [
        s for s in after[APPLY_LO] if s.facet_id == SHARED and s.practice_item_id is None
    ]
    # The APPLICATION LO — which had no attempt of its own — now reads the moved
    # shared parent.
    assert len(apply_view) == 1
    assert apply_view[0].recall_alpha > 1.0
    assert apply_view[0].recall_mean > 0.5


def test_replay_identity_after_bridge_removal(mvp07):
    """Rebuilding twice is byte-identical for canonical state AND the legacy
    table stays empty across replay (no bridge to resurrect)."""

    vault, repository = mvp07
    clock = FrozenClock(NOW)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, clock)
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 3}, clock)

    def snapshot():
        return {
            (s.facet_id, s.capability_key, s.practice_item_id): (
                round(s.recall_alpha, 9),
                round(s.recall_beta, 9),
                round(s.independent_evidence_mass, 9),
            )
            for s in repository.canonical_facet_recall_states()
        }

    live = snapshot()
    rebuild_derived_state(vault, repository)
    once = snapshot()
    rebuild_derived_state(vault, repository)
    twice = snapshot()

    assert live == once == twice
    assert repository.facet_recall_states() == []
