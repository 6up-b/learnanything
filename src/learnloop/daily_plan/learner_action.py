"""Instruct hand-off IH3 (spec_instruct_handoff_v1 §6): "Something else would help".

The learner names the router's next action. The options are what the plan can serve at that moment, in plain words
(learn this, another question, review something earlier, something new, read the source, stop); the choice is served
and logged, and an optional note is kept as written.

**Options, with and without a draw.** The set is always the boundary's own feasible candidates, computed without
drawing (:func:`~learnloop.daily_plan.engine._feasibility` over the live pool, and the lesson offer's builder), one
option per kind (the source's highest-valued candidate of that kind: which topic or block stands for a kind is the
planner's, the kind is the learner's). When a drawn block is waiting (the next block's decision exists and nothing
of it has been served), that decision is the parent: its id goes on the preference, the router's own pick is marked,
and each option carries the probability the decision logged for it, where it logged one. When none is waiting (the
next step is the next item of the block in hand, or no boundary has been crossed yet) there is no parent: the
preference stores a null ``decision_id`` and says so in ``offered_json`` (``drawn: false``); a probability the router
never computed is never invented.

**Effect.** A choice of the kind the plan had already drawn serves nothing new: the preference names the parent as the
served decision (an agreement). Any other choice is served as a ``learner_pick`` decision with no propensity and
``parent_decision_id`` set to the drawn decision, so ``router_outcomes`` reports the parent as ``overridden``; its block
is placed and the preference row is written in the same transaction (idempotent on the preference's id). An unanswered
lesson offer the choice replaces ends ``superseded`` there too. Other blocks the plan already holds stay as they are, as
for any learner pick.

**Honest labels.** A preference is self-selected. It is never evidence of mastery, no score or scheduler reads it, and
the served decision carries ``self_selected`` in its detail. Its use in a model is IH4's, not this stage's.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.daily_plan import engine as E
from learnloop.daily_plan.records import ORIGIN_LEARNER_PICK
from learnloop.daily_plan.types import LESSON_OFFER_PREFIX, STOP_FOR_TODAY, BlockCandidate
from learnloop.db.stores import router as router_store
from learnloop.ids import new_ulid
from learnloop.router import lesson_suggestions as LS
from learnloop.router_objective import preferences as PF
from learnloop.router_objective.preferences import KINDS, LESSON, NEW, QUESTION, READ, REVIEW, STOP, WORDS, kind_of

LOG = logging.getLogger(__name__)

PREFERENCE_VERSION = "learner_preference_v1"

#: Where the link was used, per device. The preference's ``surface`` is one of these.
DESKTOP_SURFACES = ("feedback", "offer_page", "today")
PHONE_SURFACES = ("phone_feedback", "phone_today")

#: What a phone says when it can log a choice but not serve it.
WAITS_ON_DESKTOP = "waits_on_desktop"


class PreferenceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Option:
    kind: str
    ref: str
    label: str
    minutes: float | None = None
    #: The probability the waiting decision logged for this ref, or None (none waiting, or it logged none).
    propensity: float | None = None
    #: The plan's own drawn pick (an agreement serves nothing new).
    plans_pick: bool = False
    #: False on a phone for what only the desktop serves (a lesson, a reading, an item the phone leaves there).
    servable: bool = True
    candidate: BlockCandidate | None = field(default=None, repr=False, compare=False)

    def view(self) -> dict[str, Any]:
        return {"kind": self.kind, "ref": self.ref, "label": self.label, "minutes": self.minutes,
                "propensity": self.propensity, "plans_pick": self.plans_pick, "servable": self.servable}


@dataclass(frozen=True)
class Options:
    enabled: bool
    options: tuple[Option, ...] = ()
    #: The parent: the waiting drawn decision, or None ("no draw existed").
    decision_id: str | None = None
    parent_kind: str | None = None
    parent_block_id: str | None = None
    parent_is_offer: bool = False
    #: Why there is no parent (``none_waiting`` | ``mid_block``), for the log.
    no_draw_reason: str | None = None
    device: str = "desktop"
    #: IH4: what ``offered_json`` freezes for the choice model and the acceptance model (empty with its switch off)
    frozen: Mapping[str, Any] = field(default_factory=dict)
    #: Everything below is internal: the live context the chosen candidate's block is built from.
    record: Any = field(default=None, repr=False, compare=False)
    context: Any = field(default=None, repr=False, compare=False)

    def offered(self) -> dict[str, Any]:
        """What ``offered_json`` keeps: the options as refs with the router's probabilities where known."""

        return {
            "version": PREFERENCE_VERSION,
            "drawn": self.decision_id is not None,
            **({"no_draw": self.no_draw_reason} if self.decision_id is None else {}),
            "device": self.device,
            "router_pick": next(({"kind": o.kind, "ref": o.ref, "propensity": o.propensity}
                                 for o in self.options if o.plans_pick), None),
            "options": [{key: value for key, value in o.view().items() if key != "label"} for o in self.options],
            **dict(self.frozen),
        }

    def view(self) -> dict[str, Any]:
        return {"enabled": self.enabled, "drawn": self.decision_id is not None, "decision_id": self.decision_id,
                "device": self.device, "options": [o.view() for o in self.options]}


