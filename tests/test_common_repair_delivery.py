"""Journey B delivery: the common minimal repair reaches the learner.

Before this wiring the ``skip_common_repair`` / ``skip_action_equivalent``
arms were reachable only from learner-initiated reads, so a factor whose
plausible causes share one repair produced no recommendation anywhere —
"ambiguity never forces a question" held only because the lane was never
consulted. These tests drive the post-attempt consultation
(``followups._consult_common_repair``) and the feedback enrichment
(``handlers.feedback._attach_common_repair``) over real repository state.
"""

from __future__ import annotations

from types import SimpleNamespace

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.followups import _consult_common_repair
from learnloop.vault.loader import load_vault
from learnloop_sidecar.handlers.feedback import _attach_common_repair

from tests.helpers import NOW, create_basic_vault

LO_ID = "lo_svd_definition"
CLOCK = FrozenClock(NOW)
ATTEMPT_ID = "att_common_repair"


def _vault(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


def _seed_factor(
    repository: Repository,
    *,
    first_repair: str | None,
    second_repair: str | None,
    attempt_id: str = ATTEMPT_ID,
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
        statement_normalized="the learner selected the wrong factorization convention",
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


def _result(attempt_id: str = ATTEMPT_ID) -> SimpleNamespace:
    return SimpleNamespace(attempt_id=attempt_id, learning_object_id=LO_ID)


def _bundle(first_id: str) -> dict:
    """The camelized feedback-bundle slice `_attach_common_repair` reads."""

    return {
        "causalFeedback": {
            "probeNeed": {
                "divergent": False,
                "commonRepairCover": True,
                "incompleteRepairMapping": False,
            },
            "causalHypotheses": [{"hypothesisId": first_id}],
        }
    }


def _episode_count(repository: Repository) -> int:
    with repository.connection() as connection:
        return int(
            connection.execute(
                "SELECT COUNT(*) FROM remediation_episodes"
            ).fetchone()[0]
        )


def test_shared_repair_factor_records_the_skip_without_minting_an_episode(tmp_path):
    vault, repository = _vault(tmp_path)
    factor_id, _first, _second = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )

    _consult_common_repair(
        vault, repository, _result(), session_id=None, clock=CLOCK
    )

    receipts = repository.causal_probe_decision_receipts(factor_id=factor_id)
    assert [receipt["decision"] for receipt in receipts] == ["skip_common_repair"]
    assert receipts[0]["repair_status"] == "safe_common_repair_available"
    # Read-only consultation: the recommendation exists, the episode does not —
    # starting the repair is the learner's action on the feedback card.
    assert _episode_count(repository) == 0


def test_feedback_bundle_carries_the_recommendation_and_stamps_durable_beliefs(
    tmp_path,
):
    vault, repository = _vault(tmp_path)
    factor_id, first_id, _second = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )
    _consult_common_repair(
        vault, repository, _result(), session_id=None, clock=CLOCK
    )

    bundle = _bundle(first_id)
    _attach_common_repair(repository, ATTEMPT_ID, bundle)
    recommendation = bundle["causalFeedback"]["commonRepair"]
    assert recommendation["decision"] == "skip_common_repair"
    assert recommendation["status"] == "safe_common_repair_available"
    assert recommendation["misconceptionId"] == first_id
    assert recommendation["factorId"] == factor_id
    assert recommendation["message"]
    assert recommendation["decisionReceiptId"]
    # A provisional belief has no disposition lifecycle to withdraw from, so —
    # exactly like the Repair screen's `_case_dto` — it is not stamped.
    assert repository.surfaced_beliefs() == []

    # A durable misconception shown on this card IS an A6 exposure.
    repository.insert_misconception(
        id=first_id,
        learning_object_id=LO_ID,
        statement="The transpose rule was not available.",
        clock=CLOCK,
    )
    bundle = _bundle(first_id)
    _attach_common_repair(repository, ATTEMPT_ID, bundle)
    surfaced = repository.surfaced_beliefs()
    assert [(row["belief_kind"], row["belief_id"]) for row in surfaced] == [
        ("misconception", first_id)
    ]


