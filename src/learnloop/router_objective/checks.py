"""RO5 §9 item 2: randomized cold checks, embedded by default.

**The draw** (:func:`draw_day`). At the day's first plan decision, before any action draw and independent of every
one (it reads only the date and the eligible set, never a decision), a seeded draw over the ``N_d`` valued topics
that have an eligible item that day. Valued topics are §8.7's population: the active goals' scopes and the
retention commitments (LOs with FSRS memory), each with its undated density. An eligible item is unseen (never
attempted), unrevealed (no reveal row at all), unassisted so far (no help row), not exam-reserved, held out,
protected or reserved by any routine exclusion, and servable. Then:

* ``check_rate = "embedded"``: ``k = embedded_checks_per_day`` topics without replacement, uniformly, so
  ``r_L = k/N_d`` exactly (``1/N_d`` at the default);
* a number ``ρ``: each eligible topic independently with probability ``ρ`` (``r_L = ρ``), as many checks as drawn;
* a topic with no eligible item has ``r_L = 0`` that day, recorded, and raises a generation need through the
  existing path (``intervention_needs``, the diagnostic practice generator's queue; nothing is generated here).

The day's record (``check-day:<date>``: the mode, ``r`` per topic, the zero topics, the needs) and one assignment
per drawn slot (``check-day:<date>:<slot>``: the topic, its item, ``r``) go to ``policy_experiment_assignments``.
Same date, same eligible set: the same draw (the seed is the date's).

**Serving** (:func:`place`). The frame administers the day's checks at the first boundary of the day's first
session, BEFORE that boundary's decision, as their own block placed by the rules (``daily_plan.engine.
_randomized_check_block``, Codex re-review F2), so whether a check is administered never depends on what any
decision draws (a practice block, a reading or a stop); outside the two-policy mix and outside ``μ``. Its minutes
come off the plan's as any block's (the policy's first block follows, with that much less room). It is an ordinary
independent attempt under the existing evidence rules, with no label for the learner (its plan origin is
:data:`ORIGIN`, shown to the learner as an ordinary item). Its administration is the ``item_planned`` receipt's
``ro5_check`` entry, with the topic's sensors frozen at that moment for the combiner (§9 item 7).

**Resolution** (:func:`resolve`, a read). Each slot is ``completed`` (the first attempt on the check's presentation,
or on its item after it was planned, scored by §6.2's label: AD's unassisted success, so any help makes it a
non-success), ``excluded:<reason>`` (answered, but its grade carries no label as it stands now: held for review,
a current grading epoch that assesses nothing, a quarantined interpretation, an attempt type AD does not read, no
correctness, or a label AD censors; never read as a zero, Codex review F1; it counts as not completed in the
completion rate, which is the rate of labelled completions), or not, with its reason:
``not_administered:no_session``, ``not_administered:no_practice_slot``
(the day had a session but its first session placed no check: no eligible item of the topic in the plan's pool
at any of its boundaries; the reason's name is kept from RO5's first build), ``displaced``, ``skipped``, ``not_answered``
or ``not_answered:device_deferred`` (a phone's step left it for the desktop, mobile v2 §2.2). A day with no session
counts toward the completion gap (§8.7): the running completion rate is completed checks over assigned checks
plus the checks of every day with no session since the first draw. Every such read is as of one closure
(:class:`Closure`, landing ruling R1): the check's (the end of a date) or a scored window's, every counted event
filtered by :meth:`Closure.admits` alone.

A leaf apart from its reads: the standard library, the router's uniform and the vault's tables.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
import hashlib
import json
import logging
from typing import Any

from learnloop.router import mixture as mx
from learnloop.router_objective import assignments as A

LOG = logging.getLogger(__name__)

VERSION = "ro5_randomized_check_v1"
RESOLVER_VERSION = "ro5_check_resolver_v1"
ORIGIN = "randomized_check"
DAY_PREFIX = "check-day:"
NEED_TRIGGER = "ro5_randomized_check"
NEED_BLOCKED = "no_unseen_unassisted_item"
#: Noncompletion reasons.
NO_SESSION = "not_administered:no_session"
NO_PRACTICE_SLOT = "not_administered:no_practice_slot"
DISPLACED = "displaced"
SKIPPED = "skipped"
NOT_ANSWERED = "not_answered"
#: Mobile v2 §2.2: administered, left for the desktop by a phone's step (its ``item_device_deferred``
#: receipt), and never answered by the day's end. Not completed, as ``not_answered`` is: its own name
#: lets the completion term and the report see what the device held.
DEVICE_DEFERRED = "not_answered:device_deferred"
DEVICE_DEFERRED_EVENT = "item_device_deferred"
OPEN = "open"
COMPLETED = "completed"
#: Answered, but its grade carries no label now (Codex review F1): the reason follows the prefix.
EXCLUDED_PREFIX = "excluded:"
EXCLUDED_TYPE = "excluded:attempt_type"
EXCLUDED_UNASSESSED = "excluded:unassessed"
EXCLUDED_QUARANTINED = "excluded:quarantined"
EXCLUDED_UNGRADED = "excluded:ungraded"
EXCLUDED_LABEL = "excluded:no_label"


def day_unit(local_date: str) -> str:
    return f"{DAY_PREFIX}{local_date}"


def slot_unit(local_date: str, slot: int) -> str:
    return f"{DAY_PREFIX}{local_date}:{slot}"


def day_seed(local_date: str) -> str:
    return hashlib.sha256(f"{A.CHECK}|{local_date}".encode("utf-8")).hexdigest()


# -- eligibility -----------------------------------------------------------------------------------------


#: ``(los, exclude) -> {lo: [eligible item ids]}``: the eligibility rule (module docstring), read by the plan
#: (``daily_plan.objective_inputs.check_eligible_items``), which owns the protection and exclusion reads.
Eligible = Any


# -- the draw --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Day:
    local_date: str
    mode: str
    value: float
    seed: str
    #: r_L per valued topic (0 for one with no eligible item)
    r: Mapping[str, float]
    zero: tuple[str, ...]
    slots: tuple[Mapping[str, Any], ...] = ()
    needs: Mapping[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"version": VERSION, "local_date": self.local_date, "mode": self.mode, "value": self.value,
                "seed": self.seed, "r": dict(self.r), "zero_topics": list(self.zero), "eligible_count": sum(
                    1 for value in self.r.values() if value > 0), "slots": [dict(slot) for slot in self.slots],
                "generation_needs": dict(self.needs)}


def draw(local_date: str, mode: str, value: float, eligible: Mapping[str, Sequence[str]],
         topics: Iterable[str]) -> Day:
    """The pure draw: same date and eligible set, same draw; it reads no decision."""

    from learnloop.router_objective_switches import CHECKS_EMBEDDED

    seed = day_seed(local_date)
    pool = sorted(lo for lo, items in eligible.items() if items)
    zero = tuple(sorted(lo for lo in topics if not eligible.get(lo)))
    slots: list[dict[str, Any]] = []
    if mode == CHECKS_EMBEDDED:
        k = min(int(value), len(pool))
        r = {lo: (k / len(pool) if pool else 0.0) for lo in pool}
        remaining = list(pool)
        for slot in range(k):
            u = mx.uniform(seed, f"slot:{slot}")
            lo = remaining.pop(min(int(u * len(remaining)), len(remaining) - 1))
            slots.append({"slot": slot, "topic": lo, "u": u, "r": r[lo]})
    else:
        r = {lo: float(value) for lo in pool}
        for lo in pool:
            u = mx.uniform(seed, f"topic:{lo}")
            if u < float(value):
                slots.append({"slot": len(slots), "topic": lo, "u": u, "r": r[lo]})
    for entry in slots:
        items = list(eligible[entry["topic"]])
        v = mx.uniform(seed, f"item:{entry['slot']}")
        entry["item_id"] = items[min(int(v * len(items)), len(items) - 1)]
        entry["item_u"] = v
        entry["item_propensity"] = 1.0 / len(items)
    full = {**{lo: 0.0 for lo in zero}, **r}
    return Day(local_date=local_date, mode=mode, value=float(value), seed=seed, r=full, zero=zero,
               slots=tuple(slots))


def _raise_need(vault: Any, repository: Any, lo: str, now_iso: str) -> str | None:
    """A topic with no eligible item: one pending generation need through the existing path (deduplicated on the
    LO, intent and facets by ``upsert_intervention_need``). Nothing is generated here, and no model is asked."""

    learning_object = vault.learning_objects.get(lo)
    facets = sorted(getattr(learning_object, "evidence_facets", None) or [])
    try:
        return repository.upsert_intervention_need({
            "learning_object_id": lo, "practice_item_id": None, "attempt_id": None, "desired_intent": "transfer",
            "trigger_reason": NEED_TRIGGER, "target_facets": facets, "error_types": [], "priority": 0.5,
            "status": "pending", "blocked_reason": NEED_BLOCKED,
            "candidate_requirements": {"same_learning_object": True, "unseen": True, "purpose": "randomized_cold_check"},
            "created_at": now_iso, "updated_at": now_iso,
        })
    except Exception:  # noqa: BLE001 - a need never blocks the plan
        LOG.warning("router objective RO5: the generation need for %s was not recorded", lo, exc_info=True)
        return None


def day_record(connection: Any, local_date: str) -> dict[str, Any] | None:
    row = A.by_unit(connection, A.CHECK, day_unit(local_date))
    return row["detail"] if row is not None else None


def draw_day(vault: Any, repository: Any, *, local_date: str, now_iso: str,
             topics: Mapping[str, float] | Any, eligible_items: Eligible,
             placeable: Any = None) -> dict[str, Any] | None:
    """The day's draw, once (idempotent: a drawn day returns its record). None with checks off. ``topics``: §8.7's
    population with each LO's undated density (``objective_inputs.population``), or a callable returning it (read
    only when the day is drawn); ``eligible_items``: the eligibility rule; ``placeable``: ``item_id -> bool``, whether
    the day's plan can serve the item (its pool, fixed before any of the day's action draws), or None for every
    eligible item. Only placeable items are drawn (Codex re-review F2: a drawn check is then administered at the day's
    first session whatever happens after the draw, and ``r_L = k/N_d`` counts the topics that can be served); a topic
    with eligible items none of which the plan can serve has ``r_L = 0`` that day and raises no generation need."""

    from learnloop.router_objective_switches import CHECKS_OFF, check_mode

    mode, value = check_mode(vault.config)
    if mode == CHECKS_OFF:
        return None
    with repository.connection() as connection:
        if not A.present(connection):
            return None
        existing = day_record(connection, local_date)
    if existing is not None:
        return existing
    topics = dict(topics() if callable(topics) else topics)
    eligible = eligible_items(list(topics), ())
    servable = eligible if placeable is None else {
        lo: [item for item in items if placeable(item)] for lo, items in eligible.items()}
    day = draw(local_date, mode, value, servable, topics)
    needs = {lo: need for lo in day.zero if not eligible.get(lo)
             and (need := _raise_need(vault, repository, lo, now_iso)) is not None}
    day = Day(**{**day.__dict__, "needs": needs})
    record = {**day.as_dict(), "densities": topics,
              "eligible_items": {lo: len(items) for lo, items in servable.items()},
              "fixed_before": "any action draw (the day's first plan decision; it reads no decision)"}
    if placeable is not None:
        record["eligible_outside_plan_pool"] = {lo: len(items) - len(servable.get(lo) or ())
                                                for lo, items in eligible.items()
                                                if len(items) > len(servable.get(lo) or ())}
    with repository.atomic(), repository.connection() as connection:
        if day_record(connection, local_date) is not None:  # a concurrent draw won
            return day_record(connection, local_date)
        A.insert(connection, experiment_id=A.CHECK, unit_id=day_unit(local_date), variant="day", propensity=1.0,
                 seed=day.seed, draw=None, candidate_refs=sorted(day.r), detail=record, at=now_iso)
        for slot in day.slots:
            A.insert(connection, experiment_id=A.CHECK, unit_id=slot_unit(local_date, int(slot["slot"])),
                     variant=str(slot["topic"]), propensity=float(slot["r"]), seed=day.seed, draw=float(slot["u"]),
                     candidate_refs=sorted(lo for lo, value in day.r.items() if value > 0),
                     detail={"version": VERSION, "local_date": local_date, "mode": mode, **dict(slot),
                             "r": dict(day.r), "replaces": mode != "rate"}, at=now_iso)
    return record


# -- serving ---------------------------------------------------------------------------------------------


def _first_session_today(connection: Any, local_date: str) -> str | None:
    rows = connection.execute("SELECT id, started_at FROM sessions ORDER BY started_at, id").fetchall()
    from learnloop.clock import parse_utc

    for session_id, started in rows:
        moment = parse_utc(str(started))
        if moment is not None and moment.astimezone().date().isoformat() == local_date:
            return str(session_id)
    return None


def administered(connection: Any) -> dict[str, dict[str, Any]]:
    """Each administered slot's ``item_planned`` receipt (its block, item and frozen sensors), by assignment id."""

    out: dict[str, dict[str, Any]] = {}
    for block_id, detail, created in connection.execute(
            "SELECT block_id, detail_json, created_at FROM attention_block_events WHERE kind = 'item_planned' "
            "AND json_extract(detail_json, '$.ro5_check.assignment_id') IS NOT NULL ORDER BY created_at, id"):
        body = json.loads(detail)
        check = body.get("ro5_check") or {}
        out.setdefault(str(check["assignment_id"]), {"block_id": str(block_id), "planned_at": str(created),
                                                     "practice_item_id": body.get("practice_item_id"), **check})
    return out


