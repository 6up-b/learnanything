"""AD2+AD3 composed with DL2's intent (the compose fix round; Opus composition verify of a84767d65).

* F1 (High): a DL2 choice (a commitment) never turns AD's slot draw off. The incumbent's frame and
  snapshot path reads the commitment tables, and the depth policy and envelope versions, in the
  incumbent's scope; every table on that path is classified and every module on it is a named
  incumbent reader, so the slot draw runs with zero guard denials.
* F2 (Medium): an AD candidate passes the plan pool's own per-item predicate
  (``scheduler.pool_admission``: the routine gate, DL2's intent gate and the build's gates), asked
  in the serve transaction, so AD never serves, nor clears the deferral of, an item the incumbent
  would withhold.
* The incumbent hands AD only a facts record (``slot_facts_schema.SlotFacts``: members, refusals, cold items and
  reserved items).
* A property: for seeded random intent scopes, choices and items, under both router settings, the
  pipeline runs with zero denials and AD never serves or clears an item the incumbent withholds.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import dataclasses
import random

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.intent.control import Scope, apply_choice
from learnloop.scheduling.intent.serving import intent_serving

from tests.ad23_fakes import LO, ad23_vault, env_for, intent_gated, selections

HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}
ITEMS = ("pi_h", "pi_e1", "pi_e2")
ROUTERS = {"staged": "[router]\nmode = \"staged\"\n", "off": "[router]\nenabled = false\n"}
#: The choices the property draws (the five the verify named).
CHOICES = ("learn", "master", "pause", "let_go", "check_once")


@pytest.fixture
def observed(monkeypatch):
    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    return seen


def _denials(observed):
    return [denial for op in observed for denial in op.guard.denials]


def _vault(tmp_path, router: str, ad: str = ""):
    paths = ad23_vault(tmp_path, items=ITEMS, features={"pi_h": HARD}, config=ROUTERS[router], ad=ad)
    env, clock = env_for(paths, items=ITEMS)
    # The fakes' supplier gated as the scheduler's due queue is, so an item intent withholds reaches
    # a served step only through AD (the property's subject).
    return paths, intent_gated(env), clock


@pytest.mark.parametrize("router", sorted(ROUTERS))
@pytest.mark.parametrize("choice", [None, "learn", "master"])
def test_f1_a_commitment_never_turns_the_slot_draw_off(tmp_path, observed, router, choice):
    """The verifier's probe: with the LO under Learn or Master, AD's slot still draws (one serve
    selection, as with no commitment), and no guard denial is recorded."""

    paths, env, clock = _vault(tmp_path, router)
    if choice:
        apply_choice(env.vault, env.repository, Scope("learning_object", LO), choice, clock=clock)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    advance(env, serve=True)
    assert _denials(observed) == [], _denials(observed)[:5]
    assert len(selections(paths, kind="serve")) == 1


@pytest.mark.parametrize("choice", ["pause", "let_go", "check_once"])
@pytest.mark.parametrize("ad", ["", "selection = false\n"])
def test_f2_ad_never_serves_an_item_intent_withholds(tmp_path, observed, choice, ad):
    """The verifier's second probe, without its patches: the slot's siblings are paused, let go or
    under a "Check once"; AD runs (zero denials; a serve selection when ``selection`` is on) and
    never serves one of them."""

    paths, env, clock = _vault(tmp_path, "staged", ad=ad)
    for item in ("pi_e1", "pi_e2"):
        apply_choice(env.vault, env.repository, Scope("practice_item", item), choice, clock=clock)
    serving = intent_serving(env.vault, env.repository, now=env.now())
    withheld = {item for item in ITEMS if serving is not None and serving.withhold_reason(item)}
    assert withheld == {"pi_e1", "pi_e2"}
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    _record, step = advance(env, serve=True)
    assert _denials(observed) == [], _denials(observed)[:5]
    if not ad:
        assert len(selections(paths, kind="serve")) == 1
        (row,) = selections(paths, kind="serve")
        support = {str(entry.get("ref")) for entry in row.get("support") or ()}
        assert not support & withheld, row
    assert step.get("practice_item_id") not in withheld


def test_the_incumbent_hands_ad_only_verdicts(tmp_path, monkeypatch):
    """(b), as the final round constructs it: what AD reads of the plan is the facts record it decodes
    (``slot_facts_schema.decode``) from JSON: ids, codes from the closed vocabulary, numbers; a
    paused sibling is no member of the plan's admitted pool."""

    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan import slot_facts_schema as SF

    seen = []
    real = SF.decode

    def spy(wire, **kwargs):
        assert isinstance(wire, str)
        facts = real(wire, **kwargs)
        seen.append(facts)
        return facts

    monkeypatch.setattr(ad_slot, "decode", spy)
    paths, env, clock = _vault(tmp_path, "staged")
    apply_choice(env.vault, env.repository, Scope("practice_item", "pi_e1"), "pause", clock=clock)
    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    advance(env, serve=True)
    assert seen
    for facts in seen:
        for item_id, codes in facts.refusals.items():
            assert isinstance(item_id, str)
            for code in codes:
                prefix, _sep, name = code.partition(":")
                assert name in (SF.CONSTRAINT_CODES if prefix == "constraint" else SF.POOL_CODES), code
        assert all(isinstance(i, str) for i in (*facts.members, *facts.reserved_items, *(facts.cold_items or ())))
    assert all("pi_e1" not in facts.members and "pi_e1" not in facts.refusals for facts in seen)


