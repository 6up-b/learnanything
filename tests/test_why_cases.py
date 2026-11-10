"""Refactor B9 (strategy §3.6, test 1): the owner's four cases, staged with fakes, answered from ``why --json`` alone.

Each case is staged through the code path that made the real one, on a synthetic vault, with every model a fake:

1. **Nov 7, router LLM answers discarded by the timeout:** a slow LLM past the configured wait, then its late answer.
   ``plan_block`` carries the configured wait (``timeout_s``), ``waited_ms`` and the mix's alternatives; the LLM's
   ``model_answer`` is ``router_llm``/``timeout``; the late receipt is listed as discarded, "answered N s late,
   discarded", and ``--payload`` shows its answer.
2. **Nov 8, offer withdrawn with forced_items:** a probe made ready while an offer waits. ``offer_withdrawn``,
   ``rule=forced_items``, its parent the offer's ``plan_block``, the forced items with their workflow and source
   attempt, and the next ``plan_block`` naming it as its parent.
3. **Nov 8, figure stored failed:** one ``figure_author`` per attempt with typed problem codes, the prompt version
   and the model, the ``interactive_figures`` row as detail; a bad prediction now drops only itself
   (``prediction_dropped``).
4. **Pre-builds after a run of skips:** ``why --kind figure_prebuild --first-build`` names the last skip
   (``no_measured_latency``), the first build (``sampled_eu_positive``), the measurement that changed between them
   (``waits_n``, ``wait_basis``) and the pass's seed, and places the first measured latency between them.

Every assertion reads the ``why --json`` output, never the tables.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from learnloop import provenance
from learnloop.algorithm_versions import ROUTER_OBJECTIVE_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance, build_plan

from tests.router_mixture_helpers import mixture_env
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime
from tests.test_ih2_lessons_compete import draw  # noqa: F401 - the fixture
from tests.test_ro4_objective_serving import policy_answer
from tests.test_te3b_offers import offerable  # noqa: F401 - the fixture

SECRET = "the learner wrote about eigenvalues here"


def why(root: Path, *args: str) -> dict[str, Any]:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", *args, "--json", "--vault", str(root)])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def why_text(root: Path, *args: str) -> str:
    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", *args, "--vault", str(root)])
    assert result.exit_code == 0, result.output
    return result.output


def of_kind(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [decision for decision in payload["decisions"] if decision["kind"] == kind]


def _wait_for(predicate, seconds: float = 10.0) -> None:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("timed out waiting")


# -- case 1: the router LLM's answer discarded by the timeout --------------------------------------------------


def stage_case_1(tmp_path) -> tuple[Path, str]:
    """A slow LLM past the 0.3 s wait, under ``TRACE_CASE1``; returns once its late answer has landed."""

    gate = threading.Event()
    llm = FakeLLM(answer=policy_answer, gate=gate)
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=llm, inline=False),
                      version=ROUTER_OBJECTIVE_ALGORITHM_VERSION,
                      toml="[router]\ntimeout_seconds = 0.3\nprefetch_timeout_seconds = 0.6\n")
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


def test_case_1_a_late_llm_answer_is_a_timeout_and_a_discarded_call_with_the_configured_wait(tmp_path):
    root, trace = stage_case_1(tmp_path)
    payload = why(root, trace)
    assert SECRET not in json.dumps(payload)
    block = of_kind(payload, "plan_block")[0]
    # plan_block: the configured wait, how long it waited, and the mix's alternatives with their chances.
    assert block["inputs"]["timeout_s"] == 0.3 and block["inputs"]["prefetch_timeout_s"] == 0.6
    assert block["inputs"]["waited_ms"] >= 0 and block["chosen"]
    assert block["alternatives"] and all(alt["lost_by"] for alt in block["alternatives"])
    assert any("p" in alt for alt in block["alternatives"])
    assert block["decided_by"] and block["versions"] and block["seed"] is not None
    # model_answer: router_llm, timeout, a child of the block ("what happened next").
    [llm_answer] = [decision for decision in of_kind(payload, "model_answer")
                    if decision["parent_id"] == block["record_id"] and decision["decided_by"] == "router_llm"]
    assert llm_answer["status"] == "timeout" and llm_answer["inputs"]["timeout_s"] == 0.3
    assert llm_answer["record_id"] in {child["record_id"] for child in block["next"]}
    # The receipts of this trace that finished after the decision: answered late, discarded.
    late = block["discarded"]
    assert late and all(entry["late_ms"] > 0 for entry in late)
    assert {entry["model"] for entry in late} == {"fake-router-llm"}
    assert "s late, discarded" in why_text(root, "TRACE_CASE1")
    # --payload shows the late answer from its receipt; plain --json never does.
    shown = why(root, "TRACE_CASE1", "--payload")
    by_call = {entry["call_id"]: entry for entry in shown["payloads"]}
    assert {entry["call_id"] for entry in late} <= set(by_call)
    # The router call's receipt holds the prompt and the answer that came too late.
    assert any(by_call[entry["call_id"]]["input_text"] and by_call[entry["call_id"]]["output_text"]
               for entry in late), [(by_call[e["call_id"]]["purpose"], bool(by_call[e["call_id"]]["output_text"])) for e in late]
    assert "payloads" not in payload


# -- case 2: the offer withdrawn with forced_items --------------------------------------------------------------


def stage_case_2(tmp_path, draw) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """An offer drawn and left open, then a probe made ready while it waits; the next Next takes it back."""

    from tests.test_ih2_lessons_compete import OFF, TAG, _env, _open_offer, _ready_probe
    from tests.test_te3b_offers import OFFER

    env = _env(tmp_path, version=TAG, toml=OFF)
    step = _open_offer(env, draw)
    workflow = _ready_probe(env)
    env.clock.advance(1)
    draw.prefer = (OFFER,)
    with provenance.trace_scope("TRACE_CASE2"):
        advance(env, serve=True)
    return env.vault.root, step, workflow


@pytest.mark.usefixtures("offerable")
def test_case_2_an_offer_taken_back_for_a_forced_probe_names_it_and_the_next_decision(tmp_path, draw):
    from tests.test_te3b_offers import OFFER

    root, step, workflow = stage_case_2(tmp_path, draw)
    probe = workflow["practice_item_id"]
    offer_decision, offer_block = step["offer"]["decision_id"], step["block_id"]

    [withdrawn] = of_kind(why(root, f"offer:{offer_decision}"), "offer_withdrawn")
    assert (withdrawn["status"], withdrawn["rule"], withdrawn["decided_by"]) == ("withdrawn", "forced_items", "plan")
    [drawn] = of_kind(why(root, f"block:{offer_block}"), "plan_block")
    assert withdrawn["parent_id"] == drawn["record_id"] and drawn["chosen"] == OFFER
    [forced] = withdrawn["alternatives"]
    assert forced["ref"] == probe and forced["workflow"] == workflow["id"]
    assert forced["source_attempt"] == workflow["source_attempt_id"]
    assert withdrawn["inputs"]["workflows"] == [workflow["id"]]
    assert withdrawn["inputs"]["source_attempts"] == [workflow["source_attempt_id"]]
    # What happened next: the next plan_block names the withdrawal as its parent.
    [nxt] = [child for child in withdrawn["next"] if child["kind"] == "plan_block"]
    assert nxt["trace_id"] == "TRACE_CASE2"
    trace = why(root, "TRACE_CASE2")
    [after] = [decision for decision in of_kind(trace, "plan_block") if decision["record_id"] == nxt["record_id"]]
    assert after["parent_id"] == withdrawn["record_id"] and after["inputs"]["forced"] == [probe]


# -- case 3: a figure stored failed ------------------------------------------------------------------------------


def stage_case_3(tmp_path: Path, answers: list[Any]) -> tuple[Path, dict[str, Any]]:
    from tests.figure_fixtures import AuthorFake, build, build_figure_vault, context

    paths, _repository = build_figure_vault(tmp_path / "vault")
    shown = build(context(paths.root, author=AuthorFake(answers)))["figure"]
    return paths.root, shown


def test_case_3_a_figure_stored_failed_has_one_author_record_per_attempt_with_typed_codes(tmp_path):
    from tests.figure_fixtures import half_density

    root, shown = stage_case_3(tmp_path, [half_density(), half_density()])
    assert shown["verification"] == "failed"
    payload = why(root, f"figure:{shown['figureId']}")
    attempts = sorted(of_kind(payload, "figure_author"), key=lambda decision: decision["inputs"]["attempt"])
    assert [decision["status"] for decision in attempts] == ["discarded", "failed"]
    for decision in attempts:
        assert decision["rule"] == "verification_failed" and decision["inputs"]["problems"]
        assert all(provenance.is_code(code) for code in decision["inputs"]["problems"])
        assert decision["versions"]["prompt_version"].startswith("figure_author")
        assert decision["versions"]["model"] == "fake-figure-model"
        assert decision["detail"] == {"table": "interactive_figures", "id": shown["figureId"]}
    assert attempts[0]["trace_id"] == attempts[1]["trace_id"]
    assert payload["source"] == "decision_records" and payload["reconstructed"] == []


def test_case_3_since_the_drop_a_bad_prediction_drops_only_itself(tmp_path):
    from tests.figure_fixtures import flagship

    bad = {"prompt": "If lam grows, does this rise?", "change": {"nothing_called_this": 1},
           "observe": {"kind": "direction", "expr": "p*lam"}}
    root, shown = stage_case_3(tmp_path, [flagship(kind="illustrative", predictions=[bad])])
    [only] = of_kind(why(root, f"figure:{shown['figureId']}"), "figure_author")
    assert (only["status"], only["rule"]) == ("chosen", "prediction_dropped")
    assert only["inputs"]["predictions_dropped"] == 1
    assert "If lam grows" not in json.dumps(only)


# -- case 4: pre-builds after a run of skips ---------------------------------------------------------------------


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
    from tests.test_figures_prefetch import env_for, make_vault

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


def test_case_4_first_build_names_the_last_skip_the_first_build_and_the_measurement_between(tmp_path):
    root, skips, measured = stage_case_4(tmp_path)
    payload = why(root, "--kind", "figure_prebuild", "--first-build")
    built = payload["first_build"]
    assert built["label"] == "native" and built["skips_before_first_build"] == len(skips)
    last, first = built["last_skip"], built["first_build"]
    assert last["rule"] == "no_measured_latency" and first["rule"] == "sampled_eu_positive"
    assert built["changed"]["waits_n"] == [0, 1] and built["changed"]["wait_basis"] == ["none", "author_call"]
    assert built["first_measurement"]["row"] == {"table": "model_call_receipts", "id": measured}
    assert built["measurement_between"] is True
    # The two records themselves: EU, the wait, the cost, p_open, the propensity and the seed.
    by_id = {decision["record_id"]: decision for decision in payload["decisions"]}
    skip, build = by_id[last["record_id"]], by_id[first["record_id"]]
    assert skip["inputs"]["eu"] is None and skip["inputs"]["waits_n"] == 0
    assert build["inputs"]["eu"] > 0 and build["inputs"]["waits_n"] == 1 and build["inputs"]["cost_min"] == 0.0
    assert build["inputs"]["wait_min"] > 0 and build["inputs"]["p_open"] is not None
    assert build["seed"] and str(build["seed"]).isdigit()
    assert built["by_trigger_kind"]["offer"]["skips_before_first_non_skip"] == len(skips)
