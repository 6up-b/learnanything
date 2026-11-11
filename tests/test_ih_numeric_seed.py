"""The instruct hand-off's paths on router speed stage 2's seed rule (landing ruling R2): the numeric policy's seed is
``objective_chooser.numeric_seed`` of the boundary's identity, the dict its prefetch key hashes.

For every decision path IH added (IH0's start-only prefetch, IH2's boundary contest and its ``plan_interrupt`` lesson arm
on both the workflow's and the need's path, with or without room to wait):

* each ``run_numeric`` call of the path carries ``numeric_seed(identity)`` of that path's own identity;
* its evaluation is determined by that seed: at a fixed draw count (no deadline, no refinement) the same seed gives the
  same values bit for bit, and another seed gives others;
* IH0's prefetch and the serve that follows compute one identity, so one key and one seed, and the job runs once;
* IH3's options and override draw nothing, so they have no seed to derive.

Fakes only; no model call.
"""

from __future__ import annotations

from typing import Any

import pytest

from learnloop.daily_plan import engine as E
from learnloop.daily_plan import learner_action as LA
from learnloop.daily_plan import objective_chooser as OC
from learnloop.daily_plan.engine import advance
from learnloop.daily_plan.router_chooser import INSERT_NOW

from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import FakeDecider, FakeLLM, block_drawing_seed, fake_runtime
from tests.ih2_lessons_compete_helpers import (
    NO_CHECKS,
    OFF,
    OFF_NO_CHECKS,
    QUIET,
    _answer,
    _miss_env,
    _need_probe_arrives,
    _open_offer,
    _ready_probe,
    _run_lane,
    draw,  # noqa: F401 - the fixture
)
from tests.daily_plan_build_helpers import _wide_items
from tests.instruct_handoff_ih0_helpers import make_world  # noqa: F401 - the fixture
from tests.ro4_objective_serving_helpers import policy_answer
from tests.te3b_offers_helpers import OFFER, offerable  # noqa: F401 - the fixture
from tests.ih_numeric_seed_helpers import spy  # noqa: F401 - fixtures, used by parameter name


def _models() -> dict[str, Any]:
    return {"decider": FakeDecider(), "llm": FakeLLM(answer=policy_answer), "seed": block_drawing_seed()}


def _assert_determined(spy, *, kind: str, offer: bool = False) -> dict[str, Any]:
    """The last numeric run's seed is ``numeric_seed`` of an identity of ``kind`` (holding the offer, if ``offer``), and
    the seed determines its values. Returns that identity."""

    assert spy.runs, "the path made no numeric draw"
    run = spy.runs[-1]
    identities = [found for found in spy.identities if found["kind"] == kind and ("offer" in found) == offer]
    assert identities, f"no identity of kind {kind}"
    identity = next((found for found in reversed(identities) if OC.numeric_seed(found) == run["seed"]), None)
    assert identity is not None, f"the numeric seed is not {kind}'s numeric_seed(identity)"
    first = run["values"](run["seed"])
    assert first == run["values"](OC.numeric_seed(identity))
    assert first != run["values"]("another seed")
    return identity


@pytest.mark.usefixtures("offerable")
@pytest.mark.parametrize("models", [False, True], ids=["no_models", "both_models"])
def test_the_boundary_contest_seeds_from_its_identity(tmp_path, draw, spy, models):
    """IH2 §5 items 1-2: a probe arriving during an open offer; the new decision's support holds both."""

    env = mixture_env(tmp_path, fake_runtime(**(_models() if models else {})), toml=QUIET, session_id="s1",
                      version=_tag())
    _open_offer(env, draw)
    probe = _ready_probe(env)["practice_item_id"]
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    before = len(spy.runs)
    advance(env, serve=True)
    assert len(spy.runs) > before
    identity = _assert_determined(spy, kind="objective_block")
    assert spy.runs[-1]["support"] == [f"followup_contest:{probe}", OFFER]
    assert any(str(row.get("candidate_id") or row).startswith("followup_contest:") for row in identity["support"])


