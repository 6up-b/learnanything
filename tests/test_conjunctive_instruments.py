"""Meas §3.A1 conjunctive items + §3.A6 opportunistic trace evidence.

Implementation-plan items 6.1 / 6.2, validated against
``spec_measurement_efficiency_v1.md`` §10.

The one thing A1 buys is cells-per-question: a criterion may now declare that
the step it owns *consumes* a facet (``supporting``) rather than only that it
*is* one (``primary``), so a single capstone attempt can credit several ledger
cells. The one thing A1 manufactures is positive smearing — the passed-facet
firewall covers only the negative direction, and nobody objects to being told
they know something. Guard 1 (supporting credit requires an A6 trace
observation) and guard 2 (the embedded-share cap) are what bound it, and the
end-to-end projection tests below are written so that a regression in either
guard shows up as *credit appearing where no trace justified it*.
"""

from __future__ import annotations

import re
import sqlite3
from types import SimpleNamespace

import pytest

from learnloop.clock import FrozenClock
from learnloop.config import EvidenceCertificationConfig, TraceEvidenceConfig
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.canonical_projection import (
    CANONICAL_PROJECTION_VERSION,
    project_canonical_facet_state,
)
from learnloop.services.capability_mapping import compile_criterion_targets
from learnloop.services.conjunctive_items import (
    CONJUNCTIVE_STRENGTH_CEILING,
    UNEXERCISED_SUPPORTING_TARGET,
    cap_embedded_credit,
    classify_item_shape,
    conjunctive_fit,
    partition_supporting_targets,
)
from learnloop.services.exam_pool import _item_components
from learnloop.services.grading import (
    MAX_EXERCISED_FACETS_PER_ATTEMPT,
    _validated_exercised_facets,
)
from learnloop.services.proposals import _criterion_target_errors
from learnloop.services.state_sync import sync_vault_state
from learnloop.services.trace_evidence import (
    decide_elicitation,
    elicitation_reward,
    trace_evidence_report,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.models import CriterionTarget, PracticeItem, Rubric, RubricCriterion
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets

CAPSTONE = "pi_conj_capstone"
SETUP = "f_setup"
SOLVE = "f_solve"
CHECK = "f_check"
ALGEBRA = "f_algebra"

FACETS = [
    {"id": SETUP, "kind": "definition", "claim": "Set up the decomposition."},
    {"id": SOLVE, "kind": "procedure_contract", "claim": "Compute the factors."},
    {"id": CHECK, "kind": "procedure_contract", "claim": "Check the reconstruction."},
    {"id": ALGEBRA, "kind": "procedure_contract", "claim": "Manipulate the algebra."},
    {"id": "recall", "kind": "definition", "claim": "SVD recall definition."},
]


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _target(facet: str, capability: str = "procedure_execution", role: str = "primary") -> dict:
    return {"facet": facet, "capability": capability, "role": role}


def _conjunctive_criteria(*, supporting: bool = True) -> list[dict]:
    """Three chained steps; step 2 also *consumes* an algebra facet."""

    solve_targets = [_target(SOLVE)]
    if supporting:
        solve_targets.append(_target(ALGEBRA, role="supporting"))
    return [
        {
            "id": "c_setup",
            "points": 2,
            "description": "Sets the decomposition up correctly.",
            "targets": [_target(SETUP)],
        },
        {
            "id": "c_solve",
            "points": 1,
            "description": "Computes the factors.",
            "depends_on": ["c_setup"],
            "targets": solve_targets,
        },
        {
            "id": "c_check",
            "points": 1,
            "description": "Verifies the reconstruction.",
            "depends_on": ["c_solve"],
            "targets": [_target(CHECK, capability="method_selection")],
        },
    ]


def _write_item(paths, item_id: str, *, criteria: list[dict], facets: list[str], **overrides) -> None:
    payload = {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": "lo_svd_definition",
        "subjects": None,
        "practice_mode": "constructed_response",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": facets,
        "evidence_weights": {facet: 1.0 for facet in facets},
        "capability": "procedure_execution",
        "prompt": "Decompose the matrix and verify.",
        "expected_answer": "U Sigma V^T, verified by reconstruction.",
        "difficulty": 0.6,
        "tags": [],
        "grading_rubric": {
            "max_points": 4,
            "criteria": criteria,
            "fatal_errors": [],
        },
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    payload.update(overrides)
    write_yaml(paths.practice_item_path("linear-algebra", item_id), payload)


def _set_max_embedded_share(paths, share: float) -> None:
    toml_path = paths.root / "learnloop.toml"
    text = toml_path.read_text(encoding="utf-8")
    updated, count = re.subn(
        r"max_groups_per_attempt = 3",
        f"max_groups_per_attempt = 3\nmax_embedded_credit_share = {share}",
        text,
        count=1,
    )
    assert count == 1
    toml_path.write_text(updated, encoding="utf-8")


def _vault(tmp_path, *, criteria=None, max_embedded_share: float | None = None, facets=None):
    """A canonical (mvp-0.7) vault holding one conjunctive capstone item."""

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(paths, FACETS)
    _write_item(
        paths,
        CAPSTONE,
        criteria=_conjunctive_criteria() if criteria is None else criteria,
        facets=facets if facets is not None else [SETUP, SOLVE, CHECK, ALGEBRA],
    )
    if max_embedded_share is not None:
        _set_max_embedded_share(paths, max_embedded_share)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, vault, repository


def _attempt(vault, repository, *, points: dict[str, float], item_id: str = CAPSTONE):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="Full worked derivation with a reconstruction check.",
            attempt_type="independent_attempt",
        ),
        SelfGradeInput(criterion_points=points, fatal_errors=[], confidence=5),
        clock=FrozenClock(NOW),
    )


