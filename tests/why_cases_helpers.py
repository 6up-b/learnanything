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
