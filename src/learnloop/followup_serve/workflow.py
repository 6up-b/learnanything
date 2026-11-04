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
from learnloop.followup_serve.queue import enqueue_workflow

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


def open_for_attempt(
    vault: Any,
    repository: Repository,
    *,
    result: Any,
    surface: str | None,
    session_id: str | None,
    grade: tuple[bool, str] | None,
    origin: str = "practice",
    hold_feedback: bool = True,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Open (or find) the attempt's workflow on the caller's transaction, or None.

    None leaves the attempt on the predecessor's path: the switch is off, the door has
    no pending and skip UI (§3.1), it is not a miss, or it answered a generated probe.
    ``grade`` is (a miss, its grade revision), which the caller reads with the one
    ``needs_diagnosis`` rule, or None when the attempt has no readable grade.
    """

    if surface != SERVING_SURFACE or not generate_and_serve_on(vault.config):
        return None
    attempt = repository.fetch_practice_attempt(result.attempt_id)
    if attempt is None:
        return None
    from learnloop.followup_serve import identity

    if identity.is_generated_probe(repository, str(attempt.get("practice_item_id") or "")):
        return None
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


def workflow_of_item(repository: Repository, practice_item_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        if not store.present(connection):
            return None
        return store.workflow_for_item(connection, practice_item_id)


def get(repository: Repository, workflow_id: str) -> dict[str, Any] | None:
    with repository.connection() as connection:
        return store.workflow(connection, workflow_id)


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
            enqueue_workflow(repository, str(row["id"]), clock=clock)
    except Exception:  # noqa: BLE001 - bookkeeping never fails a diagnosis
        logger.warning("follow-up workflow hook failed for attempt %s", attempt_id, exc_info=True)


__all__ = [
    "FAILED", "PENDING", "READY", "REFUSED", "SETTLED", "SKIPPED", "WAITING", "WORKFLOW_OWNS_REASON",
    "attempt_workflow", "diagnosis_ended", "get", "move", "open_for_attempt", "owns_attempt", "settle_open_when_off",
    "superseded", "workflow_id_for", "workflow_of_item",
]
