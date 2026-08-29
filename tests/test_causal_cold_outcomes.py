"""Migration 145: typed §4.3 dispositions for the repair lane's cold channel.

Every terminal disposition of a cold-verification opportunity lands a typed
row — expiry, decline-shaped unmeasurability, same-surface reuse, assisted
attempts and missing chains stop being indistinguishable from "no row" — and
only a genuinely servable opportunity may right-censor.
"""

from __future__ import annotations

from datetime import timedelta

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.diagnosis.causal_orchestrator import (
    record_cold_verification_from_task,
    sweep_expired_cold_retries,
)
from learnloop.diagnosis.remediation import (
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


def _custom_item(root, item_id: str, *, surface_family: str | None = None) -> None:
    payload = {
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
    }
    if surface_family is not None:
        payload["surface_family"] = surface_family
    upsert_practice_item(root, payload, clock=FrozenClock(NOW))


def _setup(tmp_path, *, extra_items=True):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    if extra_items:
        add_followup_item(vault_root)
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


def _all_tasks(repository):
    with repository.connection() as connection:
        rows = connection.execute("SELECT * FROM followup_tasks").fetchall()
    return [dict(row) for row in rows]


# -- schedule time -----------------------------------------------------------


def test_no_independent_surface_records_unmeasurable_and_schedules_nothing(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path, extra_items=False)
    treatment = _to_treatment(vault, repository, misconception_id)
    assert treatment["cold_item_id"] is None
    assert treatment["cold_unmeasurable_reason"] == "no_independent_surface"

    primed = _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW),
        primed=True,
    )
    episode = repository.remediation_episode(treatment["episode"]["id"])
    assert episode["primed_attempt_id"] == primed.attempt_id
    # No task manufactured for a verification the consume guard must reject.
    assert not [t for t in _all_tasks(repository) if t["kind"] == "cold_retry"]
    rows = repository.causal_cold_outcomes(
        remediation_episode_id=str(episode["id"])
    )
    assert [row["outcome"] for row in rows] == ["unmeasurable_no_held_out_surface"]
    assert rows[0]["servable_opportunity"] is False
    assert rows[0]["detail"]["stage"] == "schedule"
    assert rows[0]["followup_task_id"] is None
    with repository.connection() as connection:
        opportunity = dict(
            connection.execute(
                """
                SELECT * FROM cold_measurement_opportunities
                 WHERE lane = 'repair_cold_retry'
                """
            ).fetchone()
        )
    decision = repository.cold_measurement_opportunity_decision(opportunity["id"])
    assert decision["decision"] == "structurally_refused"
    assert decision["reason"] == "no_independent_surface"
    final = repository.coldness_receipt_for_opportunity_stage(
        opportunity["id"], "final"
    )
    assert final is not None
    assert final["followup_task_id"] is None
    assert final["derived"]["schedule_decision"] == "structurally_refused"
    assert final["derived"]["schedule_reason"] == "no_independent_surface"


def test_cold_pick_refuses_distinct_item_in_same_surface_group(tmp_path):
    root, _, repository, misconception_id = _setup(tmp_path, extra_items=False)
    # 002 sits in 001's surface group by surface_family: a DIFFERENT item id is
    # available, but not an independent surface — the pick must refuse it.
    _custom_item(root, "pi_svd_define_002", surface_family="item:pi_svd_define_001")
    vault = load_vault(root)
    treatment = _to_treatment(vault, repository, misconception_id)
    assert treatment["cold_item_id"] is None
    assert treatment["cold_unmeasurable_reason"] == "no_independent_surface"


def test_cold_pick_skips_same_group_and_takes_next_independent(tmp_path):
    root, _, repository, misconception_id = _setup(tmp_path, extra_items=False)
    _custom_item(root, "pi_svd_define_002", surface_family="item:pi_svd_define_001")
    _custom_item(root, "pi_svd_define_003")
    vault = load_vault(root)
    treatment = _to_treatment(vault, repository, misconception_id)
    # Never-attempted items rank first (002 by id), so 002 primes; its group is
    # 001's, and the cold pick must skip 001 for the independent 003.
    assert treatment["primed_item_id"] == "pi_svd_define_002"
    assert treatment["cold_item_id"] == "pi_svd_define_003"
    assert treatment["cold_unmeasurable_reason"] is None


# -- consume time ------------------------------------------------------------


def _with_repair_class(task):
    # The misconception scaffold carries no causal diagnosis, so the context's
    # repair_class_id is None and the recorder would (correctly) file
    # `missing_chain`. The consume-time tests are about the OTHER arms, so give
    # the chain a repair class the way a causal episode would have.
    task = dict(task)
    context = dict(task["context"])
    context["repair_class_id"] = "rc_stub"
    task["context"] = context
    return task


def _consumed_task(vault, repository, misconception_id):
    treatment = _to_treatment(vault, repository, misconception_id)
    primed = _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW),
        primed=True,
    )
    cold_item = treatment["cold_item_id"]
    cold = _attempt(
        vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=2))
    )
    task = next(t for t in _all_tasks(repository) if t["kind"] == "cold_retry")
    task = _with_repair_class(repository.followup_task(task["id"]))
    return treatment, primed, cold, task


