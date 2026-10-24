"""AD2+AD3's incumbent-scope boundary (the compose fix round 3; Codex verify of 7cf22da4d..dd35cf5fc).

* The callback capture: a callable planted where the slot's entry reads its instant (``env.now``),
  or inside an incumbent function the scope runs (as test code, or as code in AD's modules),
  captures no protected value: the instant is read outside the scope under AD's own rules, and a
  read in the scope whose stack holds AD code or a callback from outside LearnLoop is refused.
* Dynamic entry: the scope opens only through ``operation.incumbent_answer`` from its two pinned
  entry functions, checked on the live frame; ``getattr``, an alias, another module, a forged
  function with the entry's name, ``incumbent_constraints()`` and ``rules('incumbent')`` are
  refused, and each poisons the operation.
* The scope writes nothing, AD's own tables included.
* The property: random callables and AD-side objects smuggled into a request, or reachable from it,
  are refused before any incumbent question runs, and none is ever invoked.
* The slot's own item passes the same membership rule as its siblings: a slot whose item went to
  Keep or Light touch after it was planned, or that the queue's stages left out (a teach-back value
  admission rejected), is refused to AD and served as with AD off, under both router settings.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import dataclasses
import functools
import random
import sqlite3
from contextlib import closing
from types import MappingProxyType
from typing import Any

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.daily_plan.engine import advance, build_plan

from tests.ad23_fakes import LO, ad23_vault, commit, env_for, intent_gated, selections

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
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "created_at, learner_answer_md) VALUES ('att_secret', 'pi_e2', ?, 'short_answer', 'independent_attempt', "
            "'2026-01-01T00:00:00Z', ?)", (LO, SENTINEL))
        connection.commit()
    return paths, intent_gated(env), clock


def _capture(repository, sink: list) -> None:
    """Codex's probe: read whole attempt rows through a non-AD helper and keep them."""

    from learnloop.reader import recap

    try:
        sink.append(recap._attempts(repository, ["att_secret"]))
    except Exception as exc:  # noqa: BLE001 - a refusal is the expected outcome
        sink.append(("refused", type(exc).__name__))


def _leaked(sink) -> bool:
    return SENTINEL in repr(sink)


# -- the callback capture -------------------------------------------------------------------------------


def test_a_callback_planted_in_the_entrys_instant_captures_nothing(tmp_path, observed):
    """Codex's probe: ``env.now`` is a callback that reads whole attempt rows through
    ``reader.recap._attempts``. The entry reads the instant outside the incumbent's scope, under AD's
    own rules, so the read is refused (AD is unavailable for the slot) and nothing is captured.
    Failed before: the instant was read inside the scope and the row came back."""

    paths, env, _clock = _vault(tmp_path)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    sink: list = []
    real_now = env.now

    def now():
        # Codex's probe counts what the callback captures while AD runs (inside an AD operation); the
        # plan's own calls outside any operation are the incumbent reading its own database.
        if O.current() is not None:
            _capture(env.repository, sink)
        return real_now()

    env.now = now
    advance(env, serve=True)
    assert sink and not _leaked(sink), sink


def _planted(monkeypatch, sink, *, globals_of: str | None = None):
    """Plant a capture inside an incumbent function the scope runs (the pool predicate): as test code,
    or (``globals_of``) as code defined in that module's namespace (an AD module's: AD code)."""

    import importlib

    from learnloop.scheduling import scheduler

    real = scheduler.pool_admission
    if globals_of is None:
        def planted(vault, repository, **kwargs):
            _capture(repository, sink)
            return real(vault, repository, **kwargs)
    else:
        # The capture itself runs in the module's namespace (an AD module's frame on the stack).
        namespace = vars(importlib.import_module(globals_of))
        code = compile("def planted(vault, repository, **kwargs):\n"
                       "    from learnloop.reader import recap\n"
                       "    try:\n"
                       "        _ad_sink.append(recap._attempts(repository, ['att_secret']))\n"
                       "    except Exception as exc:\n"
                       "        _ad_sink.append(('refused', type(exc).__name__))\n"
                       "    return _ad_real(vault, repository, **kwargs)\n", "<planted>", "exec")
        scope: dict[str, Any] = {}
        exec(code, namespace, scope)  # noqa: S102 - the probe: a function whose frame is the module's
        planted = scope["planted"]
        monkeypatch.setitem(namespace, "_ad_sink", sink)
        monkeypatch.setitem(namespace, "_ad_real", real)
    monkeypatch.setattr(scheduler, "pool_admission", planted)


