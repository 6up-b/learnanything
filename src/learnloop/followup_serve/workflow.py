"""The durable workflow that owns one follow-up intervention (spec §5 item 1, §3.1).

A stable id exists before routing, keyed to the source attempt and the effective
grade revision. While it is open, predecessor insertion is withheld, and every Next and
serve door reads it. Each move is a compare-and-set, so a late diagnosis or generator
adds nothing after a fallback, a skip, factor closure or a newer diagnosis, and retry
and crash recovery reuse the identity. Nothing recovers a terminal workflow, so
:func:`finish` is the only way into a terminal state: it closes what the workflow
prepared in the move's own commit. ``tests/test_followup_codex_review.py`` fails on any
other writer.

States: ``pending`` (no decision or no item yet), ``ready`` (a question is pinned, Next
opens it), ``waiting`` (the router let it wait for the next block), ``refused`` (a hard
refusal), ``failed`` (nothing passed the checks), ``skipped`` (*Continue without it*, a
rollback, a superseded revision), ``settled`` (answered, the practice lane, no
intervention, a fallback).
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
import logging
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store
from learnloop.db.stores import hypothesis_marks as marks_store
from learnloop.followup_serve.gates import RIVAL_CAUSES_FACTOR_VERSION, SERVING_SURFACE, generate_and_serve_on
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
OPEN_STATES = store.OPEN_STATES

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
#: How a factor opened for this lane closes when its question won't be asked (R9).
FACTOR_DECLINED = "followup_declined"


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
    """A move between open states; False when it lost the race. :func:`finish` makes the last one."""

    if to_state in store.TERMINAL_STATES:
        raise ValueError(f"{to_state} is terminal: only finish() moves there")
    return _apply_move(repository, workflow_id, to_state=to_state, reason=reason, from_states=from_states,
                       release=release, detail=detail, clock=clock, **fields)


def finish(
    repository: Repository,
    workflow_id: str,
    *,
    to_state: str,
    reason: str,
    from_states: tuple[str, ...] = tuple(store.OPEN_STATES),
    release: str | None = None,
    detail: Mapping[str, Any] | None = None,
    answered_item: str | None = None,
    clock: Clock | None = None,
    **fields: Any,
) -> bool:
    """The one move to a terminal state, and the closing of what the workflow prepared, in
    one commit: nothing recovers a terminal workflow, so a crash between them would leave a
    probe live with nothing to withdraw it. False when the move lost the race, and then
    nothing closes. ``answered_item`` is the question whose answer settled it, which stays."""

    if to_state not in store.TERMINAL_STATES:
        raise ValueError(f"{to_state} is not terminal: move() moves there")
    with repository.atomic():
        if not _apply_move(repository, workflow_id, to_state=to_state, reason=reason, from_states=from_states,
                           release=release, detail=detail, clock=clock, **fields):
            return False
        row = get(repository, workflow_id)
        if row is not None:
            close_probe(repository, row, reason=reason, answered_item=answered_item, clock=clock)
            if to_state != FAILED and answered_item is None:
                _close_declined_factor(repository, row, reason=reason, clock=clock)
    return True


def _apply_move(
    repository: Repository,
    workflow_id: str,
    *,
    to_state: str,
    reason: str,
    from_states: tuple[str, ...],
    release: str | None,
    detail: Mapping[str, Any] | None,
    clock: Clock | None,
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


def note(repository: Repository, workflow_id: str, *, reason: str, detail: Mapping[str, Any],
         clock: Clock | None = None) -> None:
    """An event on the workflow with no move: what a retry needs to read back after a crash."""

    with repository.atomic(), repository.connection() as connection:
        row = store.workflow(connection, workflow_id)
        if row is not None:
            store.insert_event(connection, workflow_id, str(row["state"]), str(row["state"]), reason, detail, _now(clock))


def noted(repository: Repository, workflow_id: str, *, reason: str) -> dict[str, Any]:
    """The latest such note's detail, or nothing."""

    with repository.connection() as connection:
        rows = [row for row in store.workflow_events(connection, workflow_id)
                if row["reason"] == reason and row["from_state"] == row["to_state"]]
    return json.loads(rows[-1]["detail_json"]) if rows else {}


def release_feedback(repository: Repository, workflow_id: str, *, reason: str, exposed: bool = False,
                     clock: Clock | None = None) -> bool:
    """Release what is held; ``exposed`` labels a later probe's answer (§6.0). Once only."""

    now = _now(clock)
    with repository.atomic(), repository.connection() as connection:
        row = store.workflow(connection, workflow_id)
        if row is None:
            return False
        fields = _release_fields(row, reason, now)
        if exposed and not row.get("exposed_at"):
            fields["exposed_at"] = now
        if not fields:
            return False
        store.update_workflow(connection, workflow_id, at=now, **fields)
        return True


