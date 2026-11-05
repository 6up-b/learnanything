"""A2: outcomes for reading, wait and stop arms: the objective frozen, the measurement arranged.

A reading block, a follow-up that waits and a stop serve no item, so their outcome had nothing to
follow (``not_applicable``). Here each such decision gets what the lesson suggestion's draw already
has: an **objective frozen before assignment** (its learning object and a predeclared scope, from
pre-draw inputs only, so it is the same whichever arm is drawn), read by the same intention-to-treat
outcome adapter (:mod:`learnloop.router.outcomes`). The arm a decision drew never decides what is
measured, so availability is not bought with the treatment.

**The rule.** A decision has an objective when an arm of its support has no action of its own (or it
drew one). A measurement (DL2's "Check once", :mod:`learnloop.delayed_checks`' candidate rule, picker and dates;
no new constant) is arranged when a real choice was made, or the arm is reading or waiting. A stop
with nothing else feasible keeps its objective but is left to ordinary retrievals (``natural``): no
alternative was at stake, so it spends no question. One check per learning object while one is
pending and can still measure this decision (``shared``): a check comes due no earlier than the outcome
contract's delay from the decision, whatever a short interval or the date's truncation would say (Codex
review F2), so one due sooner is not shared, and another item is asked; and every answer that could satisfy it
measures this objective (landing review F11), so a broad check that another LO's answer could close is not shared
either. Learner picks and requests are the learner's own: no objective.

**The slot.** A measurement's minutes come out of the maintain lane first (``plan_slots``), so it
replaces an ordinary maintenance slot rather than the day's new work.

**The states** (``decision_measurement_events``): ``due``, ``offered``, ``answered`` and
``unavailable`` with its reason, written where Today prepares (:func:`settle`), so treatment-dependent
censoring is visible. A state is written once per reason and **episode**: a due date opens one, each
presentation opens one, and a loss belongs to the newest of those (Codex re-review F10), so availability
can come and go, and every reader folds them with :func:`learnloop.router.outcomes.fold_measurement`.

**A check answered warm** satisfies the check (it was asked on the learner's own), but the decision's outcome
rejects it: the learner had just practised the objective. That is ``unavailable`` (:data:`ANSWER_NOT_DELAYED`),
not ``answered``, and the duty stands: one replacement check is arranged, dated from now, and its states are
written under a ``replacement:`` reason. Decisions that shared the check share its replacement, as they would any
pending check that opens after the window (Codex re-review F9): one question can measure them all. A replacement
answered warm too ends the arranged measurement, because each one costs the learner a question; ordinary retrievals
still reach the outcome. **A check answered on another LO** (its items can widen after it was shared) reads the same way,
under :data:`ANSWER_OTHER_OBJECTIVE`: it satisfied the check and measured nothing of this objective, so it is never
``answered``, and it takes the same one replacement.

**Reader activity** is an exposure for the outcome whatever adaptive difficulty's logging says, and :func:`settle` judges
an answer by the same read every outcome uses, over the activity that could have made it warm
(:func:`learnloop.data_capture.reading_exposures.read_for_answer`, landing rulings R1 and R6). Its sweep only freezes that
activity: no state or outcome depends on whether it has run.

**For A7** (a probe versus continue experiment on the same outcome collection): :func:`freeze`,
:func:`record` with its ``experiment_id`` and the adapter take any decision kind; nothing here knows
what an experiment assigns.

Serving: only from mvp-0.44 with ``data_capture.serving`` (``gates.serving_on``). Never evidence, FSRS,
the projection or replay: the checks are ordinary commitments and their answers ordinary attempts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
import json
import logging
from typing import Any

from learnloop import delayed_checks as D
from learnloop import delayed_completion as DC
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.data_capture.gates import objective_receipts_on
from learnloop.data_capture.reading_exposures import reading_learning_objects
from learnloop.db.stores import data_capture as store
from learnloop.router_objective import cold_timing

logger = logging.getLogger(__name__)

OBJECTIVE_VERSION = "decision_objective_v1"
#: A measurement check's provenance (``commitments``): what the plan reads to charge its slot.
VIA = "measurement"
#: As a lesson's delayed check (``teacher.delayed.DEPTH_PRESET``).
CHECK_DEPTH_PRESET = "keep_in_touch"
ARM_READING = "reading"
ARM_WAIT = "wait"
ARM_STOP = "stop"
ARM_PRACTICE = "practice"
ARM_INSERT = "insert"
#: FG1: the router chose no follow-up at all.
ARM_NO_INTERVENTION = "no_intervention"
#: The arms with no action of their own.
ACTIONLESS_ARMS: frozenset[str] = frozenset({ARM_READING, ARM_WAIT, ARM_STOP, ARM_NO_INTERVENTION})

ARRANGED = "arranged"
SHARED = "shared"
NATURAL = "natural"
UNAVAILABLE = "unavailable"

SOURCE_READING = "reading_section"
SOURCE_STAGED = "staged_pick"
SOURCE_SUPPORT = "support"
SOURCE_LAST_BLOCK = "last_block"
SOURCE_FOLLOWUP = "followup"
SOURCE_NONE = "none"

#: Why a measurement could not be arranged, or could not be offered.
NO_LEARNING_OBJECT = "no_learning_object"
NO_QUESTION = "no_question"
CHECKS_OFF = "check_once_off"
ARRANGE_FAILED = "arrange_failed"
COMMITMENT_CLOSED = "commitment_closed"
CHECK_REPLACED = "check_replaced"
#: The check was answered, but warm or exposed: the decision's outcome cannot read that answer.
ANSWER_NOT_DELAYED = "answer_not_delayed"
#: The check was answered on another LO: the answer measures nothing of this decision's objective.
ANSWER_OTHER_OBJECTIVE = "answer_other_objective"
#: Why an answer did not measure the objective, each taking the one replacement.
_UNREAD_ANSWERS = (ANSWER_NOT_DELAYED, ANSWER_OTHER_OBJECTIVE)
#: Prefixes the reason of every state of a replacement check (a state is written once per reason and episode).
REPLACEMENT = "replacement"
#: The episode of a ``due`` written for a check found already satisfied, whose date is no longer read.
SATISFIED_EPISODE = "satisfied"


@dataclass(frozen=True)
class FrozenObjective:
    """What a decision's arms are evaluated on, from pre-draw inputs only."""

    learning_object_id: str | None
    source: str
    scope: tuple[Mapping[str, Any], ...]
    support: tuple[str, ...]
    actionless: bool
    real_choice: bool
    version: str = OBJECTIVE_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "FrozenObjective":
        return cls(learning_object_id=row.get("learning_object_id"), source=str(row.get("source")),
                   scope=tuple(row.get("scope") or ()), support=tuple(row.get("support") or ()),
                   actionless=bool(row.get("actionless")), real_choice=bool(row.get("real_choice")),
                   version=str(row.get("version") or OBJECTIVE_VERSION))


