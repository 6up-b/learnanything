"""Meas §B2/§E2 three-state (+claimed) measurement labels — plan item 3.2.

The vocabulary is ``measured | inferred | claimed | unknown`` and it says *how we
came to believe* a displayed number, orthogonal to the
``unexamined | uncertain | known_gap | solid`` bucket that says *what* we believe.
Coverage here is the licensing rule per label, the closedness of the vocabulary,
the motivating case (the pooled ``predicted_facet_recall`` that used to render
unlabelled now carries ``inferred``), and §B2's own "revert if": that nothing
written or certified reads the label.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import MasteryState, Repository
from learnloop.learner.capability_grid import capability_grid
from learnloop.goals.goal_projection import goal_report
from learnloop.learner.measurement_state import (
    CLAIMED,
    INFERRED,
    MEASURED,
    MEASUREMENT_STATES,
    UNKNOWN,
    classify_measurement_state,
    require_measurement_state,
)
from learnloop.scheduling.selection_rewards import predicted_facet_recall
from learnloop.vault.loader import load_vault

from tests.helpers import ALGORITHM_VERSION, NOW, NOW_ISO, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"
ITEM_ID = "pi_svd_define_001"
FACET_ID = "recall"
MIN_MASS = 0.50  # recall_coverage.min_facet_evidence_mass on the basic vault
BLEND = 3.0


# -- the licensing rule, in the one place that decides it ---------------------


def test_measured_requires_direct_evidence_over_the_mass_gate():
    """``measured`` is reserved for evidence actually observed, over the gate."""

    assert (
        classify_measurement_state(evidence_mass=2.0, min_evidence_mass=MIN_MASS) == MEASURED
    )
    # Strictly greater, matching facet_state_label's ``solid`` arm: exactly at
    # the gate is not over it.
    assert (
        classify_measurement_state(evidence_mass=MIN_MASS, min_evidence_mass=MIN_MASS) != MEASURED
    )


def test_inferred_requires_something_real_to_pool_from():
    """Sub-threshold direct mass, or an evidenced LO backbone, licenses inference."""

    assert (
        classify_measurement_state(evidence_mass=0.1, min_evidence_mass=MIN_MASS) == INFERRED
    )
    assert (
        classify_measurement_state(
            evidence_mass=0.0, min_evidence_mass=MIN_MASS, mastery_evidence_count=1
        )
        == INFERRED
    )


def test_ignorance_is_unknown_and_never_inferred():
    """The 0.5 default is not an inference, so it may not be labelled as one.

    ``predicted_facet_recall`` returns a flat 0.5 when there is neither facet
    mass nor an evidenced mastery row. Labelling that as ``inferred`` is exactly
    the confident wrongness §B2 exists to prevent.
    """

    assert predicted_facet_recall(None, 0, None, 0.0, BLEND) == pytest.approx(0.5)
    assert (
        classify_measurement_state(
            evidence_mass=0.0, min_evidence_mass=MIN_MASS, mastery_evidence_count=0
        )
        == UNKNOWN
    )
    # A claim-seeded mastery row carries evidence_count 0 — still nothing to pool.
    assert (
        classify_measurement_state(
            evidence_mass=None, min_evidence_mass=MIN_MASS, mastery_evidence_count=0
        )
        == UNKNOWN
    )


def test_claimed_is_licensed_only_by_absence_and_never_outranks_evidence():
    """§E2: claimed, unverified — a distinct state from unknown, and a prior only."""

    assert (
        classify_measurement_state(
            evidence_mass=0.0, min_evidence_mass=MIN_MASS, claim_present=True
        )
        == CLAIMED
    )
    # Precedence: measured > inferred > claimed. A claim cannot promote itself
    # over a number derived from evidence.
    assert (
        classify_measurement_state(
            evidence_mass=2.0, min_evidence_mass=MIN_MASS, claim_present=True
        )
        == MEASURED
    )
    assert (
        classify_measurement_state(
            evidence_mass=0.0,
            min_evidence_mass=MIN_MASS,
            mastery_evidence_count=4,
            claim_present=True,
        )
        == INFERRED
    )


def test_claim_lookup_is_only_consulted_on_the_arm_that_can_reach_claimed():
    """The thunk form exists so callers can skip a per-LO query; prove it is skipped."""

    calls: list[int] = []

    def _claim() -> bool:
        calls.append(1)
        return True

    assert (
        classify_measurement_state(
            evidence_mass=2.0, min_evidence_mass=MIN_MASS, claim_present=_claim
        )
        == MEASURED
    )
    assert calls == []
    assert (
        classify_measurement_state(
            evidence_mass=0.0, min_evidence_mass=MIN_MASS, claim_present=_claim
        )
        == CLAIMED
    )
    assert calls == [1]


def test_negative_mass_cannot_manufacture_a_label():
    assert (
        classify_measurement_state(evidence_mass=-3.0, min_evidence_mass=MIN_MASS) == UNKNOWN
    )


# -- the vocabulary is closed ------------------------------------------------


def test_vocabulary_is_closed_and_unknown_labels_are_rejected():
    """An unrecognised label raises rather than being passed through to a render site."""

    assert MEASUREMENT_STATES == (MEASURED, INFERRED, CLAIMED, UNKNOWN)
    for state in MEASUREMENT_STATES:
        assert require_measurement_state(state) == state
    # ``unknown`` is the abstention arm and IS a member; everything else is a bug.
    for rejected in ("solid", "unexamined", "Measured", "", "estimated", "inferred "):
        with pytest.raises(ValueError, match="unknown measurement state"):
            require_measurement_state(rejected)


def test_emission_boundary_rejects_a_label_outside_the_vocabulary(tmp_path):
    """The gate is load-bearing, not decorative: the wire refuses a bad label.

    ``GridCell.as_dict`` is where the label leaves Python for the UI. Nothing
    persists a provenance label, so an out-of-vocabulary value can only come
    from code — and silently forwarding it is how an inference would end up
    rendered as a measurement.
    """

    vault, _paths, repository = _loaded(tmp_path)
    cell = capability_grid(vault, repository, LO_ID).cells[0]
    assert cell.as_dict()["measurement_state"] == INFERRED

    bogus = replace(cell, measurement_state="probably_fine")
    with pytest.raises(ValueError, match="unknown measurement state"):
        bogus.as_dict()


def test_every_classified_label_is_in_the_vocabulary():
    for mass in (None, -1.0, 0.0, 0.2, MIN_MASS, 5.0):
        for count in (0, 1, 9):
            for claim in (False, True):
                state = classify_measurement_state(
                    evidence_mass=mass,
                    min_evidence_mass=MIN_MASS,
                    mastery_evidence_count=count,
                    claim_present=claim,
                )
                assert require_measurement_state(state) == state


# -- the motivating case: the goal surface's pooled prediction ----------------


def _loaded(tmp_path: Path, *, seed: bool = True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = seed_due_item(paths) if seed else Repository(paths.sqlite_path)
    return load_vault(vault_root), paths, repository


def _projection(report):
    return next(facet for facet in report.facets if facet.facet_id == FACET_ID)


def _seed_aggregate_facet(repository, *, mean: float, mass: float) -> None:
    with repository.connection() as connection:
        repository._upsert_facet_recall_state(
            connection,
            {
                "learning_object_id": LO_ID,
                "facet_id": FACET_ID,
                "practice_item_id": None,
                "recall_alpha": mean * 10.0,
                "recall_beta": (1.0 - mean) * 10.0,
                "recall_mean": mean,
                "recall_variance": 0.01,
                "independent_evidence_mass": mass,
                "raw_coverage_mass": mass,
                "last_attempt_at": "2026-05-16T12:00:00Z",
                "last_error_at": None,
                "consecutive_failures": 0,
                "algorithm_version": ALGORITHM_VERSION,
                "created_at": NOW_ISO,
                "updated_at": NOW_ISO,
            },
        )


def _insert_claim(repository) -> None:
    repository.insert_learner_claim(
        {
            "id": "claim_svd_known",
            "claim_type": "self_rating",
            "scope_type": "learning_object",
            "scope_id": LO_ID,
            "evidence_family": FACET_ID,
            "claimed_level": 0.9,
            "prior_pseudo_count": 4.0,
            "source": "manual_cli",
        },
        clock=FrozenClock(NOW),
    )


def test_pooled_prediction_that_rendered_unlabelled_now_carries_inferred(tmp_path):
    """The §B2 defect: no facet evidence, a real LO backbone, ``unexamined`` on
    the diagnostic axis — and a Ready number that used to render exactly like a
    measurement. The provenance axis now says ``inferred``, and the diagnostic
    axis is unchanged."""

    vault, _paths, repository = _loaded(tmp_path)
    report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
    projection = _projection(report)

    assert projection.evidence_mass == 0.0
    assert projection.label == "unexamined"       # unchanged diagnostic bucket
    assert projection.measurement_state == INFERRED
    # And the label qualifies the number actually rendered: the pooled prediction,
    # not the (absent) measured recall.
    assert projection.current_recall is None
    assert projection.predicted_current == pytest.approx(
        predicted_facet_recall(0.0, 1, None, 0.0, BLEND)
    )


def test_measured_label_on_a_facet_with_evidence_over_the_gate(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.95, mass=2.0)

    projection = _projection(goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW)))
    assert projection.measurement_state == MEASURED
    assert projection.label == "solid"


def test_sub_threshold_direct_mass_is_inferred_not_measured(tmp_path):
    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.8, mass=0.1)

    projection = _projection(goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW)))
    assert projection.measurement_state == INFERRED
    # Same mass gate as the diagnostic axis: below it, nothing reads as solid.
    assert projection.label == "unexamined"
    assert projection.certified is False


def test_unknown_label_when_there_is_nothing_at_all(tmp_path):
    vault, paths, repository = _loaded(tmp_path, seed=False)
    projection = _projection(goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW)))
    assert projection.measurement_state == UNKNOWN
    assert projection.label == "unexamined"


def test_claimed_label_when_only_a_learner_claim_covers_the_cell(tmp_path):
    """§E2: the claim moves the label off ``unknown`` and nothing else."""

    vault, paths, repository = _loaded(tmp_path, seed=False)
    _insert_claim(repository)
    # A claim-seeded mastery row is still zero-evidence, so there is nothing to
    # pool from: the honest label is ``claimed``, not ``inferred``.
    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=2.2,
            logit_variance=0.25,
            evidence_count=0,
            last_evidence_at=None,
            algorithm_version=ALGORITHM_VERSION,
            updated_at=NOW_ISO,
        )
    )

    projection = _projection(goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW)))
    assert projection.measurement_state == CLAIMED
    assert projection.label == "unexamined"
    assert projection.certified is False


def test_capability_grid_labels_the_ready_number(tmp_path):
    """§B2 names this surface: the grid renders Ready for untested cells."""

    vault, _paths, repository = _loaded(tmp_path)
    grid = capability_grid(vault, repository, LO_ID)
    assert grid.cells
    for cell in grid.cells:
        # No facet evidence, but an evidenced LO backbone -> the Ready number is
        # an inference, and the cell says so even though it is untested.
        assert cell.tested is False
        assert cell.measurement_state == INFERRED
        assert cell.as_dict()["measurement_state"] == INFERRED

    _seed_aggregate_facet(repository, mean=0.9, mass=2.0)
    relabelled = capability_grid(vault, repository, LO_ID)
    assert {cell.measurement_state for cell in relabelled.cells} == {MEASURED}
    # The certification axis is untouched by the provenance axis: facet-level
    # recall mass is not capability-matched credit.
    assert all(cell.demonstrated is False for cell in relabelled.cells)


# -- §B2's "revert if": nothing written or certified reads the label ----------


def _db_snapshot(repository) -> str:
    with repository.connection() as connection:
        tables = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        ]
        parts: list[str] = []
        for table in tables:
            rows = connection.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608
            parts.append(f"{table}={sorted(repr(tuple(row)) for row in rows)!r}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def test_labelling_writes_nothing(tmp_path):
    """Rendering a label is a read. The whole database is byte-identical after."""

    vault, _paths, repository = _loaded(tmp_path)
    _seed_aggregate_facet(repository, mean=0.7, mass=0.2)
    _insert_claim(repository)
    before = _db_snapshot(repository)

    grid = capability_grid(vault, repository, LO_ID)
    assert {cell.measurement_state for cell in grid.cells} == {INFERRED}
    assert _db_snapshot(repository) == before


def test_label_does_not_move_a_threshold_a_number_or_a_certification(tmp_path):
    """The provenance axis varies while every decided quantity stays put.

    ``certified`` remains ``label == "solid"``, ``on_track`` remains the
    attainment comparison, and ``predicted_current`` remains exactly
    ``predicted_facet_recall`` over the same inputs — for every label.
    """

    seen: set[str] = set()
    for case, seed, mass, claim in (
        ("unknown", False, None, False),
        ("claimed", False, None, True),
        ("inferred", True, 0.1, False),
        ("measured", True, 2.0, False),
    ):
        vault, _paths, repository = _loaded(tmp_path / case, seed=seed)
        if mass is not None:
            _seed_aggregate_facet(repository, mean=0.9, mass=mass)
        if claim:
            _insert_claim(repository)
        report = goal_report(vault, repository, vault.goals[0], clock=FrozenClock(NOW))
        projection = _projection(report)
        seen.add(projection.measurement_state)

        mastery = repository.mastery_state(LO_ID)
        assert projection.predicted_current == pytest.approx(
            predicted_facet_recall(
                mastery.logit_mean if mastery is not None else None,
                mastery.evidence_count if mastery is not None else 0,
                projection.current_recall,
                projection.evidence_mass,
                BLEND,
            )
        )
        assert projection.certified is (projection.label == "solid")
        assert projection.on_track is (
            projection.predicted_at_horizon >= vault.goals[0].target_recall
            and projection.label != "known_gap"
        )
        # Coverage/attainment counters read the diagnostic axis, never this one.
        assert report.certified_count == sum(1 for f in report.facets if f.label == "solid")
        assert report.examined_count == sum(1 for f in report.facets if f.label != "unexamined")

    assert seen == {UNKNOWN, CLAIMED, INFERRED, MEASURED}


def test_no_certification_or_write_path_reads_the_label():
    """§B2's audit: the label is display-only, so its blast radius is enumerated.

    A canary over the source tree — wiring the vocabulary into a new module has
    to be a deliberate act, and it may never be a module that certifies or
    persists belief.
    """

    source_root = Path(__file__).resolve().parents[1] / "src"
    referencing = {
        path.relative_to(source_root).as_posix()
        for path in source_root.rglob("*.py")
        if "measurement_state" in path.read_text(encoding="utf-8")
    }
    assert referencing == {
        "learnloop/learner/measurement_state.py",   # the vocabulary itself
        "learnloop/learner/capability_grid.py",     # read-only grid projection
        "learnloop/goals/goal_projection.py",       # read-only goal report
        "learnloop_sidecar/handlers/goals.py",       # DTO passthrough to the UI
    }
    # Named explicitly: the paths that decide certification and the paths that
    # write belief state must not appear above.
    for certifying in (
        "learnloop/goals/certification.py",
        "learnloop/goals/goal_certification.py",
        "learnloop/attempts/attempts.py",
        "learnloop/learner/mastery.py",
        "learnloop/learner/recall_coverage.py",
    ):
        assert (source_root / certifying).exists()
        assert certifying not in referencing
