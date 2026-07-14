from __future__ import annotations

from learnloop.services.synthesis_gates import (
    GateContext,
    GateItem,
    GateProposal,
    ProvenanceRef,
    run_synthesis_gates,
)


def _run(proposal: GateProposal, ctx: GateContext | None = None):
    return run_synthesis_gates(proposal, ctx or GateContext())


def _assert_typed(diagnostic) -> None:
    assert diagnostic.gate
    assert diagnostic.severity in {"hard_fail", "review"}
    assert isinstance(diagnostic.entity_refs, tuple)
    assert diagnostic.message
    assert diagnostic.suggested_action


def test_each_gate_emits_typed_diagnostic():
    """§14: each quality gate -> a typed diagnostic (never a generic failure)."""

    fired: dict[str, str] = {}

    def record(report):
        for diagnostic in report.diagnostics:
            _assert_typed(diagnostic)
            fired[diagnostic.gate] = diagnostic.severity

    # span_resolution
    record(
        _run(
            GateProposal(items=[GateItem("a", "facet", entity_id="f1", provenance=[ProvenanceRef(extraction_id="e1", span_id="missing")])]),
            GateContext(extraction_spans={"e1": {"s1"}}),
        )
    )
    # scope
    record(
        _run(
            GateProposal(items=[GateItem("a", "facet", entity_id="f1", provenance=[ProvenanceRef(revision_id="rev_bad")])]),
            GateContext(selected_revision_ids={"rev_ok"}),
        )
    )
    # unit_id_validity
    record(
        _run(
            GateProposal(items=[GateItem("a", "facet", entity_id="f1", provenance=[ProvenanceRef(extraction_id="e1", unit_id="u_bad")])]),
            GateContext(extraction_units={"e1": {"u_ok"}}),
        )
    )
    # conflict_disposition
    record(_run(GateProposal(conflict_candidates=["cand_1"])))
    # lock_guard
    record(_run(GateProposal(items=[GateItem("a", "learning_object", operation="update", entity_id="lo1", lock_reason="LO has attempts")])))
    # adequate_provenance
    record(_run(GateProposal(items=[GateItem("a", "facet", entity_id="f1")])))
    # criterion_target
    record(
        _run(
            GateProposal(items=[GateItem("a", "rubric", entity_id="pi1", payload={"criteria": [{"id": "c1", "targets": [{"facet": "unregistered"}]}]})]),
        )
    )
    # criterion_dag (cycle)
    record(
        _run(
            GateProposal(items=[GateItem("a", "rubric", entity_id="pi1", payload={"criteria": [{"id": "c1", "depends_on": ["c2"]}, {"id": "c2", "depends_on": ["c1"]}]})]),
        )
    )
    # recipe_validity (no recipe)
    record(_run(GateProposal(items=[GateItem("a", "learning_object", entity_id="lo1", payload={"blueprints": [{"id": "bp1", "recipes": []}]})])))
    # dependency_closure (dangling requirement)
    record(_run(GateProposal(items=[GateItem("a", "learning_object", entity_id="lo1", depends_on=["not_in_proposal"])])))
    # exam_authority
    record(_run(GateProposal(items=[GateItem("a", "facet", entity_id="f1", provenance=[ProvenanceRef(role="exam", relation="assessment_alignment")])])))
    # held_out_leakage
    record(
        _run(
            GateProposal(items=[GateItem("a", "practice_item", entity_id="pi1", is_teaching_or_practice=True, embedded_span_ids=["held1"])]),
            GateContext(held_out_span_ids={"held1"}),
        )
    )
    # token_truncation
    record(_run(GateProposal(items=[GateItem("a", "facet", entity_id="f1")]), GateContext(truncated=True)))
    # practice_exam_only
    record(_run(GateProposal(items=[GateItem("a", "practice_item", entity_id="pi1", provenance=[ProvenanceRef(role="exam", relation="assessment_alignment")])])))
    # duplicate_ids
    record(
        _run(
            GateProposal(items=[GateItem("a", "facet", entity_id="dup"), GateItem("b", "facet", entity_id="dup")]),
            GateContext(near_duplicate_threshold=1.1),  # keep near-dup gate quiet here
        )
    )
    # dangling_edge
    record(_run(GateProposal(items=[GateItem("a", "concept_edge", entity_id="edge1", payload={"source": "missing", "target": "also_missing"})])))
    # near_duplicate_facet
    record(
        _run(
            GateProposal(items=[
                GateItem("a", "facet", entity_id="f1", payload={"claim": "the determinant is multiplicative"}),
                GateItem("b", "facet", entity_id="f2", payload={"claim": "the determinant is multiplicative"}),
            ])
        )
    )
    # identifiability (degenerate duplicate signature + identical repairs)
    record(
        _run(
            GateProposal(items=[
                GateItem("a", "facet", entity_id="f1", payload={"claim": "same claim", "instructional_repairs": ["r"]}),
                GateItem("b", "facet", entity_id="f2", payload={"claim": "same claim", "instructional_repairs": ["r"]}),
            ]),
            GateContext(near_duplicate_threshold=1.1),
        )
    )

    expected = {
        "span_resolution": "hard_fail",
        "scope": "hard_fail",
        "unit_id_validity": "hard_fail",
        "conflict_disposition": "hard_fail",
        "lock_guard": "hard_fail",
        "adequate_provenance": "review",
        "criterion_target": "hard_fail",
        "criterion_dag": "hard_fail",
        "recipe_validity": "hard_fail",
        "dependency_closure": "hard_fail",
        "exam_authority": "hard_fail",
        "held_out_leakage": "hard_fail",
        "token_truncation": "hard_fail",
        "practice_exam_only": "review",
        "duplicate_ids": "hard_fail",
        "dangling_edge": "hard_fail",
        "near_duplicate_facet": "review",
        "identifiability": "review",
    }
    for gate, severity in expected.items():
        assert gate in fired, f"gate {gate} never fired"
        assert fired[gate] == severity, f"gate {gate} severity {fired[gate]} != {severity}"