def enabled(env: Any) -> bool:
    """IH3's gate (``router_objective.learner_preferences`` at the tag), and the ledger exists."""

    from learnloop.router_objective_switches import learner_preferences_on

    if not learner_preferences_on(env.vault.config):
        return False
    with env.repository.connection() as connection:
        return router_store.preferences_present(connection)


# -- the options ---------------------------------------------------------------------------------------------------


def _waiting_block(record: Any) -> Any:
    """The drawn block the next step would serve and nothing of which has been served, or None. A lesson offer waits
    until it is answered; a block with an item served is mid-block, where the next step is no new decision."""

    block = record.current_block()
    if block is None:
        return None
    if block.is_lesson_offer:
        return block
    if any(item.served_at is not None for item in block.items) or block.started_at is not None:
        return None
    return block


def _logged(connection: Any, decision_id: str | None) -> dict[str, Any] | None:
    if not decision_id:
        return None
    row = connection.execute(
        "SELECT id, decision_kind, candidates_json, chosen_ref FROM router_decisions WHERE id = ? "
        "AND decision_kind IN ('plan_block', 'plan_interrupt')", (decision_id,)).fetchone()
    return dict(row) if row is not None else None


def _logged_probabilities(row: Mapping[str, Any] | None) -> dict[str, float]:
    """The probability each ref was given by the decision (only where it logged a number)."""

    if row is None:
        return {}
    try:
        entries = json.loads(row.get("candidates_json") or "[]")
    except (TypeError, ValueError):  # pragma: no cover - the row is ours
        return {}
    return {str(entry["ref"]): float(entry["propensity"]) for entry in entries
            if isinstance(entry, dict) and entry.get("ref") and isinstance(entry.get("propensity"), (int, float))
            and not isinstance(entry.get("propensity"), bool)}


def _lesson_candidate(env: Any, record: Any) -> BlockCandidate | None:
    """The router's own best lesson candidate, read without a draw. A lesson is available only where the router could
    offer one (lesson offers on, and a candidate)."""

    from learnloop.daily_plan import lesson_offer as LO

    if not LO.offers_on(env.vault):
        return None
    local = env.now().astimezone()
    minutes_left = float(record.minutes_left()) if record is not None and record.is_open else None
    try:
        offer = LO.build(env.vault, env.repository, today=env.today(), now_iso=env.now_iso(),
                         local_hour=local.hour + local.minute / 60.0, minutes_left=minutes_left,
                         reentry=bool(env.gap().due), forced=False, learner_asked=True)
    except Exception:  # noqa: BLE001 - no lesson option is better than no link
        LOG.warning("learner preference: the lesson candidate was not built", exc_info=True)
        return None
    return offer.candidate


def _label(kind: str, candidate: BlockCandidate | None) -> str:
    if candidate is None:
        return WORDS[kind]
    if kind == LESSON:
        topic = str((candidate.annotations or {}).get("topic") or "")
        return f"Learn {topic}" if topic else WORDS[kind]
    if kind == READ and candidate.reading is not None and getattr(candidate.reading, "section_title", None):
        return f"Read {candidate.reading.section_title}"
    return WORDS[kind]


def _plans_pick_label(kind: str, block: Any) -> str:
    """The plan's own drawn pick in plain words: a lesson offer by its topic, a reading by its section, else the kind's."""

    try:
        if kind == LESSON and block is not None and block.is_lesson_offer:
            from learnloop.daily_plan.lesson_suggestion import offer_card_view

            title = str(((offer_card_view(block) or {}).get("suggestion") or {}).get("title") or "")
            return f"Learn {title}" if title else WORDS[kind]
        if kind == READ and block is not None and (block.reading or {}).get("section_title"):
            return f"Read {block.reading['section_title']}"
    except Exception:  # noqa: BLE001 - the plain kind is always a fair label
        LOG.warning("learner preference: the plan's own pick was not named", exc_info=True)
    return WORDS[kind]


