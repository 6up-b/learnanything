"""The durable workflow that owns one follow-up intervention (spec §5 item 1, §3.1).

A stable id exists before routing, keyed to the source attempt and the effective
grade revision. While it is open, predecessor insertion is withheld, and every Next and
serve door reads it. Each move is a compare-and-set, so a late diagnosis or generator
adds nothing after a fallback, a skip, factor closure or a newer diagnosis, and retry
and crash recovery reuse the identity.

States: ``pending`` (no decision or no item yet), ``ready`` (a question is pinned, Next
opens it), ``waiting`` (the router let it wait for the next block), ``refused`` (a hard
refusal), ``failed`` (nothing passed the checks), ``skipped`` (*Continue without it*, a
rollback, a superseded revision), ``settled`` (answered, the practice lane, no
intervention, a fallback).
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import logging
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store
from learnloop.followup_serve.gates import SERVING_SURFACE, generate_and_serve_on

logger = logging.getLogger(__name__)

#: The suppression the attempt's receipt carries while the workflow owns it.
WORKFLOW_OWNS_REASON = "followup_workflow_owns"

PENDING = "pending"
READY = "ready"
WAITING = "waiting"
REFUSED = "refused"
FAILED = "failed"
SKIPPED = "skipped"
SETTLED = "settled"

LANE_PROBE = "probe"
LANE_PRACTICE = "practice"

#: Why held feedback was released (§6.0).
RELEASE_PROBE_ANSWERED = "probe_answered"
RELEASE_NO_INTERVENTION = "no_intervention"
RELEASE_PRACTICE_LANE = "practice_lane"
RELEASE_CONTINUE_WITHOUT = "continue_without_it"
RELEASE_GENERATION_FAILED = "generation_failed"
RELEASE_WAIT = "wait"
RELEASE_SHOW_ANYWAY = "show_anyway"
RELEASE_REFUSED = "refused"
RELEASE_FALLBACK = "fallback"
RELEASE_SWITCH_OFF = "switch_off"


def workflow_id_for(attempt_id: str, revision_key: str) -> str:
    """Stable across retry and crash recovery: the attempt and its grade revision."""

    digest = hashlib.sha256(f"{attempt_id}\0{revision_key}".encode("utf-8")).hexdigest()[:26]
    return f"fw_{digest}"


def _now(clock: Clock | None) -> str:
    return utc_now_iso(clock)


def attempt_needs_followup(vault: Any, repository: Repository, attempt: Mapping[str, Any]) -> tuple[bool, str] | None:
    """(a miss, its grade revision), or None when the attempt has no readable grade.

    Blind records and joint grades use the one ``needs_diagnosis`` rule, so a workflow
    opens exactly where a live diagnosis would explain something.
    """

    from learnloop.diagnosis.split.live import joint_grade_record, needs_diagnosis

    attempt_id = str(attempt["id"])
    row = repository.latest_blind_grade_record(attempt_id)
    if row is not None:
        return needs_diagnosis(dict(row.get("record") or {})), str(row["id"])
    return needs_diagnosis(joint_grade_record(vault, repository, attempt)), "joint"


def open_for_attempt(
    vault: Any,
    repository: Repository,
    *,
    result: Any,
    surface: str | None,
    session_id: str | None,
    origin: str = "practice",
    hold_feedback: bool = True,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Open (or find) the attempt's workflow on the caller's transaction, or None.

    None leaves the attempt on the predecessor's path: the switch is off, the door has
    no pending and skip UI (§3.1), it is not a miss, or it answered a generated probe.
    """

    if surface != SERVING_SURFACE or not generate_and_serve_on(vault.config):
        return None
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    if attempt is None:
        return None
    from learnloop.followup_serve import identity

    if identity.is_generated_probe(repository, str(attempt.get("practice_item_id") or "")):
        return None
    grade = attempt_needs_followup(vault, repository, attempt)
    if grade is None or not grade[0]:
        return None
    revision_key = grade[1]
    now = _now(clock)
    workflow_id = workflow_id_for(result.attempt_id, revision_key)
    with repository.connection() as connection:
        store.insert_workflow(connection, {
            "id": workflow_id,
            "source_attempt_id": result.attempt_id,
            "revision_key": revision_key,
            "learning_object_id": result.learning_object_id,
            "session_id": session_id,
            "surface": surface,
            "origin": origin,
            "feedback_held": 1 if hold_feedback else 0,
            "created_at": now,
        })
        return store.workflow(connection, workflow_id)


def owns_attempt(repository: Repository, attempt_id: str) -> dict[str, Any] | None:
    """The attempt's open workflow, or None."""

    with repository.connection() as connection:
        if not store.present(connection):
            return None
        row = store.workflow_for_attempt(connection, attempt_id)
    return row if row is not None and row["state"] in store.OPEN_STATES else None