@dataclass(frozen=True)
class Placement:
    assignment_id: str
    slot: Mapping[str, Any]
    item: Any
    replaced: str | None
    detail: Mapping[str, Any]


def place(vault: Any, repository: Any, *, local_date: str, session_id: str | None, pool: Sequence[Any],
          planned: Iterable[str], chooser_items: Sequence[Any], lane: str | None,
          eligible_items: Eligible) -> list[Placement]:
    """The slots this boundary administers (before its decision): the day's undelivered checks, in the day's first
    session only. ``chooser_items`` (none from the engine since Codex re-review F2) are never excluded.
    An item no longer eligible is redrawn among the topic's eligible items in the plan's pool (its own uniform);
    with none, the slot waits for the next block."""

    from dataclasses import replace as dc_replace

    with repository.connection() as connection:
        if not A.present(connection):
            return []
        day = day_record(connection, local_date)
        if day is None or not day.get("slots"):
            return []
        first = _first_session_today(connection, local_date)
        if session_id is not None and first is not None and session_id != first:
            return []
        if session_id is None and first is not None:
            return []
        done = administered(connection)
        slots = {row["unit_id"]: row for row in A.rows(connection, A.CHECK, unit_like=f"{day_unit(local_date)}:%")}
    by_id = {str(item.practice_item_id): item for item in pool}
    # Codex review F2: the reserved item is eligible whatever the chooser picked. The chooser's items are never
    # excluded here: had they been, a check whose drawn item the policy also chose would go unadministered, so the
    # assessment would depend on the action. A collision reclassifies that chooser slot as the check instead.
    taken = set(planned)
    chosen_ids = [str(item.practice_item_id) for item in chooser_items]
    placements: list[Placement] = []
    pending = [slots[key] for key in sorted(slots) if slots[key]["id"] not in done]
    if not pending:
        return []
    topics = [str(row["variant"]) for row in pending]
    still = {lo: list(items) for lo, items in eligible_items(sorted(set(topics)), taken).items()}
    for row in pending:
        slot = row["detail"]
        topic = str(row["variant"])
        candidates = [item for item in still.get(topic, []) if item in by_id]
        chosen, how = None, "drawn"
        if str(slot.get("item_id")) in candidates:
            chosen = str(slot["item_id"])
        elif candidates:
            u = mx.uniform(str(row["seed"]), f"redraw:{slot.get('slot')}:{len(done)}")
            chosen, how = candidates[min(int(u * len(candidates)), len(candidates) - 1)], "redrawn_in_pool"
        if chosen is None:
            continue
        item = by_id[chosen]
        if lane is not None and getattr(item, "lane", None) != lane:
            item = dc_replace(item, lane=lane)
        replaced, collision = None, chosen in chosen_ids
        if collision:
            # The policy's block holds the check's own item: that slot becomes the check (it is the question the
            # embedded check replaces; for a rate check, the check takes it rather than adding a second copy).
            replaced = chosen
        elif bool(slot.get("replaces", True)):
            # An embedded check replaces the block's last chooser item not already replaced or taken by a check
            # (it stays in the pool).
            already = {placement.replaced for placement in placements if placement.replaced}
            free = [item_id for item_id in chosen_ids if item_id not in already
                    and item_id not in {str(p.item.practice_item_id) for p in placements}
                    and item_id not in {str(r["detail"].get("item_id")) for r in pending}]
            if free:
                replaced = free[-1]
        placements.append(Placement(assignment_id=str(row["id"]), slot=slot, item=item, replaced=replaced,
                                    detail={"assignment_id": str(row["id"]), "slot": slot.get("slot"),
                                            "topic": topic, "r": slot.get("r"), "item_how": how,
                                            "replaced": replaced, "collision": collision, "version": VERSION}))
        still[topic] = [item_id for item_id in still.get(topic, []) if item_id != chosen]
    return placements