def freeze(vault: Any, repository: Any, *, staged_ref: str | None, candidates: Sequence[Any], support: Sequence[str],
           stop_ref: str) -> FrozenObjective:
    """The block decision's objective, from the staged pick, the candidates and the support: nothing the
    draw decides. The reading arm's section when a reading is in the support (the contrast is about it),
    else the staged pick's LO, else the support's first LO."""

    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    support_refs = [str(ref) for ref in support]
    readings = [by_id[ref] for ref in support_refs if ref in by_id and by_id[ref].reading is not None]
    actionless = bool(readings) or stop_ref in support_refs
    scope: list[dict[str, Any]] = []
    reading_los: dict[str, list[str]] = {}
    for candidate in readings:
        reading_los[candidate.candidate_id] = reading_learning_objects(vault, repository, candidate.reading)
    for ref in support_refs:
        candidate = by_id.get(ref)
        los = [] if candidate is None else (reading_los.get(ref) or list(candidate.learning_object_ids))
        if los:
            scope.append({"ref": ref, "learning_object_ids": list(los)})
    learning_object_id, source = None, SOURCE_NONE
    for candidate in readings:
        if reading_los.get(candidate.candidate_id):
            learning_object_id, source = reading_los[candidate.candidate_id][0], SOURCE_READING
            break
    staged = by_id.get(staged_ref) if staged_ref else None
    if learning_object_id is None and staged is not None and staged.learning_object_ids:
        learning_object_id, source = staged.learning_object_ids[0], SOURCE_STAGED
    if learning_object_id is None:
        for entry in scope:
            learning_object_id, source = entry["learning_object_ids"][0], SOURCE_SUPPORT
            break
    # The objective's own entry leads the scope (the adapter's ``target``), whichever arm owns it.
    if learning_object_id is not None:
        scope.sort(key=lambda entry: learning_object_id not in entry["learning_object_ids"])
    return FrozenObjective(learning_object_id, source, tuple(scope), tuple(support_refs), actionless,
                           real_choice=len(support_refs) > 1)


