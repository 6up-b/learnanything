"""AD2+AD3's final round: the inversion (owner decision 2026-10-24; Codex verify of round 3, job 20261024-000326-w2R4PR).

The plan computes its verdicts about a slot BEFORE AD runs, outside any AD operation (phase 2,
``daily_plan.slot_facts``), hands AD a JSON facts record (``daily_plan.slot_facts_schema``), and
re-checks AD's choice before it serves (phase 4). There is no incumbent scope.

* High 1 (exceptions carried protected content across the boundary): a malformed stored follow-up
  context quoting held-out text makes the plan's phase fail; nothing AD logs at the default level,
  and no exception logged there, carries the text (its graph is searched: args, attributes, causes,
  contexts, traceback frames' locals); AD's decision never runs; the planned item is served.
* High 2 (any ``rules`` name granted reads): every name that is not a ``Scope`` member raises and
  poisons; a failure inside a scope leaves it as a ``ViewFailure`` with no cause, no context and no
  inner frame holding the text.
* No incumbent privilege exists: the plan's own functions called inside an AD operation are refused.
* Only schema data crosses: a seeded fuzz of the wire (refused or projected), a sentinel the plan
  plants in an id, a code or an LO id never reaches AD; valid facts round-trip.
* The plan serves only accepted choices: a buggy decider's pick outside the plan's facts is rolled
  back (no selection row, no substitution) and the planned item served.
* The slot's own item passes the same membership rule (kept from round 3).

Fakes only: no network, no model call.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import random
import sqlite3
import traceback
from contextlib import closing, suppress
from typing import Any

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.daily_plan.engine import advance, build_plan

from tests.ad23_fakes import LO, ad23_vault, block_events, cold_followup, commit, env_for, intent_gated, selections

HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}
ITEMS = ("pi_h", "pi_e1", "pi_e2")
ROUTERS = {"staged": "[router]\nmode = \"staged\"\n", "off": "[router]\nenabled = false\n"}
SENTINEL = "WITHHELD_SENTINEL"


@pytest.fixture
def observed(monkeypatch):
    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    return seen


def _denials(observed):
    return [denial for op in observed for denial in op.guard.denials]


def _vault(tmp_path, router: str = "staged", ad: str = "", queue=ITEMS):
    paths = ad23_vault(tmp_path, items=ITEMS, features={"pi_h": HARD}, config=ROUTERS[router], ad=ad)
    env, clock = env_for(paths, items=tuple(queue))
    return paths, intent_gated(env), clock


def _graph_holds(exc: BaseException | None, needle: str, *, seen: set[int] | None = None) -> bool:
    """Whether ``needle`` is anywhere in an exception's graph: its args and str, every attribute
    (``.doc``), its notes, its cause and context chains, and every traceback frame's locals."""

    if exc is None:
        return False
    seen = seen if seen is not None else set()
    if id(exc) in seen:
        return False
    seen.add(id(exc))
    texts = [repr(exc.args), str(exc), repr(getattr(exc, "__notes__", None))]
    texts += [repr(value) for key, value in vars(exc).items() if not key.startswith("__")] if hasattr(exc, "__dict__") else []
    for attr in ("doc", "msg", "pos"):
        texts.append(repr(getattr(exc, attr, None)))
    for frame, _line in traceback.walk_tb(exc.__traceback__):
        with suppress(Exception):
            texts.append(repr(frame.f_locals))
    if any(needle in text for text in texts):
        return True
    return _graph_holds(exc.__cause__, needle, seen=seen) or _graph_holds(exc.__context__, needle, seen=seen)


def _default_level_leak(records, needle: str) -> list[str]:
    hits = []
    for record in records:
        if record.levelno < logging.INFO:
            continue
        if needle in record.getMessage():
            hits.append(f"message: {record.getMessage()[:80]}")
        if record.exc_info and _graph_holds(record.exc_info[1], needle):
            hits.append(f"exception at {record.levelname}: {record.name}")
        if record.exc_text and needle in record.exc_text:
            hits.append("exc_text")
    return hits


# -- High 1: exceptions ------------------------------------------------------------------------------------