def _frozen_inputs(env: Any, record: Any, lesson: BlockCandidate | None) -> dict[str, Any]:
    """IH4 (spec_instruct_handoff_v1 §7): what this preference's replay reads, as it stood here: the choice model's
    features and, with a lesson on offer, the acceptance model's context and candidate. Empty with the switch off, so
    ``offered_json`` is IH3's. A failed read freezes nothing: the row is then not read, and the choice is still served."""

    from learnloop.router_objective_switches import preferences_inform_router_on

    if not preferences_inform_router_on(env.vault.config):
        return {}
    out: dict[str, Any] = {}
    try:
        minutes_left = float(record.minutes_left()) if record.is_open else None
        with env.repository.connection() as connection:
            out[PF.FEATURES_KEY] = PF.features_at(connection, env.vault.config, at=env.now_iso(),
                                                  minutes_left=minutes_left).as_dict()
        card = dict((lesson.annotations or {}).get("lesson_offer") or {}) if lesson is not None else {}
        entries = (card.get("card") or {}).get("candidates") or ()
        if entries and card.get("context") is not None:
            out[LS.LESSON_INPUTS] = {"context": card["context"], "candidate": entries[0]}
    except Exception:  # noqa: BLE001 - the link never fails on what a model reads later
        LOG.warning("learner preference: the choice model's inputs were not frozen", exc_info=True)
    return out


def _phone_serves(env: Any, kind: str, candidate: BlockCandidate | None) -> bool:
    """A phone serves a practice block whose first item it can show. Lessons and readings, and an item the device
    leaves for the desktop, it logs and says wait."""

    if env.device is None:
        return True
    if kind in (LESSON, READ):
        return False
    if kind == STOP or candidate is None or not candidate.item_ids:
        return True
    item = env.vault.practice_items.get(candidate.item_ids[0])
    return item is not None and env.device.holds(item) is None


def options(env: Any) -> Options:
    """The boundary's options without drawing (module docstring). Writes nothing."""

    device = "phone" if env.device is not None else "desktop"
    if not E.plan_active(env.vault) or not enabled(env):
        return Options(False, device=device)
    record = E.get_or_create_today(env, create=False)
    if record is None:
        return Options(False, device=device)
    record = E.reconcile(env, record)
    if not record.is_open:
        return Options(False, device=device)
    context, _built = E._live_context(env, record)
    computed = E._feasibility(record, context, env.policy)
    waiting = _waiting_block(record)
    with env.repository.connection() as connection:
        parent = _logged(connection, getattr(waiting, "decision_ref", None)) if waiting is not None else None
    probabilities = _logged_probabilities(parent)
    parent_kind = kind_of(reading=waiting.reading, subtype=waiting.subtype, lane=waiting.lane) \
        if parent is not None and waiting is not None else None
    # One candidate per kind: the source's highest-valued one (ties: its own order).
    by_kind: dict[str, BlockCandidate] = {}
    for candidate in computed.feasible:
        kind = kind_of(reading=candidate.reading, subtype=candidate.subtype, lane=candidate.lane)
        best = by_kind.get(kind)
        if best is None or candidate.planner_value > best.planner_value:
            by_kind[kind] = candidate
    lesson = _lesson_candidate(env, record)
    if lesson is not None:
        by_kind[LESSON] = lesson
    out: list[Option] = []
    for kind in KINDS:
        if kind == STOP:
            out.append(Option(kind, STOP_FOR_TODAY, WORDS[kind], None, probabilities.get(STOP_FOR_TODAY)))
            continue
        candidate = by_kind.get(kind)
        if parent is not None and parent_kind == kind:
            # The plan's own drawn pick stands for its kind: its ref, its logged probability, nothing to place.
            ref = str(parent["chosen_ref"])
            out.append(Option(kind, ref, _plans_pick_label(kind, waiting), None, probabilities.get(ref), plans_pick=True,
                              servable=_phone_serves(env, kind, None)))
        elif candidate is not None:
            out.append(Option(kind, candidate.candidate_id, _label(kind, candidate), round(candidate.est_minutes, 2),
                              probabilities.get(candidate.candidate_id),
                              servable=_phone_serves(env, kind, candidate), candidate=candidate))
    reason = None if parent is not None else ("mid_block" if record.current_block() is not None else "none_waiting")
    return Options(True, tuple(out), decision_id=str(parent["id"]) if parent is not None else None,
                   parent_kind=parent_kind, parent_block_id=getattr(waiting, "id", None) if parent else None,
                   parent_is_offer=bool(parent is not None and waiting is not None and waiting.is_lesson_offer),
                   no_draw_reason=reason, device=device, frozen=_frozen_inputs(env, record, lesson),
                   record=record, context=context)


