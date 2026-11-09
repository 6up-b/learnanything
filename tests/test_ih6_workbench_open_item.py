"""Instruct hand-off IH6 (spec_instruct_handoff_v1 §7b): an open workbench is an open item for the plan.

While a workbench problem of the plan's current practice session is open, a read of the plan writes no decision and starts
no job; a serve still decides; closing the problem lets the next read draw. Fakes only; no model call.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

import pytest

from learnloop.algorithm_versions import FAILURE_SHARE_ALGORITHM_VERSION, PHONE_PROBES_ALGORITHM_VERSION
from learnloop.config import LearnLoopConfig
from learnloop.config.schema import RouterObjectiveConfig
from learnloop.daily_plan import engine as E
from learnloop.daily_plan import learner_action as LA
from learnloop.daily_plan.engine import advance, advance_with_context
from learnloop.daily_plan.objective_chooser import objective_settings
from learnloop.daily_plan.view import plan_view
from learnloop.db.stores import router_suggestions as suggestions
from learnloop.params.parameter_registry import classify_config_path
from learnloop.reader import workbench as WB
from learnloop.router_objective_switches import SEED_NEUTRAL_SWITCHES, workbench_is_open_item_on

from tests.daily_plan_fakes import iso, record_attempt
from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version
from tests.router_mixture_helpers import mixture_env, payloads, rows
from tests.router_model_fakes import FakeDecider, FakeLLM, block_drawing_seed, fake_runtime
from tests.test_daily_plan_build import _wide_items
from tests.test_ih2_lessons_compete import (
    NO_CHECKS,
    QUIET,
    _env,
    _need_path_env,
    _need_probe_arrives,
    _open_offer,
    _ready_probe,
    draw,  # noqa: F401 - the fixture
)
from tests.test_instruct_handoff_ih0 import DECISION_TABLES, JOB_AND_HOST_TABLES, make_world  # noqa: F401 - the fixture
from tests.test_ro4_objective_serving import policy_answer
from tests.test_te3b_offers import OFFER, offerable  # noqa: F401 - the fixture
from learnloop.vault.loader import load_vault

TAG = FAILURE_SHARE_ALGORITHM_VERSION
OLD = PHONE_PROBES_ALGORITHM_VERSION
OFF = "[router_objective]\nstop_coin = 0.0\nworkbench_is_open_item = false\n"
SESSION = "s1"


@pytest.fixture(autouse=True)
def _a_block_of_items_unless_a_test_asks(draw):
    """These tests are about when a boundary is decided, not what it draws. A real draw's seed is fresh each run and a stop
    and a lesson are in its support, each at the floor, so a test assuming a block of items failed about one run in twenty.
    A test wanting a lesson names it (``draw.prefer``)."""

    draw.never_stop, draw.avoid = True, ("lesson_offer:",)


def _start_session(env, *, at: str | None = None, session_id: str = SESSION) -> None:
    env.session_id = session_id
    with env.repository.connection() as connection:
        when = at or env.now_iso()
        connection.execute("INSERT INTO sessions(id, started_at, updated_at) VALUES (?, ?, ?)", (session_id, when, when))
        connection.commit()


def _end_session(env, session_id: str = SESSION) -> None:
    with env.repository.connection() as connection:
        connection.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (env.now_iso(), session_id))
        connection.commit()


def _open_workbench(env, item: str | None = None) -> dict[str, Any]:
    """A problem on ``item`` (default: a question the plan does not hold)."""

    if item is None:
        record = E.latest_today(env)
        planned = {entry.practice_item_id for entry in record.items()} if record is not None else set()
        item = sorted(item_id for item_id in env.vault.practice_items if item_id not in planned)[0]
    row, _resumed = WB.open_session(env.repository, origin="plan", entry="plan", stem_md="A question.",
                                    practice_item_id=item, clock=env.clock)
    return row


def _plan_rows(env) -> list[dict[str, Any]]:
    return rows(env, "plan_block")


def _counts(env) -> dict[str, int]:
    with env.repository.connection() as connection:
        return {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in DECISION_TABLES}


def _to_boundary(env) -> None:
    """Serve and answer until the plan holds no open block."""

    for _ in range(30):
        record, step = advance(env, serve=True)
        assert step["kind"] == "item", step
        env.clock.advance(2)
        record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                       session_id=env.session_id)
        env.clock.advance(1)
        record = E.reconcile(env, E.latest_today(env))
        if record.current_block() is None:
            return
    raise AssertionError("no boundary reached")


@pytest.fixture
def world(tmp_path):
    """At a boundary with a session open, under the objective at the tag."""

    env = _env(tmp_path, toml=QUIET, session_id=SESSION)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=1)))
    _to_boundary(env)
    return env


# -- reads --------------------------------------------------------------------------------------------------------------


def test_a_read_with_an_open_workbench_writes_no_decision_and_says_a_question_is_in_progress(world):
    env = world
    workbench = _open_workbench(env)
    env.clock.advance(1)
    before = _counts(env)
    record, step, context = advance_with_context(env, serve=False)
    assert _counts(env) == before
    assert step["kind"] == E.QUESTION_IN_PROGRESS_STEP and step["workbench_session_id"] == workbench["id"]
    view = plan_view(env, record, context=context, next_step=step)["plan"]
    assert view["deciding"] is False, "Today polls while deciding: it would spin on this"
    assert view["current_block_id"] is None
    assert view["question_in_progress"] == {
        "workbench_session_id": workbench["id"], "practice_item_id": workbench["practice_item_id"],
        "learning_object_title": step["learning_object_title"]}
    assert step["learning_object_title"]


def test_reads_do_not_draw_however_often_they_come(world):
    env = world
    _open_workbench(env)
    before = _counts(env)
    for _ in range(5):
        env.clock.advance(1)
        advance(env, serve=False)
    assert _counts(env) == before


def test_closing_it_lets_the_next_read_draw(world):
    env = world
    workbench = _open_workbench(env)
    advance(env, serve=False)
    decisions = len(_plan_rows(env))
    WB.abandon(env.repository, workbench["id"], clock=env.clock)
    record, step, context = advance_with_context(env, serve=False)
    assert len(_plan_rows(env)) == decisions + 1
    assert step["kind"] != E.QUESTION_IN_PROGRESS_STEP
    assert "question_in_progress" not in plan_view(env, record, context=context, next_step=step)["plan"]


def test_a_submit_lets_the_next_read_draw(world):
    env = world
    workbench = _open_workbench(env)
    advance(env, serve=False)
    decisions = len(_plan_rows(env))
    env.clock.advance(5)
    attempt = record_attempt(env.repository, workbench["practice_item_id"],
                             str(env.vault.practice_items[workbench["practice_item_id"]].learning_object_id),
                             env.clock.now(), session_id=SESSION)
    WB.mark_submitted(env.repository, workbench["id"], attempt_id=attempt, practice_session_id=SESSION, clock=env.clock)
    advance(env, serve=False)
    assert len(_plan_rows(env)) == decisions + 1


def test_a_read_in_mid_block_reports_the_step_as_before_and_writes_nothing(tmp_path):
    env = _env(tmp_path, toml=QUIET)
    _start_session(env)
    _record, served = advance(env, serve=True)
    _open_workbench(env)
    before = _counts(env)
    _record, read = advance(env, serve=False)
    assert read["kind"] == "item" and read["practice_item_id"] == served["practice_item_id"]
    assert _counts(env) == before


def test_the_days_first_read_builds_a_plan_with_no_block_and_a_serve_decides_it(tmp_path):
    env = _env(tmp_path, toml=QUIET)
    _start_session(env)
    row, _resumed = WB.open_session(env.repository, origin="plan", entry="plan", stem_md="A question.",
                                    practice_item_id=sorted(env.vault.practice_items)[0], clock=env.clock)
    record, step, context = advance_with_context(env, serve=False)
    assert record.is_open and record.blocks == [] and _plan_rows(env) == []
    assert step["workbench_session_id"] == row["id"]
    assert plan_view(env, record, context=context, next_step=step)["plan"]["deciding"] is False
    _record, served = advance(env, serve=True)
    assert served["kind"] != E.QUESTION_IN_PROGRESS_STEP and rows(env, "plan_block")


# -- serves -------------------------------------------------------------------------------------------------------------


def test_a_serve_decides_regardless_and_leaves_the_problem_open(world):
    env = world
    workbench = _open_workbench(env)
    decisions = len(_plan_rows(env))
    _record, step = advance(env, serve=True)
    assert step["kind"] != E.QUESTION_IN_PROGRESS_STEP and len(_plan_rows(env)) == decisions + 1
    assert WB.session_row(env.repository, workbench["id"])["status"] == "open"


# -- what counts --------------------------------------------------------------------------------------------------------


def test_a_workbench_from_an_earlier_session_does_not_block(tmp_path):
    env = _env(tmp_path, toml=QUIET)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=30)))
    _open_workbench(env, sorted(env.vault.practice_items)[0])
    _end_session(env)
    env.clock.advance(10)
    _start_session(env, session_id="s2")
    _to_boundary(env)
    decisions = len(_plan_rows(env))
    _record, step = advance(env, serve=False)
    assert step["kind"] != E.QUESTION_IN_PROGRESS_STEP and len(_plan_rows(env)) == decisions + 1


def test_resuming_it_in_this_session_makes_it_count(tmp_path):
    env = _env(tmp_path, toml=QUIET)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=30)))
    old = _open_workbench(env, sorted(env.vault.practice_items)[0])
    _end_session(env)
    env.clock.advance(10)
    _start_session(env, session_id="s2")
    _to_boundary(env)
    WB.resume_session(env.repository, old["id"], origin="plan", entry="resume", clock=env.clock)
    _record, step = advance(env, serve=False)
    assert step["kind"] == E.QUESTION_IN_PROGRESS_STEP and step["workbench_session_id"] == old["id"]


def test_with_no_session_open_nothing_holds(tmp_path):
    env = _env(tmp_path, toml=QUIET, session_id=None)
    env.session_id = None
    _open_workbench(env, sorted(env.vault.practice_items)[0])
    _record, step = advance(env, serve=False)
    assert step["kind"] != E.QUESTION_IN_PROGRESS_STEP and rows(env, "plan_block")


def test_a_read_naming_no_session_finds_the_open_one(world):
    """The phone's Today before it adopts, the desktop before its restore."""

    env = world
    _open_workbench(env)
    env.session_id = None
    _record, step = advance(env, serve=False)
    assert step["kind"] == E.QUESTION_IN_PROGRESS_STEP


