"""Refactor B5: Decider and spend refusals, and the follow-up gate's decision, leave decision records (ADR-017).

Each failure is staged with fakes and read back through ``learnloop why --json`` (or ``provenance.read``): the rule
that refused, the limit it refused at, and never the exception's message or any learner text.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from learnloop import provenance, refusal_records
from learnloop.ai.decisions import ChoiceAnswer, ChoiceQuestion, DecisionResult
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEnvelope, SpendEstimate, SpendLimitExceeded
from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from tests.helpers import create_basic_vault

PLANTED = "the learner wrote xylophone-planted-secret"
QUESTION = ChoiceQuestion("Is the passage support for the claim?", {"yes": None, "no": None})


def _why(root: Path, target: str, *, kind: str | None = None) -> dict:
    args = ["why", target, "--json", "--vault", str(root), *(["--kind", kind] if kind else [])]
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "xylophone" not in result.output
    return json.loads(result.output)


def _kind(root: Path, target: str, kind: str) -> list[dict]:
    return [record for record in _why(root, target, kind=kind)["records"] if record["kind"] == kind]


def _all(path: Path, kind: str) -> list[provenance.DecisionRecord]:
    with connect(path, read_only=True) as connection:
        rows = connection.execute("SELECT trace_id FROM decision_records WHERE kind = ?", (kind,)).fetchall()
        return [record for trace in sorted({row[0] for row in rows})
                for record in provenance.read(connection, trace, kind=kind)]


@pytest.fixture
def basic(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    return paths, load_vault(paths.root), Repository.attach(paths.sqlite_path)


# -- spend.py: the refusal names its rule and limit ---------------------------------------------------------------


def test_a_spend_refusal_names_the_cap_and_its_numbers_and_keeps_its_message():
    budget = SpendBudget(SpendCaps(max_calls=0))
    with pytest.raises(SpendLimitExceeded) as caught:
        budget.check(SpendEstimate(calls=1, estimated_usd=0.0))
    assert str(caught.value) == "calls exceeds max_calls"
    assert (caught.value.rule, caught.value.limit, caught.value.used, caught.value.requested) == ("max_calls", 0, 0, 1)
    with pytest.raises(SpendLimitExceeded) as dollars:
        SpendBudget(SpendCaps(max_estimated_usd=0.01)).check(SpendEstimate(calls=1, estimated_usd=0.5))
    assert (dollars.value.rule, dollars.value.limit, dollars.value.requested) == ("max_estimated_usd", 0.01, 0.5)
    with pytest.raises(SpendLimitExceeded) as unknown:
        SpendBudget(SpendCaps()).check(SpendEstimate(calls=1))
    assert unknown.value.rule == "unknown_price"
    envelope = SpendEnvelope("daily_guard", 0.10)
    with pytest.raises(SpendLimitExceeded) as capped:
        envelope.reserve(__import__("decimal").Decimal("0.2"))
    assert (capped.value.rule, capped.value.limit, capped.value.scope) == ("envelope_cap", 0.10, "daily_guard")
    rule, facts = refusal_records.spend_rule(capped.value)
    assert rule == "envelope_cap" and facts == {"limit": 0.10, "used": 0.0, "requested": 0.2, "scope": "daily_guard"}
    assert refusal_records.spend_rule(SpendLimitExceeded("no rule given")) == ("spend_refused", {})


def test_route_rule_tells_no_decider_routed_from_a_route_not_ready():
    assert refusal_records.route_rule(None, {}) == ("no_decider_routed", None)
    assert refusal_records.route_rule("manual", {"manual": 1}) == ("no_decider_routed", "manual")
    assert refusal_records.route_rule("openrouter_decider", {}) == ("no_decider_routed", "openrouter_decider")
    assert refusal_records.route_rule("openrouter_decider", {"openrouter_decider": 1}) == (
        "decider_not_ready", "openrouter_decider")


# -- the Tier-1 Decider (the map's S11) ---------------------------------------------------------------------------


class _Decider:
    model = "perplexity/pplx-decider-test"
    provider_name = "fake_decider"
    settings = SimpleNamespace(price_per_million_input=0.2)

    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error
        self.calls = 0

    def decide(self, state, questions, *, purpose):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return DecisionResult(answers={name: ChoiceAnswer(choice="yes", probabilities={"yes": 0.8, "no": 0.2},
                                                          confidence=0.8) for name in questions},
                              model=self.model, input_tokens=1, output_tokens=1, cost=0.0, response_id="r",
                              provider="fake", raw={})


def _decide(vault, repository, *, config=None, **kwargs):
    from learnloop import decider_judgments

    return decider_judgments.decide(root=vault.root, config=config or vault.config, repository=repository,
                                    task="facet_span_support", state={"span": "s1"}, question=QUESTION,
                                    left_kind="facet", left_id="facet_1", **kwargs)


def test_a_disabled_judgment_leaves_a_record_where_it_left_no_row(basic):
    """Fail-first (S11): a disabled judgment returned before any write, so nothing said the Decider was never asked."""

    paths, vault, repository = basic
    config = vault.config.model_copy(update={
        "decider_routes": vault.config.decider_routes.model_copy(update={"facet_span_support": False})})
    with provenance.trace_scope("TRACE_DISABLED"):
        decision = _decide(vault, repository, config=config)
    assert decision.status == "disabled" and decision.judgment_id is None
    [record] = _kind(paths.root, "TRACE_DISABLED", "decider_judgment")
    assert (record["status"], record["rule"], record["decided_by"]) == ("excluded", "switch_off", "tier1_decider")
    assert record["facts"]["task"] == "facet_span_support" and record["detail_id"] is None


def test_no_decider_routed_and_a_spend_cap_each_name_their_rule(basic):
    paths, vault, repository = basic
    with provenance.trace_scope("TRACE_NONE"):
        unrouted = _decide(vault, repository, client_factory=lambda: None)
    assert unrouted.status == "unavailable"
    [record] = _kind(paths.root, "TRACE_NONE", "decider_judgment")
    assert record["status"] == "excluded" and record["rule"] in {"no_decider_routed", "decider_not_ready"}
    assert record["detail_table"] == "judgment_ledger" and record["detail_id"] == unrouted.judgment_id

    def capped(route, task, tokens):
        SpendBudget(SpendCaps(max_calls=0)).check(SpendEstimate(calls=1, estimated_usd=0.0))

    client = _Decider()
    with provenance.trace_scope("TRACE_SPEND"):
        refused = _decide(vault, repository, client_factory=lambda: client, admit=capped)
    assert refused.status == "refused" and client.calls == 0
    [record] = _kind(paths.root, "TRACE_SPEND", "decider_judgment")
    assert (record["status"], record["rule"]) == ("refused", "max_calls")
    assert record["facts"]["limit"] == 0 and record["facts"]["requested"] == 1
    assert record["facts"]["model"] == _Decider.model


def test_a_failed_call_keeps_its_class_and_frame_but_never_its_message(basic):
    """Fail-first (S11): the ledger's ``failed`` kept no exception at all."""

    paths, vault, repository = basic
    with provenance.trace_scope("TRACE_FAILED"):
        failed = _decide(vault, repository, client_factory=lambda: _Decider(error=RuntimeError(PLANTED)))
    assert failed.status == "failed"
    [record] = _kind(paths.root, "TRACE_FAILED", "decider_judgment")
    assert (record["status"], record["rule"], record["error_type"]) == ("failed", "request_failed", "RuntimeError")
    assert record["error_where"].startswith("tests.test_refusal_records:decide:")
    assert provenance.check_no_prose(provenance.DecisionRecord(**{
        key: (tuple(value) if key == "alternatives" else value) for key, value in record.items()})) == []