def set_fields(repository: Repository, workflow_id: str, *, clock: Clock | None = None, **fields: Any) -> None:
    with repository.atomic(), repository.connection() as connection:
        store.update_workflow(connection, workflow_id, at=_now(clock), **fields)


def superseded(repository: Repository, row: Mapping[str, Any]) -> bool:
    """A newer grade revision came after this workflow: it adds nothing."""

    latest = repository.latest_blind_grade_record(str(row["source_attempt_id"]))
    if latest is None:
        return str(row["revision_key"]) != "joint"
    return str(latest["id"]) != str(row["revision_key"])


def probe_answer_exposed(repository: Repository, presentation_id: str) -> str | None:
    """Why a generated probe's answer is not independent, or None: FG1's two labels.

    ``Show anyway`` marks it, and a wait labels the later probe exposed (spec §6.0).
    """

    if not presentation_id:
        return None
    with repository.connection() as connection:
        if not store.present(connection):
            return None
        row = store.workflow_for_presentation(connection, presentation_id)
    if row is None:
        return None
    if row.get("shown_anyway_at"):
        return "followup_feedback_shown_anyway"
    if row.get("exposed_at"):
        return "followup_feedback_released_before_probe"
    return None


def session_rows(repository: Repository, session_id: str) -> list[dict[str, Any]]:
    """Workflows with something to place: ready, or waiting for a boundary. One learner on one
    desktop, so a question prepared in a session that has since ended still comes first in this one."""

    with repository.connection() as connection:
        if not store.present(connection):
            return []
        return store.open_workflows(connection, states=(READY, WAITING))


def desktop_waiting_count(repository: Repository) -> int:
    """Generated probes the desktop will serve: what a phone says is waiting there (§10)."""

    with repository.connection() as connection:
        if not store.present(connection):
            return 0
        return len(store.open_workflows(connection, states=(READY, WAITING)))


def waiting_still_valid(repository: Repository, row: Mapping[str, Any]) -> bool:
    """§5 item 3, before serving: the factor is still open and the pin's hypotheses current."""

    factor_id = row.get("factor_id")
    if not factor_id:
        return False
    factor = repository.unresolved_cause_factor(str(factor_id))
    if factor is None or factor.get("status") != "open":
        return False
    presentation = repository.probe_presentation(str(row.get("presentation_id") or ""))
    if presentation is None or presentation.status == "ended":
        return False
    current = {
        str(value.get("hypothesis_id")) for value in factor.get("candidate_causes") or []
        if isinstance(value, Mapping) and not value.get("open_set") and value.get("hypothesis_id")
    }
    locked = repository.fetch_hypothesis_set(str(row.get("hypothesis_set_id") or ""))
    labels = {str(value.get("label")) for value in (locked or {}).get("hypotheses") or [] if isinstance(value, Mapping)}
    return current <= labels


def close_probe(repository: Repository, row: Mapping[str, Any], *, reason: str, answered_item: str | None = None,
                clock: Clock | None = None) -> None:
    """What a workflow prepared and nobody will answer is closed: its probe and anything an
    interrupted run left unbound are withdrawn, and an episode it pinned one on doesn't stay
    open on the topic if it measured nothing. An interrupted run never bound its item, so the
    row doesn't name any of that: the ledger does. One commit, held with the move by :func:`finish`.
    ``answered_item`` stays as it is, and so does whatever its answer measured."""

    from learnloop.followup_serve import identity

    with repository.atomic():
        workflow_id = str(row["id"])
        with repository.connection() as connection:
            pinned = store.episodes_pinned_by_workflow(connection, workflow_id)
        item_id = row.get("practice_item_id")
        if item_id and str(item_id) != answered_item:
            identity.withdraw(repository, str(item_id), reason=reason, workflow_id=workflow_id, clock=clock)
        identity.retire_unbound(repository, workflow_id, reason=reason, keep=answered_item, clock=clock)
        if row.get("presentation_id") and answered_item is None:
            repository.end_probe_presentation(str(row["presentation_id"]), end_reason="abandoned", clock=clock)
        for episode_id in dict.fromkeys([*filter(None, [row.get("probe_episode_id")]), *pinned]):
            _abandon_if_empty(repository, str(episode_id), clock=clock)