@pytest.mark.parametrize("router", sorted(ROUTERS))
def test_high1_a_malformed_stored_context_quoting_held_out_text_never_reaches_ad_or_the_log(
        tmp_path, monkeypatch, caplog, router):
    """Codex's path: an open cold retry on a sibling whose stored context is malformed JSON quoting
    held-out text. The plan's own phase (its routine exclusions) fails on it; the failure is logged as
    its type and a code, the traceback only at DEBUG; AD's decision never runs; the planned item is
    served. Failed before (32eee1da9): AD's ``AdUnavailable`` carried the decoder's error as its
    cause, logged with its traceback at WARNING, the text in ``__cause__.doc``."""

    from learnloop.daily_plan import ad_slot

    paths, env, clock = _vault(tmp_path, router)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    cold_followup(paths, "pi_e1", clock=clock, context_json='{"note": "' + SENTINEL + ' unterminated')
    decided: list[Any] = []
    if hasattr(ad_slot, "decide"):
        real = ad_slot.decide

        def decide(*args, **kwargs):
            decided.append(1)
            return real(*args, **kwargs)

        monkeypatch.setattr(ad_slot, "decide", decide)
    with caplog.at_level(logging.DEBUG):
        _record, step = advance(env, serve=True)
    assert _default_level_leak(caplog.records, SENTINEL) == []
    assert step.get("practice_item_id") == "pi_h" and not selections(paths, kind="serve")
    assert not decided, "AD decided from facts the plan could not compute"
    assert any("incumbent_facts_failed" in record.getMessage() for record in caplog.records
               if record.levelno == logging.WARNING)


# -- High 2: scopes -----------------------------------------------------------------------------------------


def _operation_env(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    paths = ad23_vault(tmp_path, items=ITEMS)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "created_at, learner_answer_md) VALUES ('att_secret', 'pi_e2', ?, 'short_answer', 'independent_attempt', "
            "'2026-01-01T00:00:00Z', ?)", (LO, SENTINEL))
        connection.commit()
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


@pytest.mark.parametrize("name", ["view", "derive", "predicate", "typo", "incumbent", "", "VIEW"])
def test_high2_a_rules_scope_by_any_name_but_a_scope_member_is_refused(tmp_path, name):
    """Codex's second High: ``rules('derive')``, ``rules('view')`` or a typo opened a scope that read
    protected rows unchecked. A name that is not a ``Scope`` member raises ``TypeError`` and poisons
    the operation; the protected row is not read. Failed before: the scope opened and the row came back."""

    paths, vault, repository = _operation_env(tmp_path)
    got: list[Any] = []
    with repository.atomic():
        connection = repository.connection()
        with suppress(O.GuardDenied), O.ad_operation(vault, repository) as op:
            with suppress(TypeError, sqlite3.DatabaseError):
                with O.rules(name):
                    got.append(connection.execute(
                        "/* ad-rules */ SELECT learner_answer_md FROM practice_attempts").fetchall())
            assert op.guard.poisoned
    assert SENTINEL not in repr(got)


def test_a_failure_inside_a_scope_leaves_with_no_cause_context_or_text(tmp_path, monkeypatch):
    """The codec: a view reader's delegate fails with held-out text in its message, its attributes and
    its locals; the failure leaves the scope as a ``ViewFailure`` naming only its kind and type, with
    no ``__cause__``, no ``__context__`` and no frame below the scope's exit holding the text."""

    from learnloop.adaptive_difficulty import material_view as MV

    paths, vault, repository = _operation_env(tmp_path)

    class Leaky(ValueError):
        pass

    def failing(*_args, **_kwargs):
        secret = SENTINEL  # noqa: F841 - a local the traceback would hold
        error = Leaky(f"bad row {SENTINEL}")
        error.doc = SENTINEL
        raise error

    monkeypatch.setattr(MV.MaterialView, "attempted_item_ids", MV._in_rules(failing))
    caught = None
    with repository.atomic():
        with suppress(O.GuardDenied), O.ad_operation(vault, repository) as op:
            with repository.connection() as connection:
                try:
                    op.view.attempted_item_ids(connection)
                except Exception as exc:  # noqa: BLE001
                    caught = exc
    assert isinstance(caught, O.ViewFailure), type(caught)
    assert caught.__cause__ is None and caught.__context__ is None
    assert not _graph_holds(caught, SENTINEL)
    assert caught.args == ("error", "Leaky")


# -- no incumbent privilege inside an AD operation ------------------------------------------------------------


