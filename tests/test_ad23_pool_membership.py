"""AD2+AD3 composed with the plan's pool (the compose fix round 2; Codex verify of a84767d65..7cf22da4d).

One class, three instances: a per-item predicate is not the whole pool. The build applies set-level
stages after it (teach-back value admission and caps in the scheduler's queue, the Keep and
Light-touch new-material rule in the plan's admission, and whatever comes next), so an AD candidate
must be a MEMBER of the plan's admitted pool (``engine.admitted_new_material_ids``, the output of
the build the plan used) or nothing, under both router settings; and the incumbent scope's readers
are derived (every LearnLoop module reached inside it but AD's own), not listed.

* H: a due "Check once" (on another LO, with an empty attempt ledger) leaves AD drawing, with zero
  guard denials;
* M1: a never-attempted sibling under Keep or Light touch is never AD's choice;
* M2: a sibling the build left out of its queue (as teach-back value admission or a cap does) is
  never AD's choice, with the router on or off;
* the property: every intent choice (check_once before and after its date), teach-back siblings
  kept and dropped, both router settings: zero denials, and every item AD substitutes, or whose
  deferral it clears, is in the plan's admitted pool at that boundary.

Fakes only: no network, no model call.
"""

from __future__ import annotations

import random

import pytest

from learnloop.adaptive_difficulty import operation as O
from learnloop.daily_plan.engine import advance, build_plan
from learnloop.scheduling.intent.serving import intent_serving

from tests.ad23_fakes import LO, ad23_vault, answer, block_events, commit, env_for, intent_gated, selections

HARD = {"complexity": 3, "transfer": "far", "scaffolding": "none", "span": "multi_step",
        "response": "long_constructed", "tools": ["closed_book"]}
ITEMS = ("pi_h", "pi_e1", "pi_e2")
OTHER = ("pi_o1", "pi_o2")
ROUTERS = {"staged": "[router]\nmode = \"staged\"\n", "off": "[router]\nenabled = false\n"}
DAY = 24 * 60


@pytest.fixture
def observed(monkeypatch):
    seen: list[O.Operation] = []
    monkeypatch.setattr(O, "OBSERVERS", [seen.append])
    return seen


def _denials(observed):
    return [denial for op in observed for denial in op.guard.denials]


def _setup(tmp_path, router: str, *, queue=ITEMS + OTHER, choices=(), past_due: bool = False, ad: str = ""):
    """The plan vault (the slot's LO and another), DL2 ``choices`` applied, the clock moved past a
    check's date when ``past_due``; ``queue``: the items the scheduler's queue holds after its
    stages (an item left out is one value admission or a cap removed)."""

    paths = ad23_vault(tmp_path, items=ITEMS, features={"pi_h": HARD}, config=ROUTERS[router], ad=ad,
                       learning_objects={"lo_other": OTHER})
    env, clock = env_for(paths, items=tuple(queue))
    commit(paths, choices, clock=clock)
    if past_due:
        days = int(env.vault.config.capture.test_me_later_days)
        clock.advance((days + 1) * DAY)
    return paths, intent_gated(env), clock


