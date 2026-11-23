"""What other test files use from ``tests/test_why_cases.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from learnloop import provenance
from learnloop.algorithm_versions import ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance, build_plan

from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.ro4_objective_serving_helpers import policy_answer


def why(root: Path, *args: str) -> dict[str, Any]:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", *args, "--json", "--vault", str(root)])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def of_kind(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [decision for decision in payload["decisions"] if decision["kind"] == kind]


def _wait_for(predicate, seconds: float = 10.0) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("timed out waiting")


# Case 1's waits. The gated LLM always misses them; the decider, on its own thread, must answer inside them, which
# 0.3 s did not always allow under a loaded ``-n 8 --fresh-connections`` run (arc C close).
CASE1_WAIT_S, CASE1_PREFETCH_WAIT_S = 2.0, 4.0


def stage_case_1(tmp_path) -> tuple[Path, str]:
    """A slow LLM past the router's wait, under ``TRACE_CASE1``; returns once its late answer has landed."""

    gate = threading.Event()
    llm = FakeLLM(answer=policy_answer, gate=gate)
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=llm, inline=False),
                      version=ROUTER_OBJECTIVE_ALGORITHM_VERSION,
                      toml=f"[router]\ntimeout_seconds = {CASE1_WAIT_S}\nprefetch_timeout_seconds = {CASE1_PREFETCH_WAIT_S}\n")
    try:
        with provenance.trace_scope("TRACE_CASE1"):
            build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
            advance(env, serve=True)
    finally:
        gate.set()
    root = env.vault.root

    def answered() -> bool:
        with env.repository.connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM model_call_receipts WHERE trace_id = 'TRACE_CASE1' AND owner_kind = "
                "'router_decision' AND finished_at IS NULL").fetchone()[0] == 0

    _wait_for(answered)
    return root, "TRACE_CASE1"


def stage_case_2(tmp_path, draw) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """An offer drawn and left open, then a probe made ready while it waits; the next Next takes it back."""

    from tests.ih2_lessons_compete_helpers import OFF, TAG, _env, _open_offer, _ready_probe
    from tests.te3b_offers_helpers import OFFER

    env = _env(tmp_path, version=TAG, toml=OFF)
    step = _open_offer(env, draw)
    workflow = _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    with provenance.trace_scope("TRACE_CASE2"):
        advance(env, serve=True)
    return env.vault.root, step, workflow


def stage_case_3(tmp_path: Path, answers: list[Any]) -> tuple[Path, dict[str, Any]]:
    from tests.figure_fixtures import AuthorFake, build, build_figure_vault, context

    paths, _repository = build_figure_vault(tmp_path / "vault")
    shown = build(context(paths.root, author=AuthorFake(answers)))["figure"]
    return paths.root, shown


def _measured_press(repository: Any, *, seconds: float = 40.0) -> str:
    """A completed pressed author call, timed now: the first measured latency, after the skips."""

    finished = datetime.now(UTC)
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO model_call_receipts (id, owner_kind, owner_id, purpose, provider, status, started_at, "
            "finished_at) VALUES ('mcr_press', 'figure_author', 'figure:x', 'figure_author', 'fake_figures', "
            "'completed', ?, ?)",
            ((finished - timedelta(seconds=seconds)).isoformat(), finished.isoformat()))
        connection.commit()
    return "mcr_press"


def stage_case_4(tmp_path) -> tuple[Path, list[dict[str, Any]], str]:
    """Two pre-build passes before any measured latency, a measured press, then a pass that builds."""

    from learnloop.figures import prefetch as PF
    from tests.figure_fixtures import EXTRACTION
    from tests.figures_prefetch_helpers import env_for, make_vault

    from learnloop.figures import power as P

    P.set_power_reader(lambda: P.PowerState(True, P.MAINS, "test"))
    try:
        paths, repository, vault = make_vault(tmp_path, wait=False)
        skips = []
        for ref, block in (("tutor:qe_1", "p3"), ("tutor:qe_2", "p5")):
            result = PF.run_trigger(replace(env_for(vault, repository), rng=None),
                                    PF.Trigger("offer", ref, blocks=((EXTRACTION, block),)))
            skips.extend(decision for decision in result.decisions if decision["decision"] == "skip")
        assert len(skips) == 2  # a run of skips, before any measured latency
        # The pre-build ledger stamps its rows to the second, so the measurement gets a second of its own on each
        # side.
        time.sleep(1.1)
        measured = _measured_press(repository)
        time.sleep(1.1)
        second = PF.run_trigger(replace(env_for(vault, repository), rng=None),
                                PF.Trigger("offer", "tutor:qe_3", blocks=((EXTRACTION, "p7"), (EXTRACTION, "p9"))))
        assert any(decision["decision"] == "build" for decision in second.decisions)
    finally:
        P.set_power_reader(None)
    return paths.root, skips, measured