# -- the choice ----------------------------------------------------------------------------------------------------


@dataclass
class Chosen:
    """What :func:`choose` did: the preference's id, how it was served, and the step (None when nothing is served)."""

    preference_id: str
    #: ``served`` (a block was placed), ``agreed`` (the plan's own pick stands), ``stopped``, ``lesson`` (the desktop
    #: opens it), ``waits_on_desktop`` (a phone logged what only the desktop serves), ``replayed`` (a retry).
    outcome: str
    step: dict[str, Any] | None = None
    served_decision_id: str | None = None
    kind: str | None = None
    ref: str | None = None
    lesson: dict[str, Any] | None = None
    replayed: bool = False


def _decision_row(env: Any, *, decision_id: str, preference_id: str, chosen: Option, parent_id: str | None,
                  offered: Mapping[str, Any], block_id: str | None, serving: str) -> dict[str, Any]:
    from learnloop.router import plan_log as PL

    config = env.vault.config
    candidate = chosen.candidate
    items = list(candidate.item_ids) if candidate is not None else []
    first = items[0] if items else None
    los = list(candidate.learning_object_ids) if candidate is not None else []
    refs = [{"ref": entry["ref"], "kind": entry["kind"], "feasible": True, "propensity": entry["propensity"]}
            for entry in offered["options"]]
    return {
        "id": decision_id,
        "receipt_key": f"{router_store.OVERRIDE_KEY_PREFIX}{preference_id}",
        "decision_kind": "learner_pick",
        "surface": PL._surface(E._device_detail(env).get("device")),
        "mode": "daily_plan",
        "policy": "learner",
        "algorithm_version": str(config.algorithms.algorithm_version),
        "log_version": router_store.ROUTER_LOG_VERSION,
        "session_id": env.session_id,
        "parent_decision_id": parent_id,
        "scheduler_slate_id": None,
        "controller_decision_id": None,
        "snapshot_hash": PL._hash({"offered": offered, "chosen": chosen.ref}),
        "design": None,
        "seed": None,
        "candidates_json": PL._dumps(refs),
        "exclusions_json": "{}",
        "candidate_count": len(refs),
        "chosen_ref": chosen.ref,
        "chosen_practice_item_id": first,
        "chosen_learning_object_id": los[0] if los else None,
        "chosen_scheduler_candidate_id": None,
        "propensity": None,
        "propensity_kind": "none",
        "learner_pick": 1,
        "detail_json": PL._dumps({
            "override": {"preference_id": preference_id, "kind": chosen.kind, "serving": serving,
                         "block_id": block_id, "parent_decision_id": parent_id, "version": PREFERENCE_VERSION},
            # A preference is self-selected: what the learner would take, never evidence of mastery.
            "self_selected": True,
        }),
        "created_at": env.now_iso(),
    }