def _serve(env, paths, clock, steps: int = 4):
    served = []
    for _ in range(steps):
        _record, step = advance(env, serve=True)
        if step.get("kind") != "item":
            break
        served.append(step["practice_item_id"])
        clock.advance(2)
        answer(paths, step["practice_item_id"], correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    return served


def _support(paths) -> set[str]:
    return {str(entry.get("ref")) for row in selections(paths, kind="serve") for entry in row.get("support") or ()}


@pytest.mark.parametrize("router", sorted(ROUTERS))
@pytest.mark.parametrize("scope", [("learning_object", "lo_other"), ("practice_item", "pi_o1")])
def test_h_a_due_check_once_leaves_ad_drawing(tmp_path, observed, router, scope):
    """Codex's High: a "Check once" on another LO, past its date, with an empty attempt ledger:
    the check's reads run in the incumbent's scope and AD still draws its slot (a serve selection),
    with zero guard denials."""

    paths, env, clock = _setup(tmp_path, router, choices=[(*scope, "check_once")], past_due=True)
    serving = intent_serving(env.vault, env.repository, now=env.now())
    assert serving is not None and serving.due_checks(), "the check is due"
    build_plan(env, kind="normal", budget=12.0, remembered=12, minutes_source="chip")
    _serve(env, paths, clock, steps=6)
    assert _denials(observed) == [], _denials(observed)[:5]
    assert selections(paths, kind="serve"), "AD drew no slot"


@pytest.mark.parametrize("router", sorted(ROUTERS))
@pytest.mark.parametrize("choice", ["keep", "light_touch"])
def test_m1_keep_and_light_touch_siblings_get_no_new_material_from_ad(tmp_path, observed, router, choice):
    """Codex's first Medium: the slot's never-attempted siblings under Keep or Light touch pass
    intent's withhold and the per-item predicate, but the plan admits no new material of the
    system's choosing for them, so AD never draws one."""

    choices = [("practice_item", item, choice) for item in ("pi_e1", "pi_e2")]
    paths, env, clock = _setup(tmp_path, router, choices=choices)
    build_plan(env, kind="normal", budget=12.0, remembered=12, minutes_source="chip")
    served = _serve(env, paths, clock, steps=1)
    assert _denials(observed) == [], _denials(observed)[:5]
    assert not _support(paths) & {"pi_e1", "pi_e2"}, _support(paths)
    assert not set(served) & {"pi_e1", "pi_e2"}


@pytest.mark.parametrize("router", sorted(ROUTERS))
def test_m2_a_sibling_the_build_left_out_never_returns(tmp_path, observed, router):
    """Codex's second Medium: ``pi_e1`` is not in the scheduler's queue (a teach-back its value
    admission rejected, or one its cap left out); with the router on or off, AD's support never
    holds it and AD never serves it."""

    paths, env, clock = _setup(tmp_path, router, queue=("pi_h", "pi_e2") + OTHER)
    build_plan(env, kind="normal", budget=12.0, remembered=12, minutes_source="chip")
    served = _serve(env, paths, clock, steps=3)
    assert _denials(observed) == [], _denials(observed)[:5]
    assert selections(paths, kind="serve")
    assert "pi_e1" not in _support(paths) and "pi_e1" not in served


# -- the property ------------------------------------------------------------------------------------

CHOICES = ("learn", "master", "keep", "light_touch", "pause", "let_go", "check_once")


def _cases(seed: int) -> list[tuple]:
    rng = random.Random(seed)
    cases = []
    for router in sorted(ROUTERS):
        for choice in CHOICES:
            for past_due in ((False, True) if choice == "check_once" else (False,)):
                kind = rng.choice(("learning_object", "practice_item"))
                if kind == "learning_object":
                    scope = ((kind, rng.choice((LO, "lo_other"))),)
                else:
                    scope = tuple((kind, item) for item in sorted(rng.sample(ITEMS + OTHER, rng.randint(1, 3))))
                dropped = rng.choice((None, "pi_e1", "pi_e2"))  # a teach-back below the value bar
                cases.append((router, choice, past_due, scope, dropped))
    return cases


CASES = _cases(20261024) + _cases(20261025)


def _allowed(env, queue: set[str], attempted: set[str]) -> set[str]:
    """The oracle, from the pieces the plan admits by: the queue's items (after its stages), never
    attempted, not withheld by intent, not Keep or Light touch (no request in these vaults)."""

    from learnloop.scheduling.intent.model import TIER_KEEP, TIER_LIGHT

    serving = intent_serving(env.vault, env.repository, now=env.now())
    allowed = set()
    for item in queue - attempted:
        if serving is not None and (serving.withhold_reason(item) is not None
                                    or serving.intent(item).tier in (TIER_KEEP, TIER_LIGHT)):
            continue
        allowed.add(item)
    return allowed


@pytest.mark.parametrize("router,choice,past_due,scope,dropped", CASES,
                         ids=[f"{r}-{c}{'-due' if d else ''}-{'+'.join(s[1] for s in sc)}-{dr or 'all'}"
                              for r, c, d, sc, dr in CASES])
def test_property_every_ad_choice_is_a_member_of_the_plans_admitted_pool(tmp_path, observed, router, choice,
                                                                         past_due, scope, dropped):
    from learnloop.daily_plan import ad_slot
    from learnloop.daily_plan.engine import _live_context, day_records

    queue = tuple(item for item in ITEMS + OTHER if item != dropped)
    paths, env, clock = _setup(tmp_path, router, queue=queue, choices=[(*s, choice) for s in scope],
                               past_due=past_due)
    attempted: set[str] = set()
    draws: list[int] = []
    build_plan(env, kind="normal", budget=12.0, remembered=12, minutes_source="chip")
    for _ in range(4):
        allowed = _allowed(env, set(queue), attempted)
        before = len(block_events(paths, "item_substituted"))
        drawn = len(selections(paths, kind="serve"))
        _record, step = advance(env, serve=True)
        if step.get("kind") != "item":
            break
        for event in block_events(paths, "item_substituted")[before:]:
            assert event["detail"]["practice_item_id"] in allowed, (event["detail"], allowed)
        # Everything AD could draw from (each new draw's support) is in the admitted pool.
        for row in selections(paths, kind="serve")[drawn:]:
            support = {str(entry.get("ref")) for entry in row.get("support") or ()}
            assert support <= allowed, (support - allowed, allowed)
            draws.append(len(support))
        served = step["practice_item_id"]
        assert served != dropped, "an item the build left out was served"
        attempted.add(served)
        clock.advance(2)
        answer(paths, served, correct=True, presentation_id=step["presentation_id"], clock=clock)
        clock.advance(1)
    # A deferral is cleared only for a member of the admitted pool.
    records = day_records(env)
    if records:
        _context, built = _live_context(env, records[-1])
        candidates = {item: {} for item in ITEMS + OTHER if item not in attempted}
        cleared = ad_slot.deferrals_to_clear(env, candidates, built=built, record=records[-1])
        assert set(cleared) <= _allowed(env, set(queue), attempted), cleared
    assert _denials(observed) == [], _denials(observed)[:5]
    assert dropped is None or dropped not in _support(paths)
    assert draws, "AD drew no slot (the property would be vacuous)"
