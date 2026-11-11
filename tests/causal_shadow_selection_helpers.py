"""What other test files use from ``tests/test_causal_shadow_selection.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault


CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
PASSING_REVIEW = {
    "contract_consistent": True,
    "measurement_target_independence": True,
    "undeclared_differences": [],
}


def _write_probe_item(paths, item_id: str, *, criteria: list[str]) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": ["diagnostic_probe"],
            "evidence_facets": [],
            "prompt": "Which factor makes the product valid?",
            "expected_answer": "The transposed one.",
            "difficulty": 0.4,
            "tags": [],
            "grading_rubric": {
                "max_points": len(criteria),
                "criteria": [
                    {
                        "id": criterion,
                        "points": 1,
                        "description": f"Checks {criterion}.",
                        "measurement_status": "item_local",
                    }
                    for criterion in criteria
                ],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _seed_factor(
    repository: Repository,
    *,
    first_repair: str | None = "repair:recall",
    second_repair: str | None = "repair:method",
    attempt_id: str = "att_shadow",
    with_targets: bool = False,
) -> tuple[str, str, str]:
    common = {
        "attempt_id": attempt_id,
        "learning_object_id": LO_ID,
        "cause_scope": "learner_state",
        "applicability": {"practice_item_id": "pi_svd_define_001"},
        "evidence": {"trace_consistent": True},
        "status": "candidate",
        "postdictive_claims": [],
        "clock": CLOCK,
    }
    first = repository.append_causal_hypothesis(
        **common,
        episode_key=f"{attempt_id}:first",
        statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available",
        operation="recall_omission",
        target_ref=(
            {"kind": "criterion", "criterion_id": "criterion_recall"}
            if with_targets
            else {"kind": "criterion", "criterion_id": "correctness"}
        ),
        repair_class_id=first_repair,
    )
    second = repository.append_causal_hypothesis(
        **common,
        episode_key=f"{attempt_id}:second",
        statement="The learner selected the wrong convention.",
        statement_normalized="the learner selected the wrong convention",
        operation="method_selection",
        target_ref=(
            {"kind": "criterion", "criterion_id": "criterion_method"}
            if with_targets
            else {"kind": "criterion", "criterion_id": "correctness"}
        ),
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


def _vault(tmp_path, *, probe_item: bool = False):
    paths = create_basic_vault(tmp_path / "vault")
    if probe_item:
        _write_probe_item(
            paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
        )
    vault = load_vault(paths.root)
    return vault, Repository(paths.sqlite_path)
