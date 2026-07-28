"""Bounded deferral for promotion-blocking unresolved-cause factors.

Every deferral exit is evidence-labeled on the factor row (migration 148):

(a) repair_confirmed     — cold verification success resolves the factor and
                           WITHDRAWS the candidate belief (no promotion);
(b) escalated_unrepaired — cold verification failure, or K unengaged
                           recurrences, resolve the factor TOWARD promotion;
(c) expired_unengaged    — TTL passes with no engagement; the factor retires.

Plus the diagnosis-kind checkpoint-targeting gap in remediation ranking.
"""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.causal_factor_deferral import (
    ESCALATION_RECURRENCE_K,
    FACTOR_DEFERRAL_TTL,
    apply_cold_verification_to_factors,
    sweep_promotion_blocking_factors,
)
from learnloop.services.causal_probe_coherence import (
    record_delayed_cold_verification,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, create_basic_vault

LO_ID = "lo_svd_definition"
ITEM_A = "pi_diag_transpose_a"
ITEM_B = "pi_diag_transpose_b"
STATEMENT = "the learner does not recall which factor is transposed"
DIAG_REF = {
    "kind": "facet_capability",
    "facet_id": "recall",
    "capability": "retrieval",
}
DURABLE_STATUSES = ("active", "resolving", "resolved")


def _clock(**delta) -> FrozenClock:
    return FrozenClock(NOW + timedelta(**delta))


def _write_diag_item(paths, item_id: str, prompt: str) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": [
                "diagnostic_probe",
                "independent_attempt",
                "dont_know",
            ],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": prompt,
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


def _vault(tmp_path):
    from learnloop.services.state_sync import sync_vault_state
    from tests.helpers import set_algorithm_version

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    # The promotion-discipline path under test (`_normalize_compositional`)
    # runs only in canonical-state vaults.
    set_algorithm_version(paths, "mvp-0.8")
    _write_diag_item(paths, ITEM_A, "Which SVD factor is transposed?")
    _write_diag_item(paths, ITEM_B, "In U S V^T, which factor carries the T?")
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=_clock())
    return vault, repository


def _failed_diagnostic(vault, repository, *, attempt_id, item_id, clock):
    """A failed diagnostic administration, through the live post-attempt path.

    `apply_attempt` materializes the causal episode (opening the repair-lane
    factor); `evaluate_attempt_intervention_followup` is the seam the sidecar
    drives next, and it is where normalization (and therefore the deferral
    sweep and any promotion) runs.
    """

    from learnloop.services.followups import evaluate_attempt_intervention_followup

    now_iso = clock.now().isoformat().replace("+00:00", "Z")
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U",
                attempt_type="diagnostic_probe",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0.0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Named an untransposed factor.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": now_iso,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type="conceptual_slip",
                        severity=0.7,
                        evidence="The learner named an untransposed factor.",
                        resolution_status="unresolved",
                        cause_scope="learner_state",
                        operation="recall_omission",
                        target_criterion_ids=["correctness"],
                        is_misconception=True,
                        misconception_statement=STATEMENT,
                        candidate_causes=[
                            {
                                "statement": STATEMENT,
                                "cause_scope": "learner_state",
                                "target_ref": DIAG_REF,
                            }
                        ],
                    )
                ],
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
        clock=clock,
    )
    evaluate_attempt_intervention_followup(
        vault, repository, result=result, clock=clock
    )
    return result