@pytest.mark.usefixtures("offerable")
@pytest.mark.parametrize("models", [False, True], ids=["no_models", "both_models"])
def test_the_need_paths_lesson_arm_seeds_from_its_identity(tmp_path, draw, spy, models):
    """IH2 §5 item 3, the need's mid-block ``plan_interrupt`` with the offer among its arms."""

    live = list(_wide_items())
    env = mixture_env(tmp_path, fake_runtime(**(_models() if models else {})), toml=NO_CHECKS, session_id="s1",
                      version=_tag(), items=lambda: list(live))
    _answer(env)
    _need_probe_arrives(live)
    draw.prefer = (OFFER,)
    advance(env, serve=True)
    identity = _assert_determined(spy, kind="objective_interrupt_lesson", offer=True)
    assert OFFER in identity["support"]


@pytest.mark.usefixtures("offerable")
def test_the_need_paths_decision_with_no_lesson_seeds_from_its_identity(tmp_path, draw, spy):
    """The need's call site IH2 wrapped (``_with_offer_record``), with no lesson in the support."""

    live = list(_wide_items())
    env = mixture_env(tmp_path, fake_runtime(), toml=NO_CHECKS + "lessons_compete_with_followups = false\n",
                      session_id="s1", version=_tag(), items=lambda: list(live))
    _answer(env)
    _need_probe_arrives(live)
    draw.prefer = (INSERT_NOW,)
    advance(env, serve=True)
    _assert_determined(spy, kind="objective_interrupt")


@pytest.mark.usefixtures("offerable")
@pytest.mark.parametrize("models", [False, True], ids=["no_models", "both_models"])
def test_the_workflows_lesson_arm_seeds_from_its_identity(tmp_path, draw, spy, monkeypatch, models):
    """IH2 §5 item 3, the workflow's ``plan_interrupt`` before anything is generated: the identity holds the offer."""

    env, row = _miss_env(tmp_path)
    if models:
        restraint = env.policy.restraint
        restraint.runtime.models.decider, restraint.runtime.models.llm = FakeDecider(), FakeLLM(answer=policy_answer)
    draw.prefer = (OFFER,)
    _run_lane(env, row, monkeypatch)
    identity = _assert_determined(spy, kind="objective_followup", offer=True)
    assert OFFER in spy.runs[-1]["support"] and identity["offer"]


@pytest.mark.usefixtures("offerable")
def test_the_workflows_arm_with_no_room_to_wait_seeds_from_its_identity(tmp_path, draw, spy):
    """``{insert_now, lesson}``: a real draw with no room to wait, so a numeric run the predecessor never made here."""

    from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

    env, row = _miss_env(tmp_path)
    restraint = env.policy.restraint
    gate = ObjectiveFollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                 card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                 may_defer=False)
    record = E.latest_today(env)
    offer = E.interrupt_offer(env, record, None)
    assert offer.candidate is not None
    draw.prefer = (OFFER,)
    gate.decide_followup(record, None, row, wait_feasible=False, offer=offer)
    _assert_determined(spy, kind="objective_followup", offer=True)
    assert spy.runs[-1]["support"] == [INSERT_NOW, OFFER]


@pytest.mark.usefixtures("offerable")
def test_the_workflows_decision_with_no_lesson_keeps_the_predecessors_identity(tmp_path, draw, spy, monkeypatch):
    """Switched off, the identity has no offer and no ``as_of``, so its key and seed are computed as main's are."""

    # With no lesson the decision draws (and hashes an identity) only when waiting is a choice: a current block with
    # room after it. The plan's draws are live, so a miss that finished its block (about 1 run in 50) left no current
    # block and an insert-now with no draw: an answer that leaves questions in its block keeps one.
    env, row = _miss_env(tmp_path, toml=OFF_NO_CHECKS, questions_left=True)
    draw.prefer = (INSERT_NOW,)
    _run_lane(env, row, monkeypatch)
    identity = _assert_determined(spy, kind="objective_followup")
    assert "offer" not in identity and "as_of" not in identity