def attempt_workflow(repository: Repository, attempt_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        if not store.present(connection):
            return None
        return store.workflow_for_attempt(connection, attempt_id)


def get(repository: Repository, workflow_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        return store.workflow(connection, workflow_id)


def enqueue_workflow_job(repository: Repository, workflow_id: str, *, clock: Clock | None = None) -> str | None:
    """Queue the workflow's one job (the dedupe key is its identity)."""

    with repository.atomic(), repository.connection() as connection:
        return store.enqueue_generation_job(
            connection, kind="workflow", dedupe_key=f"workflow:{workflow_id}", workflow_id=workflow_id, at=_now(clock),
        )


def _release_fields(row: Mapping[str, Any], reason: str, at: str) -> dict[str, Any]:
    if not row.get("feedback_held") or row.get("feedback_released_at"):
        return {}
    return {"feedback_released_at": at, "release_reason": reason}


def move(
    repository: Repository,
    workflow_id: str,
    *,
    to_state: str,
    reason: str,
    from_states: tuple[str, ...] = tuple(store.OPEN_STATES),
    release: str | None = None,
    detail: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
    **fields: Any,
) -> bool:
    """One state move, with its release of held feedback; False when it lost the race."""

    now = _now(clock)
    with repository.atomic(), repository.connection() as connection:
        row = store.workflow(connection, workflow_id)
        if row is None:
            return False
        extra = {**fields, **(_release_fields(row, release, now) if release else {})}
        moved = store.move_workflow(
            connection, workflow_id, from_states=from_states, to_state=to_state, reason=reason, at=now,
            detail=detail, **extra,
        )
        if moved and to_state in store.TERMINAL_STATES:
            store.cancel_generation_jobs(connection, workflow_id=workflow_id, reason=f"workflow_{to_state}", at=now)
        return moved


def set_fields(repository: Repository, workflow_id: str, *, clock: Clock | None = None, **fields: Any) -> None:
    with repository.atomic(), repository.connection() as connection:
        store.update_workflow(connection, workflow_id, at=_now(clock), **fields)


def superseded(repository: Repository, row: Mapping[str, Any]) -> bool:
    """A newer grade revision came after this workflow: it adds nothing."""

    latest = repository.latest_blind_grade_record(str(row["source_attempt_id"]))
    if latest is None:
        return str(row["revision_key"]) != "joint"
    return str(latest["id"]) != str(row["revision_key"])


def settle_practice_lane(
    vault: Any,
    repository: Repository,
    row: Mapping[str, Any],
    *,
    reason: str,
    release: str = RELEASE_PRACTICE_LANE,
    clock: Clock | None = None,
) -> bool:
    """The practice lane, or the one fallback: the predecessor's chooser runs once.

    The move and the insertion commit together, so a crash leaves neither and a retry
    runs both once; a workflow something else settled inserts nothing.
    """

    from learnloop.attempts.attempts import AttemptResult
    from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup

    workflow_id = str(row["id"])
    attempt_id = str(row["source_attempt_id"])
    work = repository.attempt_completion(attempt_id)
    decision = None
    with repository.atomic():
        if not move(repository, workflow_id, to_state=SETTLED, reason=reason, release=release, lane=LANE_PRACTICE,
                    from_states=(PENDING,), clock=clock):
            return False
        if work is not None:
            decision = evaluate_attempt_intervention_followup(
                vault, repository, result=AttemptResult.from_dict(work["result"]),
                session_id=row.get("session_id"), normalization_prepared=True,
                applied_probe_episode_id=work.get("applied_probe_episode_id"),
                defer_diagnosis_hooks=True, insertion_only=True, clock=clock,
            )
    if decision is not None and decision.need_id:
        # §4: a recorded need fills in the background, textbook first (S2b).
        from learnloop.followup_serve.jobs import enqueue_need_fill

        enqueue_need_fill(repository, str(decision.need_id), clock=clock)
    return True


def settle_open_when_off(vault: Any, repository: Repository, *, clock: Clock | None = None) -> int:
    """§10: with the switch off, open workflows settle as skipped and burns persist."""

    if generate_and_serve_on(vault.config):
        return 0
    with repository.connection() as connection:
        if not store.present(connection):
            return 0
        rows = store.open_workflows(connection)
    settled = 0
    for row in rows:
        if move(repository, str(row["id"]), to_state=SKIPPED, reason="switch_off", release=RELEASE_SWITCH_OFF,
                clock=clock):
            settled += 1
    return settled


def diagnosis_ended(vault: Any, repository: Repository, *, attempt_id: str, clock: Clock | None = None) -> None:
    """The diagnosis worker's one hook: the workflow's job runs on its own slot, so a
    later diagnosis is never delayed by generation. Never fails the diagnosis."""

    try:
        if not generate_and_serve_on(vault.config):
            return
        row = owns_attempt(repository, attempt_id)
        if row is not None and row["state"] == PENDING:
            enqueue_workflow_job(repository, str(row["id"]), clock=clock)
    except Exception:  # noqa: BLE001 - bookkeeping never fails a diagnosis
        logger.warning("follow-up workflow hook failed for attempt %s", attempt_id, exc_info=True)


__all__ = [
    "FAILED", "PENDING", "READY", "REFUSED", "SETTLED", "SKIPPED", "WAITING", "WORKFLOW_OWNS_REASON",
    "attempt_needs_followup", "attempt_workflow", "diagnosis_ended", "enqueue_workflow_job", "get", "move",
    "open_for_attempt", "owns_attempt", "settle_open_when_off", "settle_practice_lane", "superseded",
    "workflow_id_for",
]