def _failed_ordinary(
    vault,
    repository,
    *,
    attempt_id,
    item_id,
    clock,
    error_type="conceptual_slip",
    is_misconception=True,
    candidate_cause_scope="learner_state",
):
    """A failed ORDINARY attempt (G10), through the live post-attempt path."""

    from learnloop.services.followups import evaluate_attempt_intervention_followup

    now_iso = clock.now().isoformat().replace("+00:00", "Z")
    candidate_cause = {"statement": STATEMENT, "target_ref": DIAG_REF}
    if candidate_cause_scope is not None:
        candidate_cause["cause_scope"] = candidate_cause_scope
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="U",
                attempt_type="independent_attempt",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0.0},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": "correctness",
                        "points_awarded": 0.0,
                        "evidence": "Named an untransposed factor.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": now_iso,
                    }
                ],
                error_attributions=[
                    GradeAttribution(
                        error_type=error_type,
                        severity=0.7,
                        evidence="The learner named an untransposed factor.",
                        resolution_status="unresolved",
                        operation="recall_omission",
                        target_criterion_ids=["correctness"],
                        is_misconception=is_misconception,
                        misconception_statement=(
                            STATEMENT if is_misconception else None
                        ),
                        candidate_causes=[candidate_cause],
                    )
                ],
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
        clock=clock,
    )
    evaluate_attempt_intervention_followup(
        vault, repository, result=result, clock=clock
    )
    return result


def _clean_attempt(vault, repository, *, attempt_id, item_id, clock, rubric_score=4):
    now_iso = clock.now().isoformat().replace("+00:00", "Z")
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="V",
                attempt_type="independent_attempt",
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
                        "evidence": "Judged against the transpose rule.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": now_iso,
                    }
                ],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
                feedback_md="",
                repair_suggestions=[],
            ),
        ),
        clock=clock,
    )


def _open_factor(repository, attempt_id):
    factors = repository.unresolved_cause_factors_for_attempt(attempt_id)
    assert len(factors) == 1, factors
    return factors[0]


def _factor_repair_class(factor) -> tuple[str, list[str]]:
    concrete = [
        cause
        for cause in factor["candidate_causes"]
        if not cause.get("open_set") and cause.get("hypothesis_id")
    ]
    repair_class_ids = [
        str(cause["repair_class_id"])
        for cause in concrete
        if cause.get("repair_class_id")
    ]
    assert repair_class_ids
    return repair_class_ids[0], [str(cause["hypothesis_id"]) for cause in concrete]


def _durable_misconceptions(repository):
    return repository.misconceptions_for_learning_object(
        LO_ID, statuses=DURABLE_STATUSES
    )


def _cold_verification(vault, repository, *, source_attempt_id, cold_attempt_id,
                       repair_class_id, hypothesis_ids, clock):
    return record_delayed_cold_verification(
        vault,
        repository,
        source_attempt_id=source_attempt_id,
        cold_attempt_id=cold_attempt_id,
        repair_class_id=repair_class_id,
        hypothesis_ids=hypothesis_ids,
        avoided_affordances=["primed_repair_context"],
        clock=clock,
    )


# --- (a) repair confirmed ----------------------------------------------------


def test_successful_cold_verification_resolves_factor_and_withdraws_belief(tmp_path):
    vault, repository = _vault(tmp_path)
    _failed_diagnostic(
        vault, repository, attempt_id="att_src", item_id=ITEM_A, clock=_clock()
    )
    factor = _open_factor(repository, "att_src")
    repair_class_id, hypothesis_ids = _factor_repair_class(factor)
    assert _durable_misconceptions(repository) == []
    assert repository.misconception_candidate_by_normalized(LO_ID, STATEMENT)

    _clean_attempt(
        vault, repository, attempt_id="att_cold", item_id=ITEM_B, clock=_clock(days=2)
    )
    receipt = _cold_verification(
        vault,
        repository,
        source_attempt_id="att_src",
        cold_attempt_id="att_cold",
        repair_class_id=repair_class_id,
        hypothesis_ids=hypothesis_ids,
        clock=_clock(days=2),
    )
    assert receipt["success"] is True

    closed = repository.unresolved_cause_factor(str(factor["id"]))
    assert closed["status"] == "resolved"
    assert closed["resolution_kind"] == "repair_confirmed"
    assert closed["resolution_detail"]["cold_verification_id"] == receipt["id"]

    # The candidate belief is withdrawn through the hypothesis disposition
    # machinery: the episode head is a retired version carrying the reason.
    hypothesis = repository.causal_hypothesis(hypothesis_ids[0])
    head = repository.latest_causal_hypothesis_for_episode(hypothesis["episode_key"])
    assert head["status"] == "retired"
    assert head["evidence"]["withdrawal"] == {
        "reason": "repair_confirmed",
        "cold_verification_id": receipt["id"],
    }

    # Confirmed-and-fixed: nothing promotes, and nothing is left to promote.
    assert _durable_misconceptions(repository) == []
    assert repository.misconception_candidate_by_normalized(LO_ID, STATEMENT) is None
    # Promotion is no longer blocked for the attempt.
    assert repository.unresolved_cause_factors_for_attempt("att_src") == []

    # Idempotent: replaying the routing changes nothing further.
    version = int(head["version"])
    assert apply_cold_verification_to_factors(
        repository, receipt=receipt, clock=_clock(days=2)
    ) == []
    head_again = repository.latest_causal_hypothesis_for_episode(
        hypothesis["episode_key"]
    )
    assert int(head_again["version"]) == version


