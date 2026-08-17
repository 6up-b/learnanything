"""Migration 149: coldness as an explicit administration receipt.

The repair lane's "cold" claim stops being inferred from ``hints_used == 0``:
serving the cold item writes an administration snapshot, every terminal
disposition writes a final receipt with eight per-dimension statuses
(``pass|fail|unknown``), scoped absence claims (which ledgers were scanned,
which channels are known-unobserved), and three DISTINCT derived
qualifications. Only two findings hard-fail (answer reveal / hard same-surface
exposure post-primed); a retrieval co-intervention records and demotes the
attribution claim without starving the lane.
"""

from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.causal_orchestrator import record_cold_verification_from_task
from learnloop.services.coldness_receipt import (
    COLDNESS_RECEIPT_VERSION,
    TELEMETRY_COVERAGE_VERSION,
    evaluate_final_coldness,
    record_administration_snapshot,
)
from learnloop.services.remediation import (
    prescribe_remediation,
    record_prescription_delivery,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

from tests.helpers import (
    NOW,
    NOW_ISO,
    add_followup_item,
    create_basic_vault,
    seed_due_item,
)

LO_ID = "lo_svd_definition"

DAY1 = FrozenClock(NOW + timedelta(days=1))
DAY2 = FrozenClock(NOW + timedelta(days=2))


def _custom_item(root, item_id: str) -> None:
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "short_answer",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["recall"],
            "evidence_weights": {"recall": 1.0},
            "prompt": f"Define SVD ({item_id}).",
            "expected_answer": "A factorization into U, Sigma, and V transpose.",
            "grading_rubric": {
                "max_points": 4,
                "criteria": [
                    {"id": "correctness", "points": 4, "description": "Correct."}
                ],
                "fatal_errors": [],
            },
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
        clock=FrozenClock(NOW),
    )


def _setup(tmp_path, *, third_item=False):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    add_followup_item(vault_root)
    if third_item:
        _custom_item(vault_root, "pi_svd_define_003")
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    return vault_root, vault, repository, misconception_id


def _attempt(vault, repository, item_id, *, clock, primed=False, hints_used=0):
    return complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=item_id,
            learner_answer_md="U Sigma V transpose.",
            attempt_type="independent_attempt",
            hints_used=hints_used,
            primed=primed,
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4}, fatal_errors=[], confidence=4
        ),
        clock=clock,
    )


def _to_treatment(vault, repository, misconception_id):
    episode = start_remediation_episode(
        repository, misconception_id, clock=FrozenClock(NOW)
    )
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    return start_remediation_treatment(
        vault, repository, episode["id"], clock=FrozenClock(NOW)
    )


def _cold_retry_task(repository, *, repair_class="rc_stub"):
    with repository.connection() as connection:
        row = connection.execute(
            "SELECT id FROM followup_tasks WHERE kind = 'cold_retry'"
        ).fetchone()
    task = dict(repository.followup_task(row["id"]))
    # The misconception scaffold carries no causal diagnosis, so give the chain
    # the repair class a causal episode would have (same stub the §4.3 suite
    # uses) — the receipts under test are about the coldness evidence.
    context = dict(task["context"])
    context["repair_class_id"] = repair_class
    task["context"] = context
    return task


def _statuses(receipt):
    return {
        name: payload["status"] for name, payload in receipt["dimensions"].items()
    }


def test_over_budget_episode_downgrades_the_repair_effect_claim(tmp_path):
    """Slice 2 left the fact on the task; slice 3 makes the receipt say it.

    An episode that spent past ``EPISODE_REVEAL_BUDGET`` handed the learner most
    of the answer before the retry was even scheduled. The retry still runs and
    the cold attempt can still be clean on its own terms — so
    ``qualifies_as_cold_retrieval`` is untouched. What cannot survive is the
    claim that a REPAIR was verified: there is no isolated repair left to
    attribute the success to.
    """

    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW),
        primed=True,
    )
    task = _cold_retry_task(repository)
    task["context"] = dict(task["context"]) | {
        "reveal_spend": 0.95,
        "reveal_budget": 0.85,
        "reveal_over_budget": True,
    }

    record_administration_snapshot(vault, repository, task=task, clock=DAY1)
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    receipt = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    # It does NOT block: the verification still happened and still succeeded.
    assert receipt is not None and receipt["success"] is True

    derived = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")[
        "derived"
    ]
    assert derived["episode_reveal_spend"] == 0.95
    assert derived["episode_reveal_budget"] == 0.85
    assert derived["episode_reveal_over_budget"] is True
    assert derived["claim_downgraded_reason"] == "episode_reveal_over_budget"
    # The retrieval was still cold; only the repair-effect CLAIM is withheld.
    assert derived["qualifies_as_cold_retrieval"] is True
    assert derived["qualifies_as_repair_effect_verification"] is False
    assert derived["qualifies_as_held_out_validation"] is False


def test_within_budget_episode_records_the_spend_without_downgrading(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW),
        primed=True,
    )
    task = _cold_retry_task(repository)
    task["context"] = dict(task["context"]) | {
        "reveal_spend": 0.1,
        "reveal_budget": 0.85,
        "reveal_over_budget": False,
    }

    record_administration_snapshot(vault, repository, task=task, clock=DAY1)
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    derived = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")[
        "derived"
    ]
    assert derived["episode_reveal_over_budget"] is False
    assert "claim_downgraded_reason" not in derived
    assert derived["qualifies_as_repair_effect_verification"] is True