#: The objective's rule codes (refactor rule L6): what the mix serves, staged per code, and the code its record names.
RULE_CASES = (("stop_for_today", "stop_offer"), ("repair:", "repair_open_problem"), ("maintain:", "review"),
              ("lesson_offer:", "lesson_offer"))


def stage_rule_case(tmp_path, draw, prefer: str) -> Path:
    """Boundaries the objective decides with both models answering, under ``TRACE_RULE``, the mix serving the first
    option that starts with ``prefer`` whenever one is in the support (the ih2 ``draw`` fixture). No stop coin and no
    day's check, so what the mix draws is what is served. Answers what is served until such a boundary is decided."""

    from learnloop.algorithm_versions import LATEST_ALGORITHM_VERSION
    from tests.daily_plan_fakes import record_attempt

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=policy_answer)),
                      version=LATEST_ALGORITHM_VERSION,
                      toml='[router_objective]\nstop_coin = 0.0\ncheck_rate = "off"\n')
    draw.prefer = (prefer,)

    def decided() -> bool:
        with env.repository.connection() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM router_decisions WHERE decision_kind = 'plan_block' AND policy = "
                "'router_objective_v1' AND chosen_ref LIKE ?", (f"{prefer}%",)).fetchone()[0] > 0

    with provenance.trace_scope("TRACE_RULE"):
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        for _ in range(8):
            if decided():
                break
            _record, step = advance(env, serve=True)
            if decided() or step is None or step["kind"] != "item":
                break
            env.clock.advance(2)
            record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"], env.clock.now(),
                           session_id=env.session_id)
    assert decided(), f"no boundary served {prefer}"
    return env.vault.root


# -- the grade application's records: one case per rule code its core returns (refactor rule L6) ---------------------

#: ``(rule, kind)``: the grade's verdict classes and the hold's code, each staged by :func:`stage_grade_case`.
GRADE_RULE_CASES = (("full_credit", "grade"), ("partial_credit", "grade"), ("no_credit", "grade"),
                    ("dont_know", "grade"), ("stuck", "grade"), ("grade_held_for_review", "grade_held"))
GRADE_ITEM = "pi_svd_compute_001"


def stage_grade_case(tmp_path: Path, rule: str) -> tuple[Path, str]:
    """One live answer on a split vault's ``pi_svd_compute_001`` (``setup`` 2 + ``result`` 2) through the attempt
    step, under ``TRACE_GRADE_RULE``, graded so its core returns ``rule``. Returns the vault root and the attempt id."""

    from learnloop.attempts.attempts import ApplyAttemptInput, AttemptDraft, ResolvedGrade, apply_attempt
    from learnloop.clock import FrozenClock

    from tests.split_live_helpers import split_vault

    points, draft, apply = {
        "full_credit": ({"setup": 2, "result": 2}, {}, {}),
        "partial_credit": ({"setup": 2, "result": 1}, {}, {}),
        "no_credit": ({"setup": 0, "result": 0}, {}, {}),
        "dont_know": ({"setup": 0, "result": 0}, {"attempt_type": "dont_know", "learner_answer_md": ""}, {}),
        "stuck": ({"setup": 1, "result": 0}, {"declared_stuck": True}, {}),
        # Held only while nothing is assessed (``outcome_contract.grade_is_held``): both criteria unverified.
        "grade_held_for_review": ({"setup": 0, "result": 0}, {}, {
            "grading_source": "ai", "grade_held_for_review": True, "unverified_criterion_ids": ("setup", "result")}),
    }[rule]
    paths, vault, repository = split_vault(tmp_path)
    attempt_id = f"att_rule_{rule}"
    with provenance.trace_scope("TRACE_GRADE_RULE"):
        apply_attempt(vault, repository, ApplyAttemptInput(
            draft=AttemptDraft(**{"practice_item_id": GRADE_ITEM, "learner_answer_md": "U Sigma V^T from A^T A",
                                  "attempt_type": "independent_attempt", **draft}),
            attempt_id=attempt_id,
            grade=ResolvedGrade(rubric_score=float(sum(points.values())), criterion_points=points, evidence_rows=[],
                                error_attributions=[], grader_confidence=1.0, confidence=3,
                                manual_review_reason=None, feedback_md="graded"),
            **apply,
        ), clock=FrozenClock(datetime(2026, 6, 1, 12, 0, tzinfo=UTC)))
    return paths.root, attempt_id