def test_repair_success_does_not_touch_diagnosis_support(tmp_path):
    vault, repository = _vault(tmp_path)
    _failed_diagnostic(
        vault, repository, attempt_id="att_ds", item_id=ITEM_A, clock=_clock()
    )
    factor = _open_factor(repository, "att_ds")
    repair_class_id, hypothesis_ids = _factor_repair_class(factor)
    _clean_attempt(
        vault, repository, attempt_id="att_ds_cold", item_id=ITEM_B, clock=_clock(days=2)
    )
    receipt = _cold_verification(
        vault,
        repository,
        source_attempt_id="att_ds",
        cold_attempt_id="att_ds_cold",
        repair_class_id=repair_class_id,
        hypothesis_ids=hypothesis_ids,
        clock=_clock(days=2),
    )
    # The existing guard stands: the verification's diagnosis-support channel
    # stays at zero even though the repair-effect exit resolved the factor.
    assert receipt["diagnosis_support_update"]["delta"] == 0.0


# --- (b) escalation ----------------------------------------------------------


def test_failed_cold_verification_escalates_then_recurrence_promotes(tmp_path):
    vault, repository = _vault(tmp_path)
    _failed_diagnostic(
        vault, repository, attempt_id="att_e1", item_id=ITEM_A, clock=_clock()
    )
    factor = _open_factor(repository, "att_e1")
    repair_class_id, hypothesis_ids = _factor_repair_class(factor)

    _clean_attempt(
        vault,
        repository,
        attempt_id="att_e_cold",
        item_id=ITEM_B,
        clock=_clock(days=2),
        rubric_score=0,
    )
    receipt = _cold_verification(
        vault,
        repository,
        source_attempt_id="att_e1",
        cold_attempt_id="att_e_cold",
        repair_class_id=repair_class_id,
        hypothesis_ids=hypothesis_ids,
        clock=_clock(days=2),
    )
    assert receipt["success"] is False

    escalated = repository.unresolved_cause_factor(str(factor["id"]))
    assert escalated["status"] == "resolved"
    assert escalated["resolution_kind"] == "escalated_unrepaired"
    assert escalated["resolution_detail"]["trigger"] == "cold_verification_failure"
    assert escalated["resolution_detail"]["cold_verification_id"] == receipt["id"]
    assert _durable_misconceptions(repository) == []

    # The next materialization of the recurring signature promotes: the fresh
    # factor it opens closes immediately (sticky escalation), the block lifts,
    # and the two-surface candidate promotes via the independent-surface arm.
    _failed_diagnostic(
        vault, repository, attempt_id="att_e2", item_id=ITEM_B, clock=_clock(days=3)
    )
    durable = _durable_misconceptions(repository)
    assert [record.statement for record in durable] == [STATEMENT]
    assert durable[0].promotion_reason == "independent_surface"
    follow_on = repository.unresolved_cause_factors_for_attempt(
        "att_e2", status="resolved"
    )
    assert len(follow_on) == 1


