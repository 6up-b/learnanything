"""Measurement §5.2 (Stage 3.3): the coverage denominator is the contract frontier.

The defect being removed: `covered_required_fraction`'s denominator was the union
of the LO's active items' `evidence_facets`, and it feeds the mastery variance
floor. Authoring more items therefore LOWERED displayed mastery with no change in
what the learner knew — the floor was punishing the learner for the system's
authoring activity. A cell nobody's goal requires is not a measurement debt.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.learner.facet_diagnostics import (
    COVERAGE_DENOMINATOR_VERSION,
    INFERRED_CELL_COVERAGE_DISCOUNT,
    contract_frontier,
    covered_required_fraction,
    variance_floor,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version


def _declare_blueprint(paths, *, cells: list[tuple[str, str]]) -> None:
    """Give the LO a blueprint recipe requiring exactly these (facet, capability)."""

    path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    payload = read_yaml(path)
    payload["blueprints"] = [
        {
            "id": "bp_svd",
            "weight": 1.0,
            "recipes": [
                {
                    "id": "recipe_svd",
                    "composition": "conjunctive",
                    "all_of": [
                        {"facet": facet, "capability": capability, "modality": "hard"}
                        for facet, capability in cells
                    ],
                }
            ],
        }
    ]
    write_yaml(path, payload)


def _add_item(paths, item_id: str, facets: list[str]) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": facets,
            "evidence_weights": {facet: 1.0 for facet in facets},
            "prompt": f"Prompt for {item_id}.",
            "expected_answer": "An answer.",
            "difficulty": 0.5,
            "tags": [],
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct."}
                ],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def test_frontier_is_the_blueprint_cells_not_the_authored_items(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _declare_blueprint(
        paths, cells=[("recall", "retrieval"), ("recall", "transfer")]
    )
    # An item measuring a facet no blueprint requires: authoring history, not an
    # obligation. It must not enter the denominator.
    _add_item(paths, "pi_extra_facet", ["unrequired_facet"])
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    cells, authored = contract_frontier(vault, "lo_svd_definition", repository)
    assert authored is True
    assert cells == {("recall", "retrieval"), ("recall", "transfer")}
    assert not any(facet == "unrequired_facet" for facet, _capability in cells)


def test_declaring_a_contract_with_no_instruments_is_zero_not_one(tmp_path):
    """The vacuous case §5.2 names: full coverage claimed from zero measurement.

    The old denominator was item-derived, so an LO that declares obligations but
    has no items reported `1.0` — and the variance floor, which exists to say "you
    should be less certain about what you have not measured", said the opposite.
    """

    paths = create_basic_vault(tmp_path / "vault")
    _declare_blueprint(
        paths, cells=[("never_measured_a", "retrieval"), ("never_measured_b", "transfer")]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    value, trace = covered_required_fraction(
        vault, repository, learning_object_id="lo_svd_definition"
    )
    assert value == 0.0
    assert trace["denominator_basis"].startswith("contract_frontier")
    assert len(trace["uncovered_cells"]) == 2
    assert trace["measured_cells"] == []
    # And the floor now says what it means: maximum uncertainty, not minimum.
    assert variance_floor(vault.config, value) > variance_floor(vault.config, 1.0)


def test_legacy_vault_without_blueprints_keeps_current_behaviour(tmp_path):
    """§5.2 is strictly additive: no blueprint components ⇒ nothing changes."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    cells, authored = contract_frontier(vault, "lo_svd_definition", repository)
    assert authored is False

    value, trace = covered_required_fraction(
        vault, repository, learning_object_id="lo_svd_definition"
    )
    assert trace["denominator_basis"] == "legacy_item_facets"
    # The legacy branch's own reading, unchanged: the fixture LO's item declares
    # `recall`, which carries no evidence mass yet.
    assert value == 0.0
    assert trace["required_facets"] == ["recall"]


