"""The E0 re-plan (owner 2026-10-22, orchestrator ruling): the Messages API roles, no Codex, fakes only.

E0's LLM roles post directly to the Anthropic Messages API through the
experiment-only ``anthropic_api`` transport: a body grammar with no
``tools``, one admitted POST per request at its hard maximum charge, usage
from the response, the key in one header only, allowlisted errors. Two
different labellers and a different adjudicator; the system arms'
production source routes go to OpenRouter's Claude Haiku 5.5 (price pending
verification); E0 makes no Codex call at all.

No network: a socket guard refuses any connection; every HTTP exchange goes
to an in-process fake server."""
from __future__ import annotations

import json
import logging
import socket
from types import SimpleNamespace

import pytest

from learnloop.experiments.contextual_embeddings import bank as B
from learnloop.experiments.contextual_embeddings import corpus as C
from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.adapters import HttpResponse
from learnloop.experiments.contextual_embeddings.anthropic_api import (
    ALLOWED_BODY_KEYS,
    AnthropicMessagesClient,
    BodyGrammarError,
    check_body,
)
from learnloop.experiments.contextual_embeddings.budget import E0BudgetExceeded, E0Ledger, E0ProviderFailure, Request
from learnloop.experiments.contextual_embeddings.callers import (
    Checkpoints,
    E0RequestGate,
    LiveRoleCaller,
    canary_models,
    estimate_input_tokens,
    role_cost,
)
from tests.e0_fakes import build_e0_vault, fake_respond

KEY = "sk-ant-test-key-not-real-0000000000"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("network attempted in an offline E0 test")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


class FakeMessagesServer:
    """The Messages API, in process: records every POST (url, headers, body)
    and answers from ``answer(body)`` or a queued list of statuses."""

    def __init__(self, *, answer=None, statuses=(), usage=True, model=None):
        self.posts = []
        self.answer = answer or (lambda body: {"questions": []})
        self.statuses = list(statuses)
        self.usage = usage
        self.model = model

    def post(self, url, *, headers, body, timeout):
        self.posts.append({"url": url, "headers": dict(headers), "body": json.loads(json.dumps(body))})
        if self.statuses:
            status = self.statuses.pop(0)
            if status != 200:
                return HttpResponse(status, None, "req_err")
        payload = {"type": "message", "model": self.model or body["model"], "stop_reason": "end_turn",
                   "content": [{"type": "thinking", "thinking": ""},
                               {"type": "text", "text": json.dumps(self.answer(body))}]}
        if self.usage:
            payload["usage"] = {"input_tokens": 120, "output_tokens": 40}
        return HttpResponse(200, payload, "req_ok")


def _client(role, server, *, environ=None):
    return AnthropicMessagesClient(pins.ROLE_PINS[role], environ=environ or {"ANTHROPIC_API_KEY": KEY},
                                   transport=server, sleep=lambda _seconds: None)


def _entries(ledger):
    return sorted(json.loads(ledger.path.read_text(encoding="utf-8"))["entries"].values(),
                  key=lambda entry: entry["reserved_at"])


def _call(tmp_path, role, server, *, prompt="prompt_version: e0-writer-v1\n{\"context\": {\"seeds\": []}}",
          result_model=B.WrittenQuestions, ledger=None):
    from learnloop.ai.execution import gate_model_requests

    ledger = ledger or E0Ledger(tmp_path / "ledger")
    pin = pins.ROLE_PINS[role]
    client = _client(role, server)
    with gate_model_requests(E0RequestGate(ledger, pin, arm=role)):
        result = client.structured(purpose=f"e0_{role}", prompt=prompt, result_model=result_model,
                                   max_tokens=pin.max_output_tokens)
    return result, ledger, client


# -- the body grammar ---------------------------------------------------------------------


