"""The facet-belief successor (mvp-0.59, after the figure wait estimate's mvp-0.58): one constant, its switch, its gates,
its openers, its upgrade, and the predecessor served exactly with the switch off (refactor bug ledger D-1, D-3, D-5,
D-6; docs/reviews/refactor-dfb.md; docs/algorithm-change-playbook.md).

The fixes' own fail-first tests are D2a's, now passing at the tag: test_recall_coverage_interventions (D-1, D-6),
test_teach_back (D-3 with D-6) and the facet-uncertainty readers ported off the old vault (D-5:
test_facet_diagnostics_v03, test_predictive_eig, test_goal_frontier, test_goal_projection, test_teach_back's plan).
Fakes only; no model call.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.algorithm_versions import (
    FACET_BELIEF_FIX_ALGORITHM_VERSION,
    FACET_BELIEF_FIX_VERSIONS,
    FIGURE_WAIT_ALGORITHM_VERSION,
    LATEST_ALGORITHM_VERSION,
    SUCCESSOR_CHAIN,
)
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.config.schema import FacetDiagnosticConfig
from learnloop.db.repositories import Repository
from learnloop.db.table_roles import TableRole, role_for_table
from learnloop.learner.facet_state_reader import (
    facet_belief_fixes_on,
    facet_uncertainty_states_for_lo,
)
from learnloop.ops.doctor import run_doctor
from learnloop.params.parameter_registry import classify_config_path
from learnloop.router_objective_switches import (
    FACET_BELIEF_FIXES_SNAPSHOT_KEY,
    INTERVAL_FACTOR_SNAPSHOT_KEY,
    projection_switches,
)
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, set_config_switch

TAG = FACET_BELIEF_FIX_ALGORITHM_VERSION
OLD = FIGURE_WAIT_ALGORITHM_VERSION
SWITCH = "facet_diagnostic.canonical_belief_fixes"
LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"


def test_the_successor_is_one_constant_after_the_figure_wait_estimate_and_the_latest():
    assert SUCCESSOR_CHAIN[SUCCESSOR_CHAIN.index(TAG) - 1] == OLD == "mvp-0.58"
    assert TAG == "mvp-0.59" == SUCCESSOR_CHAIN[-1] == LATEST_ALGORITHM_VERSION
    assert FACET_BELIEF_FIX_VERSIONS == frozenset({TAG})


def test_the_switch_defaults_on_and_is_classified():
    assert FacetDiagnosticConfig().canonical_belief_fixes is True
    rule = classify_config_path(SWITCH)
    assert rule is not None and rule.kind == "structural" and "kill switch" in rule.rationale
    assert "mvp-0.59" in rule.rationale


def test_the_gate_reads_off_below_the_tag_and_with_the_switch_off(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, OLD)
    assert not facet_belief_fixes_on(load_vault(paths.root).config)
    set_algorithm_version(paths, TAG)
    assert facet_belief_fixes_on(load_vault(paths.root).config)
    set_config_switch(paths.root, SWITCH, False)
    assert not facet_belief_fixes_on(load_vault(paths.root).config)


def test_the_uncertainty_table_is_derived_and_learner_replay_owns_it():
    from learnloop.substrate.rebuild_orchestrator import derived_table_owners

    assert role_for_table("facet_uncertainty") is TableRole.DERIVED
    assert derived_table_owners()["facet_uncertainty"] == ("learning_state",)


def test_a_rebuild_records_the_switch_only_at_the_tag(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    assert projection_switches(load_vault(paths.root).config) == {
        INTERVAL_FACTOR_SNAPSHOT_KEY: True, FACET_BELIEF_FIXES_SNAPSHOT_KEY: True,
    }
    set_config_switch(paths.root, SWITCH, False)
    assert projection_switches(load_vault(paths.root).config)[FACET_BELIEF_FIXES_SNAPSHOT_KEY] is False
    set_algorithm_version(paths, OLD)
    # Below the tag the record is the predecessor's, one key.
    assert projection_switches(load_vault(paths.root).config) == {INTERVAL_FACTOR_SNAPSHOT_KEY: True}


# -- The scenario both sides of the switch play: two don't-knows, then a success. --------------------------------------


def _play(paths):
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for offset in (0, 1):
        complete_self_graded_attempt(
            vault, repository,
            AttemptDraft(ITEM_ID, "I do not know", attempt_type="dont_know"),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
            clock=FrozenClock(NOW + timedelta(minutes=offset)),
        )
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(ITEM_ID, "SVD factors a matrix as U Sigma V transpose."),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=2)),
    )
    return vault, repository


_RECALL_COLUMNS = (
    "facet_id", "capability_key", "practice_item_id", "recall_alpha", "recall_beta", "recall_mean",
    "recall_variance", "independent_evidence_mass", "raw_coverage_mass", "last_observed_at", "last_error_at",
    "consecutive_failures",
)
_CAPABILITY_COLUMNS = (
    "facet_id", "capability", "direct_positive_mass", "direct_negative_mass", "embedded_positive_mass",
    "embedded_negative_mass", "certification_credit", "independent_surface_groups_json",
)


def _belief(repository):
    with repository.connection() as connection:
        recall = connection.execute(
            f"SELECT {', '.join(_RECALL_COLUMNS)} FROM facet_recall_state "
            "ORDER BY facet_id, capability_key, practice_item_id"
        ).fetchall()
        capability = connection.execute(
            f"SELECT {', '.join(_CAPABILITY_COLUMNS)} FROM facet_capability_evidence ORDER BY facet_id, capability"
        ).fetchall()
        uncertainty = connection.execute("SELECT COUNT(*) FROM facet_uncertainty").fetchone()[0]
    return [tuple(row) for row in recall], [tuple(row) for row in capability], uncertainty


def test_with_the_switch_off_the_belief_is_the_predecessors_exactly(tmp_path):
    predecessor = create_basic_vault(tmp_path / "old")
    set_algorithm_version(predecessor, OLD)
    switched_off = create_basic_vault(tmp_path / "off")
    set_config_switch(switched_off.root, SWITCH, False)

    _old_vault, old_repository = _play(predecessor)
    off_vault, off_repository = _play(switched_off)

    assert _belief(off_repository) == _belief(old_repository)
    assert _belief(old_repository)[2] == 0
    assert facet_uncertainty_states_for_lo(off_vault, off_repository, LO_ID) == []


def test_at_the_tag_the_three_fixes_and_the_uncertainty_show(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = _play(paths)
    recall, _capability, uncertainty_rows = _belief(repository)
    aggregate = next(row for row in recall if row[2] is None)
    columns = dict(zip(_RECALL_COLUMNS, aggregate, strict=True))

    assert columns["consecutive_failures"] == 0  # D-1: the success ended the streak
    assert columns["independent_evidence_mass"] > 0  # D-6: the don't-knows were observations
    assert uncertainty_rows == 1  # D-5: written, per LO
    (state,) = facet_uncertainty_states_for_lo(vault, repository, LO_ID)
    assert state.facet_id == "recall" and state.algorithm_version == TAG


def test_a_whole_vault_rebuild_reproduces_the_belief_and_the_uncertainty(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = _play(paths)
    before = _belief(repository)
    with repository.connection() as connection:
        uncertainty_before = [tuple(row) for row in connection.execute(
            "SELECT learning_object_id, facet_id, hypothesis_marginal, uncertainty, status, opened_by_attempt_id, "
            "opened_reason, last_evidence_at, algorithm_version FROM facet_uncertainty ORDER BY facet_id"
        ).fetchall()]

    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW + timedelta(days=1)))

    assert _belief(repository) == before
    with repository.connection() as connection:
        uncertainty_after = [tuple(row) for row in connection.execute(
            "SELECT learning_object_id, facet_id, hypothesis_marginal, uncertainty, status, opened_by_attempt_id, "
            "opened_reason, last_evidence_at, algorithm_version FROM facet_uncertainty ORDER BY facet_id"
        ).fetchall()]
    assert uncertainty_after == uncertainty_before and uncertainty_before
    marker = repository.latest_whole_vault_rebuild()
    assert marker["projection_switches"][FACET_BELIEF_FIXES_SNAPSHOT_KEY] is True


def test_a_legacy_era_uncertainty_row_is_never_the_successors_prior_or_read(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = _play(paths)
    # Make the row an mvp-0.6-era one, which a canonical vault upgraded from that tag may still hold for an LO it
    # never replayed: it was derived under another belief.
    with repository.connection() as connection:
        connection.execute(
            "UPDATE facet_uncertainty SET algorithm_version = 'mvp-0.6', status = 'resolved', opened_by_attempt_id = ?",
            (repository.list_recent_attempts_by_learning_object(LO_ID, limit=1)[0]["id"],),
        )
        connection.commit()
    assert facet_uncertainty_states_for_lo(vault, repository, LO_ID) == []

    later = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(ITEM_ID, "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=3)),
    )
    # Not its prior: the next update opens afresh, on this attempt, under the tag.
    (state,) = facet_uncertainty_states_for_lo(vault, repository, LO_ID)
    assert state.algorithm_version == TAG and state.status == "open"
    assert state.opened_by_attempt_id == later.attempt_id


def test_uncertainty_is_written_under_the_merged_facets_survivor(tmp_path):
    # Readers outside facet_state_reader (valuation, reader follow-ups, tutor promotions) look a row up by the
    # facet's canonical id, so the successor writes it there: the item names the retired id, the row the survivor.
    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = _play(paths)
    repository.insert_facet_merge(retired_facet_id="recall", surviving_facet_id="recall_v2", clock=FrozenClock(NOW))
    later = complete_self_graded_attempt(
        vault, repository,
        AttemptDraft(ITEM_ID, "I do not know", attempt_type="dont_know"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=3)),
    )

    survivor = repository.facet_uncertainty_state(LO_ID, "recall_v2")
    assert survivor is not None and survivor.opened_by_attempt_id == later.attempt_id
    (state,) = facet_uncertainty_states_for_lo(vault, repository, LO_ID)
    assert state.facet_id == "recall_v2" and state.id == survivor.id


def test_the_legacy_recall_bridge_stays_refused_at_the_tag(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    with pytest.raises(AssertionError, match="must not be written"):
        with repository.connection() as connection:
            repository._upsert_facet_recall_state(connection, {
                "learning_object_id": LO_ID, "facet_id": "recall", "practice_item_id": None,
                "recall_alpha": 1.0, "recall_beta": 1.0, "recall_mean": 0.5, "recall_variance": 0.08,
                "independent_evidence_mass": 0.0, "raw_coverage_mass": 0.0, "last_attempt_at": None,
                "last_error_at": None, "consecutive_failures": 0, "algorithm_version": TAG,
                "created_at": NOW_ISO, "updated_at": NOW_ISO,
            })


def test_doctor_warns_when_the_switch_moved_after_the_last_whole_vault_rebuild(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault, repository = _play(paths)
    rebuild_all_derived_state(vault, repository, clock=FrozenClock(NOW))

    def stale():
        return [issue for issue in run_doctor(paths.root).issues if issue.code == "sql:projection_switches_stale"]

    assert stale() == []
    set_config_switch(paths.root, SWITCH, False)
    (issue,) = stale()
    assert "facet-belief fixes" in issue.message


# -- The upgrade link. ----------------------------------------------------------------------------------------------


# -- D-3 in the Demonstrated curve: the timeline folds the same transfer scale the belief banks. ------------------


def _transfer_item_vault(root, *, belief_fixes: bool):
    from learnloop.vault.writer import upsert_practice_item

    from tests.helpers import write_facets

    paths = create_basic_vault(root)
    if not belief_fixes:
        set_config_switch(paths.root, SWITCH, False)
    write_facets(paths, [
        {"id": "recall", "kind": "definition", "claim": "Recall the SVD definition."},
        {"id": "geometry", "kind": "definition", "claim": "SVD as rotate, scale, rotate."},
    ])
    upsert_practice_item(paths.root, {
        "id": "pi_svd_transfer_001", "learning_object_id": LO_ID, "subjects": None,
        "practice_mode": "short_answer", "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": ["recall", "geometry"], "evidence_weights": {"recall": 1.0, "geometry": 1.0},
        "criterion_facet_weights": {"core": {"recall": 1.0}, "transfer": {"geometry": 1.0}},
        "prompt": "Define the SVD, then give the SVD of a rotation.", "expected_answer": "U Sigma V^T; R = R I I.",
        "grading_rubric": {"max_points": 4, "fatal_errors": [], "criteria": [
            {"id": "core", "points": 2.0, "tier": "core", "description": "Defines the factorization."},
            {"id": "transfer", "points": 2.0, "tier": "transfer", "description": "SVD of a rotation."},
        ]},
        "created_at": NOW_ISO, "updated_at": NOW_ISO,
    }, clock=FrozenClock(NOW))
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    complete_self_graded_attempt(
        vault, repository,
        AttemptDraft("pi_svd_transfer_001", "U Sigma V transpose; a rotation is R times I times I."),
        SelfGradeInput(criterion_points={"core": 2.0, "transfer": 2.0}, confidence=5),
        clock=FrozenClock(NOW),
    )
    return vault, repository


@pytest.mark.parametrize("belief_fixes", [True, False])
def test_the_demonstrated_curve_banks_what_the_belief_banks(tmp_path, belief_fixes):
    from learnloop.learner.facet_evidence_timeline import facet_evidence_timeline

    vault, repository = _transfer_item_vault(tmp_path / "vault", belief_fixes=belief_fixes)
    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    for facet in ("recall", "geometry"):
        series = facet_evidence_timeline(vault, repository, facet)
        assert (series[-1].demonstrated if series else 0.0) == pytest.approx(banked.get(facet, 0.0), abs=1e-12)
    assert banked["recall"] > 0
    multiplier = vault.config.teach_back.transfer_evidence_multiplier if belief_fixes else 1.0
    assert banked["geometry"] == pytest.approx(multiplier * banked["recall"])