def _incumbent_calls():
    from datetime import UTC, datetime, timedelta

    def exclusions(vault, repository):
        from learnloop.scheduling.serving_exclusions import out_of_timing_serving_exclusions

        return out_of_timing_serving_exclusions(vault, repository, cold_followup_kinds=("cold_retry",),
                                                reveal_window=timedelta(hours=24))

    def pool(vault, repository):
        from learnloop.scheduling.scheduler import pool_admission

        return pool_admission(vault, repository, now=datetime(2026, 10, 12, 9, 0, tzinfo=UTC))("pi_e1")

    def recap(vault, repository):
        from learnloop.reader import recap as R

        return R._attempts(repository, ["att_secret"])

    return {"routine_exclusions": exclusions, "pool_admission": pool, "recap_attempts": recap}


@pytest.mark.parametrize("call", sorted(_incumbent_calls()))
def test_no_incumbent_privilege_exists_inside_an_ad_operation(tmp_path, call):
    """The plan's own functions (and Codex's ``recap._attempts`` probe), called inside an AD operation,
    have no privilege there: their reads of protected or denied tables are refused, the operation is
    poisoned, and nothing of the held-out row comes back."""

    paths, vault, repository = _operation_env(tmp_path)
    if call == "routine_exclusions":
        cold_followup(paths, "pi_e1")
    got: list[Any] = []
    with repository.atomic():
        with suppress(O.GuardDenied), O.ad_operation(vault, repository) as op:
            with suppress(Exception):
                got.append(_incumbent_calls()[call](op.vault, op.repository))
            assert op.guard.poisoned, call
    assert SENTINEL not in repr(got)


# -- only schema data crosses ------------------------------------------------------------------------------------


def _valid_facts():
    from learnloop.daily_plan.slot_facts_schema import EXCLUSION_NAMES, SlotFacts

    return SlotFacts(
        kind="slot", now="2026-10-12T09:00:00Z", plan_id="plan_1", members=("pi_e1", "pi_h"),
        refusals={"pi_e1": ("pool:intent_paused", "constraint:fatigue_budget")}, cold_items=(),
        reserved_items=(), exclusions={name: () for name in EXCLUSION_NAMES}, slot_admitted=True,
        block_id="blk_1", position=1, slot_item_id="pi_h", slot_learning_object_id=LO, slot_est_minutes=2.0,
        planned_counts={"pi_h": 0, "pi_e1": 0},
        budget={"slack_minutes": 1.0, "horizon_days": 14, "reviews_per_new_item": 3, "ceiling_minutes": 10.0,
                "load_per_day": 2.0, "floor_or_override": False},
        router_decision_id=None, router_propensity=1.0)


def test_valid_facts_round_trip():
    from learnloop.daily_plan.slot_facts_schema import decode, encode

    facts = _valid_facts()
    assert decode(encode(facts), visible={"pi_h", "pi_e1", "pi_e2"}, learning_objects={LO}) == facts


_MUTATIONS = ("unknown_key", "missing_key", "free_text_reason", "id_outside_view", "nan", "inf", "bad_now",
              "nested_object", "long_text_id", "wrong_type", "sentinel_lo", "non_json")


@pytest.mark.parametrize("seed", range(48))
def test_property_the_wire_is_refused_or_projected(seed):
    """A seeded fuzz of the facts' wire: each mutation is refused (``SlotFactsError``) or projected (an
    id outside AD's view dropped, a free-text reason mapped to ``…:other``); the decoded record never
    holds the sentinel."""

    from learnloop.daily_plan.slot_facts_schema import SlotFactsError, decode, encode

    rng = random.Random(seed)
    mutation = _MUTATIONS[seed % len(_MUTATIONS)]
    body = json.loads(encode(_valid_facts()))
    if mutation == "unknown_key":
        body["note"] = SENTINEL
    elif mutation == "missing_key":
        body.pop(rng.choice(sorted(body)))
    elif mutation == "free_text_reason":
        body["refusals"]["pi_e1"] = [f"pool:{SENTINEL} quoted text", f"constraint:{SENTINEL}", SENTINEL]
    elif mutation == "id_outside_view":
        body["members"].append(f"pi_{SENTINEL.lower()}")
    elif mutation == "nan":
        body["router_propensity"] = float("nan")
    elif mutation == "inf":
        body["budget"]["slack_minutes"] = float("inf")
    elif mutation == "bad_now":
        body["now"] = SENTINEL
    elif mutation == "nested_object":
        body["members"] = [{"id": SENTINEL}]
    elif mutation == "long_text_id":
        body["plan_id"] = SENTINEL + " " * 10 + "x" * 200
    elif mutation == "wrong_type":
        body["position"] = SENTINEL
    elif mutation == "sentinel_lo":
        body["slot_learning_object_id"] = SENTINEL + " with spaces"
    wire = "{" + SENTINEL if mutation == "non_json" else json.dumps(body)
    try:
        facts = decode(wire, visible={"pi_h", "pi_e1", "pi_e2"})
    except SlotFactsError as exc:
        assert SENTINEL not in str(exc) and exc.__context__ is None or SENTINEL not in repr(exc.args)
        return
    assert SENTINEL not in repr(dataclasses.asdict(facts)), (mutation, facts)