def test_every_body_is_within_the_grammar_and_never_carries_tools(tmp_path):
    server = FakeMessagesServer()
    _call(tmp_path, "writer", server)
    [post] = server.posts
    assert set(post["body"]) == {"model", "max_tokens", "system", "messages"} <= ALLOWED_BODY_KEYS
    assert "tools" not in post["body"] and "temperature" not in post["body"]
    assert post["url"] == "https://api.anthropic.com/v1/messages"
    assert post["body"]["messages"] == [{"role": "user", "content": post["body"]["messages"][0]["content"]}]
    assert post["headers"]["anthropic-version"] == "2026-10-21"
    base = {"model": "claude-haiku-5-5", "max_tokens": 10, "messages": [{"role": "user", "content": "x"}]}
    for bad in ({**base, "tools": []}, {**base, "tool_choice": {"type": "auto"}}, {**base, "mcp_servers": []},
                {**base, "output_config": {}}, {**base, "messages": [*base["messages"], *base["messages"]]},
                {**base, "messages": [{"role": "user", "content": [{"type": "text", "text": "x"}]}]},
                {**base, "max_tokens": True}, {**base, "system": ["x"]}):
        with pytest.raises(BodyGrammarError):
            check_body(bad)
    check_body(base)
    # A body outside the grammar is refused before anything is sent.
    client = _client("tutor", server)
    with pytest.raises(BodyGrammarError):
        client.send({**base, "tools": [{"name": "bash"}]}, purpose="x", prompt_identity="x")
    assert len(server.posts) == 1


# -- admission equals the wire ------------------------------------------------------------


def test_each_post_is_admitted_first_at_its_hard_maximum_and_settled_from_usage(tmp_path):
    server = FakeMessagesServer(statuses=[529, 200])  # one transient failure, then success
    _result, ledger, _client_ = _call(tmp_path, "adjudicator", server, result_model=B.WrittenQuestions)
    entries = _entries(ledger)
    assert len(server.posts) == len(entries) == 2  # one admission per physical POST
    pin = pins.ROLE_PINS["adjudicator"]
    for post, entry in zip(server.posts, entries, strict=True):
        body = post["body"]
        wire = [body["system"], body["messages"][0]["content"]]
        assert body["max_tokens"] == pin.max_output_tokens
        assert float(entry["reserved_usd"]) == pytest.approx(
            role_cost(pin, estimate_input_tokens(wire), body["max_tokens"]))
    # The failed POST keeps its reservation; the answered one settles from its usage.
    assert entries[0]["actual_usd"] is None
    assert float(entries[1]["actual_usd"]) == pytest.approx(role_cost(pin, 120, 40))


def test_a_response_without_usage_keeps_the_whole_reservation(tmp_path):
    server = FakeMessagesServer(usage=False)
    _result, ledger, _client_ = _call(tmp_path, "tutor", server, result_model=B.WrittenQuestions)
    [entry] = _entries(ledger)
    assert entry["actual_usd"] is None and entry["status"] == "unknown_billing"


def test_a_prompt_that_could_pass_100k_tokens_is_admitted_at_haikus_long_rate(tmp_path):
    server = FakeMessagesServer()
    long_prompt = "prompt_version: e0-writer-v1\n{\"context\": {\"seeds\": []}} " + "x" * 120_000
    _result, ledger, _client_ = _call(tmp_path, "context", server, prompt=long_prompt)
    [entry] = _entries(ledger)
    pin = pins.ROLE_PINS["context"]
    body = server.posts[0]["body"]
    tokens = estimate_input_tokens([body["system"], body["messages"][0]["content"]])
    assert tokens > 100_000
    assert float(entry["reserved_usd"]) == pytest.approx((tokens * 0.50 + body["max_tokens"] * 2.50) / 1e6)


# -- the key and the errors ---------------------------------------------------------------


