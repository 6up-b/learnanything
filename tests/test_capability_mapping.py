from __future__ import annotations

from learnloop.services.capability_mapping import (
    allocate_success_mass,
    compile_criterion_targets,
    criterion_pseudo_mass,
    default_capability_for,
    is_valid_capability,
    unregistered_facet_errors,
)
from learnloop.vault.models import CriterionTarget, PracticeItem, RubricCriterion


def _item(**overrides) -> PracticeItem:
    data = {
        "id": "pi_1",
        "learning_object_id": "lo_1",
        "practice_mode": "constructed_response",
        "evidence_facets": ["facet_a", "facet_b"],
        "prompt": "P",
        "expected_answer": "A",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    data.update(overrides)
    return PracticeItem(**data)


def test_default_capability_mapping_table():
    assert default_capability_for("retrieval") == "retrieval"
    assert default_capability_for("short_answer") == "schema_interpretation"
    assert default_capability_for("constructed_response") == "procedure_execution"
    assert default_capability_for("multiple_choice") == "retrieval"
    # Transfer-tier criteria escalate to method selection regardless of mode.
    assert default_capability_for("constructed_response", tier="transfer") == "method_selection"
    # Unknown mode falls back conservatively (not retrieval, not coordination).
    assert default_capability_for("mystery_mode") == "schema_interpretation"


def test_authored_targets_override_defaults():
    authored = CriterionTarget(facet="facet_a", capability="coordination", role="primary")
    criterion = RubricCriterion(id="c1", points=4, description="x", targets=[authored])
    item = _item()
    targets = compile_criterion_targets(item, criterion)
    assert targets == [authored]


def test_legacy_criterion_compiles_to_mode_default_capability():
    criterion = RubricCriterion(id="c1", points=4, description="x")
    item = _item(criterion_facet_weights={"c1": {"facet_a": 1.0}})
    targets = compile_criterion_targets(item, criterion)
    assert [(t.facet, t.capability, t.role) for t in targets] == [
        ("facet_a", "procedure_execution", "primary")
    ]


def test_inference_mass_sums_to_evidence_mass_across_rubric():
    # Two criteria splitting a 4-point rubric earn total pseudo-mass == evidence
    # mass of the attempt type (§5.4 launch allocation rule).
    evidence_mass = 1.0
    rubric_total = 4.0
    c1 = criterion_pseudo_mass(3.0, rubric_total, evidence_mass)
    c2 = criterion_pseudo_mass(1.0, rubric_total, evidence_mass)
    assert abs((c1 + c2) - evidence_mass) < 1e-9


def test_supporting_role_gets_less_mass_than_primary():
    targets = [
        CriterionTarget(facet="facet_a", capability="retrieval", role="primary"),
        CriterionTarget(facet="facet_b", capability="retrieval", role="supporting"),
    ]
    allocations = allocate_success_mass(targets, criterion_pseudo_mass=1.0)
    by_facet = {a.facet: a.pseudo_mass for a in allocations}
    assert by_facet["facet_a"] > by_facet["facet_b"]
    assert abs(sum(by_facet.values()) - 1.0) < 1e-9
    # Role weights 1.0 / 0.3 normalized.
    assert abs(by_facet["facet_a"] - (1.0 / 1.3)) < 1e-9


def test_capability_vocabulary_validation():
    assert is_valid_capability("method_selection")
    assert not is_valid_capability("fluency")


def test_unregistered_facet_errors_flags_unknown_only():
    known = {"facet_a", "facet_b"}
    errors = unregistered_facet_errors(known, ["facet_a", "facet_missing"])
    assert len(errors) == 1
    assert "facet_missing" in errors[0]
