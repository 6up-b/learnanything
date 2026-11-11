"""What other test files use from ``tests/test_causal_orchestrator.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_probe_coherence import (
    audit_manipulation_contract,
    create_probe_candidate,
    generate_blind_prediction_bundle,
    lock_causal_hypothesis_set,
    transition_probe_candidate,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import NOW, NOW_ISO, create_basic_vault


LO_ID = "lo_svd_definition"
PROBE_ITEM = "pi_causal_probe_001"
CLOCK = FrozenClock(NOW)


def _add_probe_item(root, item_id: str = PROBE_ITEM, surface: str = "contrast_surface"):
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": [
                "independent_attempt",
                "diagnostic_probe",
                "dont_know",
            ],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Choose which final factor makes the product valid.",
            "expected_answer": "U Sigma V^T",
            "surface_family": surface,
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "correctness",
                        "points": 4,
                        "description": "Correct definition.",
                    }
                ],
                "fatal_errors": [
                    {
                        "id": "conceptual_slip",
                        "description": "Confuses SVD with another decomposition.",
                        "max_grade": 1,
                    }
                ],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=CLOCK,
    )


def _seed_factor(
    repository: Repository,
    *,
    first_repair: str | None = "repair:recall",
    second_repair: str | None = "repair:method",
    attempt_id: str = "att_orchestrator",
) -> tuple[str, str, str]:
    """Two concrete P1 hypotheses plus the open-set arm, through the real API."""

    common = {
        "attempt_id": attempt_id,
        "learning_object_id": LO_ID,
        "cause_scope": "learner_state",
        "target_ref": {"kind": "criterion", "criterion_id": "correctness"},
        "applicability": {"practice_item_id": "pi_svd_define_001"},
        "postdictive_claims": [],
        "evidence": {"trace_consistent": True},
        "status": "candidate",
        "clock": CLOCK,
    }
    first = repository.append_causal_hypothesis(
        **common,
        episode_key=f"{attempt_id}:first",
        statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available",
        operation="recall_omission",
        repair_class_id=first_repair,
    )
    second = repository.append_causal_hypothesis(
        **common,
        episode_key=f"{attempt_id}:second",
        statement="The learner selected the wrong factorization convention.",
        statement_normalized=(
            "the learner selected the wrong factorization convention"
        ),
        operation="method_selection",
        repair_class_id=second_repair,
    )
    factor_id = repository.insert_unresolved_cause_factor(
        attempt_id=attempt_id,
        candidate_causes=[
            {"hypothesis_id": first["id"], "version": first["version"]},
            {"hypothesis_id": second["id"], "version": second["version"]},
            {"hypothesis_id": "H_OTHER", "open_set": True},
        ],
        algorithm_version="causal_attribution_p2",
        clock=CLOCK,
    )
    return factor_id, str(first["id"]), str(second["id"])


def _vault(tmp_path, *, with_probe_item: bool = False):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    if with_probe_item:
        _add_probe_item(root)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    return vault, repository, root


def _activate_probe_candidate(
    repository: Repository, factor_id: str, first_id: str, second_id: str
) -> dict:
    """Mint, review, and activate a real discriminating probe candidate."""

    locked = lock_causal_hypothesis_set(
        repository,
        factor_id,
        probe_phase_id="phase_orchestrator",
        algorithm_version="test",
        clock=CLOCK,
    )
    item = {
        "id": PROBE_ITEM,
        "prompt": "Choose which final factor makes the product valid.",
        "expected_answer": "U Sigma V^T",
        "practice_mode": "short_answer",
        "grading_rubric": {"criteria": [{"id": "correctness"}]},
    }
    first_bundle = generate_blind_prediction_bundle(
        repository,
        hypothesis_id=first_id,
        item=item,
        rubric=item["grading_rubric"],
        trace_contract=None,
        generator=lambda _safe: {"predicted_features": {"uses_transpose": False}},
        model_revision="model-r1",
        outcome_schema_version="probe-outcome-v1",
        clock=CLOCK,
    )
    second_bundle = generate_blind_prediction_bundle(
        repository,
        hypothesis_id=second_id,
        item=item,
        rubric=item["grading_rubric"],
        trace_contract=None,
        generator=lambda _safe: {"predicted_features": {"uses_transpose": True}},
        model_revision="model-r1",
        outcome_schema_version="probe-outcome-v1",
        clock=CLOCK,
    )
    source = {**item, "id": "pi_svd_define_001", "prompt": "State the SVD."}
    candidate_item = {
        **item,
        "variant_contract": {
            "variant_kind": "rung_shift",
            "intended_manipulations": [
                {"axis": "surface_wording", "direction": "increase"}
            ],
            "incidental_changes": [],
            "held_constant": ["answer_contract", "rubric", "measurement_targets"],
        },
    }
    audit = audit_manipulation_contract(
        repository,
        source_item=source,
        candidate_item=candidate_item,
        source_kind="causal_probe",
        adversarial_review={
            "contract_consistent": True,
            "measurement_target_independence": True,
            "undeclared_differences": [],
        },
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=CLOCK,
    )
    assert audit["status"] == "passed"
    probe = create_probe_candidate(
        repository,
        factor_id=factor_id,
        practice_item_id=PROBE_ITEM,
        hypothesis_set_id=str(locked.id),
        manipulation_audit_id=audit["id"],
        measurement_contract={
            "independently_compiled": True,
            "inherited_parent_facet_weights": False,
            "criteria": [
                {
                    "criterion_id": "correctness",
                    "target_ref": {"kind": "criterion", "criterion_id": "correctness"},
                }
            ],
        },
        clock=CLOCK,
    )
    for status, reviewer in (
        ("registered", None),
        ("reviewed", "owner"),
        ("active", None),
    ):
        probe = transition_probe_candidate(
            repository, probe["id"], to_status=status, reviewer=reviewer, clock=CLOCK
        )
    assert probe["status"] == "active"
    assert set(probe["blind_bundle_ids"]) == {
        first_bundle["id"],
        second_bundle["id"],
    }
    return {
        "candidate": probe,
        "first_bundle": first_bundle,
        "second_bundle": second_bundle,
        "hypothesis_set_id": str(locked.id),
    }
