"""Items routine serving never offers, shared by Today's queue, the quick check
and ``find_practice``.

Three exclusions keep an item out of every routine selection, whatever ranks it:

- **exam reservations**: an item reserved for a goal's held-out exam stays
  unseen so the exam remains an honest, uncontaminated test;
- **pending-variant holds**: the learner asked for an easier or harder sibling
  of this exact card and it is still being authored;
- **staged-controller ownership**: during the dual-controller cutover the
  staged policy owns these commitments' items (design §A.2 rule 3).

A selector that picks an item *outside the scheduler's timing* (the optional
quick check of learner field F2, a ``find_practice`` proposal of the Phase 5b
practice index) also honours two rules the scheduler enforces through timing
(:func:`out_of_timing_serving_exclusions`):

- **reserved cold checks**: the selected item of an open cold follow-up task is
  a single-use measurement; serving it early would spend it;
- **recent reveals**: an item whose answer was revealed within the cold
  retrieval delay is not offered (the scheduler defers a revealed cold task
  for the same window).

Callers pass the cold follow-up task kinds
(``attempts.attempts.COLD_FOLLOWUP_TASK_KINDS``) and that window
(``diagnosis.remediation.COLD_RETRIEVAL_DELAY``): this module may not add
edges from ``scheduling`` to ``attempts`` or ``diagnosis`` (the frozen
cross-package cycle contract and function-local edge inventory).

Item-level blocks that are pure reads of the vault (a dormant or resolved LO,
and a card the reader's reference-question sweep adopted while
``tutor_qa.adopt_reference_questions`` is off) live in
``vault.lifecycle.practice_item_serving_block``; every selector asks it too.

Nothing withholds an item because of a Slice 1 M2 diagnosis: a queued or
running diagnosis only delays the next routine queue build (the bounded wait
in the sidecar's ``get_today_queue``), and a held one (split switched off)
serves nothing.

``build_due_queue``, the quick check and ``find_practice`` read these sets
from here, so a selector cannot forget one of them.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, timedelta
from collections.abc import Iterable
from typing import Any

from learnloop.clock import Clock, SystemClock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.goals.exam_pool import reserved_item_ids
from learnloop.scheduling import controller_ownership


@dataclass(frozen=True)
class ServingExclusions:
    reserved_exam_item_ids: frozenset[str]
    rung_variant_hold_ids: frozenset[str]
    staged_owned_item_ids: frozenset[str]
    #: Out-of-timing rules; empty from :func:`routine_serving_exclusions`.
    cold_check_reserved_item_ids: frozenset[str] = frozenset()
    revealed_recently_item_ids: frozenset[str] = frozenset()

    @property
    def item_ids(self) -> frozenset[str]:
        """What routine serving never offers."""

        return self.reserved_exam_item_ids | self.rung_variant_hold_ids | self.staged_owned_item_ids

    @property
    def out_of_timing_item_ids(self) -> frozenset[str]:
        """What a selector outside the scheduler's timing never offers."""

        return self.item_ids | self.cold_check_reserved_item_ids | self.revealed_recently_item_ids


def routine_serving_exclusions(vault: Any, repository: Repository) -> ServingExclusions:
    """The shared exclusion sets, each read once."""

    return ServingExclusions(
        reserved_exam_item_ids=frozenset(reserved_item_ids(repository)),
        rung_variant_hold_ids=frozenset(repository.rung_variant_pending_source_ids()),
        staged_owned_item_ids=frozenset(controller_ownership.staged_owned_practice_item_ids(vault, repository)),
    )


def _iso(value: Any) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def out_of_timing_serving_exclusions(
    vault: Any,
    repository: Repository,
    *,
    cold_followup_kinds: Iterable[str],
    reveal_window: timedelta,
    clock: Clock | None = None,
) -> ServingExclusions:
    """The routine sets plus the items reserved by open cold follow-up tasks of
    ``cold_followup_kinds`` and the items revealed within ``reveal_window``
    (the cold retrieval delay), read once."""

    from learnloop.db.stores.practice_index import items_revealed_between

    now = (clock or SystemClock()).now()
    cold_reserved = {
        str(task["selected_item_id"])
        for kind in sorted(set(cold_followup_kinds))
        for task in repository.open_followup_tasks_of_kind(kind)
        if task.get("selected_item_id")
    }
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        revealed = items_revealed_between(
            connection, since=_iso(now - reveal_window), until=_iso(now),
        )
    routine = routine_serving_exclusions(vault, repository)
    return ServingExclusions(
        reserved_exam_item_ids=routine.reserved_exam_item_ids,
        rung_variant_hold_ids=routine.rung_variant_hold_ids,
        staged_owned_item_ids=routine.staged_owned_item_ids,
        cold_check_reserved_item_ids=frozenset(cold_reserved),
        revealed_recently_item_ids=frozenset(revealed),
    )