def freeze_followup(learning_object_id: str, *, support: Sequence[str]) -> FrozenObjective:
    """A follow-up's now-or-wait decision: its own LO, whichever arm is drawn."""

    refs = tuple(str(ref) for ref in support)
    return FrozenObjective(learning_object_id, SOURCE_FOLLOWUP,
                           ({"ref": refs[0] if refs else "followup", "learning_object_ids": [learning_object_id]},), refs,
                           actionless=True, real_choice=len(refs) > 1)


def with_last_block(frozen: FrozenObjective, learning_object_id: str | None) -> FrozenObjective:
    """A stop with no candidate to name its objective: what the plan last worked on (pre-draw too)."""

    if frozen.learning_object_id is not None or not learning_object_id:
        return frozen
    return replace(frozen, learning_object_id=learning_object_id, source=SOURCE_LAST_BLOCK,
                   scope=({"ref": "last_block", "learning_object_ids": [learning_object_id]},))


def applies(frozen: FrozenObjective | None, arm: str) -> bool:
    """A decision has an objective when an arm of its support, or the drawn one, has no action."""

    return frozen is not None and (frozen.actionless or arm in ACTIONLESS_ARMS)


def _window_opens(now: datetime) -> datetime:
    """When an answer can first be a delayed retrieval of a decision taken at ``now``: the outcome contract's delay."""

    return now + timedelta(seconds=DC.MIN_DELAY_SECONDS)


def _due_iso(now: datetime, days: float) -> str:
    """The check's date. A date-only hint means that local day from its midnight
    (``scheduling.intent.serving.check_date``), so the date is the first whose midnight is past the window."""

    day = (now + timedelta(days=days)).astimezone().date()
    while datetime(day.year, day.month, day.day).astimezone() < _window_opens(now):
        day += timedelta(days=1)
    return day.isoformat()


def _pending_checks(serving: Any, item_ids: set[str]) -> list[Any]:
    """The pending checks on any item of the objective's LO."""

    if not item_ids:
        return []
    return [check for check in serving.checks.values()
            if check.answered_by is None and not check.replaced and item_ids & set(check.candidates)]


def _measures_objective(check: Any, item_ids: set[str]) -> bool:
    """Every answer that could satisfy this check is on the objective's LO, so it may be shared (landing review F11)."""

    return set(check.candidates) <= item_ids


@dataclass(frozen=True)
class _Arrangement:
    measurement: str
    commitment_id: str | None = None
    practice_item_id: str | None = None
    pick: Mapping[str, Any] | None = None
    reason: str = ""
    #: RO0 row 10: how a new check's delay was chosen (None: not new, or receipts off).
    delay: str | None = None


