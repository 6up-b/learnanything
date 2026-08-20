"""Backend read/preview path for the graph/knowledge-map editor (B2).

Covers the extended ``get_knowledge_map`` facet-field lock fields and the new
``get_facet_detail`` / ``list_facets`` / ``preview_knowledge_map`` /
``preview_blueprint_readiness`` RPCs. All are pure reads; none mutate the vault
or repository.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, write_facets
from tests.test_km3_projections import COMP_A, COMP_B, INTEG, LO_ID, build_blueprint_vault

FIXTURE_VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "linear_algebra"


def test_classical_mds_reuses_exact_cached_layout():
    from learnloop_sidecar.handlers.knowledge_map import (
        _classical_mds,
        _classical_mds_cached,
    )

    distances = [
        [0.0, 1.0, 0.5],
        [1.0, 0.0, 0.75],
        [0.5, 0.75, 0.0],
    ]
    _classical_mds_cached.cache_clear()

    first = _classical_mds(distances)
    second = _classical_mds(distances)

    assert first == second
    assert _classical_mds_cached.cache_info().hits == 1
    first[0][0] = (99.0, 99.0)
    assert _classical_mds(distances)[0][0] != (99.0, 99.0)


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _blueprint_ctx(root: Path):
    """A canonical (mvp-0.7) composite-LO vault with a valid facet registry.

    ``build_blueprint_vault`` writes an invalid ``kind: procedure`` facet, so we
    rewrite the registry with the real v2 contract (valid kinds, an alias, all
    the drawer fields) before loading, then demonstrate the two components.
    """

    import learnloop_sidecar.handlers  # noqa: F401 — registers methods
    from learnloop_sidecar.context import SidecarContext

    paths = build_blueprint_vault(root)
    write_facets(
        paths,
        [
            {
                "id": COMP_A,
                "kind": "procedure_contract",
                "title": "Component A",
                "claim": "Execute component A.",
                "preconditions": ["needs x"],
                "positive_examples": ["a good case"],
                "negative_examples": ["a bad case"],
                "non_goals": ["not this"],
                "error_signatures": ["typical slip"],
                "aliases": ["comp_a_alias"],
                "status": "reviewed",
            },
            {"id": COMP_B, "kind": "definition", "claim": "Component B schema."},
            {"id": INTEG, "kind": "procedure_contract", "claim": "Coordinate the components."},
        ],
    )
    vault = load_vault(paths.root)
    assert not any(issue.code == "yaml:invalid" for issue in vault.issues), vault.issues
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    for item_id, points in (("pi_comp_a", 4), ("pi_comp_b", 4)):
        complete_self_graded_attempt(
            vault,
            repository,
            AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="An answer.",
                attempt_type="independent_attempt",
                hints_used=0,
            ),
            SelfGradeInput(criterion_points={"c1": points}, fatal_errors=[], confidence=4),
            clock=FrozenClock(NOW),
        )
    context = SidecarContext()
    context.load(paths.root)
    return context


def _fixture_ctx(root: Path):
    import learnloop_sidecar.handlers  # noqa: F401
    from learnloop_sidecar.context import SidecarContext

    shutil.copytree(FIXTURE_VAULT, root)
    context = SidecarContext()
    context.load(root)
    return context


# --- facet_field + list_facets --------------------------------------------


def test_knowledge_map_facet_field_lock_fields(tmp_path):
    ctx = _blueprint_ctx(tmp_path / "vault")
    result = _call(ctx, "get_knowledge_map", {})

    # Lock state now rides on each facet-field point (HEAD's {points, ...} shape).
    field = {row["id"]: row for row in result["facetField"]["points"]}
    assert set(field) == {COMP_A, COMP_B, INTEG}
    # Every facet is in the active goal's certified scope, so all are locked.
    for row in field.values():
        assert row["locked"] is True
        assert isinstance(row["lockSources"], list)
        assert row["lockSources"] == sorted(row["lockSources"])  # distinct + sorted
        assert "goal_certified_scope" in row["lockSources"]
    assert field[COMP_A]["title"] == "Component A"


def test_facet_field_reflects_fixture_locks(tmp_path):
    ctx = _fixture_ctx(tmp_path / "vault")
    result = _call(ctx, "get_knowledge_map", {})
    points = result["facetField"]["points"]
    assert points

    from learnloop.curriculum.curriculum_locks import identity_locks

    vault, repository = ctx.require_vault()
    expected: dict[str, set[str]] = {}
    for facet_id, reasons in identity_locks(vault, repository).items():
        canonical = vault.canonical_facet_id(facet_id)
        expected.setdefault(canonical, set()).update(reason.source for reason in reasons)
    for point in points:
        sources = sorted(expected.get(point["id"], set()))
        assert point["locked"] is bool(sources)
        assert point["lockSources"] == sources


def test_list_facets_shape_and_sorting(tmp_path):
    ctx = _blueprint_ctx(tmp_path / "vault")
    result = _call(ctx, "list_facets", {})
    facets = result["facets"]
    assert [f["id"] for f in facets] == sorted([COMP_A, COMP_B, INTEG])
    for facet in facets:
        assert set(facet) == {"id", "title", "kind", "status", "locked"}
        assert facet["locked"] is True


# --- get_facet_detail ------------------------------------------------------


def test_get_facet_detail_full_contract(tmp_path):
    ctx = _blueprint_ctx(tmp_path / "vault")
    # Resolve through an ALIAS to exercise canonical resolution.
    result = _call(ctx, "get_facet_detail", {"facetId": "comp_a_alias"})

    facet = result["facet"]
    assert facet["id"] == COMP_A  # canonicalized
    assert facet["kind"] == "procedure_contract"
    assert facet["claim"] == "Execute component A."
    assert facet["preconditions"] == ["needs x"]
    assert facet["positiveExamples"] == ["a good case"]
    assert facet["negativeExamples"] == ["a bad case"]
    assert facet["nonGoals"] == ["not this"]
    assert facet["errorSignatures"] == ["typical slip"]
    assert facet["aliases"] == ["comp_a_alias"]
    assert facet["status"] == "reviewed"

    # Lock chip: verbatim reasons with source + detail.
    assert result["lock"]["locked"] is True
    sources = {reason["source"] for reason in result["lock"]["reasons"]}
    assert "goal_certified_scope" in sources
    for reason in result["lock"]["reasons"]:
        assert set(reason) == {"source", "detail"}

    # Membership: the blueprint recipe component that references COMP_A.
    assert result["membership"] == [
        {
            "learningObjectId": LO_ID,
            "loTitle": "Composite skill",
            "blueprintId": "bp_solve",
            "recipeId": "recipe_main",
            "capability": "procedure_execution",
            "modality": "hard",
            "role": "all_of",
        }
    ]

    # Evidence: readiness pair, evidence mass, capability ledger with flags.
    evidence = result["evidence"]
    assert set(evidence) == {"ready", "readyGhost", "evidenceMass", "capabilityLedger"}
    assert evidence["ready"] is None or 0.0 <= evidence["ready"] <= 1.0
    assert evidence["evidenceMass"] >= 0.0
    assert evidence["capabilityLedger"], "expected a capability ledger row"
    for cell in evidence["capabilityLedger"]:
        assert set(cell) == {
            "capability",
            "directPositiveMass",
            "directNegativeMass",
            "certificationCredit",
            "demonstrated",
        }
        assert isinstance(cell["demonstrated"], bool)

    # Only one LO exercises COMP_A -> nothing shared beyond the first.
    assert result["sharedWith"] == []


def test_get_facet_detail_integration_role(tmp_path):
    ctx = _blueprint_ctx(tmp_path / "vault")
    result = _call(ctx, "get_facet_detail", {"facetId": INTEG})
    assert result["membership"][0]["role"] == "integration"
    assert result["membership"][0]["capability"] == "coordination"


def test_get_facet_detail_unknown_facet_raises(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    ctx = _blueprint_ctx(tmp_path / "vault")
    with pytest.raises(SidecarError) as excinfo:
        _call(ctx, "get_facet_detail", {"facetId": "facet_does_not_exist"})
    assert excinfo.value.code == "not_found"


# --- preview_knowledge_map -------------------------------------------------


def test_preview_knowledge_map_baseline_matches_live_map(tmp_path):
    ctx = _fixture_ctx(tmp_path / "vault")
    live = _call(ctx, "get_knowledge_map", {})
    preview = _call(ctx, "preview_knowledge_map", {"addedEdges": [], "removedEdgeIds": []})

    # Baseline geometry is byte-identical to the live map, and a no-op edit
    # leaves the proposed geometry equal to the baseline.
    live_xy = {p["id"]: (p["x"], p["y"]) for p in live["points"]}
    base_xy = {p["id"]: (p["x"], p["y"]) for p in preview["baseline"]["points"]}
    prop_xy = {p["id"]: (p["x"], p["y"]) for p in preview["points"]}
    assert base_xy == live_xy
    assert prop_xy == base_xy
    assert preview["baseline"]["stress"] == pytest.approx(live["stress"])
    assert preview["stress"] == pytest.approx(preview["baseline"]["stress"])


def test_preview_knowledge_map_new_edge_changes_geometry(tmp_path):
    ctx = _fixture_ctx(tmp_path / "vault")
    # A prerequisite edge between two previously-distant concepts pulls their
    # items together; geometry (or at least stress) should move.
    preview = _call(
        ctx,
        "preview_knowledge_map",
        {
            "addedEdges": [
                {
                    "source": "concept_complex_multiplication",
                    "target": "concept_linear_independence_and_basis",
                    "relationType": "prerequisite",
                }
            ],
            "removedEdgeIds": [],
        },
    )
    base_xy = {p["id"]: (p["x"], p["y"]) for p in preview["baseline"]["points"]}
    prop_xy = {p["id"]: (p["x"], p["y"]) for p in preview["points"]}
    assert set(base_xy) == set(prop_xy)
    assert prop_xy != base_xy  # the hypothetical edge moved something


def test_preview_knowledge_map_removed_edge_and_determinism(tmp_path):
    ctx = _fixture_ctx(tmp_path / "vault")
    params = {
        "addedEdges": [],
        # A real edge id plus an unknown one (the unknown must be ignored).
        "removedEdgeIds": [
            "edge_prerequisite__concept_vector_space_operations__concept_vector_space_axioms",
            "edge_bogus_missing",
        ],
    }
    first = _call(ctx, "preview_knowledge_map", params)
    second = _call(ctx, "preview_knowledge_map", params)
    assert first == second  # deterministic, unknown ids silently ignored
    base_xy = {p["id"]: (p["x"], p["y"]) for p in first["baseline"]["points"]}
    prop_xy = {p["id"]: (p["x"], p["y"]) for p in first["points"]}
    assert prop_xy != base_xy  # the real removal still exercises the preview


def test_preview_knowledge_map_unknown_concept_raises(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    ctx = _fixture_ctx(tmp_path / "vault")
    with pytest.raises(SidecarError) as excinfo:
        _call(
            ctx,
            "preview_knowledge_map",
            {
                "addedEdges": [
                    {"source": "concept_ghost", "target": "concept_vector_space_axioms", "relationType": "related"}
                ],
                "removedEdgeIds": [],
            },
        )
    assert excinfo.value.code == "invalid_request"


# --- preview_blueprint_readiness -------------------------------------------


def test_preview_blueprint_readiness_dropping_integration_raises_readiness(tmp_path):
    ctx = _blueprint_ctx(tmp_path / "vault")
    proposed_blueprints = [
        {
            "id": "bp_solve",
            "weight": 1.0,
            "recipes": [
                {
                    "id": "recipe_main",
                    "composition": "conjunctive",
                    "all_of": [
                        {"facet": COMP_A, "capability": "procedure_execution"},
                        {"facet": COMP_B, "capability": "schema_interpretation"},
                    ],
                    # integration gate removed
                }
            ],
        }
    ]
    result = _call(
        ctx,
        "preview_blueprint_readiness",
        {"learningObjectId": LO_ID, "blueprints": proposed_blueprints},
    )

    assert set(result) == {
        "version",
        "current",
        "proposed",
        "identifiabilityWarnings",
        "affectedGoals",
    }
    assert result["current"]["readiness"] is not None
    assert result["proposed"]["readiness"] is not None
    # Removing the (untested, gating) integration factor can only help readiness.
    assert result["proposed"]["readiness"] >= result["current"]["readiness"]
    assert "bottleneck" in result["current"]

    assert isinstance(result["identifiabilityWarnings"], list)
    assert {"goalId": "goal_master", "title": "Master the composite skill"} in result[
        "affectedGoals"
    ]

    # The loaded vault must be untouched (integration still present).
    vault, _repository = ctx.require_vault()
    assert vault.learning_objects[LO_ID].blueprints[0].recipes[0].integration is not None


def test_preview_blueprint_readiness_unknown_lo_raises(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    ctx = _blueprint_ctx(tmp_path / "vault")
    with pytest.raises(SidecarError) as excinfo:
        _call(ctx, "preview_blueprint_readiness", {"learningObjectId": "lo_ghost", "blueprints": []})
    assert excinfo.value.code == "not_found"


def test_preview_blueprint_readiness_malformed_payload_raises(tmp_path):
    from learnloop_sidecar.errors import SidecarError

    ctx = _blueprint_ctx(tmp_path / "vault")
    # ``recipes`` must be a list of recipe objects, not a string.
    with pytest.raises(SidecarError) as excinfo:
        _call(
            ctx,
            "preview_blueprint_readiness",
            {"learningObjectId": LO_ID, "blueprints": [{"id": "bp", "recipes": "nope"}]},
        )
    assert excinfo.value.code == "invalid_payload"