def test_unengaged_recurrences_escalate_and_promote(tmp_path):
    vault, repository = _vault(tmp_path)
    _failed_diagnostic(
        vault, repository, attempt_id="att_k1", item_id=ITEM_A, clock=_clock()
    )
    first_factor = _open_factor(repository, "att_k1")

    # K-1 further recurrences: still deferred, nothing promotes.
    for index in range(1, ESCALATION_RECURRENCE_K):
        _failed_diagnostic(
            vault,
            repository,
            attempt_id=f"att_k{index + 1}",
            item_id=ITEM_B,
            clock=_clock(days=index),
        )
    assert _durable_misconceptions(repository) == []

    # The Kth recurrence escalates during ITS OWN normalization, so the same
    # materialization promotes the durable misconception.
    _failed_diagnostic(
        vault,
        repository,
        attempt_id=f"att_k{ESCALATION_RECURRENCE_K + 1}",
        item_id=ITEM_B,
        clock=_clock(days=ESCALATION_RECURRENCE_K),
    )
    durable = _durable_misconceptions(repository)
    assert [record.statement for record in durable] == [STATEMENT]

    escalated = repository.unresolved_cause_factor(str(first_factor["id"]))
    assert escalated["status"] == "resolved"
    assert escalated["resolution_kind"] == "escalated_unrepaired"
    detail = escalated["resolution_detail"]
    assert detail["trigger"] == "unengaged_recurrences"
    assert detail["k"] == ESCALATION_RECURRENCE_K
    assert len(detail["recurrence_attempt_ids"]) >= ESCALATION_RECURRENCE_K


def test_engagement_keeps_the_deferral_window_open(tmp_path):
    vault, repository = _vault(tmp_path)
    _failed_diagnostic(
        vault, repository, attempt_id="att_g1", item_id=ITEM_A, clock=_clock()
    )
    factor = _open_factor(repository, "att_g1")
    _repair_class_id, hypothesis_ids = _factor_repair_class(factor)

    # The learner engaged the case's repair lane (TEACH_ME_NOW mints exactly
    # this row), so recurrences do NOT escalate.
    repository.get_or_create_open_remediation_episode(
        case_kind="diagnosis",
        case_ref=hypothesis_ids[0],
        states=("diagnosis", "prescribed", "treatment"),
        clock=_clock(hours=1),
    )
    for index in range(1, ESCALATION_RECURRENCE_K + 2):
        _failed_diagnostic(
            vault,
            repository,
            attempt_id=f"att_g{index + 1}",
            item_id=ITEM_B,
            clock=_clock(days=index),
        )
    assert _durable_misconceptions(repository) == []
    still_open = repository.unresolved_cause_factor(str(factor["id"]))
    assert still_open["status"] == "open"
    assert still_open["resolution_kind"] is None


# --- (c) expiry --------------------------------------------------------------


def test_expiry_retires_unengaged_factor_and_sweep_is_idempotent(tmp_path):
    vault, repository = _vault(tmp_path)
    _failed_diagnostic(
        vault, repository, attempt_id="att_ttl", item_id=ITEM_A, clock=_clock()
    )
    factor = _open_factor(repository, "att_ttl")

    # Inside the TTL nothing happens.
    assert sweep_promotion_blocking_factors(repository, clock=_clock(days=10)) == []
    assert repository.unresolved_cause_factor(str(factor["id"]))["status"] == "open"

    expired_clock = FrozenClock(NOW + FACTOR_DEFERRAL_TTL + timedelta(days=1))
    actions = sweep_promotion_blocking_factors(repository, clock=expired_clock)
    assert [action["resolution_kind"] for action in actions] == ["expired_unengaged"]

    retired = repository.unresolved_cause_factor(str(factor["id"]))
    assert retired["status"] == "retired"
    assert retired["resolution_kind"] == "expired_unengaged"
    assert retired["resolution_detail"]["ttl_days"] == FACTOR_DEFERRAL_TTL.days
    # Promotion is no longer blocked for the factor's attempt.
    assert repository.unresolved_cause_factors_for_attempt("att_ttl") == []

    # Idempotent: a second sweep finds nothing open and changes nothing.
    assert sweep_promotion_blocking_factors(repository, clock=expired_clock) == []
    again = repository.unresolved_cause_factor(str(factor["id"]))
    assert again["status"] == "retired"
    assert again["updated_at"] == retired["updated_at"]