def choose(env: Any, *, kind: str, ref: str | None, surface: str, attempt_id: str | None, note_md: str | None,
           preference_id: str | None = None) -> Chosen:
    """Serve the learner's choice and log it, in one transaction (module docstring). Raises :class:`PreferenceError`."""

    allowed = PHONE_SURFACES if env.device is not None else DESKTOP_SURFACES
    if surface not in allowed:
        raise PreferenceError("validation_error", f"surface must be one of {', '.join(allowed)}.")
    if kind not in KINDS:
        raise PreferenceError("validation_error", f"kind must be one of {', '.join(KINDS)}.")
    preference_id = preference_id or new_ulid()
    with env.repository.connection() as connection:
        if not router_store.preferences_present(connection):
            raise PreferenceError("plan_off", "Something else would help is not on in this vault.")
        existing = router_store.learner_preference(connection, preference_id)
    if existing is not None:
        return _replayed(env, existing)
    live = options(env)
    if not live.enabled:
        raise PreferenceError("plan_off", "There is no open plan to choose from.")
    chosen = next((o for o in live.options if o.ref == ref and o.kind == kind), None) if ref else None
    chosen = chosen or next((o for o in live.options if o.kind == kind), None)
    if chosen is None:
        raise PreferenceError("no_longer_available", "That is no longer something the plan can do. "
                              "Here is what it can do now.")
    note = (note_md or "").strip() or None
    offered = live.offered()
    parent_id = live.decision_id
    agrees = chosen.plans_pick and parent_id is not None

    def preference(served: str | None) -> dict[str, Any]:
        return {"id": preference_id, "decision_id": parent_id, "attempt_id": attempt_id, "session_id": env.session_id,
                "surface": surface, "offered_json": json.dumps(offered, sort_keys=True, separators=(",", ":")),
                "chosen_kind": chosen.kind, "chosen_ref": chosen.ref, "note_md": note, "served_decision_id": served,
                "algorithm_version": str(env.vault.config.algorithms.algorithm_version),
                "created_at": env.now_iso()}

    if agrees:
        # The plan had already drawn this kind: nothing new is served, and the preference says it agreed.
        with env.repository.atomic(), env.repository.connection() as connection:
            router_store.insert_learner_preference(connection, preference(parent_id))
        return Chosen(preference_id, "agreed", kind=chosen.kind, ref=chosen.ref, served_decision_id=parent_id)
    if not chosen.servable:
        # A phone logs what only the desktop serves; the pick is on record and nothing is placed.
        decision_id = _log_only(env, preference, preference_id, chosen, parent_id, offered, WAITS_ON_DESKTOP)
        return Chosen(preference_id, WAITS_ON_DESKTOP, kind=chosen.kind, ref=chosen.ref, served_decision_id=decision_id)
    if chosen.kind == LESSON:
        decision_id = _log_only(env, preference, preference_id, chosen, parent_id, offered, "desktop_opens_lesson")
        lo = chosen.ref[len(LESSON_OFFER_PREFIX):] if chosen.ref.startswith(LESSON_OFFER_PREFIX) else chosen.ref
        title = env.vault.learning_objects[lo].title if lo in env.vault.learning_objects else lo
        return Chosen(preference_id, "lesson", kind=chosen.kind, ref=chosen.ref, served_decision_id=decision_id,
                      lesson={"learning_object_ids": [lo], "title": title})
    if chosen.kind == STOP:
        return _stop(env, live, preference, preference_id, chosen, parent_id, offered)
    return _place(env, live, preference, preference_id, chosen, parent_id, offered)


def _write_decision(env: Any, connection: Any, **row_args: Any) -> str | None:
    """The learner_pick decision, or None when the router's log is off (``router.log_decisions``). Raises on a ledger
    refusal: the caller's transaction then rolls back whole, and the learner is told."""

    if not bool(getattr(env.vault.config.router, "log_decisions", True)):
        return None
    decision_id = new_ulid()
    router_store.insert_router_decision(connection, _decision_row(env, decision_id=decision_id, **row_args))
    return decision_id


def _log_only(env: Any, preference: Any, preference_id: str, chosen: Option, parent_id: str | None,
              offered: Mapping[str, Any], serving: str) -> str | None:
    with env.repository.atomic(), env.repository.connection() as connection:
        decision_id = _write_decision(env, connection, preference_id=preference_id, chosen=chosen, parent_id=parent_id,
                                      offered=offered, block_id=None, serving=serving)
        router_store.insert_learner_preference(connection, preference(decision_id))
    return decision_id


def _stop(env: Any, live: Options, preference: Any, preference_id: str, chosen: Option, parent_id: str | None,
          offered: Mapping[str, Any]) -> Chosen:
    record = live.record
    with env.repository.atomic(), env.repository.connection() as connection:
        decision_id = _write_decision(env, connection, preference_id=preference_id, chosen=chosen, parent_id=parent_id,
                                      offered=offered, block_id=None, serving="stop_for_today")
        router_store.insert_learner_preference(connection, preference(decision_id))
        _end_offer(env, connection, live, decision_id)
        E._close(env, record, status="stopped", reason="learner_stopped")
    done = E._done_step(E._reload(env, record.id))
    return Chosen(preference_id, "stopped", step=done, kind=chosen.kind, ref=chosen.ref, served_decision_id=decision_id)


def _end_offer(env: Any, connection: Any, live: Options, decision_id: str | None) -> None:
    """An unanswered lesson offer the choice replaces ends ``superseded`` (the plan's act, as IH2's), in the same
    transaction. Its block is the parent's."""

    if not live.parent_is_offer or live.parent_block_id is None:
        return
    from learnloop.daily_plan import lesson_offer as LO

    block = next((b for b in live.record.blocks if b.id == live.parent_block_id), None)
    if block is not None:
        LO.supersede(connection, block, at=env.now_iso(), by=decision_id)