def _arrange(vault: Any, repository: Any, frozen: FrozenObjective, *, decision_id: str, exclude: Iterable[str],
             clock: Clock | None) -> _Arrangement:
    """The check that measures ``frozen``, on the decision's transaction (its savepoint)."""

    from learnloop.scheduling.intent.serving import intent_serving

    lo = frozen.learning_object_id
    if lo is None or lo not in vault.learning_objects:
        return _Arrangement(UNAVAILABLE, reason=NO_LEARNING_OBJECT)
    now = (clock or SystemClock()).now()
    serving = intent_serving(vault, repository, now=now, force=True)
    if serving is None:
        # Intent is off: "Check once" is not served.
        return _Arrangement(UNAVAILABLE, reason=CHECKS_OFF)
    lo_items = [item for item in vault.practice_items.values() if item.learning_object_id == lo]
    lo_item_ids = {item.id for item in lo_items}
    pending = _pending_checks(serving, lo_item_ids)
    for check in pending:
        # Its answer comes no earlier than its date, and is on this LO, so this one can measure this decision.
        if check.date >= _window_opens(now) and _measures_objective(check, lo_item_ids):
            return _Arrangement(SHARED, commitment_id=check.commitment_id,
                                practice_item_id=check.candidates[0] if check.candidates else None)
    # A check due sooner or broader keeps its own decision: a new commitment on its item would replace it.
    held = {item_id for check in pending for item_id in check.candidates}
    return _new_check(vault, repository, lo, lo_items, exclude={*exclude, *held}, decision_id=decision_id,
                      idempotency_key=f"measurement:{decision_id}", now=now, clock=clock)


def _new_check(vault: Any, repository: Any, lo: str, lo_items: Sequence[Any], *, exclude: Iterable[str], decision_id: str,
               idempotency_key: str, now: datetime, clock: Clock | None) -> _Arrangement:
    from learnloop.curriculum import commitments as C
    from learnloop.learner_protection import withheld_items

    withheld = withheld_items(vault, repository)
    attempted, revealed = D.attempted_items(repository), D.revealed_items(repository, f"decision:{decision_id}")
    excluded = set(exclude)
    # An unseen item first, as the teacher's check; with none, one of the LO's own that can still be
    # taken cold (never one exposed past the auto-prime threshold; the attempt's delay is the outcome's rule).
    found = D.candidates(vault, repository, lo, exclude=excluded, withheld=withheld, attempted=attempted, revealed=revealed)
    pool = "unseen"
    if not found:
        found = D.candidates(vault, repository, lo, exclude=excluded, withheld=withheld, attempted=set(), revealed=revealed)
        pool = "attempted"
    item, pick = D.pick_with_receipt(vault, repository, found, seed_key=f"decision:{decision_id}")
    if item is None:
        return _Arrangement(UNAVAILABLE, reason=NO_QUESTION)
    days, basis = D.due_days(vault, repository, purpose="retention", lesson_item_ids=[entry.id for entry in lo_items])
    delay = cold_timing.delay_receipt(vault, days=days, basis=basis, purpose="retention") \
        if objective_receipts_on(vault.config) else None
    pick = {**pick, "pool": pool}
    commitment = C.create_commitment(
        repository,
        action="test_me_later",
        intent_text="one question on your own, later, to see what stuck",
        targets=[{"target_kind": "legacy_practice_item", "target_ref": item.id, "role": "required"}],
        depth_preset=CHECK_DEPTH_PRESET,
        client_idempotency_key=idempotency_key,
        due_hint=_due_iso(now, days),
        reason="decision_measurement",
        provenance={"via": VIA, "decision_id": decision_id, "learning_object_id": lo, "dated_by": basis, "pick": pick},
        clock=clock,
    )
    return _Arrangement(ARRANGED, commitment_id=commitment.id, practice_item_id=item.id, pick=pick, delay=delay)