# -- happy path ---------------------------------------------------------------


def test_happy_path_snapshot_verification_and_final_receipt(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    primed = _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)

    # Stage 1: the cold item is served the day the task opens.
    snapshot = record_administration_snapshot(
        vault, repository, task=task, clock=DAY1
    )
    assert snapshot is not None
    assert snapshot["stage"] == "administration"
    assert snapshot["cold_attempt_id"] is None
    assert snapshot["created_at"] == "2026-05-20T12:00:00Z"
    # Qualifications are final-stage claims: the snapshot asserts none.
    assert snapshot["derived"]["qualifies_as_cold_retrieval"] is None

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    receipt = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    assert receipt is not None and receipt["success"] is True

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    assert final is not None
    assert final["receipt_version"] == COLDNESS_RECEIPT_VERSION
    assert final["cold_attempt_id"] == cold.attempt_id
    assert final["cold_verification_id"] == receipt["id"]
    assert final["source_attempt_id"] == primed.attempt_id
    assert final["measurement_opportunity_id"] == task["measurement_opportunity_id"]
    assert repository.coldness_receipt_for_verification(receipt["id"]) is not None
    decision = repository.cold_measurement_opportunity_decision(
        str(task["measurement_opportunity_id"])
    )
    assert decision["decision"] == "scheduled"
    assert decision["followup_task_id"] == task["id"]

    statuses = _statuses(final)
    assert statuses == {
        "retrieval_delay": "pass",
        "exposure_isolation": "pass",
        "surface_novelty": "pass",
        "selection_basis": "pass",
        "answer_leakage": "pass",
        "window_integrity": "pass",
        # Both attempts here are self-graded: there is no model grading run to
        # separate and no grading-context receipt to read, so BOTH halves stay
        # unknown — never inferred to pass.
        "verification_blinding": "unknown",
        "unassisted": "pass",
    }
    blinding = final["dimensions"]["verification_blinding"]["evidence"]
    assert blinding["run_separation"]["status"] == "unknown"
    assert blinding["run_separation"]["reason"] == "no_model_grading_run_recorded"
    assert blinding["context_blinding"]["status"] == "unknown"
    assert blinding["context_blinding"]["reason"] == "no_grading_context_receipt"
    assert blinding["repair_generation"]["identity_is"] == "source_attempt_grading_run"
    assert (
        blinding["repair_generation"]["grading_identity"]["attempt_id"]
        == primed.attempt_id
    )
    assert blinding["cold_grading"]["grading_identity"]["attempt_id"] == cold.attempt_id
    derived = final["derived"]
    assert derived["outcome"] == "cold_success"
    assert derived["qualifies_as_cold_retrieval"] is True
    assert derived["qualifies_as_repair_effect_verification"] is True
    assert derived["qualifies_as_held_out_validation"] is True
    assert derived["administration_receipt_id"] == snapshot["id"]

    # The scoped absence claim names its ledgers, its gaps, and its interval.
    coverage = final["telemetry_coverage"]
    assert coverage["telemetry_coverage_version"] == TELEMETRY_COVERAGE_VERSION
    scanned = {entry["ledger"] for entry in coverage["scanned_ledgers"]}
    assert scanned == {
        "practice_attempts",
        "question_events",
        "source_exposure_events",
        "remediation_episodes.passages_shown_json",
        # v2: feedback reopens have had a writer since migration 010.
        "attempt_feedback_metadata",
        # v4: the cross-channel reveal ledger (migration 154).
        "reveal_events",
    }
    channels = coverage["known_unobserved_channels"]
    # v4 sees every INSTRUMENTED revealing surface, and says plainly what it
    # still cannot see: how much of a declared reveal actually landed, and any
    # revealing channel that never writes a ledger row.
    assert "reveal_amount_is_declared_not_measured" in channels
    assert "reveal_channels_without_a_ledger_writer" in channels
    # v2 observes passage DELIVERY and feedback reopens; what stays unobserved
    # is narrower and says so.
    assert "remediation_passages_render" not in channels
    assert "feedback_screen_reopens" not in channels
    assert "remediation_passage_on_screen_dwell" in channels
    assert "feedback_reopen_intermediate_timestamps" in channels
    # No writer was added for read-only detail opens, so the channel stays.
    assert "practice_item_detail_reads" in channels
    assert coverage["interval"] == {
        "from": "2026-05-19T12:00:00Z",
        "to": "2026-05-21T12:00:00Z",
    }
    delay = final["dimensions"]["retrieval_delay"]["evidence"]
    assert delay["delay_seconds_from_primed"] == 2 * 24 * 3600
    assert delay["anchor_reset_by"] is None

    # Replaying the terminal event mints no second receipt.
    record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    finals = [
        row
        for row in repository.coldness_receipts_for_task(str(task["id"]))
        if row["stage"] == "final"
    ]
    assert len(finals) == 1


# -- co-intervention ----------------------------------------------------------