# -- resolution ------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Resolved:
    assignment_id: str
    local_date: str
    topic: str
    r: float
    status: str
    outcome: float | None = None
    attempt_id: str | None = None
    item_id: str | None = None
    replaced: str | None = None
    sensors: Mapping[str, Any] = field(default_factory=dict)

    def assessment_key(self) -> str:
        """One completed check counts once however many decisions' windows hold it (§8.9)."""

        return self.attempt_id or self.assignment_id


def _label(row: Mapping[str, Any], assisted: bool) -> float | None:
    """§6.2's label: AD's unassisted success (help of any kind makes it a non-success, as RO2's resolver reads
    it); None where AD excludes the attempt (no correctness): never read as a zero (Codex review F1)."""

    from learnloop.adaptive_difficulty import outcomes as O

    facts = O.AttemptFacts(correctness=row.get("correctness"), hints_used=max(int(row.get("hints_used") or 0),
                                                                             1 if assisted else 0),
                           primed=bool(row.get("primed")), bound_presentation=True,
                           stuck=str(row.get("attempt_type") or "") == "dont_know")
    return O.unassisted_success(O.category(facts))


def _current_epoch_unassessed(connection: Any, attempt_id: str) -> bool:
    """PF-c over the attempt's current grading epoch (``grading_epochs.current_epoch``), AD's own rule
    (``adaptive_difficulty.replay._current_grade_unassessed``): every criterion's latest live row in that epoch
    recorded unverified, so the grade measures nothing whatever it schedules as."""

    from learnloop.grading_epochs import current_epoch
    from learnloop.outcome_contract import unverified_evidence_row

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'grading_evidence'"
                          ).fetchone() is None:
        return False
    rows = [dict(zip(("id", "criterion_id", "attribution_json", "grading_revision", "assessment_contract_version_id",
                      "created_at", "superseded_at"), row, strict=True)) for row in connection.execute(
        "SELECT id, criterion_id, attribution_json, grading_revision, assessment_contract_version_id, created_at, "
        "superseded_at FROM grading_evidence WHERE attempt_id = ? AND superseded_at IS NULL "
        "ORDER BY created_at, criterion_id, id", (attempt_id,))]
    epoch = current_epoch(rows)
    if epoch is None:
        return False
    latest = {str(row["criterion_id"]): row for row in sorted(epoch.rows, key=lambda r: r["grading_revision"] or -1)}
    return bool(latest) and all(unverified_evidence_row(row["attribution_json"]) for row in latest.values())