def test_a_problem_outside_the_plan_counts(world):
    env = world
    item = _open_workbench(env)["practice_item_id"]
    assert item not in {entry.practice_item_id for entry in E.latest_today(env).items()}
    assert advance(env, serve=False)[1]["kind"] == E.QUESTION_IN_PROGRESS_STEP


def test_a_reader_problem_that_is_not_an_item_yet_counts(world):
    env = world
    row, _resumed = WB.open_session(env.repository, origin="reader", entry="work_through", stem_md="Selected words.",
                                    extraction_id="ext1", span_ids=["s1"], import_status="pending", clock=env.clock)
    step = advance(env, serve=False)[1]
    assert step["kind"] == E.QUESTION_IN_PROGRESS_STEP and step["workbench_session_id"] == row["id"]
    assert step["practice_item_id"] is None and step["learning_object_title"] is None


def test_leaving_it_for_now_does_not_close_it(world):
    """"Leave for now" keeps the problem open (RW2a), and looking something up mid-question logs one: the Nov 8 failure."""

    env = world
    workbench = _open_workbench(env)
    WB.leave(env.repository, workbench["id"], clock=env.clock)
    assert advance(env, serve=False)[1]["kind"] == E.QUESTION_IN_PROGRESS_STEP


def test_a_problem_whose_item_was_answered_on_the_answer_box_holds_nothing(world):
    """Steps left for the answer box keep the problem open and resumable, but its question has been answered."""

    env = world
    workbench = _open_workbench(env)
    item = workbench["practice_item_id"]
    env.clock.advance(3)
    record_attempt(env.repository, item, str(env.vault.practice_items[item].learning_object_id), env.clock.now(),
                   session_id=SESSION)
    env.clock.advance(1)
    decisions = len(_plan_rows(env))
    step = advance(env, serve=False)[1]
    assert step["kind"] != E.QUESTION_IN_PROGRESS_STEP and len(_plan_rows(env)) == decisions + 1
    assert WB.session_row(env.repository, workbench["id"])["status"] == "open"