def test_an_answered_judgment_writes_no_record(basic):
    paths, vault, repository = basic
    with provenance.trace_scope("TRACE_OK"):
        decision = _decide(vault, repository, client_factory=lambda: _Decider())
    assert decision.status == "ok" and _kind(paths.root, "TRACE_OK", "decider_judgment") == []


def test_a_record_that_cannot_be_built_changes_no_judgment(basic, monkeypatch, caplog):
    paths, vault, repository = basic

    def broken(**_kwargs):
        raise RuntimeError(PLANTED)

    monkeypatch.setattr(refusal_records, "decider_record", broken)
    with caplog.at_level(logging.WARNING), provenance.trace_scope("TRACE_BROKEN"):
        decision = _decide(vault, repository, client_factory=lambda: _Decider(error=ValueError("x")))
    assert decision.status == "failed" and decision.judgment_id
    assert _kind(paths.root, "TRACE_BROKEN", "decider_judgment") == []
    assert "TRACE_BROKEN" in caplog.text and "xylophone" not in caplog.text


# -- the hint chooser: past bug B2 ("no Decider routed") ----------------------------------------------------------


@pytest.mark.parametrize("route, rule, models_on", [
    ("manual", "no_decider_routed", True), ("", None, True), ("", "models_off", False),
])
def test_past_bug_b2_no_decider_routed_now_leaves_a_record(tmp_path, monkeypatch, route, rule, models_on):
    """Fail-first: the owner's 2026-10-25 capture (B2), "choosing a help style changed nothing", was rooted in no
    Decider being routed, which left no row naming it; ``why item:<id>`` now answers with the rule. An empty route
    names the code-default Decider profile, which a vault without its key has but cannot use."""

    from learnloop_sidecar.context import SidecarContext
    from tests.hint_fakes import ITEM, WriterFake, hint_vault
    from tests.owner_capture_1025_helpers import _call, _press

    # The suite turns the hint models off (conftest); the owner's vault has them on and simply routes no Decider.
    if models_on:
        monkeypatch.delenv("LEARNLOOP_HINT_MODELS", raising=False)
    paths = hint_vault(tmp_path, config="[hints]\nchooser_enabled = true\n")
    toml = paths.root / "learnloop.toml"
    toml.write_text(toml.read_text().replace("[ai.routing]\n", f"[ai.routing]\nhint_chooser = \"{route}\"\n", 1))
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.hints_inline, ctx.hint_seed, ctx.hint_writer_client = True, "e", WriterFake()
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    _call(ctx, "practice.set_help_style", {"helpStyle": "let_me_struggle"})
    assert _press(ctx, session, "key-b2")["status"] == "ready"
    records = _kind(paths.root, f"item:{ITEM}", "decider_judgment")
    assert records, "no decision record names why the Decider did not choose"
    record = records[0]
    assert (record["status"], record["decided_by"]) == ("excluded", "hint_chooser")
    if rule == "models_off":
        assert record["rule"] == "models_off" and "provider" not in record["facts"]
    elif rule is not None:
        assert (record["rule"], record["facts"]["provider"]) == (rule, route)
    else:
        assert record["rule"] in {"no_decider_routed", "decider_not_ready"}
        assert record["facts"]["provider"] == "openrouter_decider"
    assert record["facts"]["help_style"] == "let_me_struggle" and record["facts"]["assist_id"]
    assert record["subject_kind"] == "item" and record["subject_id"] == ITEM