def _quarantined(connection: Any, attempt_id: str) -> bool:
    """The attempt's active grade interpretation (its newest observation's) is quarantined."""

    if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'activity_observations'"
                          ).fetchone() is None:
        return False
    row = connection.execute(
        "SELECT gi.quarantine_state FROM activity_observations o JOIN grade_interpretations gi "
        "ON gi.id = o.active_interpretation_id WHERE o.attempt_id = ? ORDER BY o.created_at DESC, o.id DESC LIMIT 1",
        (attempt_id,)).fetchone()
    return row is not None and row[0] == "quarantined"


def exclusion(connection: Any, attempt: Mapping[str, Any]) -> str | None:
    """Why the check's answer carries no label as its grade stands NOW (Codex review F1), else None: the existing
    assessment rules, read as AD's slot reads them. A grade held for review (THE predicate,
    ``held_grades.held_for_review_attempts``), a current grading epoch that assesses nothing (PF-c), a quarantined
    interpretation, an attempt type AD does not read, or no correctness is no observation; a regrade or a release
    is read on the next resolve."""

    from learnloop.adaptive_difficulty import outcomes as O
    from learnloop.held_grades import held_for_review_attempts
    from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW

    attempt_id = str(attempt["id"])
    if str(attempt.get("attempt_type") or "") not in O.ELIGIBLE_TYPES:
        return EXCLUDED_TYPE
    if attempt_id in held_for_review_attempts(connection, (attempt_id,)):
        return f"{EXCLUDED_PREFIX}{GRADE_HELD_FOR_REVIEW}"
    if _current_epoch_unassessed(connection, attempt_id):
        return EXCLUDED_UNASSESSED
    if _quarantined(connection, attempt_id):
        return EXCLUDED_QUARANTINED
    if attempt.get("correctness") is None and str(attempt.get("attempt_type") or "") != "dont_know":
        return EXCLUDED_UNGRADED
    return None