def test_a_long_lived_problem_in_a_long_lived_session_holds_reads_only_and_can_be_left(tmp_path):
    """The Nov 7-8 shape: one practice session across a day, its problem still open the next morning. No time limit: the
    plan waits for the learner's step, and Today says so."""

    env = _env(tmp_path, toml=QUIET)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=5)))
    _to_boundary(env)
    workbench = _open_workbench(env)
    env.clock.advance(20 * 60)  # the next day
    record, step, context = advance_with_context(env, serve=False)
    assert record.row["local_date"] == env.today() and record.blocks == []
    assert step["kind"] == E.QUESTION_IN_PROGRESS_STEP
    view = plan_view(env, record, context=context, next_step=step)["plan"]
    assert view["deciding"] is False and view["question_in_progress"]["workbench_session_id"] == workbench["id"]
    # Set aside: the next read decides.
    WB.abandon(env.repository, workbench["id"], clock=env.clock)
    assert advance(env, serve=False)[1]["kind"] != E.QUESTION_IN_PROGRESS_STEP
    assert any(row["created_at"] >= env.today() for row in rows(env, "plan_block"))


def test_a_long_lived_problem_can_be_stepped_past_with_a_serve(tmp_path):
    env = _env(tmp_path, toml=QUIET)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=5)))
    _open_workbench(env, sorted(env.vault.practice_items)[0])
    env.clock.advance(20 * 60)
    assert advance(env, serve=False)[1]["kind"] == E.QUESTION_IN_PROGRESS_STEP
    assert advance(env, serve=True)[1]["kind"] != E.QUESTION_IN_PROGRESS_STEP


