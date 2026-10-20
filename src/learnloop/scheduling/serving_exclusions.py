"""Items routine serving never offers, shared by Today's queue, the quick check
and ``find_practice``.

Four exclusions keep an item out of every routine selection, whatever ranks it:

- **exam reservations**: an item reserved for a goal's held-out exam stays
  unseen so the exam remains an honest, uncontaminated test;
- **held-out material**: an item made from material held out for evaluation
  (its canonical exercise or a block-level source ref in the one held-out
  partition, ``content.sources.exam_material``), whenever the unit was marked:
  held-out exam material is never leaked into practice (exam protection,
  Codex review F1; kill switch ``goals.held_out_selection``);
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

:func:`routine_withhold_reason` is the scheduler's whole per-item routine gate
(lifecycle, item state, these sets, single-use and unservable surfaces, the
learner-set LO lifecycle), in its order. ``build_due_queue`` runs it before the
intent gate, and a daily-loop DL2 "Check once" asks it before it chooses a cold
candidate over a practice one, so an item routine serving can never serve
never decides a check (DL2 Codex re-review F11).
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, timedelta
from collections.abc import Iterable
from typing import Any

from learnloop.clock import Clock, SystemClock
from learnloop.content.sources.exam_material import held_out_items, held_out_selection_active
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.goals.exam_pool import reserved_item_ids
from learnloop.scheduling import controller_ownership
from learnloop.substrate.instrument_serving import unservable_reason
from learnloop.vault.lifecycle import practice_item_servable


@dataclass(frozen=True)
class ServingExclusions:
    reserved_exam_item_ids: frozenset[str]
    rung_variant_hold_ids: frozenset[str]
    staged_owned_item_ids: frozenset[str]
    #: Out-of-timing rules; empty from :func:`routine_serving_exclusions`.
    cold_check_reserved_item_ids: frozenset[str] = frozenset()
    revealed_recently_item_ids: frozenset[str] = frozenset()
    #: Items made from held-out material (empty with ``goals.held_out_selection`` off).
    held_out_item_ids: frozenset[str] = frozenset()

    @property
    def item_ids(self) -> frozenset[str]:
        """What routine serving never offers."""

        return (self.reserved_exam_item_ids | self.rung_variant_hold_ids | self.staged_owned_item_ids
                | self.held_out_item_ids)

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
        held_out_item_ids=held_out_items(vault, repository) if held_out_selection_active(vault) else frozenset(),
    )


def routine_withhold_reason(vault: Any, item: Any, state: Any, exclusions: ServingExclusions) -> str | None:
    """Why routine serving never offers ``item`` now, or None.

    The checks ``build_due_queue`` runs first for every item, in its order and
    with its reason codes (``withheld(reason, item_id)``): a retired item, an
    inactive state, an exam reservation, held-out material, a pending-variant
    hold, staged ownership, a dialogue-turn instance, an administered
    diagnostic probe, a stimulus the practice surface cannot render, no
    learning object, and a put-away LO or adopted reference card."""

    item_id = item.id
    # Learner-retired items are never served, independent of sync ordering.
    if item.status != "active":
        return "retired"
    if state is not None and not state.active:
        return "inactive_state"
    if item_id in exclusions.reserved_exam_item_ids:
        return "reserved_exam"
    if item_id in exclusions.held_out_item_ids:
        return "held_out_material"
    # Pending-variant hold: the learner asked for an easier/harder sibling of
    # this exact card and it is still being authored; re-serving the very card
    # the learner stepped away from inverts the variant-first ordering.
    if item_id in exclusions.rung_variant_hold_ids:
        return "rung_variant_hold"
    # P4 §14.2 step 3: a staged-owned commitment's items are the staged
    # policy's to schedule, never the legacy queue's (design §A.2 rule 3).
    if item_id in exclusions.staged_owned_item_ids:
        return "staged_owned"
    # Ephemeral dialogue-turn instances (§8.1) exist only to carry their one
    # committed diagnostic attempt; they are never ordinary practice.
    if item.practice_mode == "diagnostic_microprobe":
        return "diagnostic_microprobe"
    # Vault-authored diagnostic probes are single-use surfaces: once the item
    # has carried an attempt, re-serving it would conflate memorization of the
    # question with understanding (also for vaults whose administration
    # predates the deactivation on attempt).
    if item.practice_mode == "diagnostic_probe" and state is not None and state.last_attempt_at is not None:
        return "diagnostic_probe_administered"
    # Meas §3.A2/§3.A3: an item whose stimulus the practice surface cannot
    # render is not schedulable (``learnloop.substrate.instrument_serving``).
    if unservable_reason(item) is not None:
        return "unservable_stimulus"
    if vault.learning_object_for_item(item) is None:
        return "no_learning_object"
    # Learner-set LO lifecycle: a dormant or resolved Learning Object has been
    # put away; nor is a card the reference sweep adopted while that sweep's
    # kill switch is off served (vault.lifecycle).
    if not practice_item_servable(vault, item):
        return "lifecycle_put_away"
    return None


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
        held_out_item_ids=routine.held_out_item_ids,
    )
