"""What other test files use from ``tests/test_facet_identity_ingest.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.content.synthesis.ai_contracts import (
    SynthCriterion,
    SynthCriterionTarget,
    SynthFacet,
    SynthPracticeItem,
    SynthRecipeComponent,
)

from tests.facet_identity_fakes import FakeFacetJudge
from tests.helpers import append_config_toml
from tests.source_set_synthesis_helpers import _CLOCK, _default_payload


DEF_CLAIM = "A real square matrix is symmetric exactly when A^T = A."
DUP_ID = "facet_symmetry_definition_restated"
DUP_CLAIM = "A real square matrix A is symmetric if and only if it equals its transpose."


def _with_duplicate(context, _ordinal):
    payload = _default_payload(context)
    prov = payload.facets[0].provenance
    payload.facets.append(SynthFacet(
        client_item_id="f_def_dup", id=DUP_ID, concept_client_id="c_sym", kind="definition",
        claim=DUP_CLAIM, preconditions=["the matrix is square"], positive_examples=["[[1,2],[2,1]]"],
        error_signatures=["checks only the diagonal"], instructional_repairs=["compare entries across the diagonal"],
        provenance=prov,
    ))
    payload.blueprints[0].recipes[0].all_of.append(
        SynthRecipeComponent(facet_client_id="f_def_dup", capability="retrieval"))
    payload.practice_items.append(SynthPracticeItem(
        client_item_id="pi_3", id="pi_transpose_check", learning_object_client_id="lo_diag",
        practice_mode="retrieval", prompt="When does A equal its transpose?", expected_answer="When a_ij = a_ji.",
        evidence_facet_client_ids=["f_def_dup"],
        criteria=[SynthCriterion(
            id="states_transpose_condition", points=1.0, description="States a_ij = a_ji.",
            correlation_group="transpose_condition",
            targets=[SynthCriterionTarget(facet_client_id="f_def_dup", capability="retrieval", role="primary")],
        )],
        provenance=prov,
    ))
    return payload


def _attach_absorb(tmp_path, *, absorb_as, strict=False):
    from learnloop.content.synthesis.ai_contracts import AppendReconciliation, SynthSpanRef
    from learnloop.content.synthesis.source_append import append_source

    from tests.source_append_helpers import FakeAppendClient, _bootstrap_and_add, _first_new_span

    root, repo = _bootstrap_and_add(tmp_path)
    if strict:
        # Review F2's strict lock policy: a retired key nothing reads any more.
        append_config_toml(root, "[facet_identity]\nmerge_locked_facets = false")
    restated = "Symmetry of a real square matrix means it coincides with its transpose."

    def builder(context, _n):
        ext, unit, span = _first_new_span(context)
        ref = SynthSpanRef(extraction_id=ext, unit_id=unit, span_id=span, relation="primary", role="primary_textbook")
        return AppendReconciliation(
            summary="restated definition",
            facets=[SynthFacet(client_item_id="f_new", id="facet_symmetry_restated",
                               concept_id="concept_symmetric_matrix", kind="definition", claim=restated,
                               provenance=[ref])],
        )

    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, restated]], action="absorb")
    if absorb_as == "precondition":
        original = judge.complete

        def as_precondition(request):
            verdict = original(request)
            for decided in verdict.sets:
                decided.absorb_as = "precondition"
            return verdict

        judge.complete = as_precondition  # type: ignore[method-assign]
    result = append_source(root, "set_la", client=FakeAppendClient(builder=builder), new_revision_ids=["rev_alt"],
                           repository=repo, clock=_CLOCK, facet_identity_client=judge)
    return root, repo, result, restated