# -- IH2 and IH3 ---------------------------------------------------------------------------------------------------------


@pytest.mark.usefixtures("offerable")
def test_a_drawn_offer_stays_as_it_is_when_a_workbench_opens(tmp_path, draw):
    env = _env(tmp_path)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=1)))
    step = _open_offer(env, draw)
    _open_workbench(env)
    env.clock.advance(1)
    before = _counts(env)
    _record, read = advance(env, serve=False)
    assert read["kind"] == "lesson_offer" and read["block_id"] == step["block_id"]
    assert _counts(env) == before
    with env.repository.connection() as connection:
        assert suggestions.response_for(connection, step["offer"]["decision_id"]) is None
    assert next(block for block in E.latest_today(env).blocks if block.id == step["block_id"]).ended_at is None


@pytest.mark.usefixtures("offerable")
@pytest.mark.parametrize("path", ["workflow", "need"])
def test_a_follow_up_ready_during_a_workbench_waits_then_competes_at_the_next_read(tmp_path, draw, path):
    if path == "workflow":
        env = _env(tmp_path)
        _start_session(env, at=iso(env.clock.now() - timedelta(minutes=1)))
        step = _open_offer(env, draw)
        env.clock.advance(1)
        probe = _ready_probe(env)["practice_item_id"]  # its attempt is on the first item the plan doesn't hold
        env.clock.advance(1)
        workbench = _open_workbench(env, sorted(set(env.vault.practice_items) - {probe} - {
            entry.practice_item_id for entry in E.latest_today(env).items()})[0])
    else:
        env, live = _need_path_env(tmp_path)
        _start_session(env, at=iso(env.clock.now() - timedelta(minutes=1)))
        step = _open_offer(env, draw)
        workbench = _open_workbench(env)
        probe = _need_probe_arrives(live)
    env.clock.advance(1)
    before = _counts(env)
    _record, read = advance(env, serve=False)
    # The offer stands: no redraw and no withdrawal while the question is out.
    assert read["kind"] == "lesson_offer" and read["block_id"] == step["block_id"] and _counts(env) == before
    WB.abandon(env.repository, workbench["id"], clock=env.clock)
    env.clock.advance(1)
    draw.prefer = ("followup_contest:",)
    _record, served = advance(env, serve=False)
    assert served["kind"] == "item" and served["practice_item_id"] == probe
    assert rows(env, "plan_block")[-1]["detail_json"]["mixture"]["support"] == [f"followup_contest:{probe}", OFFER]