def _cases(seed: int) -> list[tuple[str, str, str, tuple[str, ...]]]:
    rng = random.Random(seed)
    cases = []
    for router in sorted(ROUTERS):
        for kind in ("learning_object", "practice_item"):
            for choice in CHOICES:
                chosen = tuple(sorted(rng.sample(ITEMS, rng.randint(1, len(ITEMS))))) if kind == "practice_item" else ()
                cases.append((router, kind, choice, chosen))
    rng.shuffle(cases)
    return cases


CASES = _cases(20261023) + _cases(20261024)[:10]


@pytest.mark.parametrize("router,kind,choice,chosen", CASES,
                         ids=[f"{r}-{k}-{c}-{'+'.join(i) or 'lo'}" for r, k, c, i in CASES])
def test_property_ad_never_serves_or_clears_what_the_incumbent_withholds(tmp_path, observed, router, kind,
                                                                          choice, chosen):
    from learnloop.daily_plan.engine import _ad_deferrals_cleared, _live_context, day_records

    paths, env, clock = _vault(tmp_path, router)
    if kind == "learning_object":
        apply_choice(env.vault, env.repository, Scope("learning_object", LO), choice, clock=clock)
    else:
        for item in chosen:
            apply_choice(env.vault, env.repository, Scope("practice_item", item), choice, clock=clock)

    def withheld() -> set[str]:
        serving = intent_serving(env.vault, env.repository, now=env.now())
        return {item for item in ITEMS if serving is not None and serving.withhold_reason(item) is not None}

    build_plan(env, kind="normal", budget=3.0, remembered=3, minutes_source="chip")
    for _ in range(3):
        before = withheld()
        _record, step = advance(env, serve=True)
        served = step.get("practice_item_id")
        if served is None:
            break
        assert served not in before, (served, before)
    # (ii) a deferral of a withheld item is never cleared.
    (record,) = day_records(env)
    _context, built = _live_context(env, record)
    held = withheld()
    if held:
        cleared = _ad_deferrals_cleared(env, record, built, {item: {} for item in held})
        assert not set(cleared) & held, (cleared, held)
    # (i) zero guard denials over every operation.
    assert _denials(observed) == [], _denials(observed)[:5]


REAL_CHOICES = (
    (("learning_object", LO, "master"),),
    (("learning_object", LO, "learn"), ("practice_item", "pi_k2", "pause")),
    (("practice_item", "pi_k2", "let_go"),),
    (("practice_item", "pi_k2", "check_once"),),
    (("learning_object", LO, "check_once"),),
)


@pytest.mark.parametrize("router", sorted(ROUTERS))
@pytest.mark.parametrize("choices", REAL_CHOICES, ids=["+".join(c[2] for c in cs) for cs in REAL_CHOICES])
def test_the_real_scheduler_lane_with_commitments(tmp_path, monkeypatch, observed, router, choices):
    """The AD lane through the sidecar's plan RPCs and the real scheduler (no fake pool), with DL2
    commitments: zero guard denials, AD draws (a serve selection or a commission), and no served
    step is an item intent withholds. The fake-pool lanes above missed the scheduler's own reads
    (its request set reads ``question_promotions``): this lane is the one that found them."""

    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from datetime import UTC, datetime

    from learnloop import clock as clock_module
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY

    from tests.ad23_fakes import commit

    items = ("pi_k1", "pi_k2", "pi_k3")
    paths = ad23_vault(tmp_path, items=items, features={"pi_k1": HARD}, config=ROUTERS[router])
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: datetime(2026, 10, 12, 9, 0, tzinfo=UTC))
    commit(paths, choices)

    def call(ctx, name, params):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.ad_commission_enqueue = lambda *_args: None
    try:
        session_id = call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
        for _ in range(3):
            from learnloop.vault.loader import load_vault
            from learnloop.db.repositories import Repository

            serving = intent_serving(load_vault(paths.root), Repository(paths.sqlite_path),
                                     now=datetime(2026, 10, 12, 9, 0, tzinfo=UTC))
            step = call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})["step"]
            if step.get("kind") != "item":
                break
            served = step.get("practiceItemId") or step.get("practice_item_id")
            assert serving is None or serving.withhold_reason(str(served)) is None, (served, choices)
    finally:
        ctx.map_builds.close()
    assert _denials(observed) == [], _denials(observed)[:5]
    assert observed, "AD opened no operation"