def _place(env: Any, live: Options, preference: Any, preference_id: str, chosen: Option, parent_id: str | None,
           offered: Mapping[str, Any]) -> Chosen:
    candidate = chosen.candidate
    assert candidate is not None
    record, context = live.record, live.context
    by_id = {item.practice_item_id: item for item in context.pool}
    items = [(by_id[item_id], ORIGIN_LEARNER_PICK) for item_id in candidate.item_ids if item_id in by_id]
    if candidate.item_ids and not items:
        raise PreferenceError("no_longer_available", "That is no longer something the plan can do.")
    block_id = new_ulid()
    detail = {
        "source": "learner", "chooser": "learner", "chosen_by": "learner_pick", "candidate_id": candidate.candidate_id,
        "propensity": None, "why": "you chose this: something else would help", "why_kind": "computed",
        "fallback": False, "candidate_set": [], "feasible_ids": [], "forced": [], "self_selected": True,
        "preference_id": preference_id, **E._device_detail(env),
    }
    with env.repository.atomic(), env.repository.connection() as connection:
        decision_id = _write_decision(env, connection, preference_id=preference_id, chosen=chosen, parent_id=parent_id,
                                      offered=offered, block_id=block_id, serving="block")
        router_store.insert_learner_preference(connection, preference(decision_id))
        _end_offer(env, connection, live, decision_id)
        if decision_id is not None:
            detail["decision_ref"] = decision_id
        E._persist_block(
            env, connection, record, lane=candidate.lane, action=candidate.action, subtype=candidate.subtype,
            chosen_by="learner_pick", est_minutes=candidate.est_minutes, reading=candidate.reading,
            reading_full=candidate.reading_full_minutes, learning_object_ids=list(candidate.learning_object_ids),
            detail=detail, items=items, decision_ref=decision_id, block_id=block_id)
    record = E._reload(env, record.id)
    block = next(b for b in record.blocks if b.id == block_id)
    step = _serve_step(env, record, block, context)
    return Chosen(preference_id, "served", step=step, kind=chosen.kind, ref=chosen.ref, served_decision_id=decision_id)


def _serve_step(env: Any, record: Any, block: Any, context: Any) -> dict[str, Any]:
    """Serve the placed block's first step, as :func:`~learnloop.daily_plan.engine.learner_pick` serves its block."""

    if block.is_reading:
        with env.repository.atomic(), env.repository.connection() as connection:
            E._event(connection, block.id, "block_started", {"session_id": env.session_id}, env.now_iso())
        return E._reading_step(env, E._reload(env, record.id), block, boundary=False)
    item = block.items[0]
    candidate_id = context.candidate_ids.get(item.practice_item_id)
    presentation_id = E._serve(env, block, item, candidate_id=candidate_id, strict=False)
    record = E._reload(env, record.id)
    block = next(b for b in record.blocks if b.id == block.id)
    return E._item_step(env, record, block, block.items[0], boundary=False, candidate_id=candidate_id,
                        presentation_id=presentation_id)


def _replayed(env: Any, row: Mapping[str, Any]) -> Chosen:
    """A retry of a preference already written: answered as it was made, writing nothing."""

    record = E.get_or_create_today(env, create=False)
    served = row.get("served_decision_id")
    kind, ref = str(row["chosen_kind"]), str(row["chosen_ref"])
    out = Chosen(str(row["id"]), "replayed", kind=kind, ref=ref, served_decision_id=served, replayed=True)
    if record is None:
        return out
    record = E.reconcile(env, record)
    if kind == STOP:
        out.step = E._done_step(record)
        return out
    block = next((b for b in record.blocks if served and b.decision_ref == served and b.chosen_by == "learner_pick"),
                 None)
    if block is None:
        return out
    if block.is_reading:
        out.step = E._reading_step(env, record, block, boundary=False)
        return out
    item = next((i for i in block.items if i.served_at is not None), block.items[0] if block.items else None)
    if item is not None:
        out.step = E._item_step(env, record, block, item, boundary=False, candidate_id=None,
                                presentation_id=E._standing_presentation(env, block, item))
    return out


__all__ = [
    "Chosen", "DESKTOP_SURFACES", "KINDS", "Option", "Options", "PHONE_SURFACES", "PREFERENCE_VERSION",
    "PreferenceError", "WAITS_ON_DESKTOP", "WORDS", "choose", "enabled", "kind_of", "options",
]