@pytest.mark.parametrize("where", [None, "learnloop.adaptive_difficulty.reading"],
                         ids=["test_callback", "ad_module_callback"])
def test_a_callback_planted_inside_the_scope_reads_nothing(tmp_path, monkeypatch, observed, where):
    """A capture planted inside the scope (the pool predicate replaced by a callback that reads whole
    attempt rows through a non-AD helper, then delegates): the stack between that read and the
    scope's entry holds the callback's frame (test code, or code running in an AD module), so the read
    is refused, the operation poisoned, nothing captured, and the planned item served."""

    paths, env, _clock = _vault(tmp_path)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    sink: list = []
    _planted(monkeypatch, sink, globals_of=where)
    _record, step = advance(env, serve=True)
    assert sink and not _leaked(sink), sink
    why = " ".join(str(denial["why"]) for denial in _denials(observed))
    assert ("AD code inside the incumbent's scope" if where else "a callback from outside LearnLoop") in why, why
    assert step.get("practice_item_id") == "pi_h" and not selections(paths, kind="serve")


# -- dynamic entry ------------------------------------------------------------------------------------------


def _operation_env(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    paths = ad23_vault(tmp_path, items=ITEMS)
    return paths, load_vault(paths.root), Repository(paths.sqlite_path)


def _exclusions_request():
    from datetime import UTC, datetime, timedelta

    from learnloop.daily_plan import incumbent_answers as IA

    return IA.ExclusionsRequest(now=datetime(2026, 10, 12, 9, 0, tzinfo=UTC), cold_followup_kinds=(),
                                reveal_window=timedelta(hours=24), withheld_reveal_ids=frozenset())


def _forged_entry(monkeypatch, name: str):
    """A function named like a pinned entry, running in ad_slot's namespace, compiled elsewhere."""

    from learnloop.daily_plan import ad_slot

    code = compile(f"def {name}(question, request):\n    return _ad_ask(question, request)\n", "<forged>", "exec")
    scope: dict[str, Any] = {}
    exec(code, vars(ad_slot), scope)  # noqa: S102 - the probe
    monkeypatch.setitem(vars(ad_slot), "_ad_ask", O.incumbent_answer)
    return scope[name]


@pytest.mark.parametrize("how", ["getattr_constraints", "getattr_answer", "alias_other_module", "rules",
                                 "forged_entry", "forged_question"])
def test_dynamic_entry_to_the_scope_is_refused(tmp_path, monkeypatch, how):
    """Every way in but the two pinned entry functions is refused at runtime and poisons the
    operation. Failed before: ``getattr(operation, 'incumbent_constraints')()`` and
    ``rules('incumbent')`` opened the scope from anywhere."""

    from learnloop.daily_plan import incumbent_answers as IA

    _paths, vault, repository = _operation_env(tmp_path)
    request = _exclusions_request()
    with repository.atomic():
        with pytest.raises(O.GuardDenied):
            with O.ad_operation(vault, repository) as op:
                try:
                    if how == "getattr_constraints":
                        with getattr(O, "incumbent_constraints")():
                            pass
                    elif how == "getattr_answer":
                        getattr(O, "incumbent_answer")(IA.routine_exclusions, request)
                    elif how == "alias_other_module":
                        from learnloop.adaptive_difficulty.operation import incumbent_answer as ask

                        ask(IA.routine_exclusions, request)
                    elif how == "rules":
                        with O.rules("incumbent"):
                            pass
                    elif how == "forged_entry":
                        _forged_entry(monkeypatch, "incumbent_verdicts")(IA.routine_exclusions, request)
                    else:
                        def routine_exclusions(handles, request):  # an unregistered "question"
                            return None

                        _forged_entry(monkeypatch, "_exclusions")(routine_exclusions, request)
                finally:
                    assert op.guard.poisoned


# -- writes ---------------------------------------------------------------------------------------------------


def test_the_scope_writes_nothing_ad_owned_tables_included(tmp_path, monkeypatch, observed):
    """A write planted inside the scope, to an AD-owned table, by code in an incumbent module: refused,
    nothing written, the planned item served. Failed before: AD's own tables were writable there."""

    import importlib

    from learnloop.scheduling import scheduler

    paths, env, _clock = _vault(tmp_path)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    real = scheduler.pool_admission
    code = compile(
        "def planted(vault, repository, **kwargs):\n"
        "    try:\n"
        "        with repository.connection() as connection:\n"
        "            connection.execute(\"INSERT INTO ad_dose_offers(row_kind, draw_key, created_at) \"\n"
        "                               \"VALUES ('draw', 'k_scope_write', '2026-10-21T00:00:00Z')\")\n"
        "    except Exception:\n"
        "        pass\n"
        "    return _ad_real(vault, repository, **kwargs)\n", "<planted>", "exec")
    scope: dict[str, Any] = {}
    namespace = vars(importlib.import_module("learnloop.scheduling.serving_exclusions"))
    exec(code, namespace, scope)  # noqa: S102 - the probe
    monkeypatch.setitem(namespace, "_ad_real", real)
    monkeypatch.setattr(scheduler, "pool_admission", scope["planted"])
    _record, step = advance(env, serve=True)
    why = " ".join(str(denial["why"]) for denial in _denials(observed))
    assert "a write inside the incumbent's scope" in why, why
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM ad_dose_offers WHERE draw_key = 'k_scope_write'").fetchone()[0] == 0
    assert step.get("practice_item_id") == "pi_h"


# -- the property: nothing callable or AD-owned crosses ---------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _ForeignFrozen:
    """A frozen dataclass from outside LearnLoop (never plain for the scope)."""

    value: str = "x"


def _bad_values(sink: list) -> list[tuple[str, Any]]:
    from learnloop.adaptive_difficulty.serving import SlotCandidate
    from learnloop.daily_plan.engine import PlanEnv
    from learnloop.daily_plan.lanes import PoolItem

    def function():
        sink.append("called")

    class Callable_:
        def __call__(self):
            sink.append("called")

    def generator():
        sink.append("called")
        yield 1

    pool_item = PoolItem(practice_item_id="pi_x", learning_object_id=LO, rank=1, priority=0.0, lane="new",
                         reason="r", est_minutes=1.0, never_attempted=True)
    return [
        ("lambda", lambda: sink.append("called")),
        ("function", function),
        ("bound_method", sink.append),
        ("partial", functools.partial(sink.append, "called")),
        ("callable_object", Callable_()),
        ("generator", generator()),
        ("dict", {"a": 1}),
        ("list", [1]),
        ("set", {1}),
        ("ad_dataclass", SlotCandidate("pi_x", (), 1.0)),
        ("foreign_dataclass", _ForeignFrozen()),
        ("mutable_incumbent_object", PlanEnv(vault=None, repository=None)),
        ("callable_in_a_frozen_field", dataclasses.replace(pool_item, voi=MappingProxyType({"f": function}))),
        ("object", object()),
    ]


def _nest(value: Any, rng: random.Random) -> Any:
    """``value`` reachable at a random depth: inside tuples, frozensets of tuples, read-only mappings
    and frozen incumbent dataclasses' fields."""

    from learnloop.daily_plan.lanes import PoolItem

    for _ in range(rng.randint(0, 3)):
        shape = rng.choice(("tuple", "mapping", "dataclass"))
        if shape == "tuple":
            value = (1, "a", value)
        elif shape == "mapping":
            value = MappingProxyType({"k": value})
        else:
            value = PoolItem(practice_item_id="pi_y", learning_object_id=LO, rank=1, priority=0.0, lane="new",
                             reason="r", est_minutes=1.0, never_attempted=True,
                             voi=MappingProxyType({"nested": value}))
    return value


@pytest.mark.parametrize("seed", range(40))
def test_property_nothing_callable_or_ad_owned_crosses(tmp_path, monkeypatch, observed, seed):
    """Random bad values (callables of every kind, generators, mutable containers, AD-owned and
    foreign objects), nested at a random depth, smuggled into a random field of the slot's request
    (through the entry's own freezing): the request is refused before any incumbent question runs,
    no smuggled callable is ever invoked, AD is unavailable for the slot (zero leaked values) and the
    planned item is served; and the validator alone refuses each of them."""

    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan import incumbent_answers as IA

    rng = random.Random(seed)
    sink: list = []
    name, bad = rng.choice(_bad_values(sink))
    smuggled = _nest(bad, rng)
    assert O.plain_problem(smuggled) is not None, name
    paths, env, _clock = _vault(tmp_path)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    asked: list = []
    real_question = IA.slot_admission
    monkeypatch.setattr(IA, "slot_admission", lambda *a, **k: asked.append(1))  # noqa: unregistered
    monkeypatch.setattr(IA, "slot_admission", real_question)
    real_frozen = ad_slot._frozen
    state = {"seen": 0, "done": False}
    target = rng.randint(0, 6)

    def frozen(value):
        out = real_frozen(value)
        if not state["done"] and dataclasses.is_dataclass(out) and not isinstance(out, type):
            state["seen"] += 1
            if state["seen"] > target:
                field = rng.choice([f.name for f in dataclasses.fields(out) if f.init])
                object.__setattr__(out, field, smuggled)
                state["done"] = True
        return out

    monkeypatch.setattr(ad_slot, "_frozen", frozen)
    _record, step = advance(env, serve=True)
    assert sink == [], (name, sink)
    assert state["done"], "nothing was smuggled (the property would be vacuous)"
    why = " ".join(str(denial["why"]) for denial in _denials(observed))
    assert "not plain data" in why, (name, why)
    assert not selections(paths, kind="serve")
    assert step.get("practice_item_id") == "pi_h"


# -- the slot's own item: the same membership rule --------------------------------------------------------


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
    if after_plan == "keep":
        commit(paths, [("practice_item", slot, "keep")], clock=clock)
    elif after_plan == "light_touch":
        commit(paths, [("practice_item", slot, "light_touch")], clock=clock)
    elif after_plan == "left_out":
        allowed["ids"].discard(slot)  # the queue's stage (a teach-back value admission) now leaves it out
    _record, step = advance(env, serve=True)
    return slot, step.get("practice_item_id"), step.get("kind"), selections(paths, kind="serve")


@pytest.mark.parametrize("router", sorted(ROUTERS))
@pytest.mark.parametrize("change", ["keep", "light_touch", "left_out"])
def test_a_slot_whose_own_item_left_the_pool_is_the_incumbents(tmp_path, observed, router, change):
    """The slot's item planned as new material, then set to Keep or Light touch, or left out of the
    queue by its stages: AD draws nothing for the slot (no serve selection) and the step is the one
    served with AD off. Failed before: AD restored the slot's item to the pool unconditionally."""

    slot, served, kind, rows = _serve_once(tmp_path, "ad", router, after_plan=change)
    off_slot, off_served, off_kind, _off_rows = _serve_once(tmp_path, "off", router, after_plan=change,
                                                            ad="selection = false\n")
    assert slot == off_slot == "pi_h"
    assert rows == [], rows
    assert (kind, served) == (off_kind, off_served)
    assert _denials(observed) == [], _denials(observed)[:5]


@pytest.mark.parametrize("router", sorted(ROUTERS))
def test_a_slot_whose_own_item_stays_in_the_pool_is_drawn(tmp_path, observed, router):
    """The control: no change after planning, AD draws the slot."""

    _slot, _served, _kind, rows = _serve_once(tmp_path, "ad", router)
    assert len(rows) == 1
    assert _denials(observed) == [], _denials(observed)[:5]
