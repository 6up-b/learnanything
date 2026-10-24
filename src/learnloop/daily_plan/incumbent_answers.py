"""The incumbent's answers to adaptive difficulty's slot (AD2+AD3; the compose fix round 3).

The only code that runs inside AD's incumbent scope. ``adaptive_difficulty.operation.incumbent_answer``
asks one of the two questions here (``protected_tables.INCUMBENT_QUESTIONS``) from one of the two
pinned entry functions in ``daily_plan.ad_slot``, with:

* the operation's own handles on the vault and the database (``IncumbentHandles``), and
* a request of plain, immutable data (ids, scalars, datetimes, read-only mappings, frozen incumbent
  dataclasses), validated before the question runs;

and each question answers plain data, validated after it. Everything here is the incumbent's own
code (the plan's pool and admission, the staged frame, the scheduler's per-item predicate, the
routine exclusions); nothing AD defined runs here, and the guard refuses a read whose stack holds AD
code or a callback from outside LearnLoop, and every write.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from learnloop.daily_plan.lanes import PoolItem


@dataclass(frozen=True)
class ExclusionsRequest:
    """The routine exclusions a selector outside the scheduler's timing honours, at ``now``."""

    now: datetime
    cold_followup_kinds: tuple[str, ...]
    reveal_window: timedelta
    #: Reveals AD's material view withholds (they exclude nothing).
    withheld_reveal_ids: frozenset[str]


@dataclass(frozen=True)
class SlotAdmissionRequest:
    """One slot's (or one boundary's deferrals') admission question."""

    now: datetime
    session_id: str | None
    plan_id: str
    #: The scheduler's queue this advance's build produced (deep-frozen ``ScheduledItem``s).
    scheduled: tuple[Any, ...]
    #: The item states as AD's material view reads them (a read-only mapping).
    item_states: Mapping[str, Any]
    #: Every candidate AD enumerated, as the plan's pool items (synthetic when not in the pool).
    candidates: tuple[PoolItem, ...]
    #: The slot's own planned item (None for deferrals): not counted as taken, judged as its siblings.
    slot_item_id: str | None
    #: AD deferrals being re-read (released from the plan's exclusions for the membership).
    released: frozenset[str]


@dataclass(frozen=True)
class SlotAdmission:
    """The answer: the plan's admitted pool (ids) and, for its member candidates only, the refusals
    (``(item id, reasons)`` pairs), the items an open cold check holds (None: unreadable) and the
    items a reserved assessment surface holds."""

    pool: frozenset[str]
    refusals: tuple[tuple[str, tuple[str, ...]], ...]
    cold_items: frozenset[str] | None
    reserved_items: frozenset[str]


def routine_exclusions(handles: Any, request: ExclusionsRequest) -> Any:
    """``serving_exclusions.out_of_timing_serving_exclusions`` at the request's instant."""

    from learnloop.clock import FrozenClock
    from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions

    return out_of_timing_serving_exclusions(
        handles.vault,
        handles.repository,
        cold_followup_kinds=frozenset(request.cold_followup_kinds),
        reveal_window=request.reveal_window,
        clock=FrozenClock(request.now),
        exclude_reveal_ids=frozenset(request.withheld_reveal_ids),
    )


def slot_admission(handles: Any, request: SlotAdmissionRequest) -> SlotAdmission:
    """The plan's admitted pool at this boundary (``engine.admitted_new_material_ids``, classified
    with the request's item states, the slot's own item judged as its siblings); then, for the member
    candidates, the staged frame's admission on a fresh controller snapshot and the plan pool's
    per-item predicate (``scheduler.pool_admission``)."""

    from learnloop.clock import FrozenClock
    from learnloop.daily_plan.engine import PlanEnv, _reload, admitted_new_material_ids
    from learnloop.daily_plan.policy import router_active
    from learnloop.daily_plan.staged_frame import StagedFrame
    from learnloop.scheduling.scheduler import pool_admission

    vault, repository = handles.vault, handles.repository
    clock = FrozenClock(request.now)
    env = PlanEnv(vault=vault, repository=repository, clock=clock, session_id=request.session_id)
    record = _reload(env, request.plan_id)
    states = dict(request.item_states)
    unclaimed = (request.slot_item_id,) if request.slot_item_id is not None else ()
    admitted = admitted_new_material_ids(env, record, scheduled=request.scheduled, item_states=states,
                                         released=request.released, unclaimed=unclaimed)
    members = [candidate for candidate in request.candidates if candidate.practice_item_id in admitted]
    material = StagedFrame(vault, repository, clock=clock, item_states=dict(states).copy).material(members)
    refuse = pool_admission(vault, repository, now=request.now, item_states=dict(states))
    staged = router_active(vault)
    refusals = []
    for candidate in members:
        item_id = str(candidate.practice_item_id)
        reasons: list[str] = []
        if staged:
            for reason in material.refusals.get(item_id, ()):
                reasons.append(f"constraint:{reason.get('constraint') or reason.get('key') or 'refused'}")
        pooled = refuse(item_id)
        if pooled is not None:
            reasons.append(f"pool:{pooled}")
        refusals.append((item_id, tuple(str(reason) for reason in reasons)))
    cold = material.cold_items
    return SlotAdmission(
        pool=frozenset(str(item_id) for item_id in admitted),
        refusals=tuple(refusals),
        cold_items=None if cold is None else frozenset(str(item_id) for item_id in cold),
        reserved_items=frozenset(str(item_id) for item_id in material.reserved_items),
    )


__all__ = ["ExclusionsRequest", "SlotAdmission", "SlotAdmissionRequest", "routine_exclusions", "slot_admission"]