def _cells(repository) -> dict[tuple[str, str], object]:
    return {
        (cell.facet_id, cell.capability): cell
        for cell in repository.facet_capability_evidence_all()
    }


def _record_trace(repository, attempt_id: str, facet: str, *, scope: str = "opportunistic", **kw) -> int:
    return repository.insert_trace_exercised_facets(
        attempt_id,
        [{"facet_id": facet, "observation_scope": scope, "evidence": "the trace shows it", **kw}],
        clock=FrozenClock(NOW),
    )


def _pi(**overrides) -> PracticeItem:
    data = {
        "id": "pi_1",
        "learning_object_id": "lo_1",
        "practice_mode": "constructed_response",
        "evidence_facets": ["facet_a", "facet_b"],
        "prompt": "P",
        "expected_answer": "A",
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    data.update(overrides)
    return PracticeItem(**data)


# ---------------------------------------------------------------------------
# 1. compile_criterion_targets: authored targets verbatim, legacy unchanged
# ---------------------------------------------------------------------------


def test_authored_targets_compile_verbatim_including_supporting():
    authored = [
        CriterionTarget(facet="facet_a", capability="procedure_execution", role="primary"),
        CriterionTarget(facet="facet_b", capability="method_selection", role="supporting"),
    ]
    criterion = RubricCriterion(id="c1", points=2, description="x", targets=authored)
    targets = compile_criterion_targets(_pi(capability="retrieval"), criterion)
    assert targets == authored
    # The item's own declared capability does NOT override an authored target:
    # A1's whole point is that one item observes several rungs.
    assert [t.capability for t in targets] == ["procedure_execution", "method_selection"]


def test_criterion_without_targets_still_compiles_to_all_primary_at_the_item_capability():
    """Legacy behaviour is byte-identical: A1 is strictly additive."""

    criterion = RubricCriterion(id="c1", points=4, description="x")
    item = _pi(capability="method_selection")
    targets = compile_criterion_targets(item, criterion)
    assert [(t.facet, t.capability, t.role) for t in targets] == [
        ("facet_a", "method_selection", "primary"),
        ("facet_b", "method_selection", "primary"),
    ]


# ---------------------------------------------------------------------------
# 2. The core end-to-end projection: a pass credits every primary cell, and a
#    supporting cell only where A6 saw the facet exercised.
# ---------------------------------------------------------------------------


def test_full_pass_credits_every_primary_cell_and_banks_unexercised_supporting_mass(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    cells = _cells(repository)
    # One attempt, three primary cells at two capabilities: this is the whole
    # cells-per-question argument of §0, measured.
    for key in (
        (SETUP, "procedure_execution"),
        (SOLVE, "procedure_execution"),
        (CHECK, "method_selection"),
    ):
        assert key in cells, key
        assert cells[key].direct_positive_mass > 0.0
        assert cells[key].direct_certification_credit > 0.0
        assert cells[key].embedded_certification_credit == pytest.approx(0.0)
        assert cells[key].certification_credit > 0.0

    # The supporting cell has NO trace evidence behind it, so it confers nothing
    # — and the claim is recorded rather than dropped silently.
    supporting = cells[(ALGEBRA, "procedure_execution")]
    assert supporting.unexercised_supporting_mass > 0.0
    assert supporting.embedded_positive_mass == pytest.approx(0.0)
    assert supporting.embedded_certification_credit == pytest.approx(0.0)
    assert supporting.certification_credit == pytest.approx(0.0)
    assert supporting.independent_surface_groups == []


def test_trace_evidence_turns_the_supporting_target_into_embedded_credit(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    _record_trace(repository, result.attempt_id, ALGEBRA)
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    supporting = _cells(repository)[(ALGEBRA, "procedure_execution")]
    assert supporting.embedded_positive_mass > 0.0
    assert supporting.unexercised_supporting_mass == pytest.approx(0.0)
    assert supporting.embedded_certification_credit > 0.0
    # Guard 2: the cell's history is ENTIRELY embedded, so at the default 0.5
    # share it certifies nothing. Inferred, not demonstrated.
    assert supporting.direct_certification_credit == pytest.approx(0.0)
    assert supporting.certification_credit == pytest.approx(0.0)


def test_a_trace_row_for_a_different_facet_does_not_license_the_supporting_target(tmp_path):
    """Guard 1 matches on the facet the criterion authored, not "any A6 row"."""

    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    _record_trace(repository, result.attempt_id, SETUP, scope="declared")
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    supporting = _cells(repository)[(ALGEBRA, "procedure_execution")]
    assert supporting.embedded_positive_mass == pytest.approx(0.0)
    assert supporting.unexercised_supporting_mass > 0.0


def test_trace_evidence_report_surfaces_unexercised_cells_and_abstains_on_concentration(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    report = trace_evidence_report(repository)
    assert report["opportunistic_observations"] == 0
    # Below a handful of observations the statistic abstains rather than
    # reporting 1.0 from one row.
    assert report["opportunistic_concentration"] is None
    assert report["unexercised_supporting_cell_count"] == 1
    assert report["unexercised_supporting_cells"][0]["facet_id"] == ALGEBRA


def test_the_projection_version_names_the_supporting_trace_rule():
    """The guards move stored belief with no new learner evidence, so the
    version bump is what routes it through one recalibration boundary."""

    assert CANONICAL_PROJECTION_VERSION == "canonical_projection_v5_supporting_requires_trace"


# ---------------------------------------------------------------------------
# 3. A conjunctive failure localizes: only the diverged facet takes the negative
# ---------------------------------------------------------------------------


def test_failure_at_step_three_indicts_only_the_diverged_facet(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 0})
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    cells = _cells(repository)
    diverged = cells[(CHECK, "method_selection")]
    assert diverged.direct_negative_mass > 0.0
    assert diverged.direct_positive_mass == pytest.approx(0.0)
    # Steps 1 and 2 passed. A conjunctive failure says nothing about them, and
    # the passed-facet firewall is what makes A1's asymmetry safe.
    for key in ((SETUP, "procedure_execution"), (SOLVE, "procedure_execution")):
        assert cells[key].direct_positive_mass > 0.0
        assert cells[key].direct_negative_mass == pytest.approx(0.0)
        assert cells[key].embedded_negative_mass == pytest.approx(0.0)


def test_failure_at_step_one_leaves_later_steps_unassessed_not_failed(tmp_path):
    """First-error localization over the authored ``depends_on`` DAG: a learner
    who never got past setup has told you nothing about solving or checking."""

    _paths, vault, repository = _vault(tmp_path)
    _attempt(vault, repository, points={"c_setup": 0, "c_solve": 0, "c_check": 0})
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    cells = _cells(repository)
    assert cells[(SETUP, "procedure_execution")].direct_negative_mass > 0.0
    assert (SOLVE, "procedure_execution") not in cells
    assert (CHECK, "method_selection") not in cells
    # And the unexercised supporting claim is not written as blame either: an
    # unexercised supporting target that can only ever hurt is a worse
    # instrument than not authoring it at all.
    assert (ALGEBRA, "procedure_execution") not in cells


def test_an_unexercised_supporting_target_takes_no_blame_when_its_own_step_fails(tmp_path):
    """Guard 1 is symmetric: no credit AND no blame without trace evidence.

    A supporting target that could only ever hurt would be a worse instrument
    than not authoring it at all, so the negative arm skips it too.
    """

    _paths, vault, repository = _vault(tmp_path)
    _attempt(vault, repository, points={"c_setup": 2, "c_solve": 0, "c_check": 0})
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    supporting = _cells(repository).get((ALGEBRA, "procedure_execution"))
    assert supporting is None or (
        supporting.embedded_negative_mass == pytest.approx(0.0)
        and supporting.direct_negative_mass == pytest.approx(0.0)
    )


def test_an_unexercised_supporting_target_costs_its_criterion_no_measurement(tmp_path):
    """Authoring a supporting target must never REMOVE measurement.

    An unexercised supporting claim is not part of the criterion's observation
    contract for this attempt, so it is dropped from the target list before any
    of the three things that count targets: ``allocate_success_mass``, which
    normalizes across them (leaving it in would dilute the primary to 1/1.3);
    the ``observed_unresolved_failure`` gate, which opens an unresolved-cause
    factor when a failure has several candidate causes; and the attribution
    weights. Without that, the same failure that localizes cleanly onto
    ``f_solve`` becomes ambiguous the moment an author adds a supporting target
    — i.e. honest authoring would strictly reduce the evidence the item
    produces, which is the opposite of what A1 is for.
    """

    # Baseline: one primary target, and the failure localizes.
    _paths, plain_vault, plain_repository = _vault(
        tmp_path / "plain", criteria=_conjunctive_criteria(supporting=False)
    )
    _attempt(plain_vault, plain_repository, points={"c_setup": 2, "c_solve": 0, "c_check": 0})
    project_canonical_facet_state(plain_vault, plain_repository, clock=FrozenClock(NOW))
    baseline = _cells(plain_repository)[(SOLVE, "procedure_execution")]
    assert baseline.direct_negative_mass > 0.0
    assert plain_repository.unresolved_cause_observation_ids() == set()

    # Same rubric plus one supporting target that no trace supports: identical.
    _paths2, vault, repository = _vault(tmp_path / "supporting")
    _attempt(vault, repository, points={"c_setup": 2, "c_solve": 0, "c_check": 0})
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))
    solve = _cells(repository)[(SOLVE, "procedure_execution")]
    assert solve.direct_negative_mass == pytest.approx(baseline.direct_negative_mass)
    assert repository.unresolved_cause_observation_ids() == set()


def test_an_exercised_supporting_target_does_make_the_failure_ambiguous(tmp_path):
    """The complement: with an A6 observation the supporting target IS a real
    second candidate cause, so the ambiguity gate fires and the failure opens an
    unresolved-cause factor instead of localizing. That is the gate working as
    designed — the trace showed the learner used both facets in this step, so
    which one broke is genuinely open."""

    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 0, "c_check": 0})
    _record_trace(repository, result.attempt_id, ALGEBRA)
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    cells = _cells(repository)
    assert cells[(SOLVE, "procedure_execution")].direct_negative_mass == pytest.approx(0.0)
    assert repository.unresolved_cause_observation_ids() != set()