def _local_date(stamp: Any) -> str | None:
    from learnloop.clock import parse_utc

    moment = parse_utc(str(stamp)) if stamp else None
    return moment.astimezone().date().isoformat() if moment is not None else None


# -- the closure: THE cutoff of every historical read ----------------------------------------------------


@dataclass(frozen=True)
class Closure:
    """THE cutoff (landing ruling R1, Codex final verify F10). Every read that forms a check's completion, a
    completion rate or a comparison score reads as of one closure: the check's (:meth:`through`, the end of a local
    date) or the window's (:meth:`at`, its closing moment). :meth:`admits` is the one test every event it counts
    passes: the slots and the days drawn (their assignment rows), the sessions, the administrations (the
    ``item_planned`` receipts), the skips and displacements, the help shown and the answers, an answer on both its
    occurrence time and its received time (RO1's availability predicate, ``router_objective_switches.available_at``:
    it counts at a cutoff only once it happened and was known). So a closed rate or score never moves with later
    activity.

    Intended, and the one exception (Codex review F1): an answer's grade and its hold are read as they stand NOW. A
    hold placed or released, a regrade, a quarantine, or a current grading epoch that assesses nothing applies to every
    read, closed ones included: the assessment rules say what an answer measured, and a later correction of its grade
    is the truth about that answer, not later data about the learner."""

    limit: datetime
    inclusive: bool
    local_date: str

    @classmethod
    def through(cls, local_date: str) -> "Closure":
        """The end of ``local_date`` (local time): events before the next local midnight."""

        try:
            following = date.fromisoformat(local_date) + timedelta(days=1)
            limit = datetime(following.year, following.month, following.day).astimezone().astimezone(UTC)
            return cls(limit=limit, inclusive=False, local_date=local_date)
        except (OverflowError, ValueError):  # the far future (``9999-12-31``): every event
            return cls(limit=datetime.max.replace(tzinfo=UTC), inclusive=True, local_date=local_date)

    @classmethod
    def at(cls, stamp: str) -> "Closure":
        """``stamp`` itself (a window's ``window_closes_at``): events at or before it."""

        from learnloop.clock import parse_utc

        moment = parse_utc(str(stamp))
        assert moment is not None
        return cls(limit=moment, inclusive=True, local_date=moment.astimezone().date().isoformat())

    def admits(self, occurred: Any, received: Any = None) -> bool:
        """Whether an event that happened at ``occurred`` (and, for an answer, became known at ``received``, None
        where the two are one) is in the read: both at or before the closure. An event with no time is not."""

        from learnloop.clock import parse_utc

        if not occurred:
            return False
        for stamp in (occurred, received):
            if not stamp:
                continue
            moment = parse_utc(str(stamp))
            if moment is None or moment > self.limit or (moment == self.limit and not self.inclusive):
                return False
        return True