def test_retrieval_cointervention_demotes_attribution_not_the_verification(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path, third_item=True)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    record_administration_snapshot(vault, repository, task=task, clock=DAY1)

    # An intervening attempt on ANOTHER item with overlapping facets: a
    # co-intervention for attribution, not an exposure to the cold surface.
    third = next(
        item_id
        for item_id in ("pi_svd_define_001", "pi_svd_define_002", "pi_svd_define_003")
        if item_id not in (treatment["primed_item_id"], treatment["cold_item_id"])
    )
    intervening = _attempt(vault, repository, third, clock=DAY1)

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    receipt = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    # The verification itself still records — nothing here starves the lane.
    assert receipt is not None

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    derived = final["derived"]
    assert derived["qualifies_as_cold_retrieval"] is True
    assert derived["qualifies_as_repair_effect_verification"] is False
    assert derived["qualifies_as_held_out_validation"] is False
    assert derived["retrieval_cointervention_event_ids"] == [intervening.attempt_id]
    assert derived["hard_exposure_event_ids"] == []
    events = final["dimensions"]["exposure_isolation"]["evidence"]["events"]
    assert [event["type"] for event in events] == ["retrieval"]


def test_recent_retrieval_resets_the_cold_delay_anchor(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path, third_item=True)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    third = next(
        item_id
        for item_id in ("pi_svd_define_001", "pi_svd_define_002", "pi_svd_define_003")
        if item_id not in (treatment["primed_item_id"], treatment["cold_item_id"])
    )
    recent = _attempt(
        vault,
        repository,
        third,
        clock=FrozenClock(NOW + timedelta(days=1, hours=23)),
    )
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)

    assert record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    ) is not None
    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    delay = final["dimensions"]["retrieval_delay"]
    assert delay["status"] == "fail"
    assert delay["evidence"]["anchor_reset_by"] == {
        "ledger": "practice_attempts",
        "event_id": recent.attempt_id,
        "type": "retrieval",
    }
    assert delay["evidence"]["delay_seconds_from_anchor"] == 3600
    assert final["derived"]["qualifies_as_cold_retrieval"] is False
    assert final["derived"]["qualifies_as_repair_effect_verification"] is False


# -- hard leakage -------------------------------------------------------------


def test_hard_same_surface_exposure_yields_disposition_not_verification(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)

    # The cold item is answered BEFORE the task opens (feedback reveals its
    # expected answer), so the later "cold" attempt is warm by record.
    leak = _attempt(
        vault,
        repository,
        treatment["cold_item_id"],
        clock=FrozenClock(NOW + timedelta(hours=2)),
    )
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    result = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    assert result is None
    assert repository.causal_cold_verification_for_attempt(cold.attempt_id) is None
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row is not None
    assert row["outcome"] == "contaminated_or_assisted"
    assert row["detail"]["reason"] == "cold_item_answer_revealed_post_primed"
    assert row["detail"]["exposure_event_ids"] == [leak.attempt_id]

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    assert final is not None
    assert final["cold_verification_id"] is None
    statuses = _statuses(final)
    assert statuses["exposure_isolation"] == "fail"
    assert statuses["answer_leakage"] == "fail"
    assert statuses["surface_novelty"] == "fail"
    derived = final["derived"]
    assert derived["outcome"] == "contaminated_or_assisted"
    assert derived["qualifies_as_cold_retrieval"] is False
    assert derived["hard_contamination"]["event_ids"] == [leak.attempt_id]
    evidence = final["dimensions"]["exposure_isolation"]["evidence"]
    assert evidence["absence_status"] == "contaminated"


# -- v4: the cross-channel reveal ledger (migration 154) ----------------------


def _seed_reveal(repository, *, item_id, amount, clock, source_kind="tutor_answer",
                 episode_id=None, learning_object_id=LO_ID):
    return repository.insert_reveal_event(
        {
            "practice_item_id": item_id,
            "learning_object_id": learning_object_id,
            "remediation_episode_id": episode_id,
            "source_kind": source_kind,
            "amount": amount,
            "basis": "test",
        },
        clock=clock,
    )


def test_reveal_on_the_cold_item_fails_leakage_and_unassisted(tmp_path):
    """The hole v4 closes: a reveal too small to auto-prime (0.2 < 0.35) left
    the submission honestly declaring `primed=False`, and every dimension the
    receipt had could only read that flag. The ledger row is the evidence."""

    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    record_administration_snapshot(vault, repository, task=task, clock=DAY1)

    reveal_id = _seed_reveal(
        repository,
        item_id=treatment["cold_item_id"],
        amount=0.2,
        source_kind="repair_display",
        clock=DAY1,
    )

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    # The attempt itself is unprimed and unhinted by declaration...
    assert repository.fetch_practice_attempt(cold.attempt_id)["primed"] == 0

    result = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    # ... and the ledger row is still a hard contamination: no verification.
    assert result is None
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row["outcome"] == "contaminated_or_assisted"
    assert row["detail"]["reason"] == "cold_item_answer_revealed_post_primed"
    assert row["detail"]["exposure_event_ids"] == [reveal_id]

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    statuses = _statuses(final)
    assert statuses["answer_leakage"] == "fail"
    assert statuses["unassisted"] == "fail"
    assert statuses["exposure_isolation"] == "fail"
    assert final["derived"]["qualifies_as_cold_retrieval"] is False

    leakage = final["dimensions"]["answer_leakage"]["evidence"]
    assert [row["event_id"] for row in leakage["reveal_ledger_rows"]] == [reveal_id]
    assert leakage["reveal_ledger_amount"] == 0.2
    assert leakage["reveal_ledger_rows"][0]["source_kind"] == "repair_display"
    assert leakage["reveal_ledger_rows"][0]["at"] == "2026-05-20T12:00:00Z"

    unassisted = final["dimensions"]["unassisted"]["evidence"]
    # The flags say clean; the dimension fails on the ledger and names why.
    assert unassisted["primed"] is False and unassisted["hints_used"] == 0
    assert unassisted["violation"] == "answer_revealed_before_the_cold_attempt"
    assert [row["event_id"] for row in unassisted["reveal_ledger_rows"]] == [reveal_id]