# ---------------------------------------------------------------------------
# 4. Guard 2: the embedded-share cap
# ---------------------------------------------------------------------------


def test_cap_embedded_credit_boundaries():
    # A cell whose entire history is embedded is not demonstrated.
    assert cap_embedded_credit(0.0, 5.0, max_embedded_share=0.5) == pytest.approx(0.0)
    # At the default share, embedded may match but not exceed direct.
    assert cap_embedded_credit(1.0, 1.0, max_embedded_share=0.5) == pytest.approx(2.0)
    assert cap_embedded_credit(1.0, 9.0, max_embedded_share=0.5) == pytest.approx(2.0)
    # Under the allowance nothing is trimmed.
    assert cap_embedded_credit(4.0, 1.0, max_embedded_share=0.5) == pytest.approx(5.0)
    # share >= 1 disables the cap entirely.
    assert cap_embedded_credit(0.0, 5.0, max_embedded_share=1.0) == pytest.approx(5.0)
    assert cap_embedded_credit(1.0, 9.0, max_embedded_share=1.0) == pytest.approx(10.0)
    # share <= 0 admits no embedded credit at all.
    assert cap_embedded_credit(2.0, 5.0, max_embedded_share=0.0) == pytest.approx(2.0)
    # A share of 0.75 admits embedded up to 3x direct.
    assert cap_embedded_credit(1.0, 10.0, max_embedded_share=0.75) == pytest.approx(4.0)
    # Negative inputs are floored rather than propagated.
    assert cap_embedded_credit(-3.0, -1.0, max_embedded_share=0.5) == pytest.approx(0.0)