def _closure(through: str | None, closure: Closure | None) -> Closure:
    if closure is not None:
        return closure
    if through is None:
        raise TypeError("a check read needs its closure: through= a local date or closure=")
    return Closure.through(through)


def _moment(stamp: Any) -> datetime:
    from learnloop.clock import parse_utc

    return parse_utc(str(stamp)) or datetime.min.replace(tzinfo=UTC)


class Ledger:
    """Every event a check's resolution counts, read once with its times, so many closures (one per scored window)
    read one snapshot; each read filters it through :meth:`Closure.admits` alone. The grade-side exclusions (held,
    unassessed, quarantined: as they stand now, :class:`Closure`) are computed once per answer."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self.present = A.present(connection)
        rows = A.rows(connection, A.CHECK) if self.present else []
        self.days = [row for row in rows if row["unit_id"].count(":") == 1]
        self.slots = [row for row in rows if row["unit_id"].count(":") == 2]
        self.administrations: list[dict[str, Any]] = []
        self.sessions: list[tuple[str, str]] = []
        self.block_events: dict[tuple[str, str], list[tuple[str, str]]] = {}
        self.attempts: dict[str, list[dict[str, Any]]] = {}
        self.assists: dict[str, list[str]] = {}
        self._excluded: dict[str, tuple[str | None, float | None]] = {}
        if not self.present:
            return
        for block_id, detail, created in connection.execute(
                "SELECT block_id, detail_json, created_at FROM attention_block_events WHERE kind = 'item_planned' "
                "AND json_extract(detail_json, '$.ro5_check.assignment_id') IS NOT NULL ORDER BY created_at, id"):
            body = json.loads(detail)
            check = body.get("ro5_check") or {}
            self.administrations.append({"block_id": str(block_id), "planned_at": str(created),
                                         "practice_item_id": body.get("practice_item_id"), **check})
        self.sessions = [(str(sid), str(started)) for sid, started in connection.execute(
            "SELECT id, started_at FROM sessions ORDER BY started_at, id")]
        for block_id, kind, item_id, created in connection.execute(
                "SELECT block_id, kind, json_extract(detail_json, '$.practice_item_id'), created_at "
                "FROM attention_block_events WHERE kind IN ('item_skipped', 'item_displaced', ?) ORDER BY created_at, id",
                (DEVICE_DEFERRED_EVENT,)):
            self.block_events.setdefault((str(block_id), str(item_id)), []).append((str(kind), str(created)))
        items = sorted({str(entry.get("practice_item_id")) for entry in self.administrations})
        for start in range(0, len(items), 500):
            chunk = items[start:start + 500]
            for row in connection.execute(
                    "SELECT a.*, a.received_at AS ro5_received_at, p.block_id AS ro5_block_id FROM practice_attempts a "
                    "LEFT JOIN plan_presentations p ON p.id = a.plan_presentation_id "
                    f"WHERE a.practice_item_id IN ({','.join('?' for _ in chunk)}) ORDER BY a.created_at, a.id", chunk):
                found = dict(row)
                self.attempts.setdefault(str(found["practice_item_id"]), []).append(found)
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'help_assists'"
                                  ).fetchone():
                for item_id, at in connection.execute(
                        "SELECT practice_item_id, COALESCE(shown_at, requested_at) FROM help_assists "
                        f"WHERE practice_item_id IN ({','.join('?' for _ in chunk)})", chunk):
                    if at:
                        self.assists.setdefault(str(item_id), []).append(str(at))

    def _graded(self, attempt: Mapping[str, Any], assisted: bool) -> tuple[str | None, float | None]:
        """The answer's exclusion and label, as its grade stands NOW (Codex review F1; :class:`Closure`)."""

        key = f"{attempt['id']}|{int(assisted)}"
        if key not in self._excluded:
            excluded = exclusion(self.connection, attempt)
            label = _label(attempt, assisted) if excluded is None else None
            if excluded is None and label is None:
                excluded = EXCLUDED_LABEL
            self._excluded[key] = (excluded, label)
        return self._excluded[key]

    def sessions_by_day(self, closure: Closure) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for session_id, started in self.sessions:
            if closure.admits(started):
                day = _local_date(started)
                if day is not None:
                    out.setdefault(day, []).append(session_id)
        return out

    def drawn_days(self, closure: Closure) -> list[dict[str, Any]]:
        return [row for row in self.days if row["unit_id"][len(DAY_PREFIX):] <= closure.local_date
                and closure.admits(row["created_at"])]

    def resolve(self, closure: Closure) -> list[Resolved]:
        """Every slot assigned as of ``closure``, with its status (module docstring) as it stood then."""

        done: dict[str, dict[str, Any]] = {}
        for entry in self.administrations:
            if closure.admits(entry["planned_at"]):
                done.setdefault(str(entry["assignment_id"]), entry)
        sessions = self.sessions_by_day(closure)
        out: list[Resolved] = []
        for row in self.slots:
            local_date = row["unit_id"][len(DAY_PREFIX):].split(":")[0]
            if local_date > closure.local_date or not closure.admits(row["created_at"]):
                continue
            slot = row["detail"]
            base = dict(assignment_id=str(row["id"]), local_date=local_date, topic=str(row["variant"]),
                        r=float(row["propensity"]))
            planned = done.get(str(row["id"]))
            if planned is None:
                reason = OPEN if local_date == closure.local_date else (
                    NO_SESSION if not sessions.get(local_date) else NO_PRACTICE_SLOT)
                out.append(Resolved(**base, status=reason, item_id=slot.get("item_id")))
                continue
            item_id = str(planned.get("practice_item_id"))
            events = {kind for kind, at in self.block_events.get((planned["block_id"], item_id), ())
                      if closure.admits(at)}
            planned_at = _moment(planned["planned_at"])
            attempt = next((found for found in self.attempts.get(item_id, ())
                            if _moment(found["created_at"]) >= planned_at
                            and (found.get("ro5_block_id") == planned["block_id"]
                                 or found.get("plan_presentation_id") is None)
                            and closure.admits(found["created_at"], found.get("ro5_received_at"))), None)
            if attempt is None:
                status = DISPLACED if "item_displaced" in events else (SKIPPED if "item_skipped" in events else (
                    OPEN if local_date == closure.local_date else (
                        DEVICE_DEFERRED if DEVICE_DEFERRED_EVENT in events else NOT_ANSWERED)))
                out.append(Resolved(**base, status=status, item_id=item_id, replaced=planned.get("replaced"),
                                    sensors=planned.get("sensors") or {}))
                continue
            answered = _moment(attempt["created_at"])
            assisted = any(planned_at <= _moment(at) <= answered for at in self.assists.get(item_id, ())
                           if closure.admits(at))
            # Codex review F1: the answer is an observation only where the assessment rules give it a label now.
            attempt = {key: value for key, value in attempt.items() if not key.startswith("ro5_")}
            excluded, label = self._graded(attempt, assisted)
            out.append(Resolved(**base, status=excluded or COMPLETED, outcome=label,
                                attempt_id=str(attempt["id"]), item_id=item_id, replaced=planned.get("replaced"),
                                sensors=planned.get("sensors") or {}))
        return out

    def completion(self, closure: Closure) -> dict[str, Any]:
        resolved = [entry for entry in self.resolve(closure) if entry.status != OPEN]
        days = sorted({row["unit_id"][len(DAY_PREFIX):] for row in self.drawn_days(closure)})
        completed = sum(1 for entry in resolved if entry.status == COMPLETED)
        missing_days: list[str] = []
        per_day = 0.0
        if days:
            sessions = self.sessions_by_day(closure)
            cursor = date.fromisoformat(days[0])
            try:
                end = date.fromisoformat(closure.local_date)
            except ValueError:  # pragma: no cover - a closure always names a date
                end = cursor
            drawn = set(days)
            while cursor < end:
                stamp = cursor.isoformat()
                if stamp not in drawn and not sessions.get(stamp):
                    missing_days.append(stamp)
                cursor += timedelta(days=1)
            per_day = len(resolved) / len(days)
        denominator = len(resolved) + per_day * len(missing_days)
        statuses: dict[str, int] = {}
        for entry in resolved:
            statuses[entry.status] = statuses.get(entry.status, 0) + 1
        return {"completed": completed, "assigned": len(resolved), "days_without_session": len(missing_days),
                "by_status": dict(sorted(statuses.items())),
                "checks_per_day": per_day, "rate": (completed / denominator) if denominator > 0 else None,
                "label": "pooled over every randomized check and every day with no session; never conditioned on an "
                         "action"}

    def r_for(self, local_date: str, closure: Closure) -> tuple[dict[str, float], str]:
        drawn = {row["unit_id"][len(DAY_PREFIX):]: row for row in self.drawn_days(closure)}
        if local_date in drawn:
            return dict(drawn[local_date]["detail"].get("r") or {}), "drawn"
        earlier = [day for day in sorted(drawn) if day < local_date]
        if not earlier:
            return {}, "none"
        return dict(drawn[earlier[-1]]["detail"].get("r") or {}), "last_draw_stands"