def test_the_key_is_in_one_header_only_and_errors_are_allowlisted(tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    server = FakeMessagesServer(statuses=[401])
    with pytest.raises(E0ProviderFailure) as raised:
        _call(tmp_path, "tutor", server)
    assert raised.value.classification == "auth" and raised.value.status_code == 401
    assert server.posts[0]["headers"]["x-api-key"] == KEY
    ledger_text = (tmp_path / "ledger" / "e0_spend_ledger.json").read_text(encoding="utf-8")
    assert KEY not in str(raised.value) and KEY not in ledger_text and KEY not in caplog.text
    assert KEY not in json.dumps(server.posts[0]["body"])
    # No key in the environment: refused before anything is sent.
    empty = FakeMessagesServer()
    from learnloop.ai.execution import gate_model_requests

    client = AnthropicMessagesClient(pins.ROLE_PINS["tutor"], environ={}, transport=empty)
    with gate_model_requests(E0RequestGate(E0Ledger(tmp_path / "gate"), pins.ROLE_PINS["tutor"])):
        with pytest.raises(E0ProviderFailure, match="auth"):
            client.send(client.body("s", "u", 16), purpose="x", prompt_identity="x")
    assert empty.posts == []


# -- the roles ----------------------------------------------------------------------------


def test_two_independent_labellers_a_different_adjudicator_and_no_codex_role():
    role = pins.ROLE_PINS
    # Relabel round (owner 2026-10-23, "Sonnet both + rubric"): both label passes
    # are Sonnet 5.5 (independent requests, own orders); the adjudicator differs.
    assert role["label_a"].model == role["label_b"].model == "claude-sonnet-5-5"
    for adjudicator in ("adjudicator", "judge_adjudicator"):
        assert role[adjudicator].model == "claude-opus-5-5"
        assert role[adjudicator].model not in {role["label_a"].model, role["label_b"].model}
    assert role["judge_adjudicator"].model not in {role["judge_a"].model, role["judge_b"].model}
    assert role["writer"].model == "claude-sonnet-5-5"  # spec §5.1's strong writer
    for name in ("context", "tutor", "judge_a", "judge_b"):
        assert role[name].model == "claude-haiku-5-5"
    for name, pin in role.items():
        assert pin.billing == "metered" and pin.transport != "codex_sdk", name
        if pin.transport == "anthropic_api":
            assert pin.price_verified.source_url == "https://platform.claude.com/docs/en/about-claude/pricing"
            assert pin.price_verified.checked_on == "2026-10-22" and pins.price_problem(pin) is None
    assert (role["context"].input_price_per_million, role["context"].output_price_per_million) == (0.10, 0.50)
    assert role["context"].prices_for(100_001) == (0.50, 2.50)
    assert (role["writer"].input_price_per_million, role["writer"].output_price_per_million) == (2.0, 10.0)
    assert (role["adjudicator"].input_price_per_million, role["adjudicator"].output_price_per_million) == (4.0, 20.0)
    # The OpenRouter Haiku route of the system arms, verified by the orchestrator on 2026-10-22.
    verifier = role["system_verifier"]
    assert verifier.model == "anthropic/claude-haiku-5.5" and pins.price_problem(verifier) is None
    assert (verifier.price_verified.source_url, verifier.price_verified.checked_on) == (
        "https://openrouter.ai/anthropic/claude-haiku-5.5/pricing", "2026-10-22")
    assert (verifier.input_price_per_million, verifier.output_price_per_million) == (0.10, 0.50)
    assert verifier.prices_for(100_001) == (0.50, 2.50)  # still admitted at Anthropic's >100k rate


def test_the_paid_run_refuses_any_codex_role(monkeypatch):
    from learnloop.experiments.contextual_embeddings.boundary import CodexRoleRemaining, require_no_codex_roles

    require_no_codex_roles()
    codex = pins.RolePin("tutor", "codex_low", "codex_sdk", "gpt-5.6-sol", None, "subscription",
                         "answers_verification", 1, 0.0, 0.0, "x", "v")
    with pytest.raises(CodexRoleRemaining, match="tutor"):
        require_no_codex_roles({**pins.ROLE_PINS, "tutor": codex})


def test_the_plan_has_zero_codex_requests_and_the_paid_ledger_refuses_any(tmp_path):
    from learnloop.experiments.contextual_embeddings.budget import authorized_ledger
    from learnloop.experiments.contextual_embeddings.runner import dry_run

    paths, _repository = build_e0_vault(tmp_path)
    plan = dry_run([paths.root], environ={})
    assert plan["subscription_requests"]["planned"] == 0 and plan["subscription_requests"]["allowance"] == 0
    assert all(row["billing"] == "metered" for row in plan["llm_roles"])
    system_llm = [row for row in plan["system_arms"] if row.get("kind") == "system_llm"]
    assert system_llm and all(row["billing"] == "metered" and row["model"] == "anthropic/claude-haiku-5.5"
                              and row["price_status"] == "verified" for row in system_llm)
    assert plan["prices"]["unverified"] == {"embeddings": [], "roles": []}
    ledger = authorized_ledger([paths.root], plan["run_id"])
    with pytest.raises(E0BudgetExceeded, match="subscription request allowance 0"):
        ledger.reserve(Request(category="labels_audits", provider="codex", route="gpt", purpose="x",
                               billing="subscription"))


# -- the service copies' production source routes -----------------------------------------


def test_the_service_copies_route_their_source_routes_to_openrouter_haiku(tmp_path):
    import tomllib

    from learnloop.experiments.contextual_embeddings.system_arms import (
        SystemRequestGate,
        make_service_copy,
        open_service,
        route_source_llm_on_copy,
    )

    paths, _repository = build_e0_vault(tmp_path)
    root = make_service_copy(paths.root, tmp_path / "fixtures-local" / "service" / "r0")
    assert route_source_llm_on_copy(root) == {route: "e0_openrouter_haiku" for route in pins.SYSTEM_ARM_ROUTES}
    config = tomllib.loads((root / "learnloop.toml").read_text(encoding="utf-8"))
    assert {route: config["ai"]["routing"][route] for route in pins.SYSTEM_ARM_ROUTES} == {
        route: "e0_openrouter_haiku" for route in pins.SYSTEM_ARM_ROUTES}
    assert config["ai"]["providers"]["e0_openrouter_haiku"]["model"] == "anthropic/claude-haiku-5.5"
    handle = open_service(root)
    from learnloop.practice_index.paid import plan_route

    for route in pins.SYSTEM_ARM_ROUTES:
        assert plan_route(handle.vault, route).provider == "e0_openrouter_haiku"
    # Its verified price admits each request at its hard maximum, the >100k rate past 100k.
    ledger = E0Ledger(tmp_path / "ledger")
    gate = SystemRequestGate(ledger, handle.vault.config, arm="R0")
    metered = SimpleNamespace(provider_type="openrouter", provider_name="e0_openrouter_haiku",
                              model="anthropic/claude-haiku-5.5")
    verifier = pins.ROLE_PINS["system_verifier"]
    for prompt in ("p", "x" * 120_000):
        gate.settle(gate.admit(metered, purpose="verify", prompt=prompt, budget=100), {})
    short, long = _entries(ledger)
    assert float(short["reserved_usd"]) == pytest.approx(role_cost(verifier, estimate_input_tokens("p"), 100))
    tokens = estimate_input_tokens("x" * 120_000)
    assert float(long["reserved_usd"]) == pytest.approx((tokens * 0.50 + 100 * 2.50) / 1e6)


# -- the model canary ---------------------------------------------------------------------


def test_each_model_id_is_canaried_before_bulk_work_and_a_wrong_model_stops_the_run(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)
    server = FakeMessagesServer()
    caller = LiveRoleCaller(handle.root, handle.vault.config, E0Ledger(tmp_path / "ledger"),
                            checkpoints=Checkpoints(None), environ={"ANTHROPIC_API_KEY": KEY},
                            anthropic_transport=server)
    checked = canary_models(caller)
    assert set(checked) == {"claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"}
    assert len(server.posts) == 3 and all(post["body"]["max_tokens"] == 256 for post in server.posts)
    wrong = FakeMessagesServer(model="claude-other-model")
    caller = LiveRoleCaller(handle.root, handle.vault.config, E0Ledger(tmp_path / "ledger2"),
                            checkpoints=Checkpoints(None), environ={"ANTHROPIC_API_KEY": KEY},
                            anthropic_transport=wrong)
    with pytest.raises(E0ProviderFailure, match="contract"):
        canary_models(caller)


def test_a_role_call_goes_through_the_messages_api_transport(tmp_path):
    paths, _repository = build_e0_vault(tmp_path)
    handle = C.open_copy(paths.root)

    def answer(body):
        return fake_respond("label_a", body["messages"][0]["content"], B.LabelPass)

    server = FakeMessagesServer(answer=answer)
    caller = LiveRoleCaller(handle.root, handle.vault.config, E0Ledger(tmp_path / "ledger"),
                            checkpoints=Checkpoints(None), environ={"ANTHROPIC_API_KEY": KEY},
                            anthropic_transport=server)
    snapshot = C.build_snapshot(handle)
    question = B.freeze_context(B.BankQuestion("q1", "development", None, "writer", "explain", "intent_explain",
                                               "Why is the additive identity unique?"), snapshot)
    unit = snapshot.units[0]
    prompt = B.label_prompt(question, {"c1": B.label_context(snapshot, unit)}, 0)
    result = caller.call("label_a", prompt=prompt, result_model=B.LabelPass)
    assert isinstance(result, B.LabelPass)
    assert [post["body"]["model"] for post in server.posts] == ["claude-sonnet-5-5"]  # relabel round


def test_production_never_imports_the_messages_api_transport():
    from pathlib import Path

    import learnloop

    root = Path(learnloop.__file__).parent
    offenders = [str(path.relative_to(root)) for path in root.rglob("*.py")
                 if "experiments" not in path.parts and path.name != "experiments.py"
                 and "anthropic_api" in path.read_text(encoding="utf-8")]
    assert offenders == []


def test_the_paid_preflight_passes_with_every_pin_verified_zero_codex_and_the_lockdown(tmp_path):
    """Owner decision 2026-10-22 ($40 cap, models kept): the paid CLI's checks
    pass on a fresh plan, apart from the keys (absent in a dry run)."""

    from learnloop.experiments.contextual_embeddings.boundary import require_codex_lockdown, require_no_codex_roles
    from learnloop.experiments.contextual_embeddings.runner import dry_run, require_paid_authorization

    assert pins.E0_CAP_USD == 40.0
    # Re-split for the cumulative cap by the relabel round (2026-10-23).
    assert pins.ALLOCATION_USD == {"embeddings": 0.25, "drafting_context": 0.85, "labels_audits": 33.00,
                                   "answers_verification": 5.90}
    assert sum(pins.ALLOCATION_USD.values()) == pytest.approx(40.0)
    paths, _repository = build_e0_vault(tmp_path)
    plan = dry_run([paths.root], environ={})
    assert plan["totals"]["cap_usd"] == 40.0 and plan["totals"]["fits_cap"] and plan["totals"]["fits_allocations"]
    assert plan["prices"]["unverified"] == {"embeddings": [], "roles": []}
    assert plan["subscription_requests"]["planned"] == 0
    assert plan["budget"]["fits"] and plan["budget"]["carried_usd"] == 0.0
    require_paid_authorization(authorized=True, dry_run_ok=bool(plan["budget"]["fits"]),
                               unverified_prices=plan["prices"]["unverified"])
    require_no_codex_roles()
    assert require_codex_lockdown()["codex_lockdown"] == "active"
    assert set(plan["keys"].values()) == {"absent"}


# -- several env files and the preflight-only mode (owner, 2026-10-22) --------------------

FAKE = {"ANTHROPIC_API_KEY": "sk-ant-fake-value-one-1111111111", "OPENROUTER_API_KEY": "sk-or-fake-value-2222222222",
        "PERPLEXITY_API_KEY": "pplx-fake-value-3333333333", "VOYAGE_API_KEY": "pa-fake-value-4444444444"}


@pytest.fixture
def clean_environ(monkeypatch):
    """A process environment without the four key names (restored after)."""

    import os

    environ = {key: value for key, value in os.environ.items() if key not in FAKE}
    monkeypatch.setattr(os, "environ", environ)
    return environ


def _env(path, values):
    path.write_text("".join(f"{name}={value}\n" for name, value in values.items()), encoding="utf-8")
    return path


def test_several_env_files_load_by_name_and_a_conflict_is_refused_naming_the_variable_only(tmp_path,
                                                                                           clean_environ):
    from learnloop.experiments.contextual_embeddings.credentials import EnvFileError, load_env_files

    first = _env(tmp_path / "home.env", {"ANTHROPIC_API_KEY": FAKE["ANTHROPIC_API_KEY"]})
    second = _env(tmp_path / "repo.env", {"OPENROUTER_API_KEY": FAKE["OPENROUTER_API_KEY"],
                                          "ANTHROPIC_API_KEY": FAKE["ANTHROPIC_API_KEY"]})  # the same value twice
    availability = load_env_files([first, second], FAKE)
    assert availability == {"ANTHROPIC_API_KEY": "present", "OPENROUTER_API_KEY": "present",
                            "PERPLEXITY_API_KEY": "absent", "VOYAGE_API_KEY": "absent"}
    clean_environ.clear()
    conflicting = _env(tmp_path / "other.env", {"ANTHROPIC_API_KEY": "sk-ant-a-different-value-5555"})
    with pytest.raises(EnvFileError) as raised:
        load_env_files([first, conflicting], FAKE)
    message = str(raised.value)
    assert "ANTHROPIC_API_KEY" in message and FAKE["ANTHROPIC_API_KEY"] not in message
    assert "different-value" not in message and "ANTHROPIC_API_KEY" not in clean_environ  # nothing loaded
    twice = tmp_path / "twice.env"
    twice.write_text("VOYAGE_API_KEY=pa-one-value-0000\nVOYAGE_API_KEY=pa-two-value-9999\n", encoding="utf-8")
    with pytest.raises(EnvFileError, match="VOYAGE_API_KEY") as raised:
        load_env_files([twice], FAKE)
    assert "one-value" not in str(raised.value) and "two-value" not in str(raised.value)


def test_preflight_only_reports_names_and_checks_with_zero_network_and_no_value(tmp_path, clean_environ):
    from typer.testing import CliRunner

    from learnloop.cli import app

    paths, _repository = build_e0_vault(tmp_path)
    home = _env(tmp_path / "home.env", {"ANTHROPIC_API_KEY": FAKE["ANTHROPIC_API_KEY"]})
    repo = _env(tmp_path / "repo.env", {name: FAKE[name] for name in
                                        ("OPENROUTER_API_KEY", "PERPLEXITY_API_KEY", "VOYAGE_API_KEY")})
    command = ["experiments", "e0", "run", "--copy", str(paths.root), "--preflight-only", "--json",
               "--env-file", str(home), "--env-file", str(repo), "--anthropic-key-env", "ANTHROPIC_API_KEY"]
    result = CliRunner().invoke(app, command)
    assert result.exit_code == 0, result.output
    for value in FAKE.values():
        assert value not in result.output
    report = json.loads(result.output.strip().splitlines()[-1])
    assert report["ready"] is True and all(report["checks"].values()), report["checks"]
    assert report["keys"] == {name: "present" for name in FAKE}
    assert report["network_calls"] == 0
    assert report["codex"] == {"planned": 0, "allowance": 0}
    assert report["unverified_prices"] == {"embeddings": [], "roles": []}
    assert report["cap_usd"] == 40.0 and set(report["allocations"]) == set(pins.ALLOCATION_USD)
    assert report["copies_sha256"]["before"] == report["copies_sha256"]["after"]
    assert report["ledger"].endswith(f"contextual-embeddings/ledger/{report['run_id']}.ledger")
    assert not (tmp_path / "fixtures-local" / "contextual-embeddings" / "ledger").exists()  # nothing created
    # A key absent from both files: reported absent by name, not ready (exit 1), still no value printed.
    clean_environ.clear()
    result = CliRunner().invoke(app, command[:-6] + ["--env-file", str(repo)])
    assert result.exit_code == 1
    report = json.loads(result.output.strip().splitlines()[-1])
    assert report["keys"]["ANTHROPIC_API_KEY"] == "absent" and report["ready"] is False
    assert all(value not in result.output for value in FAKE.values())
