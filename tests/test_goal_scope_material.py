"""Goal scope over material that has not been authored yet.

`required_facets` derives an LO's facets from its practice ITEMS, so an LO whose
items have not been generated reported the empty set and was dropped by
`resolve_goal_scope` — the goal resolved to nothing, was created inert, and
every recovery path (`populate-goal`, the wizard's starter-practice checkbox)
routed back through the same empty scope. A goal is normally set over material
the learner has NOT practised yet, so this was the modal case, not an edge one.

These pin the fix: scope reads blueprint declarations ∪ measured facets, the
creation path refuses to write a goal that tracks nothing, the gap is reported
as fillable, and the exam defers instead of holding an exam out of a pool that
cannot support one.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml
from tests.helpers import NOW_ISO, create_basic_vault, seed_due_item

FIXTURE_VAULT = Path(__file__).resolve().parents[1] / "fixtures" / "linear_algebra"

BLUEPRINTED_LO = "lo_blueprinted_no_items"
BLUEPRINT_FACETS = ("facet_states_the_axioms", "facet_checks_closure")


def _write_blueprinted_lo(root: Path, *, concept: str = "bare_concept") -> None:
    """An ACTIVE learning object with blueprints and zero practice items."""

    from learnloop.vault.loader import load_vault

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    write_yaml(
        paths.learning_object_path("linear-algebra", BLUEPRINTED_LO),
        {
            "schema_version": 1,
            "id": BLUEPRINTED_LO,
            "title": "Read and apply the vector space definition",
            "subjects": ["linear-algebra"],
            "concept": concept,
            "knowledge_type": "definition",
            "status": "active",
            "contradicts": None,
            "summary": "Blueprinted learning object with no authored items yet.",
            "prerequisites": [],
            "confusables": [],
            "blueprints": [
                {
                    "id": "bp_definition",
                    "weight": 1.0,
                    "recipes": [
                        {
                            "id": "recipe_direct",
                            "composition": "conjunctive",
                            "all_of": [
                                {"facet": facet, "capability": "recall"}
                                for facet in BLUEPRINT_FACETS
                            ],
                        }
                    ],
                }
            ],
            "difficulty_prior": 0.55,
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _add_concept(root: Path, concept_id: str = "bare_concept") -> None:
    from learnloop.vault.loader import load_vault

    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    concepts = read_yaml(paths.concepts_path)
    concepts["concepts"][concept_id] = {
        "title": "Bare Concept",
        "type": "procedure",
        "aliases": [],
        "description": "Blueprinted, not yet authored.",
        "tags": [],
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    write_yaml(paths.concepts_path, concepts)


@pytest.fixture()
def ctx(tmp_path):
    import learnloop_sidecar.handlers  # noqa: F401 — registers methods
    from learnloop_sidecar.context import SidecarContext

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    seed_due_item(paths)
    _add_concept(root)
    _write_blueprinted_lo(root)

    context = SidecarContext()
    context.load(root)
    return context


def _call(ctx, name: str, params: dict):
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _goal_over(concepts: list[str]):
    from learnloop.vault.models import Goal

    return Goal(
        id="goal_under_test",
        title="Under test",
        creation_source="learner",
        target_recall=0.85,
        due_at=None,
        facet_scope={"concepts": concepts, "facets": []},
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )


# ── scope_facets ────────────────────────────────────────────────────────────


def test_blueprint_facets_count_when_no_items_are_authored(ctx):
    from learnloop.learner.facet_diagnostics import required_facets, scope_facets

    vault, repository = ctx.require_vault()
    # The instrument reading is unchanged: nothing is authored, so nothing is
    # measured. That distinction is the point — coverage/probe/tutor callers
    # still get the honest empty set.
    assert required_facets(vault, BLUEPRINTED_LO, repository) == set()
    assert scope_facets(vault, BLUEPRINTED_LO, repository) == set(BLUEPRINT_FACETS)


def test_scope_facets_unions_rather_than_replaces(ctx):
    """An LO WITH items keeps them — the change can never shrink a scope."""

    from learnloop.learner.facet_diagnostics import required_facets, scope_facets

    vault, repository = ctx.require_vault()
    measured = required_facets(vault, "lo_svd_definition", repository)
    assert measured, "fixture precondition: the seeded LO has authored items"
    assert measured <= scope_facets(vault, "lo_svd_definition", repository)


def test_goal_scope_resolves_over_unauthored_material(ctx):
    from learnloop.goals.goal_projection import resolve_goal_scope

    vault, repository = ctx.require_vault()
    scope = resolve_goal_scope(vault, _goal_over(["bare_concept"]), repository)
    assert set(scope) == {BLUEPRINTED_LO}
    assert scope[BLUEPRINTED_LO] == set(BLUEPRINT_FACETS)


def test_a_concept_with_no_learning_objects_still_resolves_to_nothing(ctx):
    """The blueprint fallback is not a licence to invent scope out of nothing."""

    from learnloop.goals.goal_projection import resolve_goal_scope

    vault, repository = ctx.require_vault()
    _add_concept(ctx.vault_root, "concept_with_no_los")
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    assert resolve_goal_scope(vault, _goal_over(["concept_with_no_los"]), repository) == {}


# ── material gaps ───────────────────────────────────────────────────────────


def test_material_gaps_report_the_fillable_learning_object(ctx):
    from learnloop.goals.goal_projection import goal_material_gaps

    vault, repository = ctx.require_vault()
    gaps = goal_material_gaps(vault, _goal_over(["bare_concept"]), repository)
    assert [gap["learning_object_id"] for gap in gaps] == [BLUEPRINTED_LO]
    assert gaps[0]["concept_id"] == "bare_concept"
    assert gaps[0]["scope_facet_count"] == len(BLUEPRINT_FACETS)


def test_an_authored_learning_object_is_not_a_gap(ctx):
    from learnloop.goals.goal_projection import goal_material_gaps

    vault, repository = ctx.require_vault()
    gaps = goal_material_gaps(
        vault, _goal_over(["singular_value_decomposition"]), repository
    )
    assert gaps == []


def test_feasibility_separates_fillable_gaps_from_uncovered_concepts(ctx):
    _add_concept(ctx.vault_root, "concept_with_no_los")
    ctx.reload(maintenance=False)
    out = _call(
        ctx,
        "goal_feasibility",
        {
            "title": "Mixed",
            "targetRecall": 0.85,
            "dueAt": None,
            "concepts": ["bare_concept", "concept_with_no_los"],
            "facets": [],
            "examEnabled": False,
        },
    )
    # Blueprinted-but-unauthored is a fillable gap; no-LO-at-all is uncovered.
    assert [gap["learningObjectId"] for gap in out["materialGaps"]] == [BLUEPRINTED_LO]
    assert out["uncoveredConcepts"] == ["concept_with_no_los"]
    assert out["scopeFacetCount"] > 0


# ── create_goal guard ───────────────────────────────────────────────────────


_CREATE = {
    "title": "Under test",
    "targetRecall": 0.85,
    "dueAt": None,
    "facets": [],
    "examEnabled": False,
    "populatePractice": False,
}


def test_create_goal_succeeds_over_blueprinted_material(ctx):
    out = _call(ctx, "create_goal", {**_CREATE, "concepts": ["bare_concept"]})
    assert out["goal"]["report"]["total"] == len(BLUEPRINT_FACETS)


def test_create_goal_refuses_a_concept_with_no_learning_objects(ctx):
    from learnloop_sidecar.errors import SidecarError

    _add_concept(ctx.vault_root, "concept_with_no_los")
    ctx.reload(maintenance=False)
    with pytest.raises(SidecarError) as excinfo:
        _call(ctx, "create_goal", {**_CREATE, "concepts": ["concept_with_no_los"]})
    assert excinfo.value.code == "goal_concepts_without_learning_objects"
    assert excinfo.value.details["concepts_without_learning_objects"] == [
        "concept_with_no_los"
    ]


def test_one_unmeasurable_concept_rejects_the_whole_selection(ctx):
    """Not silently dropped: carrying it would report coverage never reachable."""

    from learnloop_sidecar.errors import SidecarError

    _add_concept(ctx.vault_root, "concept_with_no_los")
    ctx.reload(maintenance=False)
    with pytest.raises(SidecarError) as excinfo:
        _call(
            ctx,
            "create_goal",
            {**_CREATE, "concepts": ["bare_concept", "concept_with_no_los"]},
        )
    assert excinfo.value.code == "goal_concepts_without_learning_objects"
    # Only the offending one is named — the measurable concept is fine.
    assert excinfo.value.details["concepts_without_learning_objects"] == [
        "concept_with_no_los"
    ]


def test_goal_population_never_authors_for_an_unmeasurable_concept(ctx):
    """`populate-goal` resolves through scope, so an LO-less concept is inert.

    Pinned because goal population is the one path that authors material from a
    goal, and it must not become a back door for generating content against a
    concept the graph has nothing to ground it in.
    """

    from learnloop.content.authoring.practice_generation import (
        PracticeExpansionError,
        build_goal_practice_plan,
    )

    _add_concept(ctx.vault_root, "concept_with_no_los")
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    goal = _goal_over(["concept_with_no_los"])
    with pytest.raises(PracticeExpansionError, match="no active learning objects"):
        build_goal_practice_plan(vault, repository, goal)


def test_goal_population_targets_only_the_measurable_concepts(ctx):
    """A mixed scope authors for the real LOs and nothing for the empty one."""

    from learnloop.content.authoring.practice_generation import build_goal_practice_plan

    _add_concept(ctx.vault_root, "concept_with_no_los")
    ctx.reload(maintenance=False)
    vault, repository = ctx.require_vault()
    goal = _goal_over(["bare_concept", "concept_with_no_los"])
    plan, _at_risk = build_goal_practice_plan(vault, repository, goal)
    assert [target.learning_object_id for target in plan.targets] == [BLUEPRINTED_LO]


def test_a_facet_only_scope_that_resolves_to_nothing_is_refused(ctx):
    """The second arm: no concepts named, so the LO check cannot catch it."""

    from learnloop_sidecar.errors import SidecarError

    with pytest.raises(SidecarError) as excinfo:
        _call(
            ctx,
            "create_goal",
            {**_CREATE, "concepts": [], "facets": ["facet_does_not_exist"]},
        )
    assert excinfo.value.code == "goal_scope_unresolved"


def test_an_empty_goal_is_still_possible_as_a_stated_intent(ctx):
    _add_concept(ctx.vault_root, "concept_with_no_los")
    ctx.reload(maintenance=False)
    out = _call(
        ctx,
        "create_goal",
        {**_CREATE, "concepts": ["concept_with_no_los"], "allowEmptyScope": True},
    )
    assert out["goal"]["report"]["total"] == 0


# ── lazy exam reservation ───────────────────────────────────────────────────


def test_creating_a_goal_no_longer_reserves_an_exam_pool(ctx):
    out = _call(
        ctx,
        "create_goal",
        {**_CREATE, "concepts": ["bare_concept"], "examEnabled": True, "examItemCount": 15},
    )
    _vault, repository = ctx.require_vault()
    assert repository.reserved_exam_pool_items(out["goal"]["id"]) == []


def test_a_thin_pool_defers_instead_of_holding_everything_out(ctx):
    from learnloop.goals.exam_pool import reserve_exam_pool

    vault, repository = ctx.require_vault()
    goal = _goal_over(["singular_value_decomposition"])
    goal = goal.model_copy(update={"exam": goal.exam.model_copy(update={"enabled": True, "item_count": 15})})
    report = reserve_exam_pool(vault, repository, goal, defer_if_insufficient=True)
    assert report.deferred is True
    assert report.deferred_reason == "insufficient_pool"
    assert report.reserved_item_ids == []
    assert repository.reserved_exam_pool_items(goal.id) == []


def test_an_explicit_ask_is_never_deferred(ctx):
    """Deferral is opt-in: `start_exam` / `exam reserve` take what exists."""

    from learnloop.goals.exam_pool import reserve_exam_pool

    vault, repository = ctx.require_vault()
    goal = _goal_over(["singular_value_decomposition"])
    goal = goal.model_copy(update={"exam": goal.exam.model_copy(update={"enabled": True, "item_count": 1})})
    report = reserve_exam_pool(vault, repository, goal)  # default: do not defer
    assert report.deferred is False
    assert len(report.reserved_item_ids) >= 1


# ── the real fixture vault ──────────────────────────────────────────────────


@pytest.mark.skipif(not FIXTURE_VAULT.exists(), reason="linear_algebra fixture absent")
def test_fixture_vault_goal_over_unauthored_concepts_resolves(tmp_path):
    """The reported case: a goal over four freshly synthesized concepts.

    Asserted as an invariant, not a golden — this vault is the live working
    fixture, so pinning counts here makes the suite fail whenever anyone uses
    it (which is exactly how the goal-decay golden broke).
    """

    from learnloop.db.repositories import Repository
    from learnloop.goals.goal_projection import goal_material_gaps, resolve_goal_scope
    from learnloop.vault.loader import load_vault

    root = tmp_path / "linear_algebra"
    shutil.copytree(FIXTURE_VAULT, root)
    vault = load_vault(root)
    repository = Repository(root / "state.sqlite")

    concepts = [
        "concept_coordinate_proofs_in_f_n",
        "concept_vector_space_axioms",
        "concept_vector_space",
    ]
    blueprinted = [
        lo_id
        for lo_id, lo in vault.learning_objects.items()
        if lo.concept in set(concepts) and lo.status == "active" and lo.blueprints
    ]
    if not blueprinted:
        pytest.skip("fixture no longer carries blueprinted LOs on these concepts")

    goal = _goal_over(concepts)
    scope = resolve_goal_scope(vault, goal, repository)
    assert set(blueprinted) <= set(scope), "blueprinted LOs must reach goal scope"
    assert sum(len(facets) for facets in scope.values()) > 0
    # Unauthored LOs surface as fillable gaps rather than vanishing.
    gap_ids = {gap["learning_object_id"] for gap in goal_material_gaps(vault, goal, repository)}
    unauthored = {
        lo_id
        for lo_id in blueprinted
        if not any(
            item.learning_object_id == lo_id for item in vault.practice_items.values()
        )
    }
    assert unauthored <= gap_ids