def test_the_configured_share_is_the_ledgers_cap_and_one_point_zero_disables_it(tmp_path):
    """The same evidence, read under the two config extremes."""

    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    _record_trace(repository, result.attempt_id, ALGEBRA)
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))
    capped = _cells(repository)[(ALGEBRA, "procedure_execution")]
    assert capped.embedded_certification_credit > 0.0
    assert capped.certification_credit == pytest.approx(0.0)

    _paths2, vault2, repository2 = _vault(tmp_path / "uncapped", max_embedded_share=1.0)
    assert vault2.config.evidence.certification.max_embedded_credit_share == 1.0
    result2 = _attempt(vault2, repository2, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    _record_trace(repository2, result2.attempt_id, ALGEBRA)
    project_canonical_facet_state(vault2, repository2, clock=FrozenClock(NOW))
    uncapped = _cells(repository2)[(ALGEBRA, "procedure_execution")]
    assert uncapped.certification_credit == pytest.approx(
        uncapped.embedded_certification_credit
    )
    assert uncapped.certification_credit > 0.0


def test_default_config_share_is_one_half():
    assert EvidenceCertificationConfig().max_embedded_credit_share == 0.5


def test_partition_supporting_targets_splits_on_trace_evidence():
    targets = [
        CriterionTarget(facet=SOLVE, capability="procedure_execution", role="primary"),
        CriterionTarget(facet=ALGEBRA, capability="procedure_execution", role="supporting"),
        CriterionTarget(facet=CHECK, capability="method_selection", role="supporting"),
    ]
    partition = partition_supporting_targets(targets, {ALGEBRA})
    # Primary targets are never partitioned — the criterion outcome IS their
    # evidence.
    assert [t.facet for t in partition.exercised] == [ALGEBRA]
    assert [t.facet for t in partition.unexercised] == [CHECK]
    assert partition.unexercised_cells == ((CHECK, "method_selection"),)
    # No observations at all => everything unexercised, which is the correct
    # reading of "no evidence the facet was exercised".
    assert len(partition_supporting_targets(targets, ()).unexercised) == 2
    # Matching is on the facet, not the (facet, capability) cell.
    assert (
        len(partition_supporting_targets(targets, {CHECK}, canonical_facet_id=str).exercised) == 1
    )
    assert UNEXERCISED_SUPPORTING_TARGET == "unexercised_supporting_target"


# ---------------------------------------------------------------------------
# 5. The shape rule
# ---------------------------------------------------------------------------


def _shape(targets_by_criterion: list[list[CriterionTarget]], *, depends_on=None):
    criteria = [
        RubricCriterion(
            id=f"c{index}",
            points=1,
            description="x",
            targets=targets,
            depends_on=list((depends_on or {}).get(f"c{index}", [])),
        )
        for index, targets in enumerate(targets_by_criterion)
    ]
    return classify_item_shape(_pi(), Rubric(max_points=4, criteria=criteria))


def test_single_cell_item_is_not_conjunctive_and_scores_exactly_zero():
    shape = _shape([[CriterionTarget(facet="a", capability="retrieval")]])
    assert shape.is_conjunctive is False
    assert shape.conjunctive_strength == 0.0
    for predicted in (0.0, 0.5, 1.0):
        assert conjunctive_fit(shape, predicted, localizing=False) == 0.0
        assert conjunctive_fit(shape, predicted, localizing=True) == 0.0


def test_a_facet_observed_at_two_capabilities_is_two_cells():
    shape = _shape(
        [
            [CriterionTarget(facet="a", capability="retrieval")],
            [CriterionTarget(facet="a", capability="method_selection")],
        ]
    )
    assert shape.is_conjunctive is True
    assert shape.primary_cells == (("a", "method_selection"), ("a", "retrieval"))
    assert shape.criterion_count == 2


def test_a_cell_observed_both_ways_is_a_primary_cell():
    shape = _shape(
        [
            [CriterionTarget(facet="a", capability="retrieval")],
            [
                CriterionTarget(facet="b", capability="retrieval"),
                CriterionTarget(facet="a", capability="retrieval", role="supporting"),
            ],
        ]
    )
    assert shape.primary_cells == (("a", "retrieval"), ("b", "retrieval"))
    assert shape.supporting_cells == ()


def test_conjunctive_fit_prefers_the_capstone_only_when_a_pass_is_likely():
    shape = _shape(
        [
            [CriterionTarget(facet="a", capability="retrieval")],
            [CriterionTarget(facet="b", capability="retrieval")],
            [CriterionTarget(facet="c", capability="retrieval")],
        ]
    )
    assert shape.is_conjunctive is True
    high = conjunctive_fit(shape, 0.9, localizing=False)
    low = conjunctive_fit(shape, 0.1, localizing=False)
    assert high > 0.0
    assert low < 0.0
    assert conjunctive_fit(shape, 0.5, localizing=False) == pytest.approx(0.0)
    assert high == pytest.approx(-low)
    # REPAIR is always penalized: a capstone answers "which step is broken"
    # worst, whatever the posterior says.
    for predicted in (0.0, 0.5, 0.95):
        assert conjunctive_fit(shape, predicted, localizing=True) < 0.0
    assert conjunctive_fit(shape, 0.95, localizing=True) == pytest.approx(
        -shape.conjunctive_strength
    )


def test_conjunctive_strength_saturates_at_the_ceiling():
    def strength(cells: int) -> float:
        return _shape(
            [
                [CriterionTarget(facet=f"f{index}", capability="retrieval")]
                for index in range(cells)
            ]
        ).conjunctive_strength

    assert strength(1) == 0.0
    assert strength(2) == pytest.approx(1.0 / (CONJUNCTIVE_STRENGTH_CEILING - 1))
    assert strength(CONJUNCTIVE_STRENGTH_CEILING) == pytest.approx(1.0)
    assert strength(CONJUNCTIVE_STRENGTH_CEILING + 3) == pytest.approx(1.0)


def test_classify_item_shape_reads_the_authored_dependency_chain(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    item = vault.practice_items[CAPSTONE]
    shape = classify_item_shape(
        item, vault.rubric_for_item(item), canonical_facet_id=vault.canonical_facet_id
    )
    assert shape.is_conjunctive is True
    assert shape.has_dependency_chain is True
    assert shape.primary_cells == (
        (CHECK, "method_selection"),
        (SETUP, "procedure_execution"),
        (SOLVE, "procedure_execution"),
    )
    assert shape.supporting_cells == ((ALGEBRA, "procedure_execution"),)
    assert shape.as_dict()["is_conjunctive"] is True


# ---------------------------------------------------------------------------
# 6. Proposal validation of authored targets
# ---------------------------------------------------------------------------


def _target_errors(criterion: dict, *, criterion_ids=("c1", "c2"), single: bool = False):
    return _criterion_target_errors(
        criterion, criterion_ids=set(criterion_ids), single_criterion=single
    )


def test_bad_capability_is_rejected():
    errors = _target_errors({"id": "c1", "targets": [_target("f", capability="fluency")]})
    assert errors == ["invalid_criterion_target:capability:c1:fluency"]


def test_bad_role_is_rejected():
    errors = _target_errors({"id": "c1", "targets": [_target("f", role="decorative")]})
    assert errors == ["invalid_criterion_target:role:c1:decorative"]


def test_two_primary_targets_on_one_criterion_are_rejected():
    errors = _target_errors(
        {"id": "c1", "targets": [_target("f_a"), _target("f_b")]}
    )
    assert errors == ["invalid_criterion_target:multiple_primary:c1"]


def test_supporting_target_on_a_single_criterion_rubric_is_rejected():
    errors = _target_errors(
        {"id": "c1", "targets": [_target("f_a"), _target("f_b", role="supporting")]},
        criterion_ids=("c1",),
        single=True,
    )
    assert errors == ["invalid_criterion_target:supporting_on_single_criterion:c1"]


def test_depends_on_naming_a_nonexistent_criterion_is_rejected():
    errors = _target_errors({"id": "c2", "targets": [_target("f")], "depends_on": ["c9"]})
    assert errors == ["invalid_criterion_depends_on:c2:c9"]


def test_missing_facet_and_non_object_targets_are_rejected():
    errors = _target_errors({"id": "c1", "targets": [{"capability": "retrieval"}, "nope"]})
    assert "invalid_criterion_target:missing_facet:c1" in errors
    assert "invalid_criterion_target:not_an_object:c1" in errors


def test_a_well_formed_conjunctive_rubric_produces_no_target_errors():
    for criterion in _conjunctive_criteria():
        assert (
            _target_errors(criterion, criterion_ids=("c_setup", "c_solve", "c_check")) == []
        )


def test_a_legacy_criterion_with_no_targets_produces_no_errors():
    assert _target_errors({"id": "c1", "points": 4, "description": "x"}) == []


# ---------------------------------------------------------------------------
# 7. A6 grading-side validation
# ---------------------------------------------------------------------------


def _proposal(*observations):
    return SimpleNamespace(
        exercised_facets=[
            SimpleNamespace(
                facet=facet,
                evidence=evidence,
                criterion_id=criterion_id,
            )
            for facet, evidence, criterion_id in observations
        ]
    )


def _validate(vault, observations):
    item = vault.practice_items[CAPSTONE]
    rubric = vault.rubric_for_item(item)
    return _validated_exercised_facets(vault, item, rubric, _proposal(*observations))


def test_an_unregistered_facet_is_dropped_not_raised(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    accepted = _validate(
        vault,
        [("f_invented_by_the_grader", "it used something", None), (SETUP, "step 1", None)],
    )
    assert [row.facet for row in accepted] == [SETUP]


def test_an_observation_with_no_evidence_citation_is_dropped(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    accepted = _validate(vault, [(SETUP, "", None), (SOLVE, "   ", None), (CHECK, "cited", None)])
    assert [row.facet for row in accepted] == [CHECK]


def test_observation_scope_is_declared_for_contract_facets_and_opportunistic_otherwise(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    accepted = _validate(vault, [(SETUP, "step 1", None), ("recall", "recited it", None)])
    scopes = {row.facet: row.observation_scope for row in accepted}
    assert scopes[SETUP] == "declared"
    assert scopes["recall"] == "opportunistic"


def test_a_supporting_target_facet_counts_as_declared(tmp_path):
    """The supporting target IS part of the item's contract, so confirming it is
    the grader confirming what the item meant to measure — not a bonus."""

    _paths, vault, _repository = _vault(tmp_path)
    accepted = _validate(vault, [(ALGEBRA, "it manipulated the algebra", None)])
    assert [row.observation_scope for row in accepted] == ["declared"]


def test_a_criterion_id_outside_the_rubric_is_nulled_rather_than_stored(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    accepted = _validate(
        vault, [(SETUP, "step 1", "c_setup"), (SOLVE, "step 2", "c_not_in_rubric")]
    )
    by_facet = {row.facet: row.criterion_id for row in accepted}
    assert by_facet[SETUP] == "c_setup"
    assert by_facet[SOLVE] is None


def test_duplicate_observations_collapse_to_one(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    accepted = _validate(
        vault, [(SETUP, "first sighting", None), (SETUP, "second sighting", None)]
    )
    assert [(row.facet, row.evidence) for row in accepted] == [(SETUP, "first sighting")]


def test_more_than_the_per_attempt_cap_is_truncated(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    many = [
        {"id": f"f_{index}", "kind": "procedure_contract", "claim": f"Claim {index}."}
        for index in range(MAX_EXERCISED_FACETS_PER_ATTEMPT + 3)
    ]
    write_facets(paths, [*FACETS, *many])
    _write_item(
        paths,
        CAPSTONE,
        criteria=_conjunctive_criteria(),
        facets=[SETUP, SOLVE, CHECK, ALGEBRA],
    )
    vault = load_vault(paths.root)
    accepted = _validate(
        vault, [(facet["id"], "seen in the trace", None) for facet in many]
    )
    assert len(accepted) == MAX_EXERCISED_FACETS_PER_ATTEMPT
    # Truncation keeps the grader's own ordering: it is the only ranking there is.
    assert [row.facet for row in accepted] == [
        facet["id"] for facet in many[:MAX_EXERCISED_FACETS_PER_ATTEMPT]
    ]
    # NOTE: the cap's own comment says the drop is "flagged, never silent", but
    # the function returns a bare list — there is no flag channel here and no
    # caller records one. Pinned as-is; the claim is currently aspirational.


def test_an_empty_proposal_yields_no_observations(tmp_path):
    _paths, vault, _repository = _vault(tmp_path)
    assert _validate(vault, []) == []


# ---------------------------------------------------------------------------
# 8. The observation store: idempotent + append-only
# ---------------------------------------------------------------------------


def test_insert_trace_exercised_facets_is_idempotent_on_attempt_facet_source(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})

    assert _record_trace(repository, result.attempt_id, ALGEBRA) == 1
    # A regrade re-reporting the same trace adds nothing, and the FIRST run's
    # wording survives: a record that can be rewritten is not evidence.
    assert (
        repository.insert_trace_exercised_facets(
            result.attempt_id,
            [
                {
                    "facet_id": ALGEBRA,
                    "observation_scope": "opportunistic",
                    "evidence": "a later, different wording",
                }
            ],
            clock=FrozenClock(NOW),
        )
        == 0
    )
    rows = repository.trace_exercised_facets(result.attempt_id)
    assert len(rows) == 1
    assert rows[0]["evidence"] == "the trace shows it"
    assert rows[0]["role"] == "supporting"

    # A different source is a different observation channel, not a duplicate.
    assert _record_trace(repository, result.attempt_id, ALGEBRA, source="teach_back") == 1
    assert len(repository.trace_exercised_facets(result.attempt_id)) == 2

    grouped = repository.all_trace_exercised_facets()
    assert set(grouped) == {result.attempt_id}
    assert len(grouped[result.attempt_id]) == 2


def test_the_observation_log_rejects_update(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    _record_trace(repository, result.attempt_id, ALGEBRA)

    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE trace_exercised_facets SET evidence = 'rewritten'"
            )


def test_the_store_refuses_a_role_other_than_supporting(tmp_path):
    """A one-value CHECK, not the two-value vocabulary used elsewhere: an
    observation from this channel can never become primary by a later edit."""

    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO trace_exercised_facets(
                  id, attempt_id, facet_id, observation_scope, role, evidence, created_at
                ) VALUES ('x', ?, ?, 'opportunistic', 'primary', 'e', ?)
                """,
                (result.attempt_id, ALGEBRA, NOW_ISO),
            )


def test_the_store_refuses_an_unknown_observation_scope(tmp_path):
    _paths, vault, repository = _vault(tmp_path)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO trace_exercised_facets(
                  id, attempt_id, facet_id, observation_scope, role, evidence, created_at
                ) VALUES ('x', ?, ?, 'guessed', 'supporting', 'e', ?)
                """,
                (result.attempt_id, ALGEBRA, NOW_ISO),
            )


# ---------------------------------------------------------------------------
# 9. A6 elicitation: the four typed refusals and the reward
# ---------------------------------------------------------------------------


def _elicitation_item(*, capability=None, trace_status=None):
    contract = None if trace_status is None else SimpleNamespace(status=trace_status)
    return SimpleNamespace(capability=capability, trace_contract=contract)


def test_an_item_with_an_available_trace_contract_is_self_documenting():
    decision = decide_elicitation(
        _elicitation_item(capability="method_selection", trace_status="available"),
        config=TraceEvidenceConfig(),
        elicitations_this_session=0,
    )
    assert decision.elicit is False
    assert decision.reason == "self_documenting_trace"
    assert decision.prompt is None


def test_procedure_execution_shows_its_work():
    decision = decide_elicitation(
        _elicitation_item(capability="procedure_execution"),
        config=TraceEvidenceConfig(),
        elicitations_this_session=0,
    )
    assert decision.elicit is False
    assert decision.reason == "capability_shows_its_work"


def test_method_selection_without_a_contract_is_elicited_with_a_decision_prompt():
    decision = decide_elicitation(
        _elicitation_item(capability="method_selection"),
        config=TraceEvidenceConfig(),
        elicitations_this_session=0,
    )
    assert decision.elicit is True
    assert decision.reason == "answer_underdetermines_reasoning"
    assert decision.prompt is not None
    assert "why this approach" in decision.prompt.lower()
    assert decision.as_dict()["elicit"] is True


def test_schema_interpretation_gets_the_applicability_prompt():
    decision = decide_elicitation(
        _elicitation_item(capability="schema_interpretation"),
        config=TraceEvidenceConfig(),
        elicitations_this_session=0,
    )
    assert decision.elicit is True
    assert "fit" in (decision.prompt or "").lower()


def test_a_no_reliable_decomposition_contract_does_not_suppress_elicitation():
    """"available" is the discriminator, not "has a contract object": an item
    that declares it CANNOT be decomposed is precisely the ambiguous case."""

    decision = decide_elicitation(
        _elicitation_item(capability="method_selection", trace_status="no_reliable_decomposition"),
        config=TraceEvidenceConfig(),
        elicitations_this_session=0,
    )
    assert decision.elicit is True


def test_the_session_budget_is_hard():
    config = TraceEvidenceConfig()
    item = _elicitation_item(capability="method_selection")
    assert (
        decide_elicitation(
            item, config=config, elicitations_this_session=config.max_elicitations_per_session - 1
        ).elicit
        is True
    )
    exhausted = decide_elicitation(
        item, config=config, elicitations_this_session=config.max_elicitations_per_session
    )
    assert exhausted.elicit is False
    assert exhausted.reason == "session_budget_exhausted"


def test_disabling_elicitation_wins_over_every_other_arm():
    decision = decide_elicitation(
        _elicitation_item(capability="method_selection"),
        config=TraceEvidenceConfig(elicitation_enabled=False),
        elicitations_this_session=0,
    )
    assert decision.elicit is False
    assert decision.reason == "disabled"


def test_elicitation_reward_counts_only_opportunistic_observations():
    declared_only = [
        {"facet_id": SETUP, "observation_scope": "declared"},
        {"facet_id": SOLVE, "observation_scope": "declared"},
    ]
    assert elicitation_reward(declared_only) is None
    assert elicitation_reward([]) is None
    assert elicitation_reward(None) is None

    one = elicitation_reward([*declared_only, {"facet_id": "recall", "observation_scope": "opportunistic"}])
    assert one == "Your explanation also demonstrated 1 additional facet."
    two = elicitation_reward(
        [
            {"facet_id": "recall", "observation_scope": "opportunistic"},
            {"facet_id": ALGEBRA, "observation_scope": "opportunistic"},
        ]
    )
    assert two == "Your explanation also demonstrated 2 additional facets."


def test_elicitation_reward_reads_objects_as_well_as_rows():
    reward = elicitation_reward(
        [SimpleNamespace(facet_id="recall", observation_scope="opportunistic")]
    )
    assert reward == "Your explanation also demonstrated 1 additional facet."


# ---------------------------------------------------------------------------
# 10. exam_pool._item_components
# ---------------------------------------------------------------------------


def test_item_components_without_authored_targets_is_unchanged(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    write_facets(paths, FACETS)
    _write_item(
        paths,
        "pi_legacy_shape",
        criteria=[{"id": "correctness", "points": 4, "description": "Correct."}],
        facets=[SETUP, SOLVE],
    )
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_legacy_shape"]
    components = _item_components(vault, item, {SETUP, SOLVE})
    assert components == frozenset(
        {(SETUP, "procedure_execution"), (SOLVE, "procedure_execution")}
    )


def test_item_components_reads_authored_primary_targets_at_both_capabilities(tmp_path):
    """A1's gain, priced: one item testifying at two rungs, not one."""

    _paths, vault, _repository = _vault(tmp_path)
    item = vault.practice_items[CAPSTONE]
    components = _item_components(vault, item, {SETUP, SOLVE, CHECK})
    assert components == frozenset(
        {
            (SETUP, "procedure_execution"),
            (SOLVE, "procedure_execution"),
            # Read only from the authored target; the item's own declared
            # capability is procedure_execution.
            (CHECK, "method_selection"),
        }
    )


def test_a_supporting_only_facet_contributes_no_reachable_cell(tmp_path):
    """A facet the rubric names ONLY as ``supporting`` contributes no cell.

    ``_item_components`` answers "which contract cells can this item close", and
    §5.3 says embedded credit never certifies a component on its own. So the
    exclusion has to survive the "facets the rubric never targets still testify
    at the item's own rung" fallback: if that fallback keyed on primary targets
    alone, a supporting-only facet would re-enter at the item's declared
    capability and the exam pool would believe a cell is reachable that no
    instrument on this item can close.
    """

    _paths, vault, _repository = _vault(tmp_path)
    item = vault.practice_items[CAPSTONE]
    components = _item_components(vault, item, {SETUP, SOLVE, CHECK, ALGEBRA})
    assert (ALGEBRA, "procedure_execution") not in components
    assert not any(facet == ALGEBRA for facet, _capability in components)
    assert len(components) == 3


# ---------------------------------------------------------------------------
# 11. The SECOND fold — receipt exactness under both guards
# ---------------------------------------------------------------------------
#
# `facet_evidence_timeline` runs an independent fold over the same ledger the
# projection banks, and `test_receipt_exactness` requires the two to agree to the
# float. That test's fixtures carry no A6 observations and no supporting targets,
# so before these cases the claim "both guards live in both folds" had no test at
# all — and the first implementation of guard 2 in the fold was reachable only
# through a default that switched it off.


def _timeline_endpoint(vault, repository, facet: str) -> float:
    """Cumulative Demonstrated credit for ``facet``, from the timeline fold.

    Deliberately the fold's own ``demonstrated`` running total rather than a sum
    over derivation lines: guard 2's per-cell cap is applied INSIDE the fold (it
    is a statement about a cell's whole history), so a sum of the per-observation
    itemization is the pre-cap number and would compare the wrong quantity.
    """

    from learnloop.services.facet_evidence_timeline import facet_evidence_timelines

    series = facet_evidence_timelines(vault, repository, [facet]).get(facet, [])
    return series[-1].demonstrated if series else 0.0


def _banked(repository, facet: str) -> float:
    """The ledger's certification credit for ``facet``, summed over capabilities."""

    return sum(
        cell.certification_credit
        for (cell_facet, _capability), cell in _cells(repository).items()
        if cell_facet == facet
    )


def test_guard_1_holds_in_the_receipt_fold_as_well_as_the_projection(tmp_path):
    """An unexercised supporting target earns nothing in EITHER fold.

    The guards are shared through one predicate, but sharing a predicate is not
    enough — the folds also have to feed it the same input. A divergence here
    does not raise; it silently makes the learner-facing Demonstrated curve
    disagree with the ledger it claims to plot.
    """

    _paths, vault, repository = _vault(tmp_path)
    _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    for facet in (SETUP, SOLVE, CHECK, ALGEBRA):
        assert _timeline_endpoint(vault, repository, facet) == pytest.approx(
            _banked(repository, facet), abs=1e-9
        ), f"folds disagree on {facet}"


def test_a_merged_facet_does_not_desynchronise_the_two_folds(tmp_path):
    """An A6 observation recorded under a RETIRED facet id.

    The projection resolves observation ids through the transitive merge map
    before comparing them to a target's facet. Reading them raw in the timeline
    would make the same supporting target exercised in one fold and unexercised
    in the other the moment a facet is merged — credit in one, none in the other,
    with the learner-facing curve understating the ledger.
    """

    # Guard 2 is disabled here on purpose. The supporting cell has no direct
    # credit, so at the default 0.5 share the cap zeroes it in the projection —
    # and both folds would then agree on zero for opposite reasons, hiding the
    # very desynchronisation this test exists to catch.
    _paths, vault, repository = _vault(tmp_path, max_embedded_share=1.0)
    result = _attempt(vault, repository, points={"c_setup": 2, "c_solve": 1, "c_check": 1})
    # Observation filed under an id that later merges into the supporting facet.
    _record_trace(repository, result.attempt_id, "f_algebra_retired")
    repository.insert_facet_merge(
        retired_facet_id="f_algebra_retired",
        surviving_facet_id=ALGEBRA,
        rationale="the retired id names the same atom",
        clock=FrozenClock(NOW),
    )
    vault = load_vault(vault.root)
    project_canonical_facet_state(vault, repository, clock=FrozenClock(NOW))

    assert _timeline_endpoint(vault, repository, ALGEBRA) == pytest.approx(
        _banked(repository, ALGEBRA), abs=1e-9
    )
    # And the observation was actually honoured rather than both folds agreeing
    # on zero: the merged id licensed the supporting target, so the cell carries
    # embedded mass it would not have if the merge had been ignored.
    cell = _cells(repository)[(ALGEBRA, "procedure_execution")]
    assert cell.embedded_positive_mass > 0.0
    assert cell.certification_credit > 0.0
    assert cell.unexercised_supporting_mass == pytest.approx(0.0)