def record(vault: Any, repository: Any, connection: Any, *, decision_id: str, decision_kind: str, frozen: FrozenObjective,
           arm: str, exclude: Iterable[str] = (), experiment_id: str | None = None, clock: Clock | None = None) -> None:
    """Freeze ``frozen`` for a committed decision and arrange its measurement, on the decision's
    transaction. Fails soft: a decision never waits on its measurement."""

    try:
        if not store.objectives_present(connection):
            return
        at = utc_now_iso(clock)
        measured = frozen.real_choice or arm in (ARM_READING, ARM_WAIT)
        arrangement = _Arrangement(NATURAL)
        if measured:
            try:
                with repository.atomic():
                    arrangement = _arrange(vault, repository, frozen, decision_id=decision_id, exclude=exclude, clock=clock)
            except Exception:  # noqa: BLE001 - its savepoint rolled back; the decision stands
                logger.warning("data capture: the measurement of %s was not arranged", decision_id, exc_info=True)
                arrangement = _Arrangement(UNAVAILABLE, reason=ARRANGE_FAILED)
        written = store.insert_objective(connection, {
            "decision_id": decision_id, "decision_kind": decision_kind, "objective_version": frozen.version,
            "learning_object_id": frozen.learning_object_id, "source": frozen.source,
            "scope_json": json.dumps(list(frozen.scope), sort_keys=True), "arm": arm,
            "support_json": json.dumps(list(frozen.support)), "measurement": arrangement.measurement,
            "commitment_id": arrangement.commitment_id, "practice_item_id": arrangement.practice_item_id,
            "pick_json": json.dumps(dict(arrangement.pick or {}), sort_keys=True), "experiment_id": experiment_id,
            "created_at": at, **({"delay_json": arrangement.delay} if arrangement.delay else {}),
        })
        if written and arrangement.measurement == UNAVAILABLE:
            store.insert_measurement_event(connection, decision_id=decision_id, state="unavailable",
                                           non_service_type=cold_timing.non_service_type(arrangement.reason)
                                           if objective_receipts_on(vault.config) else None,
                                           reason=arrangement.reason, at=at)
    except Exception:  # noqa: BLE001 - a decision never waits on its measurement
        logger.warning("data capture: the objective of %s was not recorded", decision_id, exc_info=True)


# --- the plan's slot ---------------------------------------------------------------------------


def plan_slots(intent: Any, checks: Sequence[Any], maintain_load: float) -> tuple[list[dict[str, Any]], float]:
    """The first block's measurement checks and the maintain-lane minutes they replace."""

    slots: list[dict[str, Any]] = []
    total = 0.0
    for item in checks:
        check = intent.check_for(item.practice_item_id)
        provenance = getattr(check, "provenance", None) or {}
        if provenance.get("via") != VIA:
            continue
        total += float(item.est_minutes)
        slots.append({"practice_item_id": item.practice_item_id, "commitment_id": check.commitment_id,
                      "decision_id": provenance.get("decision_id"), "est_minutes": round(float(item.est_minutes), 4)})
    return slots, min(max(float(maintain_load), 0.0), total)


# --- the states --------------------------------------------------------------------------------


def _replacement_check(vault: Any, repository: Any, decision_id: str, learning_object_id: str | None, *, answered_item: Any,
                       serving: Any, now: datetime, clock: Clock | None, fresh: dict[str, _Arrangement]) -> _Arrangement:
    """The duty an unread answer left: one check on the objective that opens past the window from now. One already pending
    whose every answer is on the objective is shared, whether ``serving`` shows it or this settlement made it (``fresh``, by LO: ``serving`` predates them),
    as a new decision shares one (:func:`_arrange`). Otherwise a new one, dated from now. Never raises."""

    try:
        lo = str(learning_object_id)
        if learning_object_id not in vault.learning_objects:
            return _Arrangement(UNAVAILABLE, reason=NO_LEARNING_OBJECT)
        if lo in fresh:
            return replace(fresh[lo], measurement=SHARED, pick=None)
        lo_items = [item for item in vault.practice_items.values() if item.learning_object_id == lo]
        lo_item_ids = {item.id for item in lo_items}
        pending = _pending_checks(serving, lo_item_ids) if serving is not None else []
        for check in pending:
            if check.date >= _window_opens(now) and _measures_objective(check, lo_item_ids):
                return _Arrangement(SHARED, commitment_id=check.commitment_id,
                                    practice_item_id=check.candidates[0] if check.candidates else None)
        held = {item_id for check in pending for item_id in check.candidates}
        with repository.atomic():
            arranged = _new_check(vault, repository, lo, lo_items,
                                  exclude={*held, *([str(answered_item)] if answered_item else [])}, decision_id=decision_id,
                                  idempotency_key=f"measurement:{decision_id}:{REPLACEMENT}", now=now, clock=clock)
        if arranged.commitment_id:
            fresh[lo] = arranged
        return arranged
    except Exception:  # noqa: BLE001 - its savepoint rolled back; the state says so
        logger.warning("data capture: the replacement measurement of %s was not arranged", decision_id, exc_info=True)
        return _Arrangement(UNAVAILABLE, reason=ARRANGE_FAILED)