def test_a_mid_block_follow_up_waits_too_with_no_decision_of_its_own(tmp_path):
    env, live = _need_path_env(tmp_path, toml=NO_CHECKS)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=1)))
    _record, step = advance(env, serve=True)
    assert step["kind"] == "item"
    env.clock.advance(2)
    record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(), session_id=SESSION)
    env.clock.advance(1)
    _open_workbench(env)
    E.reconcile(env, E.latest_today(env))  # the answered item's own event, which any read writes
    probe = _need_probe_arrives(live)
    interrupts = len(rows(env, "plan_interrupt"))
    before = _counts(env)
    advance(env, serve=False)
    assert len(rows(env, "plan_interrupt")) == interrupts and _counts(env) == before
    assert probe not in {entry.practice_item_id for entry in E.latest_today(env).items()}


def test_the_options_read_draws_nothing_and_a_choice_is_still_served(world):
    env = world
    _open_workbench(env)
    before = _counts(env)
    options = LA.options(env)
    assert _counts(env) == before
    view = options.view()
    assert view["enabled"] is True and view["decision_id"] is None and view["options"]
    chosen = next(option for option in view["options"] if option["kind"] in ("question", "review", "new"))
    made = LA.choose(env, kind=chosen["kind"], ref=chosen["ref"], surface="today", attempt_id=None, note_md=None,
                     preference_id="pref_ih6")
    assert made.outcome == "served" and made.step["kind"] == "item"
    assert len(rows(env, "learner_pick")) == 1


# -- the Nov 8 shape ----------------------------------------------------------------------------------------------------


def test_the_nov_8_shape_draws_after_the_attempt_with_that_attempt_in_its_evidence(tmp_path):
    runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer), seed=block_drawing_seed())
    env = mixture_env(tmp_path, runtime, version=TAG, toml=QUIET, session_id=SESSION)
    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=1)))
    _to_boundary(env)
    item = sorted(item_id for item_id in env.vault.practice_items
                  if item_id not in {entry.practice_item_id for entry in E.latest_today(env).items()})[0]
    workbench = _open_workbench(env, item)  # 12:34 pm
    env.clock.advance(3)
    decisions = len(_plan_rows(env))
    assert advance(env, serve=False)[1]["kind"] == E.QUESTION_IN_PROGRESS_STEP  # 12:37 pm: what drew the offer on Nov 8
    assert len(_plan_rows(env)) == decisions
    env.clock.advance(31)
    answered_at = env.now_iso()  # 1:08 pm
    attempt = record_attempt(env.repository, item, str(env.vault.practice_items[item].learning_object_id),
                             env.clock.now(), session_id=SESSION)
    WB.mark_submitted(env.repository, workbench["id"], attempt_id=attempt, practice_session_id=SESSION, clock=env.clock)
    env.clock.advance(1)
    advance(env, serve=False)
    new = _plan_rows(env)[decisions:]
    assert len(new) == 1
    row = new[0]
    # The trace shows the decision's own time, and the evidence it read.
    assert row["created_at"] > answered_at
    card = json.loads(payloads(env, row["id"])["card"]["content_json"])
    assert card["decision"]["decided_at"] == row["created_at"]
    assert card["decision"]["as_of_attempt_id"] == attempt


# -- switch off, below the tag ------------------------------------------------------------------------------------------


def _pinned(tmp_path, *, version: str, toml: str):
    """No models, and a pinned draw: two of these make the same decisions, so a difference is what's being tested."""

    return mixture_env(tmp_path, fake_runtime(seed=block_drawing_seed()), version=version, toml=toml, session_id=SESSION)


def _journey(env) -> list[tuple[Any, ...]]:
    """What a read at a boundary leaves, under whatever is open."""

    _start_session(env, at=iso(env.clock.now() - timedelta(minutes=1)))
    _to_boundary(env)
    return [(row["decision_kind"], row["policy"], row["created_at"]) for row in rows(env, "plan_block")]


@pytest.mark.parametrize(("version", "toml"), [(TAG, OFF), (OLD, "[router_objective]\nstop_coin = 0.0\n")],
                         ids=["switch_off", "below_the_tag"])