def resolve(connection: Any, *, through: str | None = None, closure: Closure | None = None,
            ledger: Ledger | None = None) -> list[Resolved]:
    """Every assigned slot as of its closure (``through`` a local date, its end; or ``closure``), with its status
    (module docstring), every event read through :meth:`Closure.admits` (landing ruling R1): an assignment,
    administration, skip, displacement or answer after the closure is not seen, so a historical read never moves with
    later activity (a grade's later hold or regrade still applies, as intended: :class:`Closure`)."""

    return (ledger or Ledger(connection)).resolve(_closure(through, closure))


def completion(connection: Any, *, through: str | None = None, closure: Closure | None = None,
               ledger: Ledger | None = None) -> dict[str, Any]:
    """The running completion rate, pooled and never conditioned on an action: completed checks over the assigned
    ones plus the expected checks of every day with no session since the first draw (§8.7's completion gap). Every
    input stands as of the closure (landing ruling R1): the assignments, the drawn days that set the checks per day,
    the sessions and the answers (:func:`resolve`), so a rate read at a past cutoff never moves with later data."""

    return (ledger or Ledger(connection)).completion(_closure(through, closure))


def r_for(connection: Any, *, local_date: str, closure: Closure | None = None,
          ledger: Ledger | None = None) -> tuple[dict[str, float], str]:
    """``r_L`` on ``local_date`` (the assignment probability alone): the day's record, or with no draw that day the
    last earlier one's (labelled: its eligible set stands for a day with no session), every draw as of ``closure``
    (by default the end of ``local_date``)."""

    return (ledger or Ledger(connection)).r_for(local_date, closure or Closure.through(local_date))