def test_reveal_elsewhere_in_the_learning_object_is_soft_not_a_failure(tmp_path):
    """The repair lane writes its suggestions against the PRIMED item, which
    shares the LO with the cold item by construction. Failing on LO-wide
    reveals would fail every repair episode ever measured, so an independent
    surface's reveal records as soft exposure and the verification stands."""

    _, vault, repository, misconception_id = _setup(tmp_path, third_item=True)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    reveal_id = _seed_reveal(
        repository,
        item_id=treatment["primed_item_id"],
        amount=0.6,
        source_kind="repair_display",
        clock=DAY1,
    )

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    assert record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    ) is not None

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    statuses = _statuses(final)
    assert statuses["answer_leakage"] == "pass"
    assert statuses["unassisted"] == "pass"
    assert final["derived"]["qualifies_as_cold_retrieval"] is True
    # Recorded, not ignored: the exposure travels as a soft event with its
    # amount and the episode it belonged to.
    soft = [
        event
        for event in final["dimensions"]["exposure_isolation"]["evidence"]["events"]
        if event["ledger"] == "reveal_events"
    ]
    assert [event["event_id"] for event in soft] == [reveal_id]
    assert soft[0]["type"] == "soft"
    assert soft[0]["why"] == "reveal_ledger_exposure_on_related_item"


def test_no_reveal_rows_is_a_scoped_absence_claim_not_a_bare_pass(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    assert record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    ) is not None

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    assert _statuses(final)["answer_leakage"] == "pass"
    assert _statuses(final)["unassisted"] == "pass"
    leakage = final["dimensions"]["answer_leakage"]["evidence"]
    assert leakage["reveal_ledger_rows"] == []
    assert leakage["reveal_ledger_amount"] == 0.0
    unassisted = final["dimensions"]["unassisted"]["evidence"]
    # The claim is "the ledger was scanned and had nothing", never "nothing
    # happened" — and the ledger is named in the coverage block with the
    # channels it still cannot see.
    assert unassisted["reveal_ledger_scanned"] is True
    coverage = final["telemetry_coverage"]
    ledger = next(
        entry
        for entry in coverage["scanned_ledgers"]
        if entry["ledger"] == "reveal_events"
    )
    assert "migration 154" in ledger["observes"]
    assert "reveal_amount_is_declared_not_measured" in coverage[
        "known_unobserved_channels"
    ]


def test_min_cold_delay_mirrors_the_lane_scheduling_constant():
    """One delay, three users (schedule, reveal-deferral, receipt floor)."""

    from learnloop.services.coldness_receipt import MIN_COLD_DELAY
    from learnloop.services.remediation import COLD_RETRIEVAL_DELAY

    assert MIN_COLD_DELAY == COLD_RETRIEVAL_DELAY


# -- unknown telemetry --------------------------------------------------------


def test_prescription_without_a_delivery_record_is_unknown_not_pass(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    record_administration_snapshot(vault, repository, task=task, clock=DAY1)

    # Passages PREPARED inside the interval for a sibling repair, with NO
    # delivery event anywhere: prepared-but-never-shown and prescribed-through-
    # an-uninstrumented-path are the same silence, so the scan cannot call the
    # interval clear — and must not call it contaminated either.
    sibling = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Thinks singular values can be negative.",
        correction_statement="They are non-negative by construction.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.5,
        clock=DAY1,
    )
    repository.create_remediation_episode(
        case_kind="misconception",
        case_ref=sibling,
        passages_shown=[{"role": "target", "facet_id": "recall"}],
        clock=DAY1,
    )

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    receipt = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    # Indeterminate telemetry records; it does not block the measurement.
    assert receipt is not None

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    isolation = final["dimensions"]["exposure_isolation"]
    assert isolation["status"] == "unknown"
    assert isolation["evidence"]["absence_status"] == "indeterminate"
    prepared = isolation["evidence"]["prepared_unconfirmed"]
    assert len(prepared) == 1
    assert prepared[0]["why"] == "passages_prepared_in_interval_no_delivery_record"
    # And the structurally-unobserved dimension stays unknown too.
    assert final["dimensions"]["verification_blinding"]["status"] == "unknown"


