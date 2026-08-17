"""B6 remediation episodes: FrozenClock cold-retry delay, consume-once,
unassisted+unprimed enforcement, and the prescription→primed→cold linkage
(spec §4.10 / §7.2)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    AttemptDraft,
    AttemptValidationError,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.services.remediation import (
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_basic_vault, seed_due_item

LO_ID = "lo_svd_definition"


def _setup(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    seed_due_item(paths)
    add_followup_item(vault_root)  # a second item so primed and cold items differ
    vault = load_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    misconception_id = repository.insert_misconception(
        learning_object_id=LO_ID,
        statement="Confuses SVD with eigendecomposition.",
        correction_statement="SVD applies to any matrix; eigendecomposition needs a square one.",
        facet_ids=["recall"],
        target_facet="recall",
        confused_with_facet="application",
        severity=0.8,
        clock=FrozenClock(NOW),
    )
    return vault, repository, misconception_id


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
        SelfGradeInput(criterion_points={"correctness": 4}, fatal_errors=[], confidence=4),
        clock=clock,
    )


def _drive_to_cold_scheduled(vault, repository, misconception_id):
    """diagnosis → prescribed → treatment → primed attempt → cold_scheduled."""

    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    assert episode["state"] == "diagnosis"
    prescribed = prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    assert prescribed["state"] == "prescribed"
    treatment = start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(NOW))
    assert treatment["episode"]["state"] == "treatment"
    primed_item = treatment["primed_item_id"]
    cold_item = treatment["cold_item_id"]
    assert primed_item != cold_item

    primed_result = _attempt(vault, repository, primed_item, clock=FrozenClock(NOW), primed=True)
    episode = repository.remediation_episode(episode["id"])
    assert episode["state"] == "cold_scheduled"
    assert episode["primed_attempt_id"] == primed_result.attempt_id
    return episode, primed_result, cold_item


def test_cold_retry_is_not_schedulable_until_not_before(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)

    task = repository.active_followup_task_for_item(
        cold_item, at=(NOW + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    assert task is not None and task["kind"] == "cold_retry"
    assert task["not_before"] == (NOW + timedelta(days=1)).isoformat().replace("+00:00", "Z")

    # Scheduled today, not schedulable today: the delayed structured task is
    # invisible to the scheduler until not_before (>= 1 day later).
    assert cold_item not in repository.pending_followup_practice_item_ids(clock=FrozenClock(NOW))
    assert cold_item not in repository.pending_followup_practice_item_ids(
        clock=FrozenClock(NOW + timedelta(hours=23))
    )
    assert cold_item in repository.pending_followup_practice_item_ids(
        clock=FrozenClock(NOW + timedelta(days=1))
    )


def test_served_cold_attempt_is_enforced_unassisted_and_unprimed(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    due = FrozenClock(NOW + timedelta(days=1))

    with pytest.raises(AttemptValidationError):
        _attempt(vault, repository, cold_item, clock=due, primed=True)
    with pytest.raises(AttemptValidationError):
        _attempt(vault, repository, cold_item, clock=due, hints_used=1)

    # A clean unassisted, unprimed retry is accepted.
    result = _attempt(vault, repository, cold_item, clock=due)
    task = next(
        task for task in _all_tasks(repository) if task["kind"] == "cold_retry"
    )
    assert task["status"] == "consumed"
    assert task["consumed_attempt_id"] == result.attempt_id


def test_cold_retry_is_consumed_exactly_once(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    episode, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    due = FrozenClock(NOW + timedelta(days=1))

    first = _attempt(vault, repository, cold_item, clock=due)
    task = next(task for task in _all_tasks(repository) if task["kind"] == "cold_retry")
    assert task["status"] == "consumed"
    assert task["consumed_attempt_id"] == first.attempt_id

    # A later attempt on the same item finds no active task and links nothing.
    second = _attempt(vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=2)))
    refreshed = repository.followup_task(task["id"])
    assert refreshed["consumed_attempt_id"] == first.attempt_id
    assert refreshed["status"] == "consumed"

    # Even a direct second consume cannot re-bind the task.
    repository.consume_followup_task(task["id"], second.attempt_id, clock=due)
    assert repository.followup_task(task["id"])["consumed_attempt_id"] == first.attempt_id

    updated = repository.remediation_episode(episode["id"])
    assert updated["cold_attempt_id"] == first.attempt_id


def test_episode_links_prescription_primed_and_cold_end_to_end(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    episode, primed_result, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)

    cold_result = _attempt(vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=1)))
    final = repository.remediation_episode(episode["id"])
    # The four recorded stage boundaries (§7.2 telemetry) survive on one row.
    assert final["state"] == "completed"
    assert final["case_kind"] == "misconception"
    assert final["case_ref"] == misconception_id
    assert final["passages_shown"] is not None  # prescription happened (may be empty)
    assert final["primed_attempt_id"] == primed_result.attempt_id
    assert final["cold_attempt_id"] == cold_result.attempt_id
    assert final["completed_at"]

    task = next(task for task in _all_tasks(repository) if task["kind"] == "cold_retry")
    assert task["remediation_episode_id"] == episode["id"]
    assert task["source_attempt_id"] == primed_result.attempt_id
    assert task["selected_item_id"] == cold_item
    assert task["consumed_attempt_id"] == cold_result.attempt_id


def _all_tasks(repository):
    with repository.connection() as connection:
        rows = connection.execute("SELECT * FROM followup_tasks ORDER BY created_at, id").fetchall()
    return [dict(row) for row in rows]


# --- funnel unblockers (July 2026) -------------------------------------------


def test_misconception_cold_context_carries_repair_class_from_fresh_receipt(tmp_path):
    """Ordering fix: `record_remediation_attempt` now runs AFTER
    `materialize_causal_episode`, so a primed attempt whose grading produced a
    repair selection resolves a non-null repair_class_id into the §6.2 task
    context (it was structurally NULL for misconception-kind episodes before)."""

    from tests.test_guided_redo import failed_attempt_with_repair

    vault, repository, misconception_id = _setup(tmp_path)
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    treatment = start_remediation_treatment(vault, repository, episode["id"], clock=FrozenClock(NOW))

    # The primed attempt fails again and its grade carries a repair suggestion:
    # materialize writes the diagnosis receipt on THIS attempt, and the cold
    # context (resolved in the same apply_attempt call) must see it.
    primed = failed_attempt_with_repair(
        vault,
        repository,
        "att_primed_receipt",
        item_id=treatment["primed_item_id"],
        primed=True,
        clock=FrozenClock(NOW),
    )
    task = repository.active_followup_task_for_item(
        treatment["cold_item_id"],
        kind="cold_retry",
        at=(NOW + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
    )
    assert task is not None
    context = task["context"]
    assert context["source_attempt_id"] == primed.attempt_id
    assert context["repair_class_id"], "the fresh diagnosis receipt's repair class must be carried"


def test_starting_the_same_repair_twice_reuses_one_episode(tmp_path):
    """StrictMode double-mount hardening: the episode create is an atomic
    get-or-create, so a doubled start mints exactly one episode."""

    _vault, repository, misconception_id = _setup(tmp_path)
    first = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    second = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    assert first["id"] == second["id"]

    # The repository primitive itself is idempotent per open case.
    third = repository.get_or_create_open_remediation_episode(
        case_kind="misconception",
        case_ref=misconception_id,
        states=("diagnosis", "prescribed"),
        clock=FrozenClock(NOW),
    )
    assert third["id"] == first["id"]
    with repository.connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS n FROM remediation_episodes WHERE case_ref = ?",
            (misconception_id,),
        ).fetchone()["n"]
    assert count == 1


# --- reveal-aware serving (migration 154) ------------------------------------


def _seed_reveal(repository, item_id, amount, *, clock, source_kind="tutor_answer", episode_id=None):
    return repository.insert_reveal_event(
        {
            "practice_item_id": item_id,
            "learning_object_id": LO_ID,
            "remediation_episode_id": episode_id,
            "source_kind": source_kind,
            "amount": amount,
            "basis": "test",
        },
        clock=clock,
    )


def _cold_lane_ids(vault, repository, clock):
    """Items the queue is serving AS the cold-retry lane this build.

    Not plain queue membership: the cold item is an ordinary practice card too,
    so it can sit in the queue on its own merits. What the deferral withholds is
    the delayed COLD lane — the max-priority resurrection whose `followup_kind`
    says the serve is the measurement.
    """

    from learnloop.services.scheduler import build_due_queue

    return [
        item.practice_item_id
        for item in build_due_queue(vault, repository, clock=clock)
        if item.followup_kind == "cold_retry"
    ]


def test_reveal_after_scheduling_defers_the_cold_retry_instead_of_burning_it(tmp_path):
    """The single-use measurement is worth more than its promptness: a due cold
    task whose answer has been shown since it was created is withheld and its
    `not_before` pushed a full retrieval delay past the reveal, rather than
    served and spent on contaminated evidence."""

    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    task_id = next(
        task["id"] for task in _all_tasks(repository) if task["kind"] == "cold_retry"
    )
    original = repository.followup_task(task_id)

    # Due, clean, and served: the baseline the deferral has to change.
    assert cold_item in _cold_lane_ids(vault, repository, FrozenClock(NOW + timedelta(days=1)))

    _seed_reveal(
        repository,
        cold_item,
        0.2,
        source_kind="repair_display",
        clock=FrozenClock(NOW + timedelta(days=1, hours=1)),
    )
    at = FrozenClock(NOW + timedelta(days=1, hours=2))
    assert cold_item not in _cold_lane_ids(vault, repository, at)

    deferred = repository.followup_task(task_id)
    assert deferred["not_before"] == (
        (NOW + timedelta(days=2, hours=1)).isoformat().replace("+00:00", "Z")
    )
    # The window itself is NEVER extended — only the earliest serve time moves.
    assert deferred["expires_at"] == original["expires_at"]
    assert deferred["status"] != "consumed"

    # Still withheld an hour before the delay elapses...
    assert cold_item not in _cold_lane_ids(
        vault, repository, FrozenClock(NOW + timedelta(days=2))
    )
    # ... and served once it does, with the task never having been spent.
    assert cold_item in _cold_lane_ids(
        vault, repository, FrozenClock(NOW + timedelta(days=2, hours=2))
    )
    cold = _attempt(
        vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=2, hours=2))
    )
    assert repository.followup_task(task_id)["consumed_attempt_id"] == cold.attempt_id


def test_an_attempt_during_the_deferral_cannot_burn_the_measurement(tmp_path):
    """Defer rather than burn: while the push is in force the task is not due,
    so an ordinary attempt on the same card links nothing and the single-use
    measurement is still there to be spent when the item is cold again."""

    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    task_id = next(
        task["id"] for task in _all_tasks(repository) if task["kind"] == "cold_retry"
    )
    _seed_reveal(
        repository, cold_item, 0.2, clock=FrozenClock(NOW + timedelta(days=1, hours=1))
    )
    at = FrozenClock(NOW + timedelta(days=1, hours=2))
    assert cold_item not in _cold_lane_ids(vault, repository, at)

    _attempt(vault, repository, cold_item, clock=at)
    task = repository.followup_task(task_id)
    assert task["status"] != "consumed"
    assert task["consumed_attempt_id"] is None


def test_a_deferred_cold_retry_still_expires_on_its_original_window(tmp_path):
    """Deferral can never outlive the task: an episode that keeps being
    revealed runs out its original 30-day window and censors honestly."""

    from learnloop.services.causal_orchestrator import sweep_expired_cold_retries

    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    task_id = next(
        task["id"] for task in _all_tasks(repository) if task["kind"] == "cold_retry"
    )
    expires_at = repository.followup_task(task_id)["expires_at"]

    # A reveal on the last day pushes `not_before` past the expiry.
    _seed_reveal(
        repository, cold_item, 0.4, clock=FrozenClock(NOW + timedelta(days=30, hours=12))
    )
    at = FrozenClock(NOW + timedelta(days=30, hours=13))
    assert cold_item not in _cold_lane_ids(vault, repository, at)
    deferred = repository.followup_task(task_id)
    assert deferred["not_before"] > expires_at
    assert deferred["expires_at"] == expires_at

    # Past the (unchanged) expiry the queue's own sweep retires it, and the
    # §4.3 sweep records the honest right-censoring.
    after = FrozenClock(NOW + timedelta(days=32))
    assert cold_item not in _cold_lane_ids(vault, repository, after)
    assert repository.followup_task(task_id)["status"] == "expired"
    recorded = sweep_expired_cold_retries(vault, repository, clock=after)
    assert [row["outcome"] for row in recorded] == ["right_censored_expired"]


def test_only_the_cold_lane_is_deferred_by_a_reveal(tmp_path):
    """An intervention follow-up is re-practice, not a measurement: being shown
    the answer is not a reason to withhold it."""

    from learnloop.services.scheduler import _defer_revealed_cold_followups

    vault, repository, misconception_id = _setup(tmp_path)
    _, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    _seed_reveal(
        repository, cold_item, 0.9, clock=FrozenClock(NOW + timedelta(days=1, hours=1))
    )
    at = FrozenClock(NOW + timedelta(days=1, hours=2))
    pending = repository.pending_followup_practice_items(clock=at)
    generic = [
        dict(entry, action_type="intervention_followup") for entry in pending
    ]

    kept, deferrals = _defer_revealed_cold_followups(
        vault, repository, generic, clock=at, persist=False
    )
    assert [entry["practice_item_id"] for entry in kept] == [
        entry["practice_item_id"] for entry in generic
    ]
    assert deferrals == []


def test_exam_attempt_does_not_consume_the_cold_retry(tmp_path):
    """An exam sitting that happens to serve the cold item must not burn the
    one unassisted cold measurement on proctored, time-pressured context."""

    from learnloop.services.attempts import ApplyAttemptInput, ResolvedGrade, apply_attempt

    vault, repository, misconception_id = _setup(tmp_path)
    episode, _, cold_item = _drive_to_cold_scheduled(vault, repository, misconception_id)
    due = FrozenClock(NOW + timedelta(days=1))

    apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=cold_item,
                learner_answer_md="U Sigma V transpose.",
                attempt_type="exam_evidence",
            ),
            attempt_id="att_exam_cold",
            grade=ResolvedGrade(
                rubric_score=4,
                criterion_points={"correctness": 4},
                evidence_rows=[],
                error_attributions=[],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
            ),
        ),
        clock=due,
    )
    task = next(task for task in _all_tasks(repository) if task["kind"] == "cold_retry")
    assert task["status"] != "consumed"
    assert task["consumed_attempt_id"] is None
    assert repository.remediation_episode(episode["id"])["state"] == "cold_scheduled"

    # The genuine unassisted retry still consumes it afterwards.
    cold_result = _attempt(vault, repository, cold_item, clock=FrozenClock(NOW + timedelta(days=2)))
    refreshed = repository.followup_task(task["id"])
    assert refreshed["status"] == "consumed"
    assert refreshed["consumed_attempt_id"] == cold_result.attempt_id
    assert repository.remediation_episode(episode["id"])["state"] == "completed"


# --- episode reveal budget (migration 154) -----------------------------------


def test_repair_status_reports_episode_reveal_spend_against_the_budget(tmp_path):
    """The repair status is the one read a surface makes before it teaches, so
    it is where "how much of the answer has this repair already handed over?"
    has to be answerable. Reported, never enforced — nothing is refused here."""

    from learnloop.services.causal_orchestrator import causal_repair_status
    from learnloop.services.remediation import EPISODE_REVEAL_BUDGET

    vault, repository, misconception_id = _setup(tmp_path)
    status = causal_repair_status(
        vault, repository, misconception_id=misconception_id, clock=FrozenClock(NOW)
    )
    assert status.episode is not None
    assert status.reveal_spend == 0.0
    assert status.reveal_budget == EPISODE_REVEAL_BUDGET

    episode_id = status.episode["id"]
    _seed_reveal(
        repository, "pi_svd_define_001", 0.5, clock=FrozenClock(NOW), episode_id=episode_id
    )
    _seed_reveal(
        repository,
        "pi_svd_define_001",
        0.4,
        source_kind="repair_display",
        clock=FrozenClock(NOW),
        episode_id=episode_id,
    )
    # An UNATTRIBUTED reveal is still a reveal, but it is not this episode's
    # spend: attribution is the ledger's own column, never inferred here.
    _seed_reveal(repository, "pi_svd_define_001", 0.7, clock=FrozenClock(NOW))

    again = causal_repair_status(
        vault, repository, misconception_id=misconception_id, clock=FrozenClock(NOW)
    )
    assert again.episode["id"] == episode_id
    assert again.reveal_spend == pytest.approx(0.9)
    assert again.reveal_spend > EPISODE_REVEAL_BUDGET
    # ... and it reaches the wire shape the surface reads.
    assert again.as_dict()["reveal_spend"] == pytest.approx(0.9)
    assert again.as_dict()["reveal_budget"] == EPISODE_REVEAL_BUDGET


def test_over_budget_episode_stamps_the_fact_on_the_cold_context(tmp_path):
    """The verification lands up to 30 days later, from a task row. If the
    episode was already over budget when the retry was scheduled, that fact has
    to travel ON the task — reconstructing it later is exactly the "future
    caller re-derives it" assumption that leaves channels unwired."""

    from learnloop.services.remediation import EPISODE_REVEAL_BUDGET

    vault, repository, misconception_id = _setup(tmp_path)
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    treatment = start_remediation_treatment(
        vault, repository, episode["id"], clock=FrozenClock(NOW)
    )
    _seed_reveal(
        repository,
        treatment["primed_item_id"],
        0.9,
        source_kind="repair_display",
        clock=FrozenClock(NOW),
        episode_id=episode["id"],
    )
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )

    task = repository.active_followup_task_for_item(
        treatment["cold_item_id"],
        kind="cold_retry",
        at=(NOW + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
    )
    context = task["context"]
    assert context["reveal_spend"] == pytest.approx(0.9)
    assert context["reveal_budget"] == EPISODE_REVEAL_BUDGET
    assert context["reveal_over_budget"] is True
    # Measurement first, policy later: the retry is still scheduled.
    assert task["status"] in {"pending", "served"}
    assert repository.remediation_episode(episode["id"])["state"] == "cold_scheduled"


def test_an_episode_within_budget_says_so(tmp_path):
    vault, repository, misconception_id = _setup(tmp_path)
    episode = start_remediation_episode(repository, misconception_id, clock=FrozenClock(NOW))
    prescribe_remediation(vault, repository, episode["id"], clock=FrozenClock(NOW))
    treatment = start_remediation_treatment(
        vault, repository, episode["id"], clock=FrozenClock(NOW)
    )
    _seed_reveal(
        repository,
        treatment["primed_item_id"],
        0.3,
        source_kind="repair_display",
        clock=FrozenClock(NOW),
        episode_id=episode["id"],
    )
    _attempt(
        vault, repository, treatment["primed_item_id"], clock=FrozenClock(NOW), primed=True
    )
    task = repository.active_followup_task_for_item(
        treatment["cold_item_id"],
        kind="cold_retry",
        at=(NOW + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
    )
    assert task["context"]["reveal_spend"] == pytest.approx(0.3)
    assert task["context"]["reveal_over_budget"] is False
