"""Router R2b serving gates under the mixture (mvp-0.24), with fake models.

* **G1**: no infeasible or unknown option can be drawn; a model answer naming
  one is rejected and its weight goes to the staged rule.
* **G2**: an irreversible block is the rule's deterministic pick or absent
  from the options (propensity 0); no model is asked about it.
* **G9**: a learner pick under the mixture is ``learner_pick`` with no propensity.
* **Payloads**: the card and both models' requests and raw answers are stored
  beside the decision; the sensors are logged (``router_qs_v2``).
* **Kill switches**: ``router.mode = "staged"`` at mvp-0.24 serves R2a
  exactly (no model asked); with no model set up the rule chooses
  deterministically (nothing explored without a model).
* **Timing**: a read never waits on a model (the decision stays open and the
  plan says it is being chosen); a serving step decides it.
* **The Decider never falls back to a chat model**; **spend**: the daily
  guard refuses metered calls past the cap, subscription calls never.
* **The why**: plain words by the component that drew; a model-written
  rationale is marked and guarded.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime

import pytest

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.algorithm_versions import ROUTER_STAGED_FRAME_ALGORITHM_VERSION
from learnloop.daily_plan.engine import advance, build_plan, learner_pick
from learnloop.daily_plan.router_runtime import RouteModels, models_disabled
from learnloop.router import why
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.helpers import create_daily_plan_vault
from tests.router_mixture_helpers import B, mixture_env, payloads, rows, run
from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime, options_in

FROZEN = datetime(2026, 10, 14, 9, 30, tzinfo=UTC)


def _call(ctx, name, params):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _blocks(record):
    return [(block.lane, tuple(item.practice_item_id for item in block.items)) for block in record.blocks]


# -- G1 / G2 / G9 ----------------------------------------------------------------------


def test_a_decider_naming_an_option_it_was_not_asked_is_rejected(tmp_path):
    def rogue(refs):
        return {ref: 1.0 for ref in refs}

    class RogueDecider(FakeDecider):
        def decide(self, state, questions, **kwargs):
            result = super().decide(state, questions, **kwargs)
            from learnloop.ai.decisions import ChoiceAnswer

            answer = result.answers["choose_block"]
            probabilities = {"ghost:block": 1.0, **{ref: 0.0 for ref in answer.probabilities}}
            result.answers["choose_block"] = ChoiceAnswer(choice="ghost:block", probabilities=probabilities)
            return result

    env = mixture_env(tmp_path, fake_runtime(decider=RogueDecider(choice=rogue), llm=FakeLLM()))
    run(env)
    for row in [row for row in rows(env) if row["policy"] == "router_mixture_v1"]:
        assert row["chosen_ref"] != "ghost:block"
        assert row["detail_json"]["mixture"]["models"]["decider"]["status"] == "invalid"
        assert row["fallback"] == "decider"
        feasible = {entry["ref"] for entry in row["candidates_json"] if entry["feasible"]}
        assert row["chosen_ref"] in feasible


def test_an_irreversible_block_is_never_an_option(tmp_path):
    from tests.test_router_r2a_serving import _hold_cold_check

    llm = FakeLLM()
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=llm))
    _hold_cold_check(env, "pi_m1a")
    run(env)
    for row in rows(env):
        irreversible = {entry["ref"] for entry in row["candidates_json"]
                        if entry.get("annotations", {}).get("reversible") is False}
        if not irreversible:
            continue
        if row["chosen_ref"] in irreversible:
            # Only as the rule's own deterministic pick, and no model asked.
            assert row["propensity_kind"] == "deterministic" and row["policy"] == "staged_v1"
            assert row["detail_json"]["router"]["decided_by"] == "irreversible"
            assert row["model_distributions_json"] is None
        else:
            support = row["detail_json"].get("mixture", {}).get("support", [])
            assert not irreversible & set(support)
            for entry in row["candidates_json"]:
                if entry["ref"] in irreversible:
                    assert entry["propensity"] == 0.0
    for request in llm.requests:
        assert not any("pi_m1a" in ref for ref in options_in(request.prompt))


def test_a_learner_pick_under_the_mixture_has_no_propensity(tmp_path):
    from tests.router_model_fakes import first_option, seed_with_first_uniform

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(choice=first_option), llm=FakeLLM(),
                                             seed=seed_with_first_uniform(at_least=0.2)),
                      toml="[router.weights]\nstaged = 0.0\ndecider = 1.0\nllm = 0.0\n")
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    advance(env, serve=True)
    record, step = learner_pick(env, "pi_p1b")
    assert step["practice_item_id"] == "pi_p1b"
    picks = [row for row in rows(env) if row["learner_pick"]]
    assert picks and all(row["propensity"] is None and row["propensity_kind"] == "none" for row in picks)


# -- what is stored --------------------------------------------------------------------------


def test_each_mixture_decision_stores_its_card_both_requests_and_both_raw_answers(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()))
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions
    for row in decisions:
        stored = payloads(env, row["id"])
        assert {"card", "decider_request", "decider_response", "llm_request", "llm_response"} <= set(stored)
        assert stored["card"]["content_hash"] == row["card_hash"]
        assert row["question_set_version"] == "router_qs_v2"
        assert row["model_ids_json"]["decider"] == "perplexity/pplx-decider-v1.1-27b"
        assert row["model_ids_json"]["llm_schema_version"] == "router_llm_v2"
        sensors = row["sensor_answers_json"]
        assert set(sensors) == {"decider", "llm"}
        assert set(sensors["decider"]) == {"teach_first", "will_pass_next"}
        # The card the models read is the stored card.
        request = stored["llm_request"]["content_text"]
        assert "# Session" in request and "# The options" in request
        assert row["cost_usd"] > 0 and row["latency_ms"] is not None


def test_the_router_llm_is_asked_in_an_isolated_turn(tmp_path):
    # The card carries learner text: no tools, files, memories or MCP servers
    # beside the prompt, as for the blind grader.
    llm = FakeLLM()
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=llm))
    run(env)
    assert llm.requests and all(request.isolated for request in llm.requests)


def test_router_log_shows_one_decisions_receipt_in_full(tmp_path):
    import json

    from typer.testing import CliRunner

    from learnloop.cli import app

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()))
    run(env)
    row = next(row for row in rows(env) if row["policy"] == "router_mixture_v1")
    runner = CliRunner()
    result = runner.invoke(app, ["router", "log", "--vault", str(env.vault.root), "--decision", row["id"], "--json"])
    assert result.exit_code == 0, result.output
    shown = json.loads(result.output)["decision"]
    assert shown["id"] == row["id"] and shown["seed"] == row["seed"]
    assert shown["model_distributions"] == row["model_distributions_json"]
    assert shown["mixture_weights"] == row["mixture_weights_json"]
    assert shown["detail"]["mixture"]["support"] and shown["candidates"]
    assert {"card", "decider_request", "decider_response", "llm_request", "llm_response"} <= set(shown["payload_kinds"])
    missing = runner.invoke(app, ["router", "log", "--vault", str(env.vault.root), "--decision", "nope"])
    assert missing.exit_code == 1


def test_the_sensors_are_logged_and_never_select(tmp_path):
    seed = lambda key, decision_id: "fixed-seed"  # noqa: E731
    first = mixture_env(tmp_path / "a", fake_runtime(decider=FakeDecider(p_yes=0.1), llm=FakeLLM(), seed=seed))
    second = mixture_env(tmp_path / "b", fake_runtime(decider=FakeDecider(p_yes=0.9), llm=FakeLLM(), seed=seed))
    assert _blocks(run(first)) == _blocks(run(second))
    noisy = [row["sensor_answers_json"]["decider"]["teach_first"] for row in rows(second) if row["sensor_answers_json"]]
    assert noisy and all(set(values.values()) == {0.9} for values in noisy)


def test_without_sensors_the_question_set_is_v1(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()), toml="[router]\nsensors = false\n")
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions and all(row["question_set_version"] == "router_qs_v1" for row in decisions)
    assert all(row["sensor_answers_json"] is None for row in decisions)


# -- kill switches and readiness ------------------------------------------------------------


def test_staged_mode_at_the_successor_serves_r2a_exactly_and_asks_no_model(tmp_path):
    decider, llm = FakeDecider(), FakeLLM()
    staged = mixture_env(tmp_path / "staged", fake_runtime(decider=decider, llm=llm), toml='[router]\nmode = "staged"\n')
    r2a = mixture_env(tmp_path / "r2a", fake_runtime(), version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    assert _blocks(run(staged)) == _blocks(run(r2a))
    assert decider.calls == [] and llm.requests == []
    assert {row["policy"] for row in rows(staged)} <= {"staged_v1", "learner"}
    assert {row["mode"] for row in rows(staged)} == {"staged"}


def test_with_no_model_set_up_the_rule_chooses_deterministically(tmp_path):
    none = mixture_env(tmp_path / "none", fake_runtime())
    r2a = mixture_env(tmp_path / "r2a", fake_runtime(), version=ROUTER_STAGED_FRAME_ALGORITHM_VERSION)
    assert _blocks(run(none)) == _blocks(run(r2a))
    for row in rows(none):
        assert row["mode"] == "mixture" and row["propensity_kind"] in {"deterministic", "none"}
        assert row["design"] is None
    record = advance(none, serve=False)[0]
    details = [block for block in record.blocks if (block.chosen.get("router") or {}).get("decided_by") == "not_ready"]
    assert details
    from learnloop.daily_plan.view import _why_details

    assert "aren't set up" in _why_details(details[0])


def test_the_test_suite_routes_ask_no_model():
    assert models_disabled()
    assert set(RouteModels().readiness(type("V", (), {"root": ".", "config": None})()).values()) == {"disabled"}


# -- timing: a read never waits ------------------------------------------------------------------


def test_a_read_leaves_the_decision_open_and_a_serve_decides_it(tmp_path, monkeypatch):
    from learnloop.daily_plan import router_runtime

    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    gate = threading.Event()
    runtime = fake_runtime(decider=FakeDecider(gate=gate), llm=FakeLLM(gate=gate), inline=False)
    monkeypatch.setattr(router_runtime, "_DEFAULT", runtime)
    paths = create_daily_plan_vault(tmp_path / "vault", version=B,
                                    learning_objects={"lo_extra": [("pi_extra_1", 2.0), ("pi_extra_2", 2.0)]})
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    try:
        view = _call(ctx, "get_daily_plan", {})
        plan = view["plan"]
        assert plan["deciding"] is True and plan["currentBlockId"] is None and plan["blocks"] == []
        again = _call(ctx, "next_plan_item", {"serve": False})
        assert again["step"] is None and again["plan"]["deciding"] is True
        gate.set()
        session_id = _call(ctx, "start_session", {"availableMinutes": 25})["sessionId"]
        served = _call(ctx, "next_plan_item", {"sessionId": session_id, "serve": True})
        assert served["step"]["kind"] == "item" and served["plan"]["deciding"] is False
        with sqlite3.connect(paths.sqlite_path) as connection:
            connection.row_factory = sqlite3.Row
            decision = connection.execute("SELECT * FROM router_decisions WHERE decision_kind = 'plan_block'").fetchone()
        assert decision["policy"] == "router_mixture_v1" and decision["fallback"] is None
    finally:
        gate.set()


def test_a_serve_waits_at_most_the_timeout_then_the_rule_takes_both_shares(tmp_path):
    gate = threading.Event()
    try:
        runtime = fake_runtime(decider=FakeDecider(gate=gate), llm=FakeLLM(gate=gate), inline=False)
        env = mixture_env(tmp_path, runtime, toml="[router]\ntimeout_seconds = 0.2\nprefetch_timeout_seconds = 0.4\n")
        build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
        import time

        started = time.monotonic()
        record, step = advance(env, serve=True)
        assert time.monotonic() - started < 3.0
        row = rows(env)[0]
        assert row["fallback"] == "both" and row["propensity_kind"] == "exact"
        assert row["detail_json"]["mixture"]["models"]["decider"]["status"] == "timeout"
    finally:
        gate.set()


# -- the Decider never falls back to chat; spend ---------------------------------------------------


def test_the_deciders_route_never_resolves_to_a_chat_model(tmp_path, monkeypatch):
    from learnloop.ai.routing import route_profile_mismatch
    from learnloop.vault.loader import load_vault

    paths = create_daily_plan_vault(tmp_path / "vault", version=B)
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("[ai.routing]\n", '[ai.routing]\nrouter_decider = "codex"\n', 1))
    vault = load_vault(paths.root)
    assert vault.config.ai.routing.router_decider == "codex"
    assert "never falls back to a chat provider" in route_profile_mismatch(vault.config, "codex", "router_decider")
    monkeypatch.delenv("LEARNLOOP_ROUTER_MODELS", raising=False)
    readiness = RouteModels().readiness(vault)
    assert readiness["decider"] is not None


def test_a_failed_decider_is_never_answered_by_the_llm_in_its_place(tmp_path):
    llm = FakeLLM()
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(error=RuntimeError("502")), llm=llm))
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    # One LLM request per decision: its own, never a second on the Decider's behalf.
    assert len(llm.requests) == len(decisions)
    assert all(row["fallback"] == "decider" for row in decisions)


def test_the_daily_guard_refuses_metered_calls_and_never_a_subscription_call(tmp_path):
    class SubscriptionLLM(FakeLLM):
        provider_type = "codex_sdk"

    decider = FakeDecider()
    llm = SubscriptionLLM()
    env = mixture_env(tmp_path, fake_runtime(decider=decider, llm=llm), toml="[router]\nmax_daily_cost_usd = 0.0\n")
    run(env)
    decisions = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert decisions
    for row in decisions:
        models = row["detail_json"]["mixture"]["models"]
        assert models["decider"]["status"] == "spend"
        assert models["llm"]["status"] == "answered" and models["llm"]["subscription"] is True
        assert row["fallback"] == "decider"
    assert decider.calls == []
    from learnloop.router.why import mixture_details

    assert "today's model budget is used" in mixture_details(
        {"decided_by": "mixture", "fallback_reasons": {"decider": "spend"}}, propensity=0.4, decision_ref="d1")


def test_the_daily_guard_counts_todays_router_receipts(tmp_path):
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(cost=0.40), llm=FakeLLM()),
                      toml="[router]\nmax_daily_cost_usd = 0.30\n")
    from learnloop.ai.execution import model_call, record_model_calls, report_call_usage
    from learnloop.daily_plan.router_runtime import RouterSpend, SpendRefused

    class Client:
        provider_name = "openrouter_decider"
        provider_type = "decider"
        model = "m"

        def __init__(self, usd):
            self.usd = usd
            self.sent = 0

        def estimated_cost(self, input_tokens):
            return self.usd

        def send(self):
            with model_call(self, purpose="router_decision", prompt="x"):
                self.sent += 1
                report_call_usage({"cost": self.usd})

    with record_model_calls(env.repository, owner_kind="router_decision", owner_id="k"):
        Client(0.29).send()
    spend = RouterSpend()
    from learnloop.clock import utc_now_iso

    assert spend.spent_today(env.repository, env.vault.config, utc_now_iso()) == pytest.approx(0.29)
    late = Client(0.02)
    with pytest.raises(SpendRefused), spend.metered(env.repository, env.vault.config,
                                                    owner_kind="router_decision", owner_id="k2"):
        late.send()
    assert late.sent == 0

    class Subscription(Client):
        provider_type = "codex_sdk"

    paid = Subscription(5.0)
    with spend.metered(env.repository, env.vault.config, owner_kind="router_decision", owner_id="k3"):
        paid.send()
    assert paid.sent == 1


def _decider_only(cap: float) -> str:
    return (f"[router]\nmax_daily_cost_usd = {cap}\n[router.weights]\nstaged = 0.0\ndecider = 1.0\n"
            "llm = 0.0\n")


class _PricedDecider(FakeDecider):
    """A Decider whose every request is estimated at one cent."""

    def estimated_cost(self, input_tokens):
        return 0.01


def test_an_unfinished_request_keeps_its_reservation_after_a_restart(tmp_path, monkeypatch):
    # Codex review F5: the process loses a metered request's finish receipt
    # (it exits, or the write fails) after the request was sent. On restart
    # the request's start receipt still holds its reservation: unknown usage
    # is never free, so the next request cannot spend the cap again.
    from learnloop.daily_plan.policy import policy_for
    from learnloop.db.repositories import Repository

    from tests.router_model_fakes import first_option

    first = _PricedDecider(choice=first_option)
    env = mixture_env(tmp_path, fake_runtime(decider=first), toml=_decider_only(0.015))
    real = Repository.record_model_event

    def finish_lost(self, action, event, **kwargs):
        if action == "finish":
            raise sqlite3.OperationalError("disk I/O error")
        return real(self, action, event, **kwargs)

    monkeypatch.setattr(Repository, "record_model_event", finish_lost)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert len(first.calls) == 1
    monkeypatch.setattr(Repository, "record_model_event", real)
    with env.repository.connection() as connection:
        (status,) = connection.execute(
            "SELECT status FROM model_call_receipts WHERE owner_kind = 'router_decision'").fetchone()
    assert status == "started"
    # A restart: a fresh runtime that remembers nothing in flight.
    second = _PricedDecider(choice=first_option)
    env.policy = policy_for(env.vault, env.repository, session_id=env.session_id, clock=env.clock,
                            runtime=fake_runtime(decider=second), serve=True)
    run(env)
    assert second.calls == []
    later = [row for row in rows(env) if row["policy"] == "router_mixture_v1"][1:]
    assert later and all(row["detail_json"]["mixture"]["models"]["decider"]["status"] == "spend" for row in later)


def test_a_json_repair_is_admitted_as_its_own_request(tmp_path, monkeypatch):
    # Codex review F4: the production chat provider answers malformed JSON
    # and its transport asks again (a JSON repair) inside one structured
    # operation. The repair is a physical request of its own, admitted by
    # the daily guard: the first request's reservation leaves no room for
    # it, so it is never sent and the LLM's share goes to the rule.
    from learnloop.ai.providers import openai_chat
    from learnloop.ai.providers.openai_chat import OpenAIChatProviderClient
    from learnloop.clock import utc_now_iso
    from learnloop.config import AIProviderConfig
    from learnloop.daily_plan.router_runtime import RouterSpend

    from tests.openai_fakes import install_fake_openai

    monkeypatch.setattr(openai_chat, "_sleep", lambda _seconds: None)
    monkeypatch.setenv("ROUTER_TEST_KEY", "test-key-not-a-credential")
    fake = install_fake_openai(monkeypatch, "not json", "still not json")
    client = OpenAIChatProviderClient(
        "metered_chat",
        AIProviderConfig(type="openai_chat", model="m", base_url="https://example.invalid",
                         api_key_env="ROUTER_TEST_KEY"),
    )
    # $1 a million tokens: a request (its prompt plus 16,384 output tokens)
    # reserves about $0.02, so the cap holds one request, not two.
    toml = ("[router]\nmax_daily_cost_usd = 0.03\n[router.weights]\nstaged = 0.0\ndecider = 0.0\nllm = 1.0\n"
            "[ingest.cost_pause.prices]\nmetered_chat = 1.0\n")
    env = mixture_env(tmp_path, fake_runtime(llm=client), toml=toml)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    assert sum(len(instance.requests) for instance in fake.instances) == 1
    (row,) = [row for row in rows(env) if row["policy"] == "router_mixture_v1"]
    assert row["detail_json"]["mixture"]["models"]["llm"]["status"] == "spend"
    assert RouterSpend().spent_today(env.repository, env.vault.config, utc_now_iso()) <= 0.03


# -- the why ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("component", ["staged", "decider", "llm", "uniform"])
def test_every_mixture_why_is_plain(component):
    text, kind = why.model_why(component, "Eigenvalues again, before it slips.", option_count=4,
                               rationale="Your last two answers on this slipped.", rationale_shown=component == "llm")
    body = text.replace(why.MODEL_MARK, "").strip()
    assert why.jargon_in(body) == [], text
    assert kind == {"staged": "computed", "decider": "model_no_rationale", "llm": "model_written",
                    "uniform": "computed"}[component]
    if component == "decider":
        assert text.startswith("LearnLoop's model picked this among 4 close options.")
    if component == "uniform":
        assert text.startswith("Picked to vary the order today.")
    if component == "llm":
        assert text.startswith(why.MODEL_MARK)


def test_every_details_line_is_plain():
    for status in ("mixture", "not_ready", "irreversible", "single_option"):
        for component in ("staged", "decider", "llm", "uniform"):
            for reasons in ({}, {"decider": "timeout"}, {"llm": "spend"}, {"decider": "failed", "llm": "invalid"}):
                text = why.mixture_details(
                    {"decided_by": status, "drawn_component": component, "fallback_reasons": reasons,
                     "rationale_hidden": True, "evidence_labels": ["your answer on Bases on 2026-10-12 (correct)"]},
                    propensity=0.34, decision_ref=None,
                )
                assert why.jargon_in(text) == [], text
    assert why.jargon_in(why.FOLLOWUP_WAITS) == []


@pytest.mark.parametrize("rationale, cited, reason", [
    ("Your answers on this topic slipped twice.", ["att_1"], None),
    ("", [], "empty"),
    ("One. Two. Three. Four.", [], "too_long"),
    ("The staged lane picked this probe.", [], "jargon"),
    ("You have a 40% chance of passing.", [], "probability"),
    ("Your answer slipped.", ["att_unknown"], "unknown_evidence"),
])
def test_the_rationale_guard(rationale, cited, reason):
    assert why.rationale_guard(rationale, cited, {"att_1"}) == reason


def test_a_drawn_llm_pick_shows_its_rationale_and_its_cited_answers(tmp_path):
    def cited(request):
        answer = FakeLLM.default_answer(request)
        refs = options_in(request.prompt)
        answer["choose_block"] = [{"id": refs[0], "probability": 1.0}]
        ids = [line.split(":", 1)[0].strip("- ").strip() for line in request.prompt.splitlines()
               if line.startswith("- att_")]
        answer["evidence_ids"] = ids[:1]
        answer["rationale"] = "Your recent answers here slipped, so another short round helps."
        return answer

    from tests.router_model_fakes import seed_with_first_uniform

    # Pin the first stage to the LLM's branch: staged and decider weights 0.
    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=cited),
                                             seed=seed_with_first_uniform(at_least=0.12)),
                      toml="[router.weights]\nstaged = 0.0\ndecider = 0.0\nllm = 1.0\n")
    run(env)
    record = advance(env, serve=False)[0]
    written = [block for block in record.blocks if block.chosen.get("why_kind") == "model_written"]
    assert written
    block = written[0]
    assert block.chosen["why"].startswith(why.MODEL_MARK)
    from learnloop.daily_plan.view import _why_details

    details = _why_details(block)
    assert "second model" in details and "Receipt: learnloop router log --decision" in details


# -- G8 at the successor, on the owner's working vaults' backup copies ------------------------------


@pytest.mark.parametrize("fixture", ("linear_algebra", "probability", "arxiv_v2"))
def test_the_switches_at_the_successor_serve_their_predecessors_on_fixture_copies(tmp_path, monkeypatch, fixture):
    """``router.enabled = false`` at mvp-0.24 serves mvp-0.22's plan, and
    ``router.mode = "staged"`` serves mvp-0.23's (block sequence and every
    ``block_chosen`` detail apart from ids and the card's hash, which names
    the version), on backup-API copies."""

    from pathlib import Path

    from learnloop.db.copies import copy_tree_with_databases

    from tests.helpers import append_config_toml, set_algorithm_version
    from tests.test_router_r2a_serving import _plan_trace

    fixtures = Path(__file__).resolve().parents[1] / "fixtures"
    if not (fixtures / fixture / "state.sqlite").exists():
        pytest.skip(f"{fixture} fixture absent")
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)

    def trace(name: str, version: str, toml: str | None):
        root = tmp_path / name
        copy_tree_with_databases(fixtures / fixture, root)
        set_algorithm_version(type("Paths", (), {"root": root})(), version)
        if toml:
            append_config_toml(root, toml)
        out = []
        for lane, chosen_by, items, detail in _plan_trace(root):
            router = {key: value for key, value in (detail.get("router") or {}).items() if key != "card_hash"}
            out.append((lane, chosen_by, items, {**detail, **({"router": router} if router else {})}))
        return out

    pre = trace("pre", "mvp-0.22", None)
    off = trace("off", B, "[router]\nenabled = false\n")
    assert pre and pre == off
    a = trace("a", ROUTER_STAGED_FRAME_ALGORITHM_VERSION, None)
    staged = trace("staged", B, '[router]\nmode = "staged"\n')
    assert a and a == staged