# --- Task 2: diagnosis-kind checkpoint targeting -----------------------------


def _add_ranked_item(root, item_id: str, *, facets, checkpoints=None) -> None:
    from learnloop.vault.writer import upsert_practice_item

    payload: dict = {
        "id": item_id,
        "learning_object_id": LO_ID,
        "subjects": None,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": facets,
        "evidence_weights": {facet: 1.0 for facet in facets},
        "prompt": f"Item {item_id}.",
        "expected_answer": "A factorization into U, Sigma, and V transpose.",
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {"id": "correctness", "points": 4, "description": "Correct."}
            ],
            "fatal_errors": [],
        },
        "created_at": "2026-05-19T12:00:00Z",
        "updated_at": "2026-05-19T12:00:00Z",
    }
    if checkpoints:
        payload["trace_contract"] = {
            "status": "available",
            "recipes": [
                {
                    "id": f"recipe_{item_id}",
                    "checkpoints": checkpoints,
                    "dependencies": {checkpoint: [] for checkpoint in checkpoints},
                }
            ],
        }
    upsert_practice_item(root, payload, clock=FrozenClock(NOW))


def test_diagnosis_case_ranks_checkpoint_covering_item_first(tmp_path):
    from learnloop.services.remediation import (
        _case_target_checkpoint_ids,
        start_remediation_treatment,
    )
    from tests.helpers import seed_due_item

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    seed_due_item(paths)
    # Lower facet overlap than the seeded recall item, but it exercises the
    # repair class's targeted checkpoint.
    _add_ranked_item(
        root, "pi_svd_trace_003", facets=["application"],
        checkpoints=["apply_transpose"],
    )
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)

    hypothesis = repository.append_causal_hypothesis(
        episode_key="att_diag_case:first",
        attempt_id="att_diag_case",
        learning_object_id=LO_ID,
        cause_scope="learner_state",
        statement=STATEMENT,
        statement_normalized=STATEMENT,
        operation="recall_omission",
        target_ref=DIAG_REF,
        applicability={"practice_item_id": "pi_svd_define_001"},
        evidence={},
        repair_class_id="rc_diag_case",
        status="candidate",
        clock=FrozenClock(NOW),
    )
    repository.record_causal_repair_class_definitions(
        [
            {
                "repair_class_id": "rc_diag_case",
                "repair_equivalence_id": "req_diag_case",
                "episode_id": "att_diag_case",
                "operator": "restate_transpose_rule",
                "repair_policy_version": "test",
                "target_refs": [
                    {"kind": "item_step", "checkpoint_id": "apply_transpose"},
                    DIAG_REF,
                ],
                "preserve_refs": [],
                "definition": {},
            }
        ],
        clock=FrozenClock(NOW),
    )

    case = repository.misconception_candidate_by_id(str(hypothesis["id"]))
    assert case is not None
    assert _case_target_checkpoint_ids(
        repository,
        case,
        case_kind="diagnosis",
        case_ref=str(hypothesis["id"]),
    ) == ("apply_transpose",)

    episode = repository.get_or_create_open_remediation_episode(
        case_kind="diagnosis",
        case_ref=str(hypothesis["id"]),
        states=("diagnosis",),
        clock=FrozenClock(NOW),
    )
    result = start_remediation_treatment(
        vault, repository, episode["id"], clock=FrozenClock(NOW)
    )
    # The checkpoint-covering item wins the primed slot despite its weaker
    # facet overlap; the cold pick inherits the same ranked list.
    assert result["primed_item_id"] == "pi_svd_trace_003"
    assert result["cold_item_id"] != "pi_svd_trace_003"


def test_diagnosis_case_without_repair_class_falls_back_to_facets(tmp_path):
    from learnloop.services.remediation import _case_target_checkpoint_ids

    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    repository = Repository(paths.sqlite_path)
    hypothesis = repository.append_causal_hypothesis(
        episode_key="att_diag_unmapped:first",
        attempt_id="att_diag_unmapped",
        learning_object_id=LO_ID,
        cause_scope="learner_state",
        statement=STATEMENT,
        statement_normalized=STATEMENT,
        target_ref=DIAG_REF,
        applicability={},
        evidence={},
        repair_class_id=None,
        status="candidate",
        clock=FrozenClock(NOW),
    )
    case = repository.misconception_candidate_by_id(str(hypothesis["id"]))
    assert _case_target_checkpoint_ids(
        repository,
        case,
        case_kind="diagnosis",
        case_ref=str(hypothesis["id"]),
    ) == ()