# -- the router's daily guard: a refused request leaves no call row -----------------------------------------------


class _Client:
    provider_name = "openrouter_decider"
    provider_type = "decider"
    model = "m"

    def __init__(self, usd: float) -> None:
        self.usd = usd
        self.sent = 0

    def estimated_cost(self, input_tokens):
        return self.usd

    def send(self):
        from learnloop.ai.execution import model_call, report_call_usage

        with model_call(self, purpose="router_decision", prompt="x"):
            self.sent += 1
            report_call_usage({"cost": self.usd})


def test_a_refused_router_request_leaves_a_record_though_no_call_row_exists(tmp_path):
    from learnloop.daily_plan.router_runtime import RouterSpend, SpendRefused
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()),
                      toml="[router]\nmax_daily_cost_usd = 0.30\n")
    late = _Client(0.45)
    with provenance.trace_scope("TRACE_GUARD"):
        with pytest.raises(SpendRefused) as caught, RouterSpend().metered(
                env.repository, env.vault.config, owner_kind="router_decision", owner_id="key_1"):
            late.send()
    assert late.sent == 0 and caught.value.rule == "router_daily_cap"
    with env.repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE owner_id = 'key_1'").fetchone()[0] == 0
    explanation = _why(env.vault.root, "TRACE_GUARD")
    [record] = [record for record in explanation["records"] if record["kind"] == "spend_admission"]
    assert (record["status"], record["rule"], record["decided_by"]) == ("refused", "router_daily_cap",
                                                                       "router_daily_guard")
    assert record["facts"]["limit_usd"] == 0.30 and record["facts"]["request_usd"] == pytest.approx(0.45)
    assert record["facts"]["spent_usd"] == 0.0 and record["facts"]["boundary_key"] == "key_1"
    assert record["facts"]["owner_kind"] == "router_decision" and explanation["model_calls"] == []