def _close_declined_factor(repository: Repository, row: Mapping[str, Any], *, reason: str, clock: Clock | None) -> None:
    """R9: the factor this lane opened for its question goes when the question won't be asked:
    left open, it would hold the topic in the plan's repair lane with no repair to serve. A failed
    workflow keeps it, since its need stays open for background generation (§6.2)."""

    for factor in repository.unresolved_cause_factors_for_attempt(str(row["source_attempt_id"]), status="open"):
        if factor.get("algorithm_version") == RIVAL_CAUSES_FACTOR_VERSION:
            repository.close_unresolved_cause_factor(
                str(factor["id"]), status="retired", resolution_kind=FACTOR_DECLINED,
                resolution_detail={"workflow_id": str(row["id"]), "reason": reason}, clock=clock,
            )


def _abandon_if_empty(repository: Repository, episode_id: str, *, clock: Clock | None) -> None:
    """An open episode with no observation, and no presentation left that could make one."""

    episode = repository.probe_episode(episode_id)
    if episode is None or episode.status not in {"pending_items", "in_progress"}:
        return
    # ``probe_episodes.episode_has_observations``, read here: a leaf imports no domain package.
    if repository.probe_observations_for_episode(episode_id):
        return
    if all(presentation.status == "ended" for presentation in repository.probe_presentations_for_episode(episode_id)):
        repository.update_probe_episode_status(episode_id, status="abandoned", clock=clock)


def retire_waiting(repository: Repository, row: Mapping[str, Any], *, reason: str, clock: Clock | None = None) -> None:
    """A wait that can't be served now: its probe retires, unused, and nothing else follows."""

    finish(repository, str(row["id"]), to_state=SKIPPED, reason=reason, release=RELEASE_FALLBACK,
           from_states=(WAITING, READY), clock=clock)


def probe_answered(repository: Repository, practice_item_id: str, *, attempt_id: str, clock: Clock | None = None,
                   link_exposures: bool = False) -> bool:
    """The probe's answer settles the workflow, and §6.0's hold ends, by the item whichever
    way it was answered: a contract that could not stand (no grading route at the serve) must
    not strand what was held. Runs on the live path only.

    ``link_exposures`` (FG1c, the caller reads ``followup.hypothesis_marks``): each earlier display
    of the miss's list of causes gets its later linked receipt. The display's row never changes,
    and a refused link rolls back alone, so it never blocks the answer."""

    if not practice_item_id:
        return False
    with repository.connection() as connection:
        if not store.present(connection):
            return False
        row = store.workflow_for_item(connection, practice_item_id)
    if row is None or row["state"] not in {READY, WAITING}:
        return False
    with repository.atomic():
        if not finish(repository, str(row["id"]), to_state=SETTLED, reason="probe_answered",
                      release=RELEASE_PROBE_ANSWERED, from_states=(READY, WAITING), detail={"attempt_id": attempt_id},
                      answered_item=practice_item_id, clock=clock):
            return False
        if row.get("decision_id"):
            with repository.connection() as connection:
                store.append_binding(connection, decision_id=str(row["decision_id"]), workflow_id=str(row["id"]),
                                     binding_kind="outcome", outcome="answered", at=_now(clock))
        if link_exposures:
            with repository.connection() as connection:
                if marks_store.present(connection):
                    marks_store.link_probe_answer(connection, attempt_id=str(row["source_attempt_id"]),
                                                  probe_attempt_id=attempt_id, at=_now(clock))
    return True


def settle_open_when_off(vault: Any, repository: Repository, *, clock: Clock | None = None) -> int:
    """§10: with the switch off, open workflows settle as skipped and burns persist. What they
    prepared closes with them: an unserved probe and its presentation, an empty episode. A
    standing plan displaces the retired item at its next reconcile, whatever the switch says."""

    if generate_and_serve_on(vault.config):
        return 0
    with repository.connection() as connection:
        if not store.present(connection):
            return 0
        rows = store.open_workflows(connection)
    settled = 0
    for row in rows:
        if finish(repository, str(row["id"]), to_state=SKIPPED, reason="switch_off", release=RELEASE_SWITCH_OFF,
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
    "FAILED", "OPEN_STATES", "PENDING", "READY", "REFUSED", "SETTLED", "SKIPPED", "WAITING", "WORKFLOW_OWNS_REASON",
    "attempt_workflow", "close_probe", "desktop_waiting_count", "diagnosis_ended", "finish", "get", "move", "open_for_attempt", "probe_answer_exposed", "probe_answered", "release_feedback", "retire_waiting", "session_rows", "waiting_still_valid", "owns_attempt", "settle_open_when_off",
    "superseded", "workflow_id_for", "workflow_of_item",
]