def test_clean_consume_records_cold_success_row_idempotently(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold, task = _consumed_task(vault, repository, misconception_id)

    receipt = record_cold_verification_from_task(
        vault,
        repository,
        task=task,
        cold_attempt_id=cold.attempt_id,
        clock=FrozenClock(NOW + timedelta(days=2)),
    )
    assert receipt is not None and receipt["success"] is True
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row is not None
    assert row["outcome"] == "cold_success"
    assert row["cold_verification_id"] == receipt["id"]
    assert row["cold_attempt_id"] == cold.attempt_id
    assert row["servable_opportunity"] is True
    # Self-graded attempts carry no latency: missing, never zero.
    assert row["duration_state"] == "missing"

    # Replaying the same terminal event is one row.
    record_cold_verification_from_task(
        vault,
        repository,
        task=task,
        cold_attempt_id=cold.attempt_id,
        clock=FrozenClock(NOW + timedelta(days=2)),
    )
    assert len(repository.causal_cold_outcomes()) == 1


def test_contaminated_consume_records_typed_row(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    primed = _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW),
        primed=True,
    )
    task = next(t for t in _all_tasks(repository) if t["kind"] == "cold_retry")
    task = _with_repair_class(repository.followup_task(task["id"]))
    # Consume the task first so the unassisted-attempt guard no longer covers
    # the item, then present an assisted attempt to the recorder directly.
    clean = _attempt(
        vault,
        repository,
        treatment["cold_item_id"],
        clock=FrozenClock(NOW + timedelta(days=2)),
    )
    assisted = _attempt(
        vault,
        repository,
        treatment["cold_item_id"],
        clock=FrozenClock(NOW + timedelta(days=3)),
        hints_used=2,
    )
    del clean
    result = record_cold_verification_from_task(
        vault,
        repository,
        task=task,
        cold_attempt_id=assisted.attempt_id,
        clock=FrozenClock(NOW + timedelta(days=3)),
    )
    assert result is None
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row is not None
    assert row["outcome"] == "contaminated_or_assisted"
    assert row["detail"]["hints_used"] == 2


def test_same_surface_consume_records_typed_row(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment, _, _, task = _consumed_task(vault, repository, misconception_id)
    # A retry on the SOURCE item's own surface is not a verification.
    same_surface = _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW + timedelta(days=3)),
    )
    result = record_cold_verification_from_task(
        vault,
        repository,
        task=task,
        cold_attempt_id=same_surface.attempt_id,
        clock=FrozenClock(NOW + timedelta(days=3)),
    )
    assert result is None
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row is not None and row["outcome"] == "same_surface"


def test_missing_chain_records_typed_row(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold, task = _consumed_task(vault, repository, misconception_id)
    stripped = dict(task)
    stripped["context"] = {
        "kind": "causal_cold_verification",
        "source_attempt_id": task["context"]["source_attempt_id"],
        # No repair class: no repair-effect claim to make.
    }
    # (the helper injected one on `task`; `stripped` deliberately lacks it)
    result = record_cold_verification_from_task(
        vault,
        repository,
        task=stripped,
        cold_attempt_id=cold.attempt_id,
        clock=FrozenClock(NOW + timedelta(days=2)),
    )
    assert result is None
    row = repository.causal_cold_outcome_for_task(str(task["id"]))
    assert row is not None
    assert row["outcome"] == "missing_chain"
    assert row["detail"]["reason"] == "no_repair_class"


# -- expiry ------------------------------------------------------------------


def _expire_all(repository, *, clock):
    # The queue's own expiry transition, as the scheduler would run it.
    repository.due_followup_tasks(clock=clock)


def test_expired_servable_task_right_censors(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW),
        primed=True,
    )
    late = FrozenClock(NOW + timedelta(days=40))
    _expire_all(repository, clock=late)
    rows = sweep_expired_cold_retries(vault, repository, clock=late)
    assert [row["outcome"] for row in rows] == ["right_censored_expired"]
    assert rows[0]["servable_opportunity"] is True
    # The sweep is a reconciliation: a second pass records nothing new.
    assert sweep_expired_cold_retries(vault, repository, clock=late) == []


def test_expired_inactive_surface_is_unmeasurable_not_censored(tmp_path):
    _, vault, repository, misconception_id = _setup(tmp_path)
    treatment = _to_treatment(vault, repository, misconception_id)
    _attempt(
        vault,
        repository,
        treatment["primed_item_id"],
        clock=FrozenClock(NOW),
        primed=True,
    )
    repository.upsert_practice_item_state(
        treatment["cold_item_id"], active=False, clock=FrozenClock(NOW)
    )
    late = FrozenClock(NOW + timedelta(days=40))
    _expire_all(repository, clock=late)
    rows = sweep_expired_cold_retries(vault, repository, clock=late)
    assert [row["outcome"] for row in rows] == ["unmeasurable_unservable_surface"]
    assert rows[0]["servable_opportunity"] is False
    assert rows[0]["detail"]["reason"] == "selected_item_inactive"