def support_at(connection: Any, at: str, *, days: Sequence[Mapping[str, Any]] | None = None
               ) -> tuple[dict[str, float], str]:
    """RO6's landing ruling R7: each topic's check support for the days after ``at``, as known at ``at`` (a stop
    coin's draw): ``r_L`` of the latest day drawn as of ``Closure.at(at)``, every draw admitted through
    :meth:`Closure.admits` (RO1's availability predicate on its assignment row), the last draw standing for the days
    after it, as :meth:`Ledger.r_for` reads a day not yet drawn. ``({}, "none")`` with no draw yet. ``days``: the day
    assignment rows (:attr:`Ledger.days`), read once for many moments."""

    closure = Closure.at(at)
    if days is None:
        if not A.present(connection):
            return {}, "none"
        days = [row for row in A.rows(connection, A.CHECK) if row["unit_id"].count(":") == 1]
    drawn = [row for row in days if row["unit_id"][len(DAY_PREFIX):] <= closure.local_date
             and closure.admits(row["created_at"])]
    if not drawn:
        return {}, "none"
    latest = max(drawn, key=lambda row: row["unit_id"])
    return dict(latest["detail"].get("r") or {}), "latest_draw"


__all__ = [
    "Closure", "DAY_PREFIX", "DEVICE_DEFERRED", "DISPLACED", "Day", "Ledger", "NOT_ANSWERED", "NO_PRACTICE_SLOT",
    "NO_SESSION",
    "OPEN", "ORIGIN", "Placement", "RESOLVER_VERSION", "Resolved", "SKIPPED", "VERSION", "administered", "completion",
    "day_record", "day_seed", "day_unit", "draw", "draw_day", "place", "r_for", "resolve",
    "slot_unit", "support_at",
]