def _answer_missed_window(connection: Any, attempt_id: str, decided_at: str | None,
                          reader_exposures: Iterable[tuple[str, str]]) -> bool:
    """Whether the decision's outcome cannot read this answer because it was warm or exposed (a held or
    unscorable answer is still an answer: its outcome says why it is not read). The same definition as
    the outcome, so a state never disagrees with it."""

    from learnloop.router.outcomes import answer_completion

    if not decided_at:
        return False
    completion = answer_completion(connection, attempt_id, decided_at=decided_at, reader_exposures=reader_exposures)
    return completion is not None and completion.status in (DC.NOT_DELAYED, DC.PRE_EXPOSED)


def _replacement_detail(connection: Any, decision_id: str) -> dict[str, Any] | None:
    """The early answer's event of this decision's measurement, if it had one."""

    row = connection.execute(
        "SELECT detail_json FROM decision_measurement_events WHERE decision_id = ? AND state = 'unavailable' "
        f"AND reason IN ({','.join('?' for _ in _UNREAD_ANSWERS)})", (decision_id, *_UNREAD_ANSWERS)).fetchone()
    return json.loads(row[0] or "{}") if row is not None else None


def _unplanned_reasons(connection: Any, today: str) -> dict[str, list[str]]:
    """Today's plans' reasons a due check was not planned, by commitment."""

    from learnloop.db.stores import daily_plans as plans

    out: dict[str, list[str]] = {}
    for row in plans.plans_for_date(connection, today):
        for entry in (row.get("split") or {}).get("checks_unplanned") or ():
            if entry.get("commitment_id"):
                out.setdefault(str(entry["commitment_id"]), []).append(str(entry.get("reason") or "unplanned"))
    return out


