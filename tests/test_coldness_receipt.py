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
    record_administration_snapshot,
)
from learnloop.services.remediation import (
    prescribe_remediation,
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
    assert repository.coldness_receipt_for_verification(receipt["id"]) is not None

    statuses = _statuses(final)
    assert statuses == {
        "retrieval_delay": "pass",
        "exposure_isolation": "pass",
        "surface_novelty": "pass",
        "selection_basis": "pass",
        "answer_leakage": "pass",
        "window_integrity": "pass",
        # Model/profile/agent_run identities are not captured per call, so
        # blinding is recorded unknown — never inferred to pass.
        "verification_blinding": "unknown",
        "unassisted": "pass",
    }
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
    }
    assert "remediation_passages_render" in coverage["known_unobserved_channels"]
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


# -- unknown telemetry --------------------------------------------------------


def test_unconfirmed_render_channel_is_unknown_not_pass(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = _cold_retry_task(repository)
    record_administration_snapshot(vault, repository, task=task, clock=DAY1)

    # Passages PREPARED inside the interval for a sibling repair: no render
    # telemetry exists, so the scan cannot call the interval clear — and must
    # not call it contaminated either.
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
    assert prepared[0]["why"] == "passages_prepared_in_interval_render_unconfirmed"
    # And the structurally-unobserved dimension stays unknown too.
    assert final["dimensions"]["verification_blinding"]["status"] == "unknown"


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
    # with no expiry so it is active NOW, as it would be in a live vault.
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

    # Serving the detail again is the same administration: one snapshot.
    practice_item_detail(vault, repository, treatment["cold_item_id"])
    rows = repository.coldness_receipts_for_task(str(live["id"]))
    assert [row["stage"] for row in rows] == ["administration"]
    assert rows[0]["id"] == first["id"]


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