def test_divergent_causes_get_no_common_repair_card(tmp_path):
    vault, repository = _vault(tmp_path)
    _factor_id, first_id, _second = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:method"
    )
    _consult_common_repair(
        vault, repository, _result(), session_id=None, clock=CLOCK
    )

    bundle = _bundle(first_id)
    bundle["causalFeedback"]["probeNeed"]["divergent"] = True
    _attach_common_repair(repository, ATTEMPT_ID, bundle)
    assert "commonRepair" not in bundle["causalFeedback"]

    # Even when the bundle's probe_need is stale/absent, a divergent factor
    # never produces a skip receipt, so nothing can attach.
    bundle = _bundle(first_id)
    _attach_common_repair(repository, ATTEMPT_ID, bundle)
    assert "commonRepair" not in bundle["causalFeedback"]


def test_receipted_divergence_skips_the_consultation_entirely(tmp_path):
    from learnloop.services.attempts import (
        AttemptDraft,
        SelfGradeInput,
        complete_self_graded_attempt,
    )
    from learnloop.services.state_sync import sync_vault_state

    vault, repository = _vault(tmp_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="An answer.",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 0}, fatal_errors=[], confidence=4
        ),
        clock=CLOCK,
    )
    attempt_id = result.attempt_id
    _seed_factor(
        repository,
        first_repair="repair:recall",
        second_repair="repair:method",
        attempt_id=attempt_id,
    )
    # The screen's learner-initiated read owns receipted divergence; the hook
    # consulting too would append a duplicate decision for the same view.
    payload = (
        '{"causal_attribution": {"diagnosis_receipt": {'
        '"schema_version": 3, "hypotheses": [], '
        '"probe_need": {"divergent": true, "repair_class_ids": [], '
        '"common_repair_cover": false, '
        '"incomplete_repair_mapping": false, '
        '"reason": "plausible causes map to different repair classes"'
        "}}}}"
    )
    with repository.connection() as connection:
        connection.execute(
            """
            INSERT INTO attempt_debug_payloads(
              attempt_id, payload_json, algorithm_version, created_at
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(attempt_id) DO UPDATE SET
              payload_json = excluded.payload_json
            """,
            (attempt_id, payload, "test", "2026-01-01T00:00:00Z"),
        )
        connection.commit()

    _consult_common_repair(
        vault,
        repository,
        _result(attempt_id),
        session_id=None,
        clock=CLOCK,
    )
    assert repository.causal_probe_decision_receipts() == []


def test_attempt_without_factors_is_untouched(tmp_path):
    vault, repository = _vault(tmp_path)

    _consult_common_repair(
        vault, repository, _result("att_no_factor"), session_id=None, clock=CLOCK
    )

    bundle = _bundle("hyp_none")
    _attach_common_repair(repository, "att_no_factor", bundle)
    assert "commonRepair" not in bundle["causalFeedback"]


# --- diagnostic administrations reach the repair lane -----------------------
#
# A vault-authored ``diagnostic_probe`` item's single-target contract never
# trips the canonical projection's multi-target ambiguity gate, so before
# ``causal_attribution._open_diagnostic_repair_factor`` a failed diagnostic
# attempt materialized hypotheses WITH mapped repair classes but no factor —
# ``causal_repair_status`` raised and the consultation above bailed at its
# first check.

DIAG_ITEM = "pi_diag_transpose_probe"
DIAG_REF = {
    "kind": "facet_capability",
    "facet_id": "recall",
    "capability": "retrieval",
}


def _diagnostic_vault(tmp_path):
    from learnloop.vault.yaml_io import write_yaml

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    write_yaml(
        paths.practice_item_path("linear-algebra", DIAG_ITEM),
        {
            "schema_version": 1,
            "id": DIAG_ITEM,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": ["diagnostic_probe", "dont_know"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": "Which SVD factor is transposed in the product?",
            "expected_answer": "V",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {
                        "id": "correctness",
                        "points": 4,
                        "description": "Correct selection.",
                    }
                ],
                "fatal_errors": [],
            },
            "created_at": "2026-05-19T12:00:00Z",
            "updated_at": "2026-05-19T12:00:00Z",
        },
    )
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    return vault, repository