def test_unrelated_remediation_is_counted_but_does_not_change_coldness(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    unrelated = repository.insert_misconception(
        learning_object_id="lo_unrelated_subject",
        statement="An unrelated misunderstanding.",
        correction_statement="An unrelated correction.",
        # Deliberately reuse generic facet names: LO scope must keep this from
        # becoming "related" merely because both subjects contain recall work.
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.5,
        clock=DAY1,
    )
    delivered = repository.create_remediation_episode(
        case_kind="misconception",
        case_ref=unrelated,
        passages_shown=[
            {
                "role": "target",
                "facet_id": "recall",
                "span_view": {
                    "extraction_id": "ext_other",
                    "span_id": "s_other",
                },
            }
        ],
        clock=DAY1,
    )
    record_prescription_delivery(repository, delivered, clock=DAY1)
    repository.create_remediation_episode(
        case_kind="misconception",
        case_ref=unrelated,
        passages_shown=[{"role": "target", "facet_id": "recall"}],
        clock=DAY1,
    )

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    assert record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    ) is not None
    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    isolation = final["dimensions"]["exposure_isolation"]
    assert isolation["status"] == "pass"
    assert isolation["evidence"]["events"] == []
    assert isolation["evidence"]["prepared_unconfirmed"] == []
    assert isolation["evidence"]["irrelevant_by_ledger"] == {
        "remediation_episodes.passages_shown_json": 2,
        "source_exposure_events": 1,
    }
    delay = final["dimensions"]["retrieval_delay"]["evidence"]
    assert delay["anchor_reset_by"] is None
    assert delay["delay_seconds_from_anchor"] == 2 * 24 * 3600


# -- delivered passages (v2) --------------------------------------------------


def _sibling_case(repository, *, clock):
    return repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Thinks singular values can be negative.",
        correction_statement="They are non-negative by construction.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.5,
        clock=clock,
    )


def _episode_with_passages(repository, *, clock, span_id="s1"):
    """An episode whose prescription resolved to a real span view."""

    return repository.create_remediation_episode(
        case_kind="misconception",
        case_ref=_sibling_case(repository, clock=clock),
        passages_shown=[
            {
                "role": "confused_with",
                "facet_id": "application",
                "span_view": {
                    "extraction_id": "ext_repair",
                    "span_id": span_id,
                    "revision_id": "rev1",
                    "source_id": "src1",
                    "page": 1,
                    "locator": f"span:ext_repair/{span_id}",
                    "section_path": ["Chapter 1"],
                },
            }
        ],
        clock=clock,
    )


def test_delivered_passages_in_interval_are_typed_exposure_not_indeterminate(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    record_administration_snapshot(vault, repository, task=task, clock=DAY1)

    episode = _episode_with_passages(repository, clock=DAY1)
    written = record_prescription_delivery(repository, episode, clock=DAY1)
    assert len(written) == 1

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    receipt = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    # A delivered comparison passage is a real, typed exposure — soft, so it
    # records without starving the lane.
    assert receipt is not None

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    isolation = final["dimensions"]["exposure_isolation"]
    assert isolation["status"] == "pass"
    assert isolation["evidence"]["absence_status"] == "clear_in_observed_channels"
    # The prescription is no longer an unresolved gap.
    assert isolation["evidence"]["prepared_unconfirmed"] == []
    delivered = [
        event
        for event in isolation["evidence"]["events"]
        if event["ledger"] == "source_exposure_events"
    ]
    assert len(delivered) == 1
    assert delivered[0]["type"] == "soft"
    assert delivered[0]["why"] == "remediation_passage_delivered_for_render"
    assert delivered[0]["remediation_episode_id"] == episode["id"]

    # A soft exposure still resets the cold-delay anchor: the retrieval is a day
    # from the passage, not two days from the primed attempt.
    delay = final["dimensions"]["retrieval_delay"]["evidence"]
    assert delay["anchor_at"] == "2026-05-20T12:00:00Z"
    assert delay["delay_seconds_from_anchor"] == 24 * 3600
    assert delay["anchor_reset_by"]["ledger"] == "source_exposure_events"
    assert final["derived"]["qualifies_as_cold_retrieval"] is True


def test_delivery_outside_the_interval_is_observed_silence_not_indeterminate(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)

    episode = _episode_with_passages(repository, clock=DAY1)
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    # The prescription is only delivered AFTER the cold retrieval: its passages
    # have a render record, and none of it lands inside the interval.
    later = FrozenClock(NOW + timedelta(days=3))
    record_prescription_delivery(repository, episode, clock=later)

    record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=later
    )
    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    isolation = final["dimensions"]["exposure_isolation"]
    assert isolation["status"] == "pass"
    assert isolation["evidence"]["prepared_unconfirmed"] == []
    outside = isolation["evidence"]["delivered_outside_interval"]
    assert len(outside) == 1
    assert outside[0]["why"] == "passages_delivered_outside_interval"
    assert outside[0]["remediation_episode_id"] == episode["id"]