def settle(vault: Any, repository: Any, *, clock: Clock | None = None) -> int:
    """Write the measurement states the ledgers now show. Idempotent; runs where Today prepares, never
    in replay. Returns how many states it wrote. A no-op off, or below the tag."""

    from learnloop.data_capture.gates import serving_on

    from learnloop.data_capture import reading_exposures

    # Freezes what the read below already sees.
    reading_exposures.sweep_quietly(vault, repository, clock=clock)
    if not serving_on(vault.config):
        return 0
    typed = objective_receipts_on(vault.config)
    from learnloop.curriculum import commitments as C
    from learnloop.scheduling.intent.serving import intent_serving

    now = (clock or SystemClock()).now()
    today = now.astimezone().date().isoformat()  # the plan's day (``engine.local_date``)
    written = 0
    with repository.atomic(), repository.connection() as connection:
        if not store.objectives_present(connection):
            return 0
        open_rows = [dict(row) for row in connection.execute(
            "SELECT o.decision_id, o.commitment_id, o.practice_item_id, o.learning_object_id, d.created_at AS decided_at "
            "FROM decision_objectives o LEFT JOIN router_decisions d ON d.id = o.decision_id "
            "WHERE o.commitment_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM decision_measurement_events e "
            "WHERE e.decision_id = o.decision_id AND (e.state = 'answered' OR (e.state = 'unavailable' "
            f"AND e.reason IN ({','.join('?' for _ in _UNREAD_ANSWERS)}))))",
            tuple(f"{REPLACEMENT}:{reason}" for reason in _UNREAD_ANSWERS))]
        if not open_rows:
            return 0
        serving = intent_serving(vault, repository, now=now)
        unplanned = _unplanned_reasons(connection, today)
        at = utc_now_iso(clock)
        # Replacements made during this pass, which ``serving`` predates (Codex re-review F9).
        fresh: dict[str, _Arrangement] = {}
        for row in open_rows:
            decision_id, commitment_id = str(row["decision_id"]), str(row["commitment_id"])
            early = _replacement_detail(connection, decision_id)
            if early is not None and not early.get("replacement_commitment_id"):
                continue  # answered warm with no question left to ask: its reason stands
            replacement = bool(early)
            if early:
                commitment_id = str(early["replacement_commitment_id"])
                row = {**row, "practice_item_id": early.get("practice_item_id")}
            prefix = f"{REPLACEMENT}:" if replacement else ""
            check = serving.checks.get(commitment_id) if serving is not None else None
            answered_by = check.answered_by if check is not None else None
            if answered_by is None and check is None:
                answered_by = _satisfied_by(connection, commitment_id)
                if answered_by is None and C.resolve_disposition(repository, commitment_id) != "one_check_pending":
                    written += _lost(connection, decision_id, prefix, COMMITMENT_CLOSED, at=at, typed=typed)
                    continue
            if check is None and answered_by is None:
                continue
            if check is not None and check.replaced and answered_by is None:
                # Another commitment decides every item it covered: this check will not be served.
                written += _lost(connection, decision_id, prefix, CHECK_REPLACED, at=at, typed=typed)
                continue
            attempt = connection.execute(
                "SELECT created_at, practice_item_id, learning_object_id FROM practice_attempts WHERE id = ?", (answered_by,)
            ).fetchone() if answered_by is not None else None
            answered_at = str(attempt[0]) if attempt is not None else at
            if check is None:
                # Satisfied since the last settlement: its date is gone with the pending check, so at most one more
                # ``due``, no later than the answer, which it opened.
                written += _event(connection, decision_id, "due", reason=prefix, at=answered_at, episode=SATISFIED_EPISODE)
            elif check.due:
                due_at = check.date.strftime("%Y-%m-%dT%H:%M:%SZ")
                # A check dated again by assisted practice comes due again: that is a new episode.
                written += _event(connection, decision_id, "due", reason=prefix, at=due_at, episode=due_at)
                offers = _offers(connection, check, row, since=due_at)
                for offer in offers:
                    written += _event(connection, decision_id, "offered", reason=prefix, at=offer["served_at"],
                                      practice_item_id=offer["practice_item_id"], detail={"presentation_id": offer["id"]},
                                      episode=str(offer["id"]))
                # A plan's reason stands only for a day the check was not offered at all.
                if not any(_local_day(offer["served_at"]) == today for offer in offers):
                    for reason in unplanned.get(commitment_id, ()):
                        written += _lost(connection, decision_id, prefix, reason, at=at, typed=typed)
            if answered_by is None:
                continue
            answered_lo = str(attempt[2]) if attempt is not None else None
            if answered_lo != str(row.get("learning_object_id")):
                unread = ANSWER_OTHER_OBJECTIVE
            else:
                try:
                    exposures = reading_exposures.read_for_answer(connection, vault, repository, answered_at=answered_at)
                except Exception:  # noqa: BLE001 - never blocks Today; an answer waits for a read that can judge it
                    logger.warning("data capture: Reader exposures were not read", exc_info=True)
                    continue
                if not _answer_missed_window(connection, answered_by, row.get("decided_at"), exposures):
                    written += _event(connection, decision_id, "answered", attempt_id=answered_by, at=answered_at)
                    continue
                unread = ANSWER_NOT_DELAYED
            if replacement:
                written += _event(connection, decision_id, "unavailable", reason=f"{prefix}{unread}",
                                  attempt_id=answered_by, at=at, typed=typed)
            else:
                arranged = _replacement_check(vault, repository, decision_id, row.get("learning_object_id"),
                                              answered_item=attempt[1] if attempt is not None else None, serving=serving,
                                              now=now, clock=clock, fresh=fresh)
                written += _event(connection, decision_id, "unavailable", reason=unread, attempt_id=answered_by,
                                  at=at, detail={"replacement_commitment_id": arranged.commitment_id,
                                                 "practice_item_id": arranged.practice_item_id,
                                                 "replacement_unavailable": arranged.reason or None,
                                                 **({"answered_learning_object_id": answered_lo}
                                                    if unread == ANSWER_OTHER_OBJECTIVE else {})},
                                  typed=typed, delay=arranged.delay)
    return written


