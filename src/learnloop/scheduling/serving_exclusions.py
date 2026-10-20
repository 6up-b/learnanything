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

:func:`routine_withhold_reason` is the scheduler's per-item routine gate
(lifecycle, item state, these sets, single-use and unservable surfaces, the
learner-set LO lifecycle), in its order. :func:`admission_reason` is the
scheduler's WHOLE per-item admission: the routine gate, then the build's own
gates (:class:`BuildGates`: the diagnostic freshness reserve, placement, the
cold-start gate and the probe-episode gates), in ``build_due_queue``'s order
and with its reason codes (:data:`ADMISSION_GATES`). ``build_due_queue`` asks
it for every item, and a daily-loop DL2 "Check once" asks it for every
candidate before it prefers a cold one over practice, so an item the build
would not serve never decides a check (DL2 Codex re-review F11, orchestrator
ruling R1: one admission predicate).
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, timedelta
from collections.abc import Iterable
from typing import Any, Protocol

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


#: The routine gate's reason codes, in the order :func:`routine_withhold_reason` asks.
ROUTINE_GATES: tuple[str, ...] = (
    "retired",
    "inactive_state",
    "reserved_exam",
    "held_out_material",
    "rung_variant_hold",
    "staged_owned",
    "diagnostic_microprobe",
    "diagnostic_probe_administered",
    "unservable_stimulus",
    "no_learning_object",
    "lifecycle_put_away",
)
#: The build's own gates (:class:`BuildGates`), in the order
#: :func:`admission_reason` asks them after the routine gate.
BUILD_GATES: tuple[str, ...] = (
    "diagnostic_freshness_reserve",
    "placement_assumed_withheld",
    "placement_maintained_withheld",
    "cold_start_unattempted",
    "voi_value_below_minutes_cost",
    "diagnostic_reserved",
)
#: Every reason :func:`admission_reason` can give: every per-item gate of
#: ``build_due_queue`` (a test enumerates the build's ``withheld`` reasons
#: against it). Intent's own reasons (``intent_*``) are the check's, and
#: ``zero_priority`` is ranking: a request (every check candidate is one)
#: carries the requested floor, so it never meets it.
ADMISSION_GATES: tuple[str, ...] = ROUTINE_GATES + BUILD_GATES
#: The probe-episode gates: a diagnostic surface of an in-progress episode
#: that is not a probe this build (the build annotates it on the slate).
PROBE_RESERVED_GATES: frozenset[str] = frozenset({"voi_value_below_minutes_cost", "diagnostic_reserved"})


class BuildGates(Protocol):
    """The build's per-item gates after the routine one. The scheduler
    implements them (``scheduler._BuildAdmission``) over one build's reads;
    each returns a reason from :data:`BUILD_GATES` or None."""

    def freshness_gate(self, item: Any, state: Any) -> str | None:
        """A diagnostic_probe surface outside an in-progress, unblocked episode."""

    def placement_gate(self, item: Any, state: Any) -> str | None:
        """Placement's withholding of an unrequested item (assumed, maintained)."""

    def cold_start_gate(self, item: Any, state: Any) -> str | None:
        """An unrequested item on a never-practised LO with nothing to start it."""

    def probe_gate(self, item: Any, state: Any) -> str | None:
        """A diagnostic_probe surface of an in-progress episode that is not a
        probe this build (surface seen, no binding, its value below its
        minutes, no information)."""


def admission_reason(
    vault: Any,
    item: Any,
    state: Any,
    exclusions: ServingExclusions,
    gates: BuildGates | None,
    *,
    requested: bool,
    intent_gate: Any = None,
) -> str | None:
    """Why the build does not serve ``item`` now, or None: THE per-item
    admission predicate (orchestrator ruling R1).

    In ``build_due_queue``'s order: the routine gate
    (:func:`routine_withhold_reason`); ``intent_gate(item_id)`` when given
    (the build's intent gate, which is the check's own decision, so the check
    selection passes none); then the build's gates: the diagnostic freshness
    reserve, placement and the cold-start gate (a request is exempt from
    both: the learner asked for it), and the probe-episode gates. ``gates``
    None asks the routine gate only (a selector outside the build)."""

    reason = routine_withhold_reason(vault, item, state, exclusions)
    if reason is not None:
        return reason
    if intent_gate is not None and (reason := intent_gate(item.id)) is not None:
        return reason
    if gates is None:
        return None
    probe_surface = item.practice_mode == "diagnostic_probe"
    # Freshness reserve: a diagnostic surface carries one diagnostic
    # administration; outside an in-progress episode it is never served.
    if probe_surface and (reason := gates.freshness_gate(item, state)) is not None:
        return reason
    if not requested:
        if (reason := gates.placement_gate(item, state)) is not None:
            return reason
        if (reason := gates.cold_start_gate(item, state)) is not None:
            return reason
    if probe_surface and (reason := gates.probe_gate(item, state)) is not None:
        return reason
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
