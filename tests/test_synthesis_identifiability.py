"""Synthesis-time identifiability gate (knowledge-model §11.3, ING M6 §8.7).

The real check the M5 gate stubbed: non-identifiable distinctions emit a
generate-discriminator need FIRST; a coarsening item only when no distinguishing
assessment exists AND the instructional repairs are identical.
"""

from __future__ import annotations

from learnloop.services.identifiability import (
    ProposalView,
    analyze_identifiability,
    build_proposal_view,
)
from learnloop.services.source_set_synthesis import create_study_map

from tests.test_source_set_synthesis import FakeSynthesisClient, _default_payload, _setup


def test_duplicate_signature_distinct_repairs_generates_discriminator():
    view = build_proposal_view(
        facets=[
            {"id": "f_a", "instructional_repairs": ["repair A"]},
            {"id": "f_b", "instructional_repairs": ["repair B"]},
        ],
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "g", "facet": "f_a", "capability": "retrieval", "role": "primary"},
            {"criterion_id": "c1", "correlation_group": "g", "facet": "f_b", "capability": "retrieval", "role": "primary"},
        ],
        recipe_components=[],
    )
    findings = analyze_identifiability(view)
    kinds = {f.kind for f in findings}
    assert "generate_discriminator" in kinds
    assert not any(f.kind == "coarsen_distinction" for f in findings)


def test_duplicate_signature_identical_repairs_coarsens():
    view = build_proposal_view(
        facets=[
            {"id": "f_a", "instructional_repairs": ["same repair"]},
            {"id": "f_b", "instructional_repairs": ["same repair"]},
        ],
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "g", "facet": "f_a", "capability": "retrieval", "role": "primary"},
            {"criterion_id": "c1", "correlation_group": "g", "facet": "f_b", "capability": "retrieval", "role": "primary"},
        ],
        recipe_components=[],
    )
    findings = analyze_identifiability(view)
    coarsen = [f for f in findings if f.kind == "coarsen_distinction"]
    assert coarsen and set(coarsen[0].facet_ids) == {"f_a", "f_b"}


def test_missing_anchor_for_required_facet_capability():
    view = build_proposal_view(
        facets=[{"id": "f_a", "instructional_repairs": ["r"]}],
        criterion_targets=[],  # nothing primarily observes it
        recipe_components=[{"facet": "f_a", "capability": "method_selection"}],
    )
    findings = analyze_identifiability(view)
    assert any(f.detail == "missing_anchor" and f.capability == "method_selection" for f in findings)


def test_capability_confounding_within_a_facet():
    view = ProposalView(
        facet_repairs={"f_a": ("r",)},
        criterion_targets=[
            {"criterion_id": "c1", "facet": "f_a", "capability": "retrieval", "role": "primary"},
            {"criterion_id": "c1", "facet": "f_a", "capability": "method_selection", "role": "primary"},
        ],
        recipe_components=[],
    )
    findings = analyze_identifiability(view)
    assert any(f.detail == "capability_confounding" for f in findings)


def test_identifiable_proposal_has_no_findings():
    view = build_proposal_view(
        facets=[{"id": "f_a", "instructional_repairs": ["r1"]}, {"id": "f_b", "instructional_repairs": ["r2"]}],
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "ga", "facet": "f_a", "capability": "retrieval", "role": "primary"},
            {"criterion_id": "c2", "correlation_group": "gb", "facet": "f_b", "capability": "retrieval", "role": "primary"},
        ],
        recipe_components=[
            {"facet": "f_a", "capability": "retrieval"},
            {"facet": "f_b", "capability": "retrieval"},
        ],
    )
    assert analyze_identifiability(view) == []


def _non_identifiable_builder(context, call_index):
    """Two facets sharing one correlation group with identical repairs."""

    payload = _default_payload(context)
    # collapse both facets' repairs to the same string and observe them jointly.
    for facet in payload.facets:
        facet.instructional_repairs = ["contrast symmetric and orthogonal matrices"]
    # make the second practice item observe the SAME correlation group as the first,
    # targeting the second facet — so both facets share signature "g".
    payload.practice_items[0].criteria[0].correlation_group = "g"
    payload.practice_items[1].criteria[0].correlation_group = "g"
    payload.practice_items[1].criteria[0].targets[0].facet_client_id = "f_spectral"
    payload.practice_items[0].criteria[0].targets[0].facet_client_id = "f_def"
    return payload


def test_non_identifiable_bootstrap_persists_generation_need(tmp_path):
    root, repo = _setup(tmp_path, with_exam=False)
    client = FakeSynthesisClient(builder=_non_identifiable_builder)
    result = create_study_map(root, "set_la", client=client, repository=repo, clock=None)
    # the identifiability finding surfaces as a review diagnostic...
    assert any(d["gate"] == "identifiability" for d in result.gate_diagnostics)
    # ...and a coarsen need is persisted through the generation-needs machinery.
    needs = repo.synthesis_generation_needs(subject_id="linear-algebra")
    assert needs
    assert any(n["need_kind"] in {"coarsen_distinction", "generate_discriminator"} for n in needs)
