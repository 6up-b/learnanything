"""Slice 2 T1 §3.4: the K=3 deferral escalation counts recurrence groups.

The same scenario as ``test_causal_factor_deferral`` (failed diagnostic
administrations through the live post-attempt path, mvp-0.11 here), except
that the learner words the recurring belief differently after the first
time. Only a recorded ``same_cause`` verdict makes the reworded answers
recurrences of the first.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_factor_deferral import ESCALATION_RECURRENCE_K
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version
from tests.recurrence_fakes import record_verdict
from tests.test_causal_factor_deferral import DIAG_REF, ITEM_A, ITEM_B, LO_ID, _write_diag_item

FIRST = "the learner does not recall which factor is transposed"
REWORDED = "believes the transpose sits on U rather than on V"


def _clock(**delta) -> FrozenClock:
    return FrozenClock(NOW + timedelta(**delta))


def _vault(tmp_path, version):
    from learnloop.substrate.state_sync import sync_vault_state

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, version)
    _write_diag_item(paths, ITEM_A, "Which SVD factor is transposed?")
    _write_diag_item(paths, ITEM_B, "In U S V^T, which factor carries the T?")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=_clock())
    return vault, repository


def _failed(vault, repository, *, attempt_id, item_id, statement, clock):
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

    now_iso = clock.now().isoformat().replace("+00:00", "Z")
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(practice_item_id=item_id, learner_answer_md="U", attempt_type="diagnostic_probe"),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=0,
                criterion_points={"correctness": 0.0},
                evidence_rows=[{
                    "id": f"ge_{attempt_id}", "criterion_id": "correctness", "points_awarded": 0.0,
                    "evidence": "Named an untransposed factor.", "notes": None, "local_grader_id": "test",
                    "grader_tier": 1, "created_at": now_iso,
                }],
                error_attributions=[GradeAttribution(
                    error_type="conceptual_slip", severity=0.7, evidence="The learner named an untransposed factor.",
                    resolution_status="unresolved", cause_scope="learner_state", operation="recall_omission",
                    target_criterion_ids=["correctness"], is_misconception=True, misconception_statement=statement,
                    candidate_causes=[{"statement": statement, "cause_scope": "learner_state", "target_ref": DIAG_REF}],
                )],
                grader_confidence=0.9,
                confidence=3,
                manual_review_reason=None,
                feedback_md="Check which factor carries the transpose.",
                repair_suggestions=[{
                    "practice_mode": "targeted_review", "operator": "restate_transpose_rule",
                    "rationale": "Re-establish which factor is transposed.", "target_refs": [DIAG_REF],
                    "expected_minutes": 3.0,
                }],
            ),
        ),
        clock=clock,
    )
    evaluate_attempt_intervention_followup(vault, repository, result=result, clock=clock)
    return result


def _episode(repository, attempt_id):
    return next(row for row in repository.causal_hypotheses_for_attempt(attempt_id) if row["status"] != "open_set")


@pytest.mark.parametrize("merged", [True, False])
def test_reworded_recurrences_escalate_only_once_judged_the_same_cause(tmp_path, merged):
    vault, repository = _vault(tmp_path, "mvp-0.11")
    _failed(vault, repository, attempt_id="att_k1", item_id=ITEM_A, statement=FIRST, clock=_clock())
    first_factor = repository.unresolved_cause_factors_for_attempt("att_k1")[0]
    for index in range(1, ESCALATION_RECURRENCE_K):
        _failed(vault, repository, attempt_id=f"att_k{index + 1}", item_id=ITEM_B, statement=REWORDED,
                clock=_clock(days=index))
        if merged and index == 1:
            record_verdict(repository, left=_episode(repository, "att_k2")["episode_key"],
                           right=_episode(repository, "att_k1")["episode_key"], verdict="same")
    _failed(vault, repository, attempt_id=f"att_k{ESCALATION_RECURRENCE_K + 1}", item_id=ITEM_B,
            statement=REWORDED, clock=_clock(days=ESCALATION_RECURRENCE_K))
    factor = repository.unresolved_cause_factor(str(first_factor["id"]))
    durable = repository.misconceptions_for_learning_object(LO_ID, statuses=("active", "resolving", "resolved"))
    if merged:
        assert factor["resolution_kind"] == "escalated_unrepaired"
        assert factor["resolution_detail"]["trigger"] == "unengaged_recurrences"
        assert len(durable) == 1
    else:
        # Without the verdict the reworded answers are a separate signature:
        # two recurrences of it, one short of K, and the first stays deferred.
        assert factor["status"] == "open"
        assert durable == []


def test_below_the_successor_the_verdict_changes_nothing(tmp_path):
    vault, repository = _vault(tmp_path, "mvp-0.10")
    _failed(vault, repository, attempt_id="att_k1", item_id=ITEM_A, statement=FIRST, clock=_clock())
    first_factor = repository.unresolved_cause_factors_for_attempt("att_k1")[0]
    for index in range(1, ESCALATION_RECURRENCE_K + 1):
        _failed(vault, repository, attempt_id=f"att_k{index + 1}", item_id=ITEM_B, statement=REWORDED,
                clock=_clock(days=index))
        if index == 1:
            record_verdict(repository, left=_episode(repository, "att_k2")["episode_key"],
                           right=_episode(repository, "att_k1")["episode_key"], verdict="same")
    assert repository.unresolved_cause_factor(str(first_factor["id"]))["status"] == "open"
    assert repository.recurrence_group_map() == {}