@pytest.mark.usefixtures("offerable")
def test_an_offer_changes_the_identity_and_so_the_seed(tmp_path, draw, spy):
    from learnloop.daily_plan.objective_chooser import ObjectiveFollowupGate

    env, row = _miss_env(tmp_path)
    restraint = env.policy.restraint
    gate = ObjectiveFollowupGate(env.vault, env.repository, restraint.runtime, frame=restraint.frame,
                                 card_builder=restraint.card_builder, session_id=env.session_id, clock=env.clock,
                                 may_defer=False)
    record = E.latest_today(env)
    gate.decide_followup(record, None, row, wait_feasible=True)
    alone = spy.runs[-1]["seed"]
    gate.decide_followup(record, None, row, wait_feasible=True, offer=E.interrupt_offer(env, record, None))
    assert spy.runs[-1]["seed"] != alone


def test_the_start_only_prefetch_and_its_serve_compute_one_key_and_one_seed(make_world, spy):
    """IH0 §3a item 2: the prefetch's job carries the identity's seed, and the serve computes the same identity, so it
    finds that job: no second job, no second numeric run, and the decision made with what the prefetch started."""

    world = make_world()
    reply = world.to_boundary()
    assert reply["started"] is True and reply["reason"] == "started"
    at_prefetch = [found for found in spy.identities if found["kind"] == "objective_block"][-1]
    key, seed = OC._hash(at_prefetch), OC.numeric_seed(at_prefetch)
    entry = world.runtime._entries[next(found for found in world.runtime._entries if key in found)]
    assert entry.key == key and entry.material["numeric_seed"] == seed
    world.wait_for_job()
    assert [run["seed"] for run in spy.runs][-1] == seed
    runs, jobs = len(spy.runs), list(world.runtime._entries)
    known = len(spy.identities)

    assert world.next()["step"] is not None
    at_serve = [found for found in spy.identities[known:] if found["kind"] == "objective_block"]
    assert at_serve, "the serve computed no boundary identity"
    assert OC._hash(at_serve[0]) == key and OC.numeric_seed(at_serve[0]) == seed
    assert list(world.runtime._entries) == jobs
    assert len(spy.runs) == runs
    assert world.last_trace()["policies"]["numeric"]["status"] == "answered"


def test_the_serve_without_a_prefetch_starts_the_same_job_the_prefetch_would(make_world, spy):
    """The same boundary through the serve's own start: the seed in the job is still the identity's."""

    world = make_world()
    step = world.next()["step"]
    for _ in range(12):
        world.answer(step)
        before = len(spy.runs)
        step = world.next()["step"]
        if len(spy.runs) > before:
            break
        assert step["kind"] == "item", step
    identity = _assert_determined(spy, kind="objective_block")
    assert any(entry.material["numeric_seed"] == OC.numeric_seed(identity) for entry in world.runtime._entries.values())


@pytest.mark.usefixtures("offerable")
def test_the_learners_options_and_override_draw_nothing(tmp_path, draw, spy):
    """IH3 reads the boundary's candidates and serves the learner's own pick: no numeric run, no mix, no seed."""

    env = mixture_env(tmp_path, fake_runtime(), toml=QUIET, session_id="s1", version=_tag())
    _open_offer(env, draw)
    runs, known = len(spy.runs), len(spy.identities)
    live = LA.options(env)
    pick = next(option for option in live.options if option.kind not in {LA.LESSON, LA.STOP} and not option.plans_pick)
    result = LA.choose(env, kind=pick.kind, ref=pick.ref, surface="offer_page", attempt_id=None, note_md=None,
                       preference_id="p1")
    assert result.outcome == "served"
    assert len(spy.runs) == runs and len(spy.identities) == known


@pytest.mark.usefixtures("offerable")
def test_with_the_switch_off_the_block_still_seeds_from_its_identity(tmp_path, draw, spy):
    """Switched off at the tag the block's seed still comes from the identity (below the tag, ``test_rospeed2``'s R2)."""

    env = mixture_env(tmp_path, fake_runtime(), toml=OFF, session_id="s1", version=_tag())
    _open_offer(env, draw)
    _assert_determined(spy, kind="objective_block")


def _tag() -> str:
    from tests.ih2_lessons_compete_helpers import TAG

    return TAG