# -- the due queue's slate record: one case per rule code ``rank_due`` returns (refactor rule L6) -------------------

SLATE_RULE_CASES = ("empty_slate", "presentation_pin", "pending_followup", "check_once", "seeded_exploration",
                    "greedy_order", "composition_order")


def stage_slate_case(tmp_path: Path, rule: str) -> tuple[Path, list[str]]:
    """One serving build with a session, under ``TRACE_SLATE_RULE``, on a vault where ``rule`` puts the head first.

    ``presentation_pin`` and ``check_once`` are the due-queue golden's vault (``tests/due_queue_helpers.py``): its
    session committed a probe an hour ago, so that session's next build pins it; another session's build serves the
    due "Check once" first. The rest are the placement vault (``tests/helpers.py``): new material ranked greedily; a
    due cold retry inserted first; a tutor promotion the requested-items floor pulls to the front; every candidate a
    near-tie at an exploration rate of one, with no goal quota to reorder the draw; and the basic vault with its one
    learning object paused, which leaves nothing to serve. Returns the root and the served queue's ids."""

    from datetime import timedelta

    from learnloop.clock import FrozenClock
    from learnloop.db.repositories import Repository
    from learnloop.scheduling.scheduler import SchedulerSession, serve_due_queue
    from learnloop.substrate.state_sync import sync_vault_state
    from learnloop.vault.loader import load_vault

    from tests.helpers import NOW, NOW_ISO, append_config_toml, create_basic_vault, create_placement_vault

    clock, session = FrozenClock(NOW + timedelta(minutes=5)), "sess_slate_rule"
    if rule in ("presentation_pin", "check_once"):
        from tests.due_queue_helpers import CLOCK, SESSION, build_rich_vault

        vault, repository = build_rich_vault(tmp_path / "vault")
        clock, session = CLOCK, SESSION if rule == "presentation_pin" else session
    else:
        make = create_basic_vault if rule == "empty_slate" else create_placement_vault
        paths = make(tmp_path / "vault")
        if rule == "seeded_exploration":
            append_config_toml(paths.root, "[scheduler]\nselection_exploration_rate = 1.0\n"
                               "selection_exploration_reward_window = 10.0\ngoal_quota_floor_min = 0.0\n"
                               "goal_quota_floor_max = 0.0\n")
        vault, repository = load_vault(paths.root), Repository(paths.sqlite_path)
        sync_vault_state(vault, repository, clock=FrozenClock(NOW))
        if rule == "empty_slate":
            from learnloop.intent.control import Scope, apply_choice

            apply_choice(vault, repository, Scope("learning_object", "lo_svd_definition"), "pause",
                         clock=FrozenClock(NOW))
            vault = load_vault(paths.root)
        elif rule == "pending_followup":
            repository.create_followup_task(
                kind="cold_retry", case_kind="misconception", case_ref="mc_slate_rule",
                learning_object_id="lo_eigen_basics", selected_item_id="pi_eig_easy",
                not_before=(NOW - timedelta(hours=6)).isoformat().replace("+00:00", "Z"),
                expires_at=(NOW + timedelta(days=5)).isoformat().replace("+00:00", "Z"),
                clock=FrozenClock(NOW - timedelta(days=2)),
            )
        elif rule == "composition_order":
            event_id = repository.insert_question_event({
                "context": "practice", "practice_item_id": "pi_svd_define_001", "session_id": "sess_request",
                "question_md": "Chase this?", "answer_md": "A guiding question.", "question_type": "mechanism",
                "facets": ["recall"], "hint_equivalent": True, "answer_status": "answered", "created_at": NOW_ISO,
            })
            repository.insert_question_promotion(question_event_id=event_id, intent="practice", route="auto_apply",
                                                 created_practice_item_id="pi_diag_easy", clock=FrozenClock(NOW))
    with provenance.trace_scope("TRACE_SLATE_RULE"):
        queue = serve_due_queue(vault, repository, clock=clock, session=SchedulerSession(session_id=session))
    return Path(vault.root), [item.practice_item_id for item in queue]