def test_off_or_below_the_tag_a_read_is_the_predecessors_exactly(tmp_path, version, toml):
    plain = _pinned(tmp_path / "plain", version=version, toml=toml)
    held = _pinned(tmp_path / "held", version=version, toml=toml)
    assert _journey(plain) == _journey(held)
    _open_workbench(held)
    record_plain, step_plain, context_plain = advance_with_context(plain, serve=False)
    record_held, step_held, context_held = advance_with_context(held, serve=False)
    assert E.open_workbench(held) is None
    assert step_held["kind"] != E.QUESTION_IN_PROGRESS_STEP and step_plain["kind"] != E.QUESTION_IN_PROGRESS_STEP
    # The same decision, read for read. The numeric policy's choice is not compared: its seed names each plan's own ids.
    assert [(row["id"] is not None, sorted(entry["ref"] for entry in row["candidates_json"]), row["decision_kind"],
             row["policy"], row["created_at"]) for row in rows(held, "plan_block")] == \
        [(row["id"] is not None, sorted(entry["ref"] for entry in row["candidates_json"]), row["decision_kind"],
          row["policy"], row["created_at"]) for row in rows(plain, "plan_block")]
    view_plain = plan_view(plain, record_plain, context=context_plain, next_step=step_plain)["plan"]
    view_held = plan_view(held, record_held, context=context_held, next_step=step_held)["plan"]
    assert set(view_held) == set(view_plain) and "question_in_progress" not in view_held
    assert view_held["deciding"] == view_plain["deciding"]


@pytest.mark.parametrize(("version", "toml"), [(TAG, OFF), (OLD, "[router_objective]\nstop_coin = 0.0\n")],
                         ids=["switch_off", "below_the_tag"])
def test_off_or_below_the_tag_the_days_first_read_still_draws(tmp_path, version, toml):
    env = _env(tmp_path, version=version, toml=toml)
    _start_session(env)
    _open_workbench(env, sorted(env.vault.practice_items)[0])
    record = advance(env, serve=False)[0]
    assert record.blocks and rows(env, "plan_block")


# -- the wiring ---------------------------------------------------------------------------------------------------------


def test_the_switch_defaults_on_and_is_classified():
    assert RouterObjectiveConfig().workbench_is_open_item is True
    rule = classify_config_path("router_objective.workbench_is_open_item")
    assert rule is not None and "kill switch" in rule.rationale and "IH6" in rule.rationale


def test_the_gate_reads_the_tag_the_switch_and_the_workbench(tmp_path):
    paths = create_basic_vault(tmp_path / "at_tag")
    set_algorithm_version(paths, TAG)
    assert workbench_is_open_item_on(load_vault(paths.root).config)
    below = create_basic_vault(tmp_path / "below")
    set_algorithm_version(below, OLD)
    assert not workbench_is_open_item_on(load_vault(below.root).config)
    for n, toml in enumerate(("[router_objective]\nworkbench_is_open_item = false\n", "[workbench]\nenabled = false\n")):
        other = create_basic_vault(tmp_path / f"off{n}")
        set_algorithm_version(other, TAG)
        append_config_toml(other.root, toml)
        assert not workbench_is_open_item_on(load_vault(other.root).config), toml
    # It needs no objective: every chooser's boundary crosses on a read.
    plain = create_basic_vault(tmp_path / "no_objective")
    set_algorithm_version(plain, TAG)
    append_config_toml(plain.root, "[router_objective]\nenabled = false\n")
    assert workbench_is_open_item_on(load_vault(plain.root).config)


def test_the_switch_is_not_in_the_prefetch_key_so_it_moves_no_seed(tmp_path):
    """It changes when a boundary is decided, not what its job computes: a job from before a flip is still right for that
    boundary, and the numeric seed (hashed from the key's identity) doesn't move, so neither does ``SEED_NEUTRAL_SWITCHES``."""

    on = create_basic_vault(tmp_path / "on")
    off = create_basic_vault(tmp_path / "off")
    set_algorithm_version(on, TAG)
    set_algorithm_version(off, TAG)
    append_config_toml(off.root, "[router_objective]\nworkbench_is_open_item = false\n")
    assert objective_settings(load_vault(on.root).config) == objective_settings(load_vault(off.root).config)
    assert "workbench_is_open_item" not in SEED_NEUTRAL_SWITCHES