def _local_day(at: str) -> str | None:
    """A UTC stamp's local day (the plan's, ``engine.local_date``)."""

    when = parse_utc(str(at))
    return when.astimezone().date().isoformat() if when is not None else None


def _lost(connection: Any, decision_id: str, prefix: str, reason: str, *, at: str, typed: bool = False) -> int:
    """The check cannot be offered, in the episode its newest ``due`` or ``offered`` opened: the same reason again
    only counts after availability came back. (``prefix`` is the reason of those states: this check's own.)"""

    return _event(connection, decision_id, "unavailable", reason=f"{prefix}{reason}", at=at,
                  episode=store.latest_episode(connection, decision_id, reason=prefix), typed=typed)


def _event(connection: Any, decision_id: str, state: str, *, at: str, reason: str = "",
           practice_item_id: str | None = None, attempt_id: str | None = None,
           detail: Mapping[str, Any] | None = None, episode: str = "", typed: bool = False,
           delay: str | None = None) -> int:
    # RO0 row 10 (``typed``: its switch): an unserved check's reason keeps its words and gains a type.
    return 1 if store.insert_measurement_event(connection, decision_id=decision_id, state=state, reason=reason,
                                               practice_item_id=practice_item_id, attempt_id=attempt_id, detail=detail,
                                               at=at, episode=episode, delay=delay,
                                               non_service_type=cold_timing.non_service_type(reason)
                                               if typed and state == "unavailable" else None) else 0


def _satisfied_by(connection: Any, commitment_id: str) -> str | None:
    row = connection.execute(
        "SELECT json_extract(detail_json, '$.administration_id') FROM commitment_events WHERE commitment_id = ? "
        "AND kind = 'disposition_changed' AND json_extract(detail_json, '$.disposition') = 'satisfied' "
        "ORDER BY created_at, id LIMIT 1", (commitment_id,)).fetchone()
    return str(row[0]) if row is not None and row[0] else None


def _offers(connection: Any, check: Any, row: Mapping[str, Any], *, since: str) -> list[dict[str, Any]]:
    """The check's presentations at or after it came due (its item, or any it decides), oldest first."""

    items = list(getattr(check, "candidates", ()) or ()) or ([row["practice_item_id"]] if row.get("practice_item_id") else [])
    if not items:
        return []
    marks = ",".join("?" for _ in items)
    return [dict(found) for found in connection.execute(
        f"SELECT id, practice_item_id, served_at FROM plan_presentations WHERE practice_item_id IN ({marks}) "
        "AND served_at >= ? ORDER BY served_at, id", [*items, since])]


__all__ = [
    "ACTIONLESS_ARMS",
    "ANSWER_NOT_DELAYED",
    "ANSWER_OTHER_OBJECTIVE",
    "ARM_INSERT",
    "ARM_PRACTICE",
    "ARM_READING",
    "ARM_STOP",
    "ARM_WAIT",
    "ARRANGED",
    "FrozenObjective",
    "NATURAL",
    "OBJECTIVE_VERSION",
    "REPLACEMENT",
    "SHARED",
    "UNAVAILABLE",
    "VIA",
    "applies",
    "freeze",
    "freeze_followup",
    "plan_slots",
    "reading_learning_objects",
    "record",
    "settle",
    "with_last_block",
]