def test_a_guard_record_that_cannot_be_built_still_refuses(tmp_path, monkeypatch):
    from learnloop.daily_plan.router_runtime import RouterSpend, SpendRefused
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import fake_runtime

    env = mixture_env(tmp_path, fake_runtime(), toml="[router]\nmax_daily_cost_usd = 0.0\n")
    monkeypatch.setattr(refusal_records, "router_spend_record", lambda **_k: 1 / 0)
    late = _Client(0.01)
    with pytest.raises(SpendRefused), RouterSpend().metered(env.repository, env.vault.config,
                                                            owner_kind="router_decision", owner_id="k"):
        late.send()
    assert late.sent == 0 and _all(env.repository.sqlite_path, "spend_admission") == []


def _router_day(tmp_path: Path, name: str, *, write) -> tuple[list[tuple], list]:
    from tests.router_mixture_helpers import mixture_env, rows, run
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    runtime = fake_runtime(decider=FakeDecider(), llm=FakeLLM(), seed=lambda _key, _decision: "pinned-seed")
    env = mixture_env(tmp_path / name, runtime, toml="[router]\nmax_daily_cost_usd = 0.0\n")
    with pytest.MonkeyPatch.context() as patch:
        if write is not None:
            from learnloop.db.stores import provenance as store

            patch.setattr(refusal_records, "write", write)
            patch.setattr(store, "write_decision_without_waiting", write)  # the router guard's own writer
        run(env)
    served = [(row["chosen_ref"], row["propensity"], row["fallback"],
               {name: model["status"] for name, model in row["detail_json"]["mixture"]["models"].items()})
              for row in rows(env) if row["policy"] == "router_mixture_v1"]
    return served, _all(env.repository.sqlite_path, "spend_admission")


def test_refusals_forced_by_fakes_serve_the_same_with_or_without_their_records(tmp_path):
    """A record never changes a decision: the same refused day, its records written or dropped, serves the same."""

    recorded, records = _router_day(tmp_path, "recorded", write=None)
    dropped, none = _router_day(tmp_path, "dropped", write=lambda *_a, **_k: None)
    assert recorded == dropped and recorded
    assert records and none == []
    assert all(served[3]["decider"] == "spend" for served in recorded)
    assert {(record.status, record.rule) for record in records} == {("refused", "router_daily_cap")}


# -- the router ledger refusing a row (S13) -----------------------------------------------------------------------