def test_delivered_passage_on_the_cold_items_own_source_span_is_hard(tmp_path):
    from learnloop.vault.models import Provenance, SourceRef

    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)

    # The cold item was authored from the very span the repair prescribes.
    cold_id = treatment["cold_item_id"]
    vault.practice_items[cold_id] = vault.practice_items[cold_id].model_copy(
        update={
            "provenance": Provenance(
                origin="canonical_extract",
                source_refs=[
                    SourceRef(
                        ref_type="canonical_source",
                        ref_id="src1",
                        extraction_id="ext_repair",
                        span_ids=["s1"],
                    )
                ],
            )
        }
    )
    episode = _episode_with_passages(repository, clock=DAY1)
    record_prescription_delivery(repository, episode, clock=DAY1)

    cold = _attempt(vault, repository, cold_id, clock=DAY2)
    result = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    # Reveal of the cold item's own material: a refusal, not a verification.
    assert result is None
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row["outcome"] == "contaminated_or_assisted"
    assert row["detail"]["reason"] == "cold_item_answer_revealed_post_primed"

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    assert final["dimensions"]["exposure_isolation"]["status"] == "fail"
    leakage = final["dimensions"]["answer_leakage"]
    assert leakage["status"] == "fail"
    assert [event["why"] for event in leakage["evidence"]["reveal_events"]] == [
        "remediation_passage_revealed_cold_item_source_span"
    ]


def test_prescribe_handler_records_the_delivery(tmp_path):
    """The delivery seam is the sidecar handing passage text to the surface."""

    from types import SimpleNamespace

    from learnloop_sidecar.handlers.remediation import prescribe_remediation_handler
    from learnloop_sidecar.handlers.remediation import EpisodeInput

    from tests.test_source_inventory import _persist, _register_revision

    from learnloop.ingest.ir import (
        DocumentBlock,
        DocumentIR,
        DocumentUnit,
        ExtractionHealth,
    )

    _, vault, repository, misconception_id = _setup(tmp_path)
    _register_revision(repository, source_id="src1", revision_id="rev1")
    block = DocumentBlock.build(
        span_id="s1",
        block_type="Text",
        text="Singular values are non-negative.",
        ordinal=0,
        page=1,
        bbox=[10.0, 10.0, 200.0, 40.0],
        section_path=["Chapter 1"],
    )
    ir = DocumentIR(
        extractor="marker",
        extractor_version="1",
        units=[
            DocumentUnit(
                unit_id="u0",
                label="SVD",
                ordinal=0,
                semantic_hash="sha256:svd",
                page_start=1,
                page_end=1,
                span_ids=["s1"],
            )
        ],
        blocks=[block],
        assets=[],
        health=ExtractionHealth(),
    )
    _persist(repository, ir, revision_id="rev1", extraction_id="ext1")
    repository.insert_entity_source_link(
        entity_type="facet",
        entity_id="recall",
        locator="span:ext1/s1",
        locator_scheme="block_span_v1",
        relation="primary",
        source_id="src1",
        revision_id="rev1",
        extraction_id="ext1",
    )
    episode = start_remediation_episode(
        repository, misconception_id, clock=FrozenClock(NOW)
    )

    ctx = SimpleNamespace(require_vault=lambda: (vault, repository))
    payload = prescribe_remediation_handler(ctx, EpisodeInput(episode_id=episode["id"]))

    assert payload["episode"]["passagesShown"]
    events = repository.source_exposure_events(
        entity_type="remediation_episode", entity_id=episode["id"]
    )
    assert [event["context"] for event in events] == ["remediation_delivery"]
    assert events[0]["span_id"] == "s1"
    # Prescribing does NOT claim the learner opened the span: the deliberate
    # Open-in-source context stays unused by this path.
    assert repository.source_exposure_events(extraction_id="ext1", span_id="s1") == events


# -- feedback reopens (v2) ----------------------------------------------------


def _record_feedback_view(repository, result, *, shown_clock):
    """Mirror a real door: persist the feedback row, then open the screen."""

    from learnloop.services.post_attempt import persist_attempt_feedback_metadata

    persist_attempt_feedback_metadata(repository, result, clock=FrozenClock(NOW))
    assert repository.record_feedback_shown(result.attempt_id, clock=shown_clock)