@pytest.mark.parametrize("router", sorted(ROUTERS))
@pytest.mark.parametrize("where", ["member", "refusal", "exclusion", "slot_lo"])
def test_a_sentinel_the_plan_plants_never_reaches_ad(tmp_path, monkeypatch, router, where):
    """The plan's facts carry a sentinel (as a member id, a refusal code, an exclusion id, the slot's
    LO id): what AD decodes, writes and serves never holds it."""

    from learnloop.daily_plan import ad_slot, slot_facts

    paths, env, _clock = _vault(tmp_path, router)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    real = slot_facts.for_slot

    def planted(*args, **kwargs):
        facts = real(*args, **kwargs)
        if where == "member":
            return dataclasses.replace(facts, members=(*facts.members, f"pi_{SENTINEL}"))
        if where == "refusal":
            return dataclasses.replace(facts, refusals={**facts.refusals, "pi_e1": (f"pool:{SENTINEL}",)})
        if where == "exclusion":
            return dataclasses.replace(facts, exclusions={**facts.exclusions,
                                                          "held_out_item_ids": (f"pi_{SENTINEL}",)})
        return dataclasses.replace(facts, slot_learning_object_id=f"lo_{SENTINEL}")

    decoded: list[Any] = []
    real_decode = ad_slot.decode

    def spy(wire, **kwargs):
        facts = real_decode(wire, **kwargs)
        decoded.append(facts)
        return facts

    monkeypatch.setattr(slot_facts, "for_slot", planted)
    monkeypatch.setattr(ad_slot, "decode", spy)
    _record, step = advance(env, serve=True)
    assert decoded and all(SENTINEL not in repr(dataclasses.asdict(facts)) for facts in decoded)
    rows = repr(selections(paths)) + repr(block_events(paths, "item_substituted"))
    assert SENTINEL not in rows and SENTINEL not in repr(step)


# -- the plan serves only accepted choices -------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(16))
def test_property_a_buggy_deciders_pick_outside_the_facts_is_rolled_back(tmp_path, monkeypatch, seed):
    """Phase 3 replaced by a buggy decider picking, per seed, a member, a non-member, a refused item,
    a cold item or an item planned elsewhere: the served item is always the planned item or an
    accepted member, and a rejected pick leaves no selection row and no substitution."""

    from learnloop.adaptive_difficulty.serving import SlotDecision
    from learnloop.daily_plan import ad_slot, slot_facts

    rng = random.Random(seed)
    router = sorted(ROUTERS)[seed % 2]
    paths, env, clock = _vault(tmp_path, router)
    paused = rng.random() < 0.5
    if paused:
        commit(paths, [("practice_item", "pi_e2", "pause")], clock=clock)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    pick = rng.choice(("pi_e1", "pi_e2", "pi_unknown", "pi_h"))
    seen_facts: list[Any] = []
    real_for_slot = slot_facts.for_slot

    def for_slot(*args, **kwargs):
        facts = real_for_slot(*args, **kwargs)
        seen_facts.append(facts)
        return facts

    real_decide = ad_slot.decide

    def buggy(vault, repository, wire, *, session):
        decision, request = real_decide(vault, repository, wire, session=session)
        return dataclasses.replace(decision, action="substitute", chosen_item_id=pick), request

    monkeypatch.setattr(slot_facts, "for_slot", for_slot)
    monkeypatch.setattr(ad_slot, "decide", buggy)
    _record, step = advance(env, serve=True)
    facts = seen_facts[-1]
    admissible = pick in facts.members and not facts.refusals.get(pick) and pick != facts.slot_item_id
    served = step.get("practice_item_id")
    if admissible:
        assert served == pick
    else:
        assert served == "pi_h"
        assert not selections(paths, kind="serve") and not block_events(paths, "item_substituted")
    assert served in ("pi_h", *facts.members)
    assert isinstance(SlotDecision, type)