def test_a_row_the_ledger_refuses_leaves_a_record_and_the_callers_work_commits(basic):
    from learnloop.db.stores.router import append_router_decision

    paths, _vault, repository = basic
    with provenance.trace_scope("TRACE_ROW"), repository.atomic(), repository.connection() as connection:
        assert append_router_decision(connection, {"id": "dec_1", "receipt_key": "rk_1", "decision_kind": "plan_block",
                                                   "design": "not_a_design", "policy": "p"}) is False
        connection.execute("CREATE TABLE callers_work (x)")
    with connect(paths.sqlite_path, read_only=True) as connection:
        assert connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'callers_work'").fetchone() is not None
        assert connection.execute("SELECT COUNT(*) FROM router_decisions").fetchone()[0] == 0
    [record] = _kind(paths.root, "decision:dec_1", "router_decision_row")
    assert (record["status"], record["rule"], record["error_type"]) == ("refused", "unregistered_design", "ValueError")
    assert record["facts"]["applied"] is True and record["facts"]["receipt_key"] == "rk_1"
    assert record["trace_id"] == "TRACE_ROW"


# -- the figure gate ----------------------------------------------------------------------------------------------


def test_the_figure_gate_records_its_first_refusal_once(basic):
    from learnloop.figure_admission import FiguresChanged, FiguresGate

    paths, _vault, repository = basic
    root = paths.root
    on = SimpleNamespace(root=root, config=SimpleNamespace(figures=SimpleNamespace(enabled=True)))
    off = SimpleNamespace(root=root, config=SimpleNamespace(figures=SimpleNamespace(enabled=False)))
    current = [on]
    gate = FiguresGate(on, lambda vault: "k", live_vault=lambda: current[0], repository=repository)
    with provenance.trace_scope("TRACE_FIG"):
        gate.check("figure_author")
        current[0] = off
        for _ in range(2):
            with pytest.raises(FiguresChanged):
                gate.check("figure_author")
    assert gate.rule == "figures_off" and gate.changed == "figures were switched off"
    [record] = _kind(root, "TRACE_FIG", "figure_admission")
    assert (record["status"], record["rule"], record["facts"]) == ("refused", "figures_off", {"purpose": "figure_author"})


# -- the follow-up gate's decision (B2's open item) and its value checks (S14) ------------------------------------


def test_the_follow_up_gates_decision_names_its_rule_arms_and_components(tmp_path):
    from learnloop.daily_plan.router_chooser import NO_INTERVENTION
    from learnloop.followup_run import router
    from tests.router_model_fakes import fake_runtime
    from tests.followup_router_helpers import _decide as decide_arm
    from tests.followup_router_helpers import _env, _workflow

    env, plan = _env(tmp_path, fake_runtime())
    row = _workflow(env)
    with provenance.trace_scope("TRACE_GATE"):
        decision = router.record_decision(env.vault, env.repository, row, decide_arm(env, plan, NO_INTERVENTION),
                                          clock=env.clock)
    [record] = _kind(env.vault.root, f"attempt:{row['source_attempt_id']}", "followup_gate")
    assert (record["status"], record["chosen_ref"], record["decided_by"]) == ("chosen", NO_INTERVENTION, "mixture")
    assert record["rule"].startswith("drawn_") and record["trace_id"] == "TRACE_GATE"
    assert (record["detail_table"], record["detail_id"]) == ("router_decisions", decision.decision_id)
    assert record["facts"]["logged"] is True and record["facts"]["workflow_id"] == "fw_test"
    assert record["facts"]["propensity"] == decision.propensity
    assert set(record["facts"]["components"]) >= {"decider", "llm"}
    assert {alt["ref"] for alt in record["alternatives"]} >= {router.ASK_NOW}
    assert all(alt["lost_by"] == "not_drawn" and 0 <= alt["p"] <= 1 for alt in record["alternatives"])


