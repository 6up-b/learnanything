"""Projection v6 — absent evidence is not an observation (stabilization A3).

Two changes under one version bump, both directions of the same honesty rule:

* A criterion with NO grading-evidence row produces NO outcome. Before v6 a
  missing row read as fraction 0.0 -> passed=False, so absent data banked
  negative mass, advanced consecutive-failure runs, and could open
  unresolved-cause factors — confident wrongness manufactured from nothing.
  A PRESENT row with zero points is unchanged: that is an observed failure.
* The facet evidence timeline applies the same mvp-0.8 response-level
  reliability discount the canonical projection banks (shared helper
  ``p0_effective_evidence_mass``), so the learner-facing Demonstrated curve
  cannot over-report the ledger under the shipping algorithm version.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.learner.facet_evidence_timeline import facet_evidence_timeline
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets

CLOCK = FrozenClock(NOW)

ITEM = "pi_polarity_two_step"
F_A = "f_polarity_a"
F_B = "f_polarity_b"

FACETS = [
    {"id": F_A, "kind": "definition", "claim": "Facet A claim."},
    {"id": F_B, "kind": "procedure_contract", "claim": "Facet B claim."},
    {"id": "recall", "kind": "definition", "claim": "SVD recall definition."},
]


def _write_two_criterion_item(paths) -> None:
    """Two independent criteria on two facets — no dependency coupling, so a
    deleted row for one criterion cannot affect the other through localization."""

    write_yaml(
        paths.practice_item_path("linear-algebra", ITEM),
        {
            "schema_version": 1,
            "id": ITEM,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "constructed_response",
            "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
            "evidence_facets": [F_A, F_B],
            "evidence_weights": {F_A: 1.0, F_B: 1.0},
            "capability": "procedure_execution",
            "prompt": "State the claim, then apply it.",
            "expected_answer": "Both steps.",
            "difficulty": 0.5,
            "tags": [],
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "c_state",
                        "points": 2,
                        "description": "States the claim.",
                        "targets": [
                            {"facet": F_A, "capability": "retrieval", "role": "primary"}
                        ],
                    },
                    {
                        "id": "c_apply",
                        "points": 2,
                        "description": "Applies it.",
                        "targets": [
                            {
                                "facet": F_B,
                                "capability": "procedure_execution",
                                "role": "primary",
                            }
                        ],
                    },
                ],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _vault(tmp_path, algorithm_version="mvp-0.7"):
    paths = create_basic_vault(tmp_path / "vault")
    write_facets(paths, FACETS)
    _write_two_criterion_item(paths)
    set_algorithm_version(paths, algorithm_version)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository


def _attempt(vault, repository, points):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=ITEM,
            learner_answer_md="Both steps worked through.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points=points, fatal_errors=[], confidence=4),
        clock=CLOCK,
    )


def _cells(repository):
    return {
        (cell.facet_id, cell.capability): cell
        for cell in repository.facet_capability_evidence_all()
    }


def _delete_evidence(repository, attempt_id, criterion_id=None):
    with repository.connection() as connection:
        if criterion_id is None:
            connection.execute(
                "DELETE FROM grading_evidence WHERE attempt_id = ?", (attempt_id,)
            )
        else:
            connection.execute(
                "DELETE FROM grading_evidence WHERE attempt_id = ? AND criterion_id = ?",
                (attempt_id, criterion_id),
            )


def _negative_mass(repository) -> float:
    return sum(
        cell.direct_negative_mass + cell.embedded_negative_mass
        for cell in repository.facet_capability_evidence_all()
    )


# -- The polarity split -------------------------------------------------------


def test_present_zero_point_row_banks_an_observed_failure(tmp_path):
    """The unchanged half: a graded zero is a real failure and must keep
    banking negative evidence — v6 narrows only the ABSENT-row case."""

    vault, repository = _vault(tmp_path)
    _attempt(vault, repository, {"c_state": 0, "c_apply": 0})

    assert _negative_mass(repository) > 0.0
    failures = [
        row
        for row in repository.canonical_facet_recall_states()
        if row.consecutive_failures > 0
    ]
    assert failures, "an observed zero must advance the failure run"


def test_missing_evidence_rows_bank_nothing(tmp_path):
    """Deleting an attempt's grading evidence and re-projecting must leave no
    trace of it: no negative mass, no failure runs, no unresolved-cause
    factors, and a timeline that shows nothing rather than a phantom failure.

    Pre-v6 this banked a full-rubric failure (fraction 0.0 on every criterion)
    for an attempt nobody graded.
    """

    vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, {"c_state": 2, "c_apply": 2})
    _delete_evidence(repository, result.attempt_id)

    project_canonical_facet_state(vault, repository, clock=CLOCK)

    assert _negative_mass(repository) == pytest.approx(0.0)
    assert all(
        row.consecutive_failures == 0
        for row in repository.canonical_facet_recall_states()
    )
    assert not repository.open_unresolved_cause_observation_ids()
    for facet in (F_A, F_B):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        assert final == pytest.approx(0.0)


def test_partially_graded_attempt_credits_only_the_graded_criterion(tmp_path):
    """One criterion's row deleted: the graded facet keeps its positive
    evidence, the ungraded facet gets neither credit nor blame, and both
    folds agree per facet."""

    vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, {"c_state": 2, "c_apply": 2})
    _delete_evidence(repository, result.attempt_id, criterion_id="c_apply")

    project_canonical_facet_state(vault, repository, clock=CLOCK)
    cells = _cells(repository)

    graded = cells[(F_A, "retrieval")]
    assert graded.direct_positive_mass > 0.0
    assert graded.direct_negative_mass == pytest.approx(0.0)

    # The ungraded criterion's facet: no cell at all — absent, not failed.
    assert (F_B, "procedure_execution") not in cells
    assert all(
        row.consecutive_failures == 0
        for row in repository.canonical_facet_recall_states()
    )

    banked: dict[str, float] = {}
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    for facet in (F_A, F_B):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        assert final == pytest.approx(banked.get(facet, 0.0), abs=1e-12)


# -- mvp-0.8 fold parity -------------------------------------------------------


def test_p0_timeline_matches_banked_ledger_including_a6_supporting_credit(tmp_path):
    """Fold agreement under the shipping version, with the A6 channel live.

    Uses a conjunctive criterion (primary + supporting target) plus a recorded
    trace observation, so the comparison covers the embedded-credit path and
    the response-level reliability discount together — the exact combination
    the mvp-0.7-pinned guard never saw.
    """

    paths = create_basic_vault(tmp_path / "vault")
    write_facets(paths, FACETS)
    write_yaml(
        paths.practice_item_path("linear-algebra", ITEM),
        {
            "schema_version": 1,
            "id": ITEM,
            "learning_object_id": "lo_svd_definition",
            "subjects": None,
            "practice_mode": "constructed_response",
            "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
            "evidence_facets": [F_A, F_B],
            "evidence_weights": {F_A: 1.0, F_B: 1.0},
            "capability": "procedure_execution",
            "prompt": "Apply the claim, showing the algebra.",
            "expected_answer": "Worked application.",
            "difficulty": 0.5,
            "tags": [],
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "c_apply",
                        "points": 4,
                        "description": "Applies it, consuming the stated claim.",
                        "targets": [
                            {
                                "facet": F_B,
                                "capability": "procedure_execution",
                                "role": "primary",
                            },
                            {"facet": F_A, "capability": "retrieval", "role": "supporting"},
                        ],
                    },
                ],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    set_algorithm_version(paths, "mvp-0.8")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)

    result = _attempt(vault, repository, {"c_apply": 4})
    repository.insert_trace_exercised_facets(
        result.attempt_id,
        [
            {
                "facet_id": F_A,
                "observation_scope": "opportunistic",
                "evidence": "the trace restates the claim while applying it",
            }
        ],
        clock=CLOCK,
    )
    project_canonical_facet_state(vault, repository, clock=CLOCK)

    banked: dict[str, float] = {}
    embedded_positive = 0.0
    for cell in repository.facet_capability_evidence_all():
        banked[cell.facet_id] = banked.get(cell.facet_id, 0.0) + cell.certification_credit
    for cell in repository.facet_capability_evidence_all():
        embedded_positive += cell.embedded_positive_mass
    # The scenario is real: reliability-discounted direct credit banked, and the
    # A6-licensed supporting target actually flowed through the embedded channel.
    assert banked.get(F_B, 0.0) > 0.0
    assert embedded_positive > 0.0

    for facet in (F_A, F_B):
        series = facet_evidence_timeline(vault, repository, facet)
        final = series[-1].demonstrated if series else 0.0
        assert final == pytest.approx(banked.get(facet, 0.0), abs=1e-12), (
            f"{facet} timeline={final} banked={banked.get(facet, 0.0)}"
        )