# -- the slot's own item: the same membership rule (round 3, kept) -------------------------------------------------


def _serve_once(tmp_path, name, router, *, ad="", after_plan=None, queue=ITEMS):
    paths = ad23_vault(tmp_path / name, items=ITEMS, features={"pi_h": HARD}, config=ROUTERS[router], ad=ad)
    env, clock = env_for(paths, items=tuple(queue))
    allowed = {"ids": set(queue)}
    base = env.eligible

    def eligible(minutes):
        return [item for item in base(minutes) if item.practice_item_id in allowed["ids"]]

    env = intent_gated(dataclasses.replace(env, eligible=eligible))
    record = build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    slot = record.blocks[0].items[0].practice_item_id
    if after_plan in ("keep", "light_touch"):
        commit(paths, [("practice_item", slot, after_plan)], clock=clock)
    elif after_plan == "left_out":
        allowed["ids"].discard(slot)  # the queue's stage (a teach-back value admission) now leaves it out
    _record, step = advance(env, serve=True)
    return slot, step.get("practice_item_id"), step.get("kind"), selections(paths, kind="serve")


@pytest.mark.parametrize("router", sorted(ROUTERS))
@pytest.mark.parametrize("change", ["keep", "light_touch", "left_out"])
def test_a_slot_whose_own_item_left_the_pool_is_the_incumbents(tmp_path, observed, router, change):
    """The slot's item planned as new material, then set to Keep or Light touch, or left out of the
    queue by its stages: AD draws nothing for the slot and the step is the one served with AD off."""

    slot, served, kind, rows = _serve_once(tmp_path, "ad", router, after_plan=change)
    off_slot, off_served, off_kind, _off_rows = _serve_once(tmp_path, "off", router, after_plan=change,
                                                            ad="selection = false\n")
    assert slot == off_slot == "pi_h"
    assert rows == [], rows
    assert (kind, served) == (off_kind, off_served)
    assert _denials(observed) == [], _denials(observed)[:5]


@pytest.mark.parametrize("router", sorted(ROUTERS))
def test_a_slot_whose_own_item_stays_in_the_pool_is_drawn(tmp_path, observed, router):
    _slot, _served, _kind, rows = _serve_once(tmp_path, "ad", router)
    assert len(rows) == 1
    assert _denials(observed) == [], _denials(observed)[:5]


# -- the vocabulary follows the code ---------------------------------------------------------------------------------


def test_the_codes_vocabulary_covers_the_incumbents_reasons():
    """Every reason the plan pool's predicate and DL2's intent gate can give, and every constraint key
    the constraint engine and the frame register, is in the schema's closed vocabulary (a new one
    fails here until it is named)."""

    import inspect
    import re

    from learnloop.daily_plan import slot_facts_schema as SF
    from learnloop.scheduling import constraint_engine, frame_constraints, staged_policy
    from learnloop.scheduling.intent import model as intent_model
    from learnloop.scheduling.intent import serving as intent_serving
    from learnloop.scheduling.serving_exclusions import ADMISSION_GATES

    assert set(ADMISSION_GATES) <= SF.POOL_CODES
    dispositions = set(intent_model.EXCLUDING_DISPOSITIONS)
    assert {f"intent_{d}" for d in dispositions} <= SF.POOL_CODES
    assert set(re.findall(r'"(intent_check_[a-z_]+)"', inspect.getsource(intent_serving))) <= SF.POOL_CODES
    keys = set(re.findall(r'ExclusionReason\(\s*"([a-z_]+)"', inspect.getsource(constraint_engine)))
    keys |= {staged_policy.OWNERSHIP_REFUSAL_KEY, frame_constraints.CONSTRAINTS_UNAVAILABLE_KEY}
    keys |= set(re.findall(r'"constraint_key": "([a-z_]+)"', inspect.getsource(frame_constraints)))
    assert keys <= SF.CONSTRAINT_CODES, keys - SF.CONSTRAINT_CODES