# --- G10: ordinary nontrivial failures open the repair lane ------------------


def test_ordinary_nontrivial_failure_opens_repair_factor(tmp_path):
    vault, repository = _vault(tmp_path)
    result = _failed_ordinary(
        vault, repository, attempt_id="att_ord", item_id=ITEM_A, clock=_clock()
    )
    factor = _open_factor(repository, result.attempt_id)
    assert factor["observation_id"] is None
    repair_class_id, hypothesis_ids = _factor_repair_class(factor)
    assert repair_class_id and hypothesis_ids
    # G11 rides along: the learner-derived hypotheses are learner_state, so
    # the candidate projection (and therefore the repair offer) sees them.
    assert repository.misconception_candidate_by_normalized(LO_ID, STATEMENT)


def test_ordinary_trivial_slip_opens_no_factor(tmp_path):
    vault, repository = _vault(tmp_path)
    result = _failed_ordinary(
        vault,
        repository,
        attempt_id="att_slip",
        item_id=ITEM_A,
        clock=_clock(),
        error_type="arithmetic_slip",  # -> local_slip: excluded
        is_misconception=False,
    )
    for status in ("open", "resolved", "retired"):
        assert (
            repository.unresolved_cause_factors_for_attempt(
                result.attempt_id, status=status
            )
            == []
        )


def test_ordinary_failure_escalation_still_promotes(tmp_path):
    """G10 widens promotion deferral to ordinary attempts; the bounded exits
    still bound it — a cold failure escalates, and the recurring signature
    promotes on its next materialization."""

    vault, repository = _vault(tmp_path)
    _failed_ordinary(
        vault, repository, attempt_id="att_oe1", item_id=ITEM_A, clock=_clock()
    )
    factor = _open_factor(repository, "att_oe1")
    repair_class_id, hypothesis_ids = _factor_repair_class(factor)
    assert _durable_misconceptions(repository) == []

    _clean_attempt(
        vault,
        repository,
        attempt_id="att_oe_cold",
        item_id=ITEM_B,
        clock=_clock(days=2),
        rubric_score=0,
    )
    receipt = _cold_verification(
        vault,
        repository,
        source_attempt_id="att_oe1",
        cold_attempt_id="att_oe_cold",
        repair_class_id=repair_class_id,
        hypothesis_ids=hypothesis_ids,
        clock=_clock(days=2),
    )
    assert receipt["success"] is False
    escalated = repository.unresolved_cause_factor(str(factor["id"]))
    assert escalated["resolution_kind"] == "escalated_unrepaired"

    _failed_ordinary(
        vault, repository, attempt_id="att_oe2", item_id=ITEM_B, clock=_clock(days=3)
    )
    durable = _durable_misconceptions(repository)
    assert [record.statement for record in durable] == [STATEMENT]
    assert durable[0].promotion_reason == "independent_surface"


# --- G15: observation-keyed factors join the deferral exits ------------------


def _seed_observation_factor(
    repository, *, attempt_id: str, observation_id: str, repair_class_id: str
):
    hypothesis = repository.append_causal_hypothesis(
        episode_key=f"{attempt_id}:cause",
        attempt_id=attempt_id,
        learning_object_id=LO_ID,
        cause_scope="learner_state",
        statement=STATEMENT,
        statement_normalized=STATEMENT,
        operation="recall_omission",
        target_ref=DIAG_REF,
        applicability={"observation_id": observation_id},
        evidence={},
        repair_class_id=repair_class_id,
        status="candidate",
        clock=_clock(),
    )
    factor_id = repository.insert_unresolved_cause_factor(
        attempt_id=attempt_id,
        candidate_causes=[
            {"hypothesis_id": hypothesis["id"], "version": hypothesis["version"]},
            {"hypothesis_id": "H_OTHER", "open_set": True},
        ],
        algorithm_version="mvp-0.8",
        observation_id=observation_id,
        clock=_clock(),
    )
    return factor_id, hypothesis


