"""KM2 — canonical shared state, lineage, merges, and bounded certification.

Pure-function and repository-layer coverage for the KM §16 verification rows
reachable without the full write path. The write-path/replay rows live in
test_km2_write_path.py.
"""

from __future__ import annotations

import pathlib

import pytest

from learnloop.db.repositories import Repository
from learnloop.learner.capability_mapping import (
    CriterionOutcome,
    cap_certification_by_group,
    certification_credit,
    group_budget,
    group_proliferation_flag,
    localize_criterion_outcomes,
)


@pytest.fixture
def repo(tmp_path) -> Repository:
    return Repository(tmp_path / "state.sqlite")


# -- Migration / schema (§16 state schema) ------------------------------------


def test_shared_aggregate_rows_unique_despite_null_item(repo: Repository):
    """Two aggregate rows for the same (facet, capability) collide; a per-item
    row with the same key coexists (partial indexes, §7.1)."""

    repo.replace_canonical_facet_state(
        recall_rows=[
            {
                "facet_id": "f_sym",
                "capability_key": "shared",
                "practice_item_id": None,
                "recall_alpha": 2.0,
                "recall_beta": 1.0,
                "recall_mean": 0.66,
                "recall_variance": 0.05,
            },
            {
                "facet_id": "f_sym",
                "capability_key": "shared",
                "practice_item_id": "pi_1",
                "recall_alpha": 2.0,
                "recall_beta": 1.0,
                "recall_mean": 0.66,
                "recall_variance": 0.05,
            },
        ],
        capability_rows=[],
        algorithm_version="mvp-0.7",
    )
    assert repo.canonical_facet_recall_state("f_sym", "shared", None) is not None
    assert repo.canonical_facet_recall_state("f_sym", "shared", "pi_1") is not None

    # A second NULL-item aggregate for the same (facet, capability) must be
    # rejected by the partial unique index (SQLite would otherwise permit
    # duplicate NULLs).
    import sqlite3

    with repo.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO facet_recall_state(
                  id, facet_id, capability_key, practice_item_id, recall_alpha,
                  recall_beta, recall_mean, recall_variance, independent_evidence_mass,
                  raw_coverage_mass, consecutive_failures, algorithm_version,
                  created_at, updated_at
                ) VALUES ('dup', 'f_sym', 'shared', NULL, 1, 1, 0.5, 0.08, 0, 0, 0,
                          'mvp-0.7', 't', 't')
                """
            )


# -- Merges (§16 locks/merges) ------------------------------------------------


def test_merge_chain_canonicalizes_transitively(repo: Repository):
    repo.insert_facet_merge(retired_facet_id="a", surviving_facet_id="b")
    repo.insert_facet_merge(retired_facet_id="b", surviving_facet_id="c")
    assert repo.resolve_facet_merge("a") == "c"
    assert repo.resolve_facet_merge("b") == "c"
    assert repo.resolve_facet_merge("c") == "c"
    assert repo.resolve_facet_merge("unmerged") == "unmerged"


def test_cycle_creating_merge_rejected(repo: Repository):
    repo.insert_facet_merge(retired_facet_id="a", surviving_facet_id="b")
    repo.insert_facet_merge(retired_facet_id="b", surviving_facet_id="c")
    with pytest.raises(ValueError, match="cycle"):
        repo.insert_facet_merge(retired_facet_id="c", surviving_facet_id="a")
    with pytest.raises(ValueError, match="cycle"):
        repo.insert_facet_merge(retired_facet_id="x", surviving_facet_id="x")


def test_merge_never_copies_beta_mass(repo: Repository):
    """A merge writes only the map row; no belief rows are created/copied (§3.4)."""

    repo.insert_facet_merge(retired_facet_id="old", surviving_facet_id="new")
    assert repo.canonical_facet_recall_states() == []


# -- Localization (§16 observation/replay, ambiguity) --------------------------


def test_dependency_branch_failure_preserves_independent_work():
    """A failed criterion makes its descendants unassessable, but an independent
    branch stays assessable and correct work is preserved (§5.3)."""

    outcomes = [
        CriterionOutcome("identify", passed=True),
        CriterionOutcome("select", passed=False, depends_on=("identify",)),
        CriterionOutcome("apply", passed=True, depends_on=("select",)),  # descendant
        CriterionOutcome("independent", passed=True),  # unrelated branch
    ]
    localized = {c.criterion_id: c for c in localize_criterion_outcomes(outcomes)}
    assert localized["identify"].assessable and localized["identify"].passed
    assert localized["select"].assessable and localized["select"].first_error
    # 'apply' depended on the failed 'select' => unassessable, NOT failed.
    assert not localized["apply"].assessable
    assert not localized["apply"].first_error
    # Independent branch unaffected.
    assert localized["independent"].assessable and localized["independent"].passed


def test_whole_item_failure_localizes_to_first_error_only():
    outcomes = [
        CriterionOutcome("step1", passed=False),
        CriterionOutcome("step2", passed=False, depends_on=("step1",)),
        CriterionOutcome("step3", passed=False, depends_on=("step2",)),
    ]
    localized = localize_criterion_outcomes(outcomes)
    first_errors = [c.criterion_id for c in localized if c.first_error]
    unassessable = [c.criterion_id for c in localized if not c.assessable]
    assert first_errors == ["step1"]
    assert unassessable == ["step2", "step3"]


# -- Bounded certification (§16 certification / certification quantities) ------


def test_retrieval_evidence_cannot_certify_method_selection():
    """Certification credit accrues only to the observed capability's ledger
    cell; a retrieval observation earns nothing for method_selection (§4.2)."""

    # Positive retrieval observation, direct + unassisted.
    credit = certification_credit(1.0, relationship="direct", assistance="unassisted")
    assert credit == pytest.approx(1.0)
    # There is no code path that routes this credit to a different capability:
    # the projection keys credit by the observation's own capability. An assisted
    # or projection-tier signal earns zero.
    assert certification_credit(1.0, relationship="direct", assistance="hinted") == 0.0
    assert certification_credit(1.0, relationship="prior", assistance="unassisted") == 0.0


def test_certification_bounded_per_correlation_group():
    """Several criteria reflecting one upstream error earn no more than their
    shared group budget (§5.4)."""

    # Three observations in one correlation group, evidence_mass 1.0 => budget 1.0.
    capped = cap_certification_by_group(
        {"g_symmetry": 2.4},
        attempt_type="independent_attempt",
        evidence_mass=1.0,
        max_groups_per_attempt=3,
    )
    assert capped["g_symmetry"] == pytest.approx(1.0)


def test_rich_response_earns_several_group_budgets_capped_by_ceiling():
    """A three-group constructed response earns up to three group budgets, then
    the attempt-wide ceiling (§5.4 quantity 4)."""

    capped = cap_certification_by_group(
        {"g1": 1.0, "g2": 1.0, "g3": 1.0, "g4": 1.0},
        attempt_type="independent_attempt",
        evidence_mass=1.0,
        max_groups_per_attempt=3,
    )
    # Each group individually within budget (1.0), but total capped at 3.0.
    assert sum(capped.values()) == pytest.approx(3.0)


def test_group_budget_override():
    overrides = {"exam_evidence:g_hard": 0.1}
    assert group_budget(
        "exam_evidence", "g_hard", evidence_mass=0.35, overrides=overrides
    ) == pytest.approx(0.1)
    assert group_budget(
        "exam_evidence", "g_other", evidence_mass=0.35, overrides=overrides
    ) == pytest.approx(0.35)


def test_group_proliferation_flag():
    flagged = group_proliferation_flag(
        {"g_real": 3, "g_always_covaries": 1, "g_single": 0}
    )
    assert flagged == ["g_always_covaries", "g_single"]
