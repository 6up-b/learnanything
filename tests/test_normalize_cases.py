"""The normalizer's branches the bootstrap and append goldens do not reach, pinned on small answers.

Each case builds a plain answer (``SourceSetSynthesis`` or ``AppendReconciliation``), runs the normalizer on a small
applied study map and compares everything it returns (rows, gate items, diagnostics, id lists) with a golden file under
``tests/goldens/synthesis_normalize/``. The ULID stream is seeded, so minted ids are part of what is compared.
Regenerate with ``NORMALIZE_GOLDEN_WRITE=1 uv run pytest tests/test_normalize_cases.py`` and read the difference.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.content.facet_identity.plan import FacetIdentityPlan, Retirement
from learnloop.content.synthesis.ai_contracts import (
    AppendProvenanceLink,
    AppendReconciliation,
    AppendRestructure,
    ConceptRelation,
    SourceSetSynthesis,
    SynthBlueprint,
    SynthConcept,
    SynthCriterion,
    SynthCriterionTarget,
    SynthFacet,
    SynthIntegrationComponent,
    SynthLearningObject,
    SynthPracticeItem,
    SynthRecipe,
    SynthRecipeComponent,
    SynthRequiredMethod,
    SynthSpanRef,
)
from learnloop.content.synthesis.source_append import _normalize_append

from tests.facet_authority_helpers import EXAM_CLAIM, NOW, SUBJECT
from tests.facet_reword_paths_helpers import NEW_SPAN, SYMMETRY, TEXT_SPAN
from tests.normalize_helpers import check, run, seed_ids, world


@pytest.fixture(autouse=True)
def _seeded(monkeypatch):
    seed_ids(monkeypatch)


def _concept(client, title, **kwargs):
    return SynthConcept(client_item_id=client, title=title, **kwargs)


def _lo(client, concept, **kwargs):
    return SynthLearningObject(client_item_id=client, concept_client_id=concept, title=f"Learn {client}", **kwargs)


def test_concept_references_resolve_by_title_by_entity_id_or_mint_a_concept(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    synth = SourceSetSynthesis(
        concepts=[
            _concept("c_gram", "Gram matrix"),
            _concept("c_k1", "Kernel"),
            _concept("c_k2", "Kernel"),
            _concept("c_x", "Rank", id="concept_rank_entity"),
            SynthConcept(client_item_id="c_untitled"),
            SynthConcept(client_item_id="c_dup_a", id="concept_dup", title="Dup A"),
            SynthConcept(client_item_id="c_dup_b", id="concept_dup", title="Dup B"),
        ],
        learning_objects=[
            # a title (one concept answers), an entity id of a client-keyed concept, and an ambiguous title
            SynthLearningObject(client_item_id="lo_by_title", title="By title", concept_id="Gram matrix",
                                prerequisites=["Kernel", "ghost"], confusable_concept_client_ids=["c_gram", "c_nope"],
                                prerequisite_concept_client_ids=["c_x"]),
            SynthLearningObject(client_item_id="lo_by_entity", title="By entity", concept_id="concept_rank_entity",
                                prerequisites=["concept_symmetric_matrix", "Symmetric matrix"]),
            SynthLearningObject(client_item_id="lo_ambiguous", title="Ambiguous", concept_id="Kernel"),
            SynthLearningObject(client_item_id="lo_anchorless", title="Ambiguous", summary="no anchor"),
            SynthLearningObject(client_item_id="lo_registry", title="Registry", concept_id="concept_symmetric_matrix"),
        ],
    )
    check("concept_references", run(synth, vault, inputs))


def test_edges_drop_what_cannot_stand_and_keep_the_floor_from_prerequisites(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    # Registry edges the new ones are checked against.
    vault.edges.extend([
        SimpleNamespace(source="concept_symmetric_matrix", target="c_registry_parent", relation_type="part_of"),
        SimpleNamespace(source="c_registry_parent", target="c_registry_root", relation_type="prerequisite"),
    ])
    relation = lambda s, t, kind, **kw: ConceptRelation(source=s, target=t, relation_type=kind, **kw)  # noqa: E731
    synth = SourceSetSynthesis(
        concepts=[_concept(name, name.upper()) for name in ("a", "b", "c", "d", "e", "p1", "p2", "p3", "p4", "px")],
        learning_objects=[_lo("lo_a", "a", prerequisite_concept_client_ids=["b"], confusable_concept_client_ids=["d"])],
        concept_relations=[
            relation("a", "b", "prerequisite"),
            relation("b", "c", "prerequisite", rationale="b first", strength=0.5),
            relation("c", "a", "prerequisite"),  # closes a cycle
            relation("a", "a", "related"),  # a self edge
            relation("a", "b", "prerequisite"),  # a duplicate
            relation("a", "ghost", "related"),  # an endpoint nothing answers
            relation("", "b", "related"),
            relation("d", "e", "confusable_with"),
            relation("e", "d", "confusable_with"),  # the same pair reversed
            relation("a", "b", "part_of"),
            relation("a", "c", "part_of"),  # a second parent
            relation("b", "a", "part_of"),  # closes a hierarchy cycle
            relation("concept_symmetric_matrix", "e", "part_of"),  # the registry already parents it
            relation("c", "concept_symmetric_matrix", "related"),
            relation("c_registry_root", "a", "prerequisite"),
            relation("a", "c_registry_parent", "related"),
            # a diamond, then an edge into its head: the cycle search meets p4 twice
            relation("p1", "p2", "prerequisite"), relation("p1", "p3", "prerequisite"),
            relation("p2", "p4", "prerequisite"), relation("p3", "p4", "prerequisite"),
            relation("px", "p1", "prerequisite"),
        ],
    )
    check("edges", run(synth, vault, inputs))


def _facet(client, claim, *, concept="c_sym", **kwargs):
    return SynthFacet(client_item_id=client, id=kwargs.pop("id", f"facet_{client}"), concept_client_id=concept,
                      claim=claim, provenance=kwargs.pop("provenance", [SynthSpanRef(**TEXT_SPAN, relation="primary")]),
                      **kwargs)


def test_blueprints_default_flag_and_drop_capabilities_and_depend_on_each_facet_once(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    comp = lambda client, cap=None, **kw: SynthRecipeComponent(facet_client_id=client, capability=cap, **kw)  # noqa: E731
    integ = lambda facet, cap=None: SynthIntegrationComponent(facet_client_id=facet, capability=cap)  # noqa: E731
    synth = SourceSetSynthesis(
        concepts=[_concept("c_sym", "Symmetry")],
        facets=[_facet("f_one", "One holds."), _facet("f_two", "Two holds."), _facet("f_three", "Three holds.")],
        learning_objects=[_lo("lo_one", "c_sym")],
        blueprints=[
            SynthBlueprint(client_item_id="bp_one", learning_object_client_id="lo_one", weight=2.0, recipes=[
                SynthRecipe(id="r_one", all_of=[comp("f_one"), comp("f_one", "retrieval"), comp("f_two", "procedure_execution")],
                            any_of=[comp("f_two", "method_selection", modality="facilitating")],
                            integration=integ("f_one", "coordination")),
                SynthRecipe(id="r_two", all_of=[comp("f_one", "retrieval")], integration=integ("f_two")),
                SynthRecipe(all_of=[comp("", "retrieval", facet="facet_spectral_applicability")],
                            integration=integ("f_three", "procedure_execution")),
            ]),
            SynthBlueprint(learning_object_id="lo_diagonalize_symmetric", recipes=[SynthRecipe(all_of=[comp("f_one")])]),
        ],
    )
    check("blueprints", run(synth, vault, inputs))


def test_practice_items_flag_defaults_drop_dependencies_and_hold_a_method_to_its_target(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    crit = lambda cid, *targets, **kw: SynthCriterion(id=cid, description=cid, targets=list(targets), **kw)  # noqa: E731
    tgt = lambda facet, cap=None, **kw: SynthCriterionTarget(facet_client_id=facet, capability=cap, **kw)  # noqa: E731
    items = [
        SynthPracticeItem(
            client_item_id="pi_plain", learning_object_client_id="lo_one", prompt="State it.", expected_answer="It.",
            evidence_facet_client_ids=["f_one"], evidence_facets=["f_one", "facet_spectral_applicability"],
            criteria=[crit("k1", tgt("f_one"), tgt("f_two", "retrieval", role="supporting")),
                      crit("k2", depends_on=["k1", "k1", "elsewhere", "k2"], correlation_group="g")],
            provenance=[SynthSpanRef(**TEXT_SPAN, relation="exercise")],
        ),
        SynthPracticeItem(
            client_item_id="pi_method_dropped", learning_object_client_id="lo_one", prompt="Compute det(A).",
            evidence_facet_client_ids=["f_one"], criteria=[crit("m", tgt("f_one", "retrieval"))],
            required_method=SynthRequiredMethod(name="cofactor expansion", criterion_ids=["m"]),
        ),
        SynthPracticeItem(
            client_item_id="pi_method_kept", learning_object_client_id="lo_proc", prompt="Compute det(A) without cofactor expansion.",
            evidence_facet_client_ids=["f_proc"], criteria=[crit("p", tgt("f_proc", "procedure_execution"))],
            required_method=SynthRequiredMethod(name="cofactor expansion", criterion_ids=["p"]),
        ),
    ]
    synth = SourceSetSynthesis(
        concepts=[_concept("c_sym", "Symmetry"), SynthConcept(client_item_id="c_proc", title="Cofactor expansion", type="procedure")],
        facets=[_facet("f_one", "One holds."), _facet("f_two", "Two holds."),
                SynthFacet(client_item_id="f_proc", id="facet_proc", concept_client_id="c_proc", kind="procedure_contract",
                           claim="Expand along a row.", provenance=[SynthSpanRef(**TEXT_SPAN, relation="primary")])],
        learning_objects=[_lo("lo_one", "c_sym"), _lo("lo_proc", "c_proc")],
        practice_items=items,
    )
    check("practice_items", run(synth, vault, inputs))
    check("practice_items_off", run(synth, vault, inputs, items_off=True))


class _RaisingNominator:
    def __getattr__(self, name):
        raise RuntimeError("nominator down")


def test_a_failing_nominator_is_recorded_beside_the_mint_verdicts_and_never_fails_the_build(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    synth = SourceSetSynthesis(concepts=[_concept("c_sym", "Symmetry")], facets=[_facet("f_one", "One holds.")])
    check("nominator_fails", run(synth, vault, inputs, nominator=_RaisingNominator()))


def test_retirements_that_name_no_candidate_no_survivor_or_a_retired_survivor_are_skipped(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    in_run = lambda client, survivor: Retirement(  # noqa: E731
        client_id=client, scope="in_run", action="merge", absorb_as=None, survivor_client=survivor, group_id="g")
    plan = FacetIdentityPlan(status="judged", retirements={
        "f_ghost": in_run("f_ghost", "f_one"),  # no such candidate
        "f_two": in_run("f_two", "f_missing"),  # no such survivor
        "f_three": in_run("f_three", "f_two"),  # its survivor is itself retired
        "f_four": Retirement(client_id="f_four", scope="attach", action="merge", absorb_as=None,
                             survivor_facet="facet_not_registered", group_id="g"),
        "f_five": in_run("f_five", "f_one"),
    })
    synth = SourceSetSynthesis(
        concepts=[_concept("c_sym", "Symmetry")],
        facets=[_facet("f_one", "One holds."), _facet("f_two", "Two holds."), _facet("f_three", "Three holds."),
                _facet("f_four", "Four holds."), _facet("f_five", "Five holds.", id=SYMMETRY)],
    )
    check("retirements_skipped", run(synth, vault, inputs, facet_identity_plan=plan))


def test_a_reword_of_a_registered_facet_that_only_exam_material_supports_is_kept_as_it_is(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    synth = SourceSetSynthesis(
        concepts=[_concept("c_sym", "Symmetry")],
        facets=[_facet("f_again", EXAM_CLAIM, id=SYMMETRY, provenance=[SynthSpanRef(**NEW_SPAN, relation="primary")]),
                _facet("f_ref", "Spectral.", id="facet_spectral_applicability", provenance=[])],
        blueprints=[SynthBlueprint(client_item_id="bp", learning_object_id="lo_diagonalize_symmetric", recipes=[
            SynthRecipe(all_of=[SynthRecipeComponent(facet_client_id="f_again", capability="retrieval")])])],
    )
    check("reword_refused", run(synth, vault, inputs))


def _append(vault, inputs, answer, **kwargs):
    return _normalize_append(answer, inputs, vault, NOW, subject_id=SUBJECT, **kwargs)


def test_an_append_drops_an_exam_link_to_a_facet_and_carries_a_restructure_of_another_kind(tmp_path):
    vault, inputs, _repo = world(tmp_path)
    answer = AppendReconciliation.model_validate({
        "provenance_links": [
            AppendProvenanceLink(client_item_id="pl_exam", target_entity_type="facet", target_entity_id=SYMMETRY,
                                 span=SynthSpanRef(**NEW_SPAN)).model_dump(),
            AppendProvenanceLink(client_item_id="pl_ok", target_entity_type="facet", target_entity_id=SYMMETRY,
                                 span=SynthSpanRef(**TEXT_SPAN)).model_dump(),
            AppendProvenanceLink(client_item_id="pl_blank", target_entity_type="facet", target_entity_id=SYMMETRY).model_dump(),
        ],
        "restructures": [
            AppendRestructure(client_item_id="rs_lo", target_entity_type="learning_object",
                              target_entity_id="lo_diagonalize_symmetric", operation="update",
                              payload={"title": "Diagonalize symmetric matrices"}, expected_target_hash="h").model_dump(),
        ],
    })
    check("append_links_restructure", _append(vault, inputs, answer))