def test_the_desktop_learns_the_switch_from_its_config_only_while_on(tmp_path):
    from learnloop_sidecar.context import config_dto

    on = create_basic_vault(tmp_path / "on")
    set_algorithm_version(on, TAG)
    assert config_dto(load_vault(on.root))["workbench"]["openItem"] is True
    off = create_basic_vault(tmp_path / "off")
    set_algorithm_version(off, TAG)
    append_config_toml(off.root, "[router_objective]\nworkbench_is_open_item = false\n")
    assert "openItem" not in config_dto(load_vault(off.root))["workbench"]
    below = create_basic_vault(tmp_path / "below")
    set_algorithm_version(below, OLD)
    assert "openItem" not in config_dto(load_vault(below.root))["workbench"]


def test_the_config_loads_the_key_at_every_version():
    assert LearnLoopConfig().router_objective.workbench_is_open_item is True


# -- through the phone's host -------------------------------------------------------------------------------------------


def _phone_boundary(world) -> None:
    reply = world.to_boundary()
    assert reply["reason"] != "not_a_boundary"
    world.wait_for_job()
    world.quiet_counts()


def _phone_workbench(world) -> dict[str, Any]:
    item = sorted(load_vault(world.paths.root).practice_items)[0]
    with world.repository.connection() as connection:
        connection.execute("UPDATE sessions SET started_at = ? WHERE id = ?",
                           (iso(world.now["at"] - timedelta(minutes=1)), world.session))
        connection.commit()
    row, _resumed = WB.open_session(world.repository, origin="plan", entry="plan", stem_md="A question.",
                                    practice_item_id=item)
    return row


def test_plan_prefetch_reports_the_workbench_and_starts_no_job(make_world):
    world = make_world(llm=FakeLLM(answer=policy_answer))
    world.answer(world.next()["step"])
    _phone_workbench(world)
    world.llm.requests.clear()
    before = world.quiet_counts()
    for _ in range(12):
        reply = world.prefetch()
        if reply["reason"] != "not_a_boundary":
            break
        world.answer(world.next()["step"])
        before = world.quiet_counts()
    assert reply == {"version": reply["version"], "started": False, "reason": "workbench_open"}
    assert world.llm.requests == []
    after = world.counts()
    assert {table for table in after if after[table] != before[table]} <= JOB_AND_HOST_TABLES


def test_closing_the_workbench_lets_the_next_prefetch_start_the_job(make_world):
    world = make_world(llm=FakeLLM(answer=policy_answer))
    world.answer(world.next()["step"])
    workbench = _phone_workbench(world)
    for _ in range(12):
        reply = world.prefetch()
        if reply["reason"] != "not_a_boundary":
            break
        world.answer(world.next()["step"])
    assert reply["reason"] == "workbench_open"
    WB.abandon(world.repository, workbench["id"])
    assert world.prefetch()["reason"] == "started"
    world.wait_for_job()
    assert world.llm.requests


def test_a_phone_read_holds_says_so_and_a_phone_serve_still_decides(make_world):
    world = make_world(llm=FakeLLM(answer=policy_answer))
    world.answer(world.next()["step"])
    _phone_workbench(world)
    for _ in range(12):
        if world.prefetch()["reason"] != "not_a_boundary":
            break
        world.answer(world.next()["step"])
    before = world.quiet_counts()
    world.llm.requests.clear()
    jobs = len(world.runtime._entries)
    read = world.phone.rpc("get_daily_plan", {"sessionId": world.session})
    assert world.llm.requests == [] and len(world.runtime._entries) == jobs, "a read started a job"
    plan = read["plan"]
    assert plan["deciding"] is False and plan["questionInProgress"]["practiceItemId"]
    assert plan["nextStep"]["kind"] == "question_in_progress"
    after = world.counts()
    for table in DECISION_TABLES:
        if table != "attention_block_events":  # the answered item's own event, which any read's reconcile writes
            assert after[table] == before[table], table
    decisions = after["router_decisions"]
    served = world.next()
    assert served["step"]["kind"] != "question_in_progress"
    assert world.counts()["router_decisions"] > decisions