def test_a_hard_refusal_and_no_plan_each_leave_the_gates_record(tmp_path):
    from learnloop.diagnosis.causal_orchestrator import defer_probe_offer
    from learnloop.followup_run import router
    from learnloop.followup_serve import workflow as wf
    from tests.followup_serve_helpers import AuthorFake, author_clients, miss_with_rivals, rival_causes_vault, run_jobs

    vault, repository, _paths = rival_causes_vault(tmp_path / "plain")
    _result, outcome = miss_with_rivals(vault, repository)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    [record] = _all(repository.sqlite_path, "followup_gate")
    assert (record.status, record.rule, record.chosen_ref, record.decided_by) == ("chosen", "no_plan", router.ASK_NOW,
                                                                                  "no_plan")
    assert record.facts["logged"] is False and record.subject_id == wf.get(repository, outcome.workflow_id)[
        "source_attempt_id"]

    vault, repository, _paths = rival_causes_vault(tmp_path / "refused")
    _result, outcome = miss_with_rivals(vault, repository)
    factor = repository.unresolved_cause_factors_for_attempt(
        wf.get(repository, outcome.workflow_id)["source_attempt_id"])[0]
    defer_probe_offer(repository, factor_id=factor["id"])
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    [record] = _all(repository.sqlite_path, "followup_gate")
    assert (record.status, record.chosen_ref, record.decided_by) == ("refused", router.DECLINE, "refused")
    assert record.rule.startswith("learner_") and record.facts["refusals"] == [record.rule]


def test_a_value_check_that_fails_is_named_on_the_gates_record(tmp_path, monkeypatch):
    """Fail-first (S14): the logged causal check's failure became ``{}`` and a log line, with no stored trace."""

    import learnloop.diagnosis.causal_probe_coherence as coherence
    from tests.followup_serve_helpers import AuthorFake, author_clients, miss_with_rivals, rival_causes_vault, run_jobs

    def exploding(**_kwargs):
        raise LookupError(PLANTED)

    vault, repository, _paths = rival_causes_vault(tmp_path)
    _result, _outcome = miss_with_rivals(vault, repository)
    monkeypatch.setattr(coherence, "decide_probe", exploding)
    run_jobs(vault, repository, clients=author_clients(AuthorFake()))
    [record] = _all(repository.sqlite_path, "followup_gate")
    assert record.facts["value_check"] == "failed" and record.facts["value_check_error_type"] == "LookupError"
    assert record.facts["value_check_error_where"].startswith("tests.test_refusal_records:exploding:")
    assert "xylophone" not in json.dumps(record.as_dict())


def test_every_record_here_passes_the_prose_check_with_item_text_planted():
    row = {"id": "fw 1 with spaces", "learning_object_id": PLANTED, "source_attempt_id": "att_1"}
    decision = SimpleNamespace(chosen_ref="insert_now", decided_by="mixture", refused=False, reason="insert_now",
                               record={"mixture": {"pi": {"insert_now": 0.6, PLANTED: 0.4}, "drawn_component": "llm",
                                                   "models": {"llm": {"status": "answered", "error": PLANTED}}}},
                               observational={}, refusals=(), propensity=0.6, decision_id="d1")
    built = [
        refusal_records.followup_gate_record(row, decision, logged=True),
        refusal_records.decider_record(status="failed", rule="request_failed", route="tier1_decider", task="t",
                                       left_kind="input", left_id=PLANTED, facts={"note": PLANTED},
                                       error=RuntimeError(PLANTED)),
        refusal_records.router_row_record({"id": PLANTED, "receipt_key": PLANTED}, ValueError(PLANTED)),
        refusal_records.router_spend_record(cap_usd=5.0, spent_usd=1.0, request_usd=0.1, owner_kind="router_decision",
                                            owner_id=PLANTED, event={"purpose": PLANTED, "model": "m"}),
    ]
    for record in built:
        assert provenance.check_no_prose(record) == [], record
        assert "xylophone" not in json.dumps(record.as_dict())