def test_feedback_reopen_on_the_source_attempt_is_a_soft_exposure(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    primed = _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    record_administration_snapshot(vault, repository, task=task, clock=DAY1)

    # The learner re-opened the graded repair attempt the day after it happened.
    _record_feedback_view(repository, primed, shown_clock=DAY1)

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    receipt = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    assert receipt is not None

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    events = final["dimensions"]["exposure_isolation"]["evidence"]["events"]
    reopens = [
        event for event in events if event["ledger"] == "attempt_feedback_metadata"
    ]
    assert len(reopens) == 1
    assert reopens[0]["type"] == "soft"
    assert reopens[0]["why"] == "source_attempt_feedback_reopened"
    assert reopens[0]["event_id"] == f"feedback_shown:{primed.attempt_id}"
    assert final["dimensions"]["exposure_isolation"]["status"] == "pass"
    # Re-reading the repair resets the anchor without failing the retrieval.
    delay = final["dimensions"]["retrieval_delay"]["evidence"]
    assert delay["anchor_at"] == "2026-05-20T12:00:00Z"
    assert final["derived"]["qualifies_as_cold_retrieval"] is True


def test_feedback_reopen_on_the_cold_item_is_a_hard_answer_reveal(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    # An OLD attempt on the cold item, before the repair: outside the interval,
    # so only its feedback reopen can put it inside.
    old = _attempt(
        vault,
        repository,
        treatment["cold_item_id"],
        clock=FrozenClock(NOW - timedelta(hours=2)),
    )
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    _record_feedback_view(repository, old, shown_clock=DAY1)

    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    result = record_cold_verification_from_task(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    assert result is None
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row["outcome"] == "contaminated_or_assisted"
    assert row["detail"]["reason"] == "cold_item_answer_revealed_post_primed"
    assert row["detail"]["exposure_event_ids"] == [f"feedback_shown:{old.attempt_id}"]

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    assert final["dimensions"]["answer_leakage"]["status"] == "fail"
    assert final["dimensions"]["exposure_isolation"]["status"] == "fail"


# -- verification blinding (v2) -----------------------------------------------


def _model_graded(repository, attempt_id, *, run_id, model="model-a"):
    repository.insert_agent_run(
        {
            "id": run_id,
            "purpose": "grading",
            "provider": "codex",
            "model": model,
            "prompt_template": "grading",
            "prompt_version": "g1",
            "started_at": NOW_ISO,
            "status": "completed",
        }
    )
    repository.insert_grading_evidence(
        attempt_id,
        [
            {
                "criterion_id": "correctness",
                "points_awarded": 4.0,
                "grader_tier": 3,
                "agent_run_id": run_id,
                "created_at": NOW_ISO,
            }
        ],
    )


def _phase_c_receipt(repository, attempt_id, *, history):
    repository.insert_diagnostic_augmentation_receipt(
        {
            "attempt_id": attempt_id,
            "grading_prompt_version": "g1",
            "grader_provider": "codex",
            "grader_model": "model-b",
            "c1_repair_before_structure": True,
            "c2_verifier_observations": [],
            "c3_sample_count": 1,
            "c3_agreement_support": 1.0,
            "c3_disagreement_causes": [],
            "c4_history_attempt_ids": history,
            "hypotheses": {},
            "revert_criteria": {},
            "created_at": NOW_ISO,
        }
    )


def _blinding_evidence(vault, repository, *, history):
    """Both attempts model-graded by distinct runs; `history` is what the cold
    grading call was actually given."""

    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    treatment = _to_treatment(vault, repository, misconception_id)
    primed = _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    _model_graded(repository, primed.attempt_id, run_id="run_repair")
    _model_graded(repository, cold.attempt_id, run_id="run_cold", model="model-b")
    _phase_c_receipt(
        repository,
        cold.attempt_id,
        history=[primed.attempt_id] if history == "source" else [],
    )
    evaluation = evaluate_final_coldness(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    )
    return primed, cold, evaluation.dimensions["verification_blinding"]


def test_verification_blinding_passes_when_both_halves_are_established(tmp_path):
    _, vault, repository, _ = _setup(tmp_path)
    primed, cold, dimension = _blinding_evidence(vault, repository, history="none")

    assert dimension["status"] == "pass"
    evidence = dimension["evidence"]
    separation = evidence["run_separation"]
    assert separation["status"] == "pass"
    assert separation["source_agent_run_ids"] == ["run_repair"]
    assert separation["cold_agent_run_ids"] == ["run_cold"]
    assert separation["shared_agent_run_ids"] == []
    context = evidence["context_blinding"]
    assert context["status"] == "pass"
    assert context["diagnostic_history_attempt_ids"] == []
    assert context["prior_diagnoses_in_context"] is False
    # Both identities travel, so a consumer can see WHICH run graded what.
    assert evidence["repair_generation"]["grading_identity"]["agent_run"]["id"] == (
        "run_repair"
    )
    assert evidence["repair_generation"]["grading_identity"]["attempt_id"] == (
        primed.attempt_id
    )
    assert evidence["cold_grading"]["grading_identity"]["model_graded"] is True
    assert evidence["cold_grading"]["grading_identity"]["attempt_id"] == cold.attempt_id


def test_verification_blinding_fails_when_the_cold_grader_saw_the_repair_trace(
    tmp_path,
):
    _, vault, repository, _ = _setup(tmp_path)
    primed, _cold, dimension = _blinding_evidence(vault, repository, history="source")

    # Run separation is established; the context half is not — and the split is
    # visible rather than collapsed into one verdict.
    assert dimension["evidence"]["run_separation"]["status"] == "pass"
    context = dimension["evidence"]["context_blinding"]
    assert context["status"] == "fail"
    assert context["source_attempt_in_grading_history"] is True
    assert context["diagnostic_history_attempt_ids"] == [primed.attempt_id]
    assert dimension["status"] == "fail"


def test_verification_blinding_is_unknown_without_a_grading_context_receipt(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    primed = _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    cold = _attempt(vault, repository, treatment["cold_item_id"], clock=DAY2)
    _model_graded(repository, primed.attempt_id, run_id="run_repair")
    _model_graded(repository, cold.attempt_id, run_id="run_cold", model="model-b")

    dimension = evaluate_final_coldness(
        vault, repository, task=task, cold_attempt_id=cold.attempt_id, clock=DAY2
    ).dimensions["verification_blinding"]

    # Distinct runs are proved; what the cold grader was shown is not recorded.
    # One established half never carries the dimension.
    assert dimension["evidence"]["run_separation"]["status"] == "pass"
    assert dimension["evidence"]["context_blinding"]["status"] == "unknown"
    assert dimension["status"] == "unknown"


# -- serving-time hook --------------------------------------------------------


def test_detail_serve_writes_one_snapshot_for_an_active_cold_task(tmp_path):
    from learnloop_sidecar.handlers.serializers import practice_item_detail

    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    scheduled = _cold_retry_task(repository)
    # The scheduled task's 30-day expiry sits in the fixture past, where the
    # serializer's wall-clock read cannot see it — mint the same task shape
    # with no expiry so it is active NOW, as it would be in a live vault. Put a
    # certification task on the same item FIRST: an unqualified lookup would
    # return it and shadow the repair administration snapshot.
    certification = repository.create_followup_task(
        kind="certification_cold_probe",
        case_kind="certification",
        case_ref="cert_shadow",
        not_before=str(scheduled["not_before"]),
        expires_at=None,
        selected_item_id=scheduled["selected_item_id"],
        learning_object_id=LO_ID,
        context={
            "kind": "certification_cold_probe",
            "certificate_id": "cert_shadow",
            "learning_object_id": LO_ID,
            "certified_at": NOW_ISO,
            "measurement_anchor_at": NOW_ISO,
            "horizon_days": 1.0,
            "excluded_surface_groups": [],
            "held_out_basis": "distinct_surface_group",
            "probe_surface_group": f"item:{scheduled['selected_item_id']}",
            "certificate_receipt": {"cells": [{"facet_id": "recall"}]},
        },
        clock=FrozenClock(NOW),
    )
    live = repository.create_followup_task(
        kind="cold_retry",
        case_kind=str(scheduled["case_kind"]),
        case_ref=str(scheduled["case_ref"]),
        source_attempt_id=scheduled["source_attempt_id"],
        remediation_episode_id=scheduled["remediation_episode_id"],
        not_before=str(scheduled["not_before"]),
        expires_at=None,
        selected_item_id=scheduled["selected_item_id"],
        context=scheduled["context"],
        clock=FrozenClock(NOW),
    )

    detail = practice_item_detail(vault, repository, treatment["cold_item_id"])
    assert detail["activeFollowupKind"] == "cold_retry"
    first = repository.coldness_receipt_for_task_stage(str(live["id"]), "administration")
    assert first is not None
    cert_first = repository.coldness_receipt_for_task_stage(
        str(certification["id"]), "administration"
    )
    assert cert_first is not None
    assert cert_first["lane"] == "certification_cold_probe"

    # Serving the detail again is the same administration: one snapshot.
    practice_item_detail(vault, repository, treatment["cold_item_id"])
    rows = repository.coldness_receipts_for_task(str(live["id"]))
    assert [row["stage"] for row in rows] == ["administration"]
    assert rows[0]["id"] == first["id"]
    assert len(repository.coldness_receipts_for_task(str(certification["id"]))) == 1


# -- expiry -------------------------------------------------------------------


def test_expired_task_gets_a_partial_final_receipt(tmp_path):
    from learnloop.services.causal_orchestrator import sweep_expired_cold_retries

    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    late = FrozenClock(NOW + timedelta(days=40))
    repository.due_followup_tasks(clock=late)
    rows = sweep_expired_cold_retries(vault, repository, clock=late)
    assert [row["outcome"] for row in rows] == ["right_censored_expired"]

    final = repository.coldness_receipt_for_task_stage(str(task["id"]), "final")
    assert final is not None
    assert final["cold_attempt_id"] is None
    assert final["derived"]["outcome"] == "right_censored_expired"
    statuses = _statuses(final)
    # Never opened, never answered: no silent passes anywhere.
    assert statuses["unassisted"] == "unknown"
    assert statuses["window_integrity"] == "unknown"


# -- append-only --------------------------------------------------------------


def test_coldness_receipts_are_append_only(tmp_path):
    _, _, repository, _ = _setup(tmp_path)
    row = repository.insert_coldness_receipt(
        receipt_id="cr_test",
        lane="repair_cold_retry",
        stage="final",
        followup_task_id="task_x",
        remediation_episode_id=None,
        source_attempt_id=None,
        cold_attempt_id=None,
        cold_verification_id=None,
        dimensions={"unassisted": {"status": "unknown", "evidence": {}}},
        derived={"outcome": "missing_chain"},
        telemetry_coverage={"telemetry_coverage_version": TELEMETRY_COVERAGE_VERSION},
        receipt_version=COLDNESS_RECEIPT_VERSION,
        clock=FrozenClock(NOW),
    )
    assert row is not None
    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                "UPDATE coldness_receipts SET lane = 'other' WHERE id = 'cr_test'"
            )
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM coldness_receipts WHERE id = 'cr_test'")

    # A second insert into an occupied (task, stage) slot is ignored, and the
    # occupying row is returned.
    again = repository.insert_coldness_receipt(
        receipt_id="cr_test_other",
        lane="repair_cold_retry",
        stage="final",
        followup_task_id="task_x",
        remediation_episode_id=None,
        source_attempt_id=None,
        cold_attempt_id=None,
        cold_verification_id=None,
        dimensions={},
        derived={},
        telemetry_coverage={},
        receipt_version=COLDNESS_RECEIPT_VERSION,
        clock=FrozenClock(NOW),
    )
    assert again is not None and again["id"] == "cr_test"