def test_clean_proposal_passes_all_gates():
    proposal = GateProposal(
        items=[
            GateItem("f", "facet", entity_id="facet_det", payload={"claim": "det is multiplicative"}, provenance=[ProvenanceRef(role="primary_textbook", relation="primary", revision_id="rev_1", extraction_id="e1", unit_id="u1", span_id="s1")]),
            GateItem("lo", "learning_object", entity_id="lo_det", depends_on=["f"], provenance=[ProvenanceRef(role="primary_textbook", relation="support", revision_id="rev_1", extraction_id="e1", unit_id="u1", span_id="s1")]),
        ]
    )
    ctx = GateContext(
        registered_facet_ids={"facet_det"},
        selected_revision_ids={"rev_1"},
        extraction_units={"e1": {"u1"}},
        extraction_spans={"e1": {"s1"}},
    )
    report = run_synthesis_gates(proposal, ctx)
    assert not report.blocked
    assert not report.requires_review


def test_report_separates_hard_fail_and_review():
    proposal = GateProposal(
        items=[
            GateItem("a", "facet", entity_id="f1"),  # adequate_provenance review
            GateItem("b", "learning_object", operation="update", entity_id="lo1", lock_reason="locked"),  # lock_guard hard_fail
        ]
    )
    report = run_synthesis_gates(proposal, GateContext())
    assert any(d.gate == "lock_guard" for d in report.hard_fails)
    assert any(d.gate == "adequate_provenance" for d in report.reviews)
    assert report.blocked and report.requires_review


def test_exam_authority_allows_manual_override():
    proposal = GateProposal(
        items=[GateItem("a", "facet", entity_id="f1", manual_authority=True, provenance=[ProvenanceRef(role="exam", relation="assessment_alignment")])]
    )
    report = run_synthesis_gates(proposal, GateContext())
    assert not any(d.gate == "exam_authority" for d in report.diagnostics)
