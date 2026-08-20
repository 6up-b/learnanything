"""``any_of`` and vacuous recipes in the certification authority (§9.2/§9.5).

``recipe_gaps`` is the single predicate both ``lo_certification`` and the §5.7
cold probe run. It used to iterate ``all_of`` only, so a recipe whose
requirements lived in ``any_of`` certified on *no* evidence at all and minted a
certificate with zero cells — nothing for the probe to re-test, so nothing that
could ever revoke it. These tests pin the three claims that closes: an
alternative group is an obligation, satisfying one alternative discharges the
whole group, and a recipe that declares no obligation certifies nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.goals.certification_cold_probe import current_certificate
from learnloop.goals.goal_certification import lo_certification, recipe_gaps
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import (
    NOW,
    NOW_ISO,
    create_basic_vault,
    set_algorithm_version,
    write_facets,
)

LO_ID = "lo_composite"
CONCEPT = "singular_value_decomposition"

COMP_A = "facet_component_a"
ALT_X = "facet_alternative_x"
ALT_Y = "facet_alternative_y"
INTEG = "facet_integration"

# (facet, capability, item id) for every cell these recipes can name.
CELLS = {
    COMP_A: ("procedure_execution", "pi_comp_a"),
    ALT_X: ("method_selection", "pi_alt_x"),
    ALT_Y: ("method_selection", "pi_alt_y"),
    INTEG: ("coordination", "pi_integrated"),
}


def _item(item_id, *, facet, capability, correlation_group):
    return {
        "schema_version": 1,
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "constructed_response",
        "attempt_types_allowed": ["independent_attempt", "hinted_attempt", "dont_know"],
        "evidence_facets": [facet],
        "evidence_weights": {facet: 1.0},
        "prompt": f"Prompt for {item_id}.",
        "expected_answer": "An answer.",
        "difficulty": 0.5,
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {
                    "id": "c1",
                    "points": 4,
                    "description": "criterion",
                    "targets": [{"facet": facet, "capability": capability, "role": "primary"}],
                    "correlation_group": correlation_group,
                    "recipe_ids": ["recipe_main"],
                }
            ],
            "fatal_errors": [],
        },
        "evidence_fingerprint": {"source_family": correlation_group},
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }


def _component(facet, *, modality="hard"):
    capability, _item_id = CELLS[facet]
    return {"facet": facet, "capability": capability, "modality": modality}


def build_vault(root: Path, recipe: dict):
    """An mvp-0.7 vault whose single LO carries exactly ``recipe``.

    Every cell the recipes can name has an instrument, so a certification result
    is always a statement about evidence rather than about missing items.
    """

    paths = create_basic_vault(root)
    write_facets(
        paths,
        [
            {"id": COMP_A, "kind": "procedure", "claim": "Component A procedure."},
            {"id": ALT_X, "kind": "procedure", "claim": "Alternative method X."},
            {"id": ALT_Y, "kind": "procedure", "claim": "Alternative method Y."},
            {"id": INTEG, "kind": "procedure", "claim": "Coordinate the components."},
        ],
    )
    write_yaml(
        paths.learning_object_path("linear-algebra", LO_ID),
        {
            "schema_version": 1,
            "id": LO_ID,
            "title": "Composite skill",
            "subjects": ["linear-algebra"],
            "concept": CONCEPT,
            "knowledge_type": "procedure",
            "status": "active",
            "contradicts": None,
            "summary": "A composite skill with alternative methods.",
            "prerequisites": [],
            "confusables": [],
            "blueprints": [{"id": "bp_solve", "weight": 1.0, "recipes": [recipe]}],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    for facet, (capability, item_id) in CELLS.items():
        write_yaml(
            paths.practice_item_path("linear-algebra", item_id),
            _item(item_id, facet=facet, capability=capability, correlation_group=f"cg_{facet}"),
        )
    default_item = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    if default_item.exists():
        default_item.unlink()
    set_algorithm_version(paths, "mvp-0.7")
    return paths


def _vault(tmp_path, recipe: dict):
    paths = build_vault(tmp_path / "vault", recipe)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return vault, repository


def _demonstrate(vault, repository, facet):
    """One full-marks unassisted attempt on the instrument for ``facet``."""

    _capability, item_id = CELLS[facet]
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="An answer.",
            attempt_type="independent_attempt",
            hints_used=0,
        ),
        SelfGradeInput(criterion_points={"c1": 4}, fatal_errors=[], confidence=4),
        clock=FrozenClock(NOW),
    )


def _lo(vault):
    return vault.learning_objects[LO_ID]


def _only_recipe(vault, repository):
    rows = recipe_gaps(vault, repository, _lo(vault))
    assert len(rows) == 1
    return rows[0]


# ---------------------------------------------------------------------------
# (a)/(b) an ``any_of``-only recipe is an obligation, discharged by one alternative
# ---------------------------------------------------------------------------

ANY_OF_ONLY = {
    "id": "recipe_main",
    "composition": "conjunctive",
    "all_of": [],
    "any_of": [_component(ALT_X), _component(ALT_Y)],
}


def test_any_of_only_recipe_does_not_certify_without_evidence(tmp_path):
    """The reported bug: ``all_of=[]`` + ``any_of`` certified on zero evidence."""

    vault, repository = _vault(tmp_path, ANY_OF_ONLY)

    gaps = _only_recipe(vault, repository)
    assert gaps.satisfied is False
    assert gaps.alternative_gaps == ((ALT_X, ALT_Y),)
    assert gaps.satisfying_alternatives == ()

    certification = lo_certification(vault, repository, _lo(vault))
    assert certification.demonstrated is False
    # Both alternatives are unmet today, so both are reported — the flat LO-level
    # list has no OR, and only one of them has to close.
    assert certification.component_gaps == (ALT_X, ALT_Y)
    # No certificate means nothing for the delayed cold probe to rest on.
    assert current_certificate(vault, repository, _lo(vault)) is None


def test_one_demonstrated_alternative_satisfies_the_group(tmp_path):
    vault, repository = _vault(tmp_path, ANY_OF_ONLY)
    _demonstrate(vault, repository, ALT_Y)

    gaps = _only_recipe(vault, repository)
    assert gaps.satisfied is True
    assert gaps.alternative_gaps == ()
    assert gaps.satisfying_alternatives == ((ALT_Y, "method_selection"),)
    # The unused alternative is NOT a gap: the group is OR-joined.
    assert gaps.component_gaps == ()
    assert lo_certification(vault, repository, _lo(vault)).demonstrated is True


# ---------------------------------------------------------------------------
# (c) ``all_of`` and ``any_of`` are both required
# ---------------------------------------------------------------------------

MIXED = {
    "id": "recipe_main",
    "composition": "conjunctive",
    "all_of": [_component(COMP_A)],
    "any_of": [_component(ALT_X), _component(ALT_Y)],
}


@pytest.mark.parametrize(
    "demonstrated, expected",
    [
        ((), False),
        ((COMP_A,), False),  # the milder reported case: certified on X alone
        ((ALT_X,), False),
        ((COMP_A, ALT_X), True),
        ((COMP_A, ALT_Y), True),
    ],
)
def test_mixed_recipe_needs_the_conjunct_and_one_alternative(tmp_path, demonstrated, expected):
    vault, repository = _vault(tmp_path, MIXED)
    for facet in demonstrated:
        _demonstrate(vault, repository, facet)

    assert _only_recipe(vault, repository).satisfied is expected
    assert lo_certification(vault, repository, _lo(vault)).demonstrated is expected


# ---------------------------------------------------------------------------
# (d) a recipe that declares no obligation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "recipe",
    [
        pytest.param(
            {"id": "recipe_main", "composition": "conjunctive", "all_of": [], "any_of": []},
            id="empty",
        ),
        pytest.param(
            {
                "id": "recipe_main",
                "composition": "conjunctive",
                "all_of": [_component(COMP_A, modality="facilitating")],
                "any_of": [_component(ALT_X, modality="instructional_order")],
            },
            id="advisory_only",
        ),
    ],
)
def test_recipe_with_no_contract_component_never_certifies(tmp_path, recipe):
    """Vacuous certification: empty gap tuples must not read as "all met"."""

    vault, repository = _vault(tmp_path, recipe)
    _demonstrate(vault, repository, COMP_A)
    _demonstrate(vault, repository, ALT_X)

    gaps = _only_recipe(vault, repository)
    assert gaps.contract_component_count == 0
    assert gaps.satisfied is False
    assert lo_certification(vault, repository, _lo(vault)).demonstrated is False
    assert current_certificate(vault, repository, _lo(vault)) is None


def test_advisory_integration_is_not_an_obligation(tmp_path):
    """Certification and the commissioning queue must name the same cells.

    ``contract_reachability.contract_cells`` filters the integration component
    through ``CONTRACT_MODALITIES``, so a ``facilitating`` integration is never
    queued for commissioning; gating certification on it would be an obligation
    that is invisible and by construction uncloseable.
    """

    vault, repository = _vault(
        tmp_path,
        {
            "id": "recipe_main",
            "composition": "conjunctive",
            "all_of": [_component(COMP_A)],
            "any_of": [],
            "integration": _component(INTEG, modality="facilitating"),
        },
    )
    _demonstrate(vault, repository, COMP_A)

    gaps = _only_recipe(vault, repository)
    assert gaps.integration_gaps == ()
    assert gaps.contract_component_count == 1
    assert gaps.satisfied is True


# ---------------------------------------------------------------------------
# (e) the certificate names the alternative it rests on
# ---------------------------------------------------------------------------


def test_certificate_cells_include_the_satisfying_alternative(tmp_path):
    vault, repository = _vault(tmp_path, MIXED)
    _demonstrate(vault, repository, COMP_A)
    _demonstrate(vault, repository, ALT_X)

    certificate = current_certificate(vault, repository, _lo(vault))
    assert certificate is not None
    cells = {(cell.facet_id, cell.capability) for cell in certificate.cells}
    assert cells == {(COMP_A, "procedure_execution"), (ALT_X, "method_selection")}
    # Load-bearing means probeable: every cell carries real certification credit.
    assert all(cell.certification_credit > 0 for cell in certificate.cells)
    # The alternative NOT used is not part of the claim.
    assert ALT_Y not in {cell.facet_id for cell in certificate.cells}


def test_certificate_id_tracks_which_alternative_certified(tmp_path):
    """Two learners on different methods hold different certificates.

    The certificate id hashes the cells, so if the satisfying alternative were
    dropped from them both paths would hash identically and the probe would
    re-test a method the learner never used.
    """

    vault_x, repo_x = _vault(tmp_path / "x", MIXED)
    _demonstrate(vault_x, repo_x, COMP_A)
    _demonstrate(vault_x, repo_x, ALT_X)
    vault_y, repo_y = _vault(tmp_path / "y", MIXED)
    _demonstrate(vault_y, repo_y, COMP_A)
    _demonstrate(vault_y, repo_y, ALT_Y)

    cert_x = current_certificate(vault_x, repo_x, _lo(vault_x))
    cert_y = current_certificate(vault_y, repo_y, _lo(vault_y))
    assert cert_x is not None and cert_y is not None
    assert cert_x.certificate_id != cert_y.certificate_id


# ---------------------------------------------------------------------------
# (f) regression: ``all_of``-only recipes are untouched
# ---------------------------------------------------------------------------

ALL_OF_ONLY = {
    "id": "recipe_main",
    "composition": "conjunctive",
    "all_of": [_component(COMP_A)],
    "any_of": [],
    "integration": _component(INTEG),
}


def test_all_of_only_recipe_behaviour_is_unchanged(tmp_path):
    """The shape every tracked fixture LO uses: all_of (+ integration), any_of=[]."""

    vault, repository = _vault(tmp_path, ALL_OF_ONLY)

    gaps = _only_recipe(vault, repository)
    assert (gaps.component_gaps, gaps.integration_gaps) == ((COMP_A,), (INTEG,))
    assert gaps.alternative_gaps == ()
    assert gaps.satisfied is False

    _demonstrate(vault, repository, COMP_A)
    gaps = _only_recipe(vault, repository)
    assert (gaps.component_gaps, gaps.integration_gaps) == ((), (INTEG,))
    assert gaps.satisfied is False

    _demonstrate(vault, repository, INTEG)
    gaps = _only_recipe(vault, repository)
    assert (gaps.component_gaps, gaps.integration_gaps) == ((), ())
    assert gaps.satisfied is True

    certification = lo_certification(vault, repository, _lo(vault))
    assert certification.demonstrated is True
    assert certification.component_gaps == ()
    certificate = current_certificate(vault, repository, _lo(vault))
    assert certificate is not None
    # Unchanged: the integration cell is carried twice, once per role.
    assert [(cell.facet_id, cell.role) for cell in certificate.cells] == [
        (COMP_A, "component"),
        (INTEG, "integration"),
    ]


def test_single_hard_component_recipe_still_certifies(tmp_path):
    """`lo_orient_to_the_vector_space_idea`'s shape: one hard cell, no integration."""

    vault, repository = _vault(
        tmp_path,
        {
            "id": "recipe_main",
            "composition": "conjunctive",
            "all_of": [_component(COMP_A)],
            "any_of": [],
            "integration": None,
        },
    )
    assert lo_certification(vault, repository, _lo(vault)).demonstrated is False

    _demonstrate(vault, repository, COMP_A)
    assert lo_certification(vault, repository, _lo(vault)).demonstrated is True