def test_an_lo_with_no_facets_at_all_still_reports_one(tmp_path):
    """The legacy "nothing required ⇒ 1.0" arm is preserved verbatim: a vault
    with no obligations recorded anywhere is not a measurement debt either."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    value, trace = covered_required_fraction(
        vault, repository, learning_object_id="lo_missing_entirely"
    )
    assert value == 1.0
    assert trace["denominator_basis"] == "legacy_item_facets"


def test_capability_axis_distinguishes_the_cells(tmp_path):
    """The 72% lever: evidence at `retrieval` does not close a `transfer` cell."""

    paths = create_basic_vault(tmp_path / "vault")
    # The per-cell ledger only exists on canonical (mvp-0.7+) vaults.
    set_algorithm_version(paths, "mvp-0.7")
    _declare_blueprint(
        paths, cells=[("recall", "retrieval"), ("recall", "transfer")]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    threshold = vault.config.recall_coverage.min_facet_evidence_mass
    repository.replace_canonical_facet_state(
        recall_rows=[],
        capability_rows=[
            {
                "facet_id": "recall",
                "capability": "retrieval",
                "direct_positive_mass": threshold + 1.0,
                "independent_surface_groups": ["group_a"],
            }
        ],
        algorithm_version="test",
        clock=FrozenClock(NOW),
    )

    value, trace = covered_required_fraction(
        vault, repository, learning_object_id="lo_svd_definition"
    )
    assert trace["denominator_basis"] == "contract_frontier"
    assert value == pytest.approx(0.5)
    assert trace["measured_cells"] == [
        {"facet": "recall", "capability": "retrieval"}
    ]
    assert trace["uncovered_cells"] == [
        {"facet": "recall", "capability": "transfer"}
    ]


def test_a_canonical_vault_with_no_ledger_rows_credits_no_cell(tmp_path):
    """The fallback is gated on whether the vault SUPPORTS the per-cell ledger,
    not on whether rows happen to exist. Keying on row presence would credit a
    `transfer` cell out of facet-level mass earned at `retrieval`, which is the
    exact error the capability axis exists to stop."""

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    _declare_blueprint(
        paths, cells=[("recall", "retrieval"), ("recall", "transfer")]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    threshold = vault.config.recall_coverage.min_facet_evidence_mass

    value, trace = covered_required_fraction(
        vault,
        repository,
        learning_object_id="lo_svd_definition",
        # Facet-level mass well over threshold, with no capability ledger rows
        # behind it at all.
        aggregate_facet_recall={
            "recall": {"independent_evidence_mass": threshold + 10.0}
        },
    )
    assert trace["denominator_basis"] == "contract_frontier"
    assert value == 0.0
    assert trace["measured_cells"] == []


def test_inference_relieves_the_floor_at_a_discount(tmp_path):
    """§5.2: an inferred cell is not a measured cell, but it is also not an
    unexamined one, and the variance floor should say so."""

    paths = create_basic_vault(tmp_path / "vault")
    _declare_blueprint(
        paths, cells=[("recall", "retrieval"), ("recall", "transfer")]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    baseline, _trace = covered_required_fraction(
        vault, repository, learning_object_id="lo_svd_definition"
    )
    value, trace = covered_required_fraction(
        vault,
        repository,
        learning_object_id="lo_svd_definition",
        inferred_cells={("recall", "transfer"): 0.9},
    )
    assert baseline == 0.0
    assert value == pytest.approx(INFERRED_CELL_COVERAGE_DISCOUNT / 2)
    assert trace["inferred_cells"] == [
        {"facet": "recall", "capability": "transfer"}
    ]
    # Inferred is never counted as measured.
    assert trace["measured_cells"] == []
    assert variance_floor(vault.config, value) < variance_floor(vault.config, baseline)


def test_the_denominator_change_is_narrated_as_one_recalibration(tmp_path):
    """Displayed mastery moves with no new evidence, so the learner is told —
    once, through the existing "estimates recomputed" entry (A6's machinery),
    naming the coverage denominator rather than blaming an algorithm rewrite."""

    from learnloop.learner.learner_review_feed import build_learner_review_feed

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    # A pre-existing rebuild that predates the coverage version, having replayed
    # evidence the learner already saw.
    repository.record_derived_state_rebuild(
        scope="all",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=1,
        replayed_attempts=3,
        canonical_projection_version="canonical_projection_v4_item_declared_capability",
        clock=FrozenClock(NOW),
    )
    repository.record_derived_state_rebuild(
        scope="all",
        learning_object_ids=["lo_svd_definition"],
        algorithm_version=vault.config.algorithms.algorithm_version,
        rebuilt_learning_objects=1,
        replayed_attempts=3,
        canonical_projection_version="canonical_projection_v4_item_declared_capability",
        coverage_denominator_version=COVERAGE_DENOMINATOR_VERSION,
        clock=FrozenClock(NOW),
    )

    changes = repository.derived_state_rebuild_version_changes()
    coverage_boundaries = [
        change
        for change in changes
        if change.get("coverage_denominator_version") == COVERAGE_DENOMINATOR_VERSION
    ]
    assert len(coverage_boundaries) == 1
    assert coverage_boundaries[0]["previous_coverage_denominator_version"] is None
    assert (
        coverage_boundaries[0]["algorithm_version"]
        == coverage_boundaries[0]["previous_algorithm_version"]
    ), "the algorithm did not change; only the denominator did"

    feed = build_learner_review_feed(vault, repository)
    entries = [
        entry
        for entry in feed["changelog"]
        if entry["kind"] == "recalibration"
        and entry.get("coverage_denominator_version") == COVERAGE_DENOMINATOR_VERSION
    ]
    assert len(entries) == 1