def test_cold_success_resolves_observation_keyed_factor(tmp_path):
    _vault_obj, repository = _vault(tmp_path)
    factor_id, hypothesis = _seed_observation_factor(
        repository,
        attempt_id="att_obs",
        observation_id="obs_g15",
        repair_class_id="rc_obs",
    )
    actions = apply_cold_verification_to_factors(
        repository,
        receipt={"id": "cv_g15", "repair_class_id": "rc_obs", "success": True},
        clock=_clock(days=2),
    )
    assert [
        (action["factor_id"], action["resolution_kind"]) for action in actions
    ] == [(factor_id, "repair_confirmed")]

    closed = repository.unresolved_cause_factor(factor_id)
    assert closed["status"] == "resolved"
    assert closed["resolution_kind"] == "repair_confirmed"
    # Belief withdrawal uses the same retired-hypothesis-version mechanism as
    # the attempt-keyed factors — refs hydrate identically.
    head = repository.latest_causal_hypothesis_for_episode(
        str(hypothesis["episode_key"])
    )
    assert head["status"] == "retired"
    assert head["evidence"]["withdrawal"]["reason"] == "repair_confirmed"

    # Idempotent re-application: nothing left open to act on.
    assert (
        apply_cold_verification_to_factors(
            repository,
            receipt={"id": "cv_g15", "repair_class_id": "rc_obs", "success": True},
            clock=_clock(days=2),
        )
        == []
    )


def test_projection_sync_does_not_resurrect_deferral_closed_factors(tmp_path):
    from learnloop.services.canonical_projection import (
        _sync_unresolved_cause_factors,
    )

    _vault_obj, repository = _vault(tmp_path)
    resolved_id, _hyp = _seed_observation_factor(
        repository,
        attempt_id="att_obs_r",
        observation_id="obs_resolved",
        repair_class_id="rc_r",
    )
    apply_cold_verification_to_factors(
        repository,
        receipt={"id": "cv_r", "repair_class_id": "rc_r", "success": True},
        clock=_clock(days=2),
    )
    retired_id, _hyp2 = _seed_observation_factor(
        repository,
        attempt_id="att_obs_t",
        observation_id="obs_retired",
        repair_class_id="rc_t",
    )
    assert repository.close_unresolved_cause_factor(
        retired_id,
        status="retired",
        resolution_kind="expired_unengaged",
        resolution_detail={"ttl_days": FACTOR_DEFERRAL_TTL.days},
        clock=_clock(days=31),
    )

    # The projection still sees both failures (and one genuinely new one).
    wanted = [
        {
            "attempt_id": "att_obs_r",
            "observation_id": "obs_resolved",
            "candidate_causes": [{"statement": STATEMENT}],
        },
        {
            "attempt_id": "att_obs_t",
            "observation_id": "obs_retired",
            "candidate_causes": [{"statement": STATEMENT}],
        },
        {
            "attempt_id": "att_obs_new",
            "observation_id": "obs_new",
            "candidate_causes": [{"statement": STATEMENT}],
        },
    ]
    _sync_unresolved_cause_factors(repository, wanted, clock=_clock(days=31))

    # Neither deferral-closed factor is re-opened or duplicated; the sync
    # still inserts the genuinely new failure.
    factors = repository.unresolved_cause_factors(status=None)
    by_observation = {
        str(factor.get("observation_id")): factor for factor in factors
    }
    assert by_observation["obs_resolved"]["id"] == resolved_id
    assert by_observation["obs_resolved"]["status"] == "resolved"
    assert by_observation["obs_retired"]["id"] == retired_id
    assert by_observation["obs_retired"]["status"] == "retired"
    assert by_observation["obs_retired"]["resolution_kind"] == "expired_unengaged"
    assert by_observation["obs_new"]["status"] == "open"
    assert len(factors) == 3
