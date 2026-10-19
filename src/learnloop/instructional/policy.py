"""Server-side caller contexts (spec_source_practice_and_probes_v1 §5.2).

Every call's retrieval policy is derived on the server from where the call
comes from: the tutor's question event, the item and attempt it is bound to,
whether a cold administration of that item is open, and whether its attempt
window has closed. A model's arguments, or a frontend's, can narrow a request;
they can never widen its policy (SC2). The pure mapping from a context to a
policy is ``source_retrieval.policy.derive_policy``.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from typing import Any

from learnloop.attempts.attempts import COLD_FOLLOWUP_TASK_KINDS
from learnloop.content.sources.exam_material import exam_reserved
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.source_retrieval.policy import ITEM_BOUND_CONTEXTS, CallerContext, PolicyRefused, derive_policy
from learnloop.vault.models import LoadedVault

#: A submission at or above this correctness closes the item's attempt window
#: (a redo, guided redo or retry is no longer offered). It names what
#: "correct" means for the window; it decides no learning.
WINDOW_CLOSING_CORRECTNESS = 0.999


#: A caller note: the item is reserved for a goal's held-out exam.
EXAM_RESERVED_NOTE = "exam_reserved"


def cold_administration_open(repository: Repository, item_id: str | None) -> bool:
    """Whether ``item_id`` is reserved by an open cold follow-up task, or for a
    goal's held-out exam.

    An item reserved for a held-out exam is a cold administration until its
    pool is released (exam protection, 2026-10-13): nothing is retrieved,
    compared or proposed for it, and the tutor grounds in nothing, exactly as
    for an open cold check (the one exam predicate,
    ``content.sources.exam_material.exam_reserved``)."""

    if not item_id:
        return False
    if exam_reserved(repository, item_id):
        return True
    for kind in sorted(COLD_FOLLOWUP_TASK_KINDS):
        for task in repository.open_followup_tasks_of_kind(kind):
            if str(task.get("selected_item_id") or "") == item_id:
                return True
    return False


def attempt_window_open(repository: Repository, item_id: str | None) -> bool | None:
    """False once the item's latest attempt was a correct submission; else True.

    A grade held for review (THE predicate, ``held_grades``) is the grader's
    provisional score, not a correct submission: it keeps the window open
    (so it never unlocks the item's own passages or solution)."""

    from learnloop.held_grades import held_for_review_attempts

    if not item_id:
        return None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute(
            "SELECT id, correctness FROM practice_attempts WHERE practice_item_id=? "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            (item_id,),
        ).fetchone()
        held = bool(row is not None and held_for_review_attempts(connection, (row[0],)))
    if row is None:
        return True
    correctness = row[1]
    return held or not (correctness is not None and float(correctness) >= WINDOW_CLOSING_CORRECTNESS)


def cold_notes(repository: Repository, item_id: str | None) -> tuple[str, ...]:
    """Why a cold administration is open, when it is for the exam's sake."""

    return (EXAM_RESERVED_NOTE,) if exam_reserved(repository, item_id) else ()


def learning_objects_for_event(vault: LoadedVault, event: Mapping[str, Any]) -> tuple[str, ...]:
    """The LOs a tutor question is about: its item's, its note's or its span's."""

    found: list[str] = []
    item_id = event.get("practice_item_id")
    item = vault.practice_items.get(item_id) if item_id else None
    if item is not None:
        found.append(item.learning_object_id)
    note_id = event.get("note_id")
    note = vault.notes.get(note_id) if note_id else None
    if note is not None:
        found.extend(str(lo_id) for lo_id in note.related_los)
    source_context = event.get("source_context") or {}
    found.extend(str(lo_id) for lo_id in source_context.get("candidate_learning_object_ids") or ())
    # The question-time facet -> LO mapping the tutor grounded (prerequisite
    # questions point below the anchors).
    for owners in (source_context.get("facet_learning_object_ids") or {}).values():
        found.extend(str(lo_id) for lo_id in owners or ())
    return tuple(lo_id for lo_id in dict.fromkeys(found) if lo_id in vault.learning_objects)


def caller_for_question_event(vault: LoadedVault, repository: Repository, event_id: str, *,
                              post_attempt: bool = False) -> CallerContext:
    """The tutor's caller context, rebuilt from the stored question event."""

    event = repository.question_event(event_id)
    if event is None:
        raise PolicyRefused("unknown_caller", f"Unknown question event {event_id}")
    context = str(event.get("context") or "")
    item_id = event.get("practice_item_id") if context in ITEM_BOUND_CONTEXTS else None
    stored_cold = False
    if context == "reader":
        # Reader workbench RW1c (Codex review F2, re-review F2): a Reader
        # question asked inside a workbench session bound to an item is stored
        # on that item, and one asked during a cold administration carries the
        # restriction it was asked under (``reader_caller``, or the lookup's
        # own ``cold_attempt`` policy). Anything later rebuilt from it reads as
        # that item's practice, or cold, never wider than it was asked under:
        # a stored cold stays cold, whatever today's status.
        source_context = event.get("source_context") or {}
        restriction = source_context.get("reader_caller") or {}
        retrieval = (source_context.get("reader_tutor") or {}).get("retrieval") or {}
        stored_cold = bool(restriction.get("cold")) or "cold_attempt" in (
            restriction.get("policy"), retrieval.get("policy"))
        bound = event.get("practice_item_id") or restriction.get("item_id")
        if bound:
            item_id, context = str(bound), "practice"
    return CallerContext(
        kind="tutor", ref=event_id, context=context, item_id=item_id,
        attempt_id=event.get("attempt_id"),
        learning_object_ids=learning_objects_for_event(vault, event),
        cold=stored_cold or cold_administration_open(repository, item_id),
        window_open=attempt_window_open(repository, item_id) if item_id else None,
        post_attempt_requested=post_attempt, notes=cold_notes(repository, item_id),
    )


def caller_for(repository: Repository, kind: str, ref: str | None = None, *,
               item_id: str | None = None, attempt_id: str | None = None,
               learning_object_ids: Sequence[str] = (), post_attempt: bool = False,
               context: str | None = None) -> CallerContext:
    """A server-side caller with no question event (plan, Reader UI, need, agent)."""

    return CallerContext(
        kind=kind, ref=ref, context=context, item_id=item_id, attempt_id=attempt_id,
        learning_object_ids=tuple(learning_object_ids),
        cold=cold_administration_open(repository, item_id),
        window_open=attempt_window_open(repository, item_id) if item_id else None,
        post_attempt_requested=post_attempt, notes=cold_notes(repository, item_id),
    )


def policy_for(caller: CallerContext) -> dict[str, Any]:
    policy, reason = derive_policy(caller)
    return {"policy": policy, "derived_from": reason, "caller": caller.as_dict()}


def check_named_ids(caller: CallerContext, *, item_id: str | None = None,
                    attempt_id: str | None = None) -> None:
    """A request naming an item or attempt it was not called about is refused (G2)."""

    if item_id is not None and caller.item_id is not None and item_id != caller.item_id:
        raise PolicyRefused("caller_mismatch", "the request names an item this caller was not called about")
    if attempt_id is not None and caller.attempt_id is not None and attempt_id != caller.attempt_id:
        raise PolicyRefused("caller_mismatch", "the request names an attempt this caller was not called about")


__all__ = [
    "EXAM_RESERVED_NOTE",
    "WINDOW_CLOSING_CORRECTNESS",
    "attempt_window_open",
    "caller_for",
    "caller_for_question_event",
    "check_named_ids",
    "cold_administration_open",
    "cold_notes",
    "learning_objects_for_event",
    "policy_for",
]