def _diagnostic_attempt(
    vault,
    repository,
    *,
    attempt_id: str,
    rubric_score: int = 2,
    with_diagnosis: bool = True,
):
    from learnloop.services.attempts import (
        ApplyAttemptInput,
        AttemptDraft,
        GradeAttribution,
        ResolvedGrade,
        apply_attempt,
    )

    now_iso = "2026-05-19T12:00:00Z"
    attributions = (
        [
            GradeAttribution(
                error_type="conceptual_slip",
                severity=0.7,
                evidence="The learner named an untransposed factor.",
                resolution_status="unresolved",
                cause_scope="learner_state",
                operation="recall_omission",
                target_criterion_ids=["correctness"],
                candidate_causes=[
                    {
                        "statement": (
                            "The learner does not recall which factor is transposed."
                        ),
                        "cause_scope": "learner_state",
                        "target_ref": DIAG_REF,
                    }
                ],
            )
        ]
        if with_diagnosis
        else []
    )
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=DIAG_ITEM,
                learner_answer_md="U",
                attempt_type="diagnostic_probe",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=rubric_score,
                criterion_points={"correctness": float(rubric_score)},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": float(rubric_score),
                        "evidence": "Selection judged against the transpose rule.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": now_iso,
                    }
                ],
                error_attributions=attributions,
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
                feedback_md="Check which factor carries the transpose.",
                repair_suggestions=[
                    {
                        "practice_mode": "targeted_review",
                        "operator": "restate_transpose_rule",
                        "rationale": "Re-establish which factor is transposed.",
                        "target_refs": [DIAG_REF],
                        "expected_minutes": 3.0,
                    }
                ],
            ),
        ),
        clock=CLOCK,
    )


def _all_status_factors(repository, attempt_id: str) -> list[dict]:
    return [
        factor
        for status in ("open", "resolved", "retired")
        for factor in repository.unresolved_cause_factors_for_attempt(
            attempt_id, status=status
        )
    ]


def test_failed_diagnostic_attempt_opens_the_repair_lane(tmp_path):
    from learnloop.services.causal_orchestrator import causal_repair_status

    vault, repository = _diagnostic_vault(tmp_path)
    result = _diagnostic_attempt(
        vault, repository, attempt_id="att_diag_repair_lane"
    )

    factors = repository.unresolved_cause_factors_for_attempt(result.attempt_id)
    assert len(factors) == 1
    causes = factors[0]["candidate_causes"]
    concrete_ids = [
        str(c["hypothesis_id"]) for c in causes if not c.get("open_set")
    ]
    assert concrete_ids
    # Hydrated refs carry the mapped repair class, and the open-set arm rides
    # along (mirroring record_causal_diagnosis_contest's thinnest factor).
    assert any(c.get("repair_class_id") for c in causes)
    assert any(c.get("open_set") for c in causes)

    # The consultation the hook runs post-attempt now records its receipt.
    _consult_common_repair(
        vault, repository, _result(result.attempt_id), session_id=None, clock=CLOCK
    )
    receipts = repository.causal_probe_decision_receipts(
        factor_id=str(factors[0]["id"])
    )
    assert [receipt["decision"] for receipt in receipts] == ["skip_common_repair"]
    assert receipts[0]["repair_status"] == "safe_common_repair_available"

    # And the learner-initiated read returns a real status instead of raising.
    status = causal_repair_status(
        vault,
        repository,
        misconception_id=concrete_ids[0],
        start_repair=False,
        clock=CLOCK,
    )
    assert status.status == "safe_common_repair_available"
    assert status.factor_id == str(factors[0]["id"])


def test_diagnostic_factor_is_not_reopened_by_rematerialization(tmp_path):
    from learnloop.services.causal_attribution import materialize_causal_episode

    vault, repository = _diagnostic_vault(tmp_path)
    result = _diagnostic_attempt(
        vault, repository, attempt_id="att_diag_idempotent"
    )
    assert len(_all_status_factors(repository, result.attempt_id)) == 1

    stored = repository.fetch_attempt_feedback_metadata(result.attempt_id) or {}
    for _ in range(3):
        materialize_causal_episode(
            vault,
            repository,
            attempt_id=result.attempt_id,
            repair_suggestions=list(stored.get("repair_suggestions") or []),
            clock=CLOCK,
        )

    assert len(_all_status_factors(repository, result.attempt_id)) == 1


def test_fully_correct_diagnostic_attempt_opens_no_factor(tmp_path):
    vault, repository = _diagnostic_vault(tmp_path)
    result = _diagnostic_attempt(
        vault,
        repository,
        attempt_id="att_diag_correct",
        rubric_score=4,
        with_diagnosis=False,
    )
    assert _all_status_factors(repository, result.attempt_id) == []
