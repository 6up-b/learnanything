"""`learnloop ai …` commands and the doctor check for ChatGPT-plan routes."""
from __future__ import annotations

import json
import threading

import pytest
import tomlkit
from typer.testing import CliRunner

from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.cli import app
from learnloop.ops.doctor import run_doctor

from tests.chatgpt_plan_fakes import Reply, completed_events, complete_browser_flow, fake_chatgpt, sign_in
from tests.helpers import create_basic_vault

runner = CliRunner()


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)


@pytest.fixture
def server(monkeypatch):
    with fake_chatgpt() as fake:
        original = PlanSession.begin_sign_in

        def against_fake(self, **kwargs):
            return original(self, **{**kwargs, "issuer": fake.issuer, "port": 0})

        monkeypatch.setattr(PlanSession, "begin_sign_in", against_fake)
        yield fake


def _browser(monkeypatch, opened: list[str]):
    def open_browser(url):
        opened.append(url)
        threading.Thread(target=complete_browser_flow, args=(url,), daemon=True).start()
        return True

    monkeypatch.setattr("learnloop.cli.ai.webbrowser.open", open_browser)


def _vault(tmp_path, server, routes: dict[str, str]):
    root = tmp_path / "vault"
    create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    table = tomlkit.table()
    for key, value in {"type": "chatgpt_plan", "model": "gpt-test-fast", "base_url": server.base_url,
                       "timeout_seconds": 10}.items():
        table[key] = value
    document["ai"]["providers"]["chatgpt"] = table
    for task, name in routes.items():
        document["ai"]["routing"][task] = name
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def test_signin_opens_the_browser_saves_and_welcomes_once(server, monkeypatch):
    opened: list[str] = []
    _browser(monkeypatch, opened)
    result = runner.invoke(app, ["ai", "signin", "chatgpt"])
    assert result.exit_code == 0, result.output
    assert "Signed in with ChatGPT as learner@example.com." in result.output
    assert "You're using your ChatGPT plan." in result.output
    assert opened and opened[0].startswith(server.issuer + "/api/accounts/authorize?")
    assert "access-" not in result.output and "refresh-" not in result.output
    # The confirmation shows only the first time.
    again = runner.invoke(app, ["ai", "signin", "chatgpt"])
    assert again.exit_code == 0 and "You're using your ChatGPT plan." not in again.output


def test_signin_json_and_no_browser_prints_the_url_to_stderr(server, monkeypatch):
    def fake_echo_browser(url):
        raise AssertionError("--no-browser must not open a browser")

    monkeypatch.setattr("learnloop.cli.ai.webbrowser.open", fake_echo_browser)
    captured: dict[str, str] = {}
    original = PlanSession.begin_sign_in

    def begin(self, **kwargs):
        pending = original(self, **kwargs)
        captured["url"] = pending.authorize_url
        threading.Thread(target=complete_browser_flow, args=(pending.authorize_url,), daemon=True).start()
        return pending

    monkeypatch.setattr(PlanSession, "begin_sign_in", begin)
    result = runner.invoke(app, ["ai", "signin", "chatgpt", "--no-browser", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["ok"] and payload["plan_usage_enabled"] and payload["client_id"] == "oaiapp_test_client"
    assert captured["url"] in result.stderr


def test_declined_signin_exits_nonzero(server, monkeypatch):
    server.deny = True
    _browser(monkeypatch, [])
    result = runner.invoke(app, ["ai", "signin", "chatgpt", "--json"])
    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"] == "access_denied"


def test_status_models_resume_and_signout(server, monkeypatch, tmp_path):
    status = runner.invoke(app, ["ai", "status", "chatgpt", "--json"])
    assert json.loads(status.stdout)["state"] == "signed_out"
    sign_in(PlanSession(), server)
    vault = _vault(tmp_path, server, {"source_query_rewrite": "chatgpt", "source_rerank": "chatgpt"})
    status = json.loads(runner.invoke(app, ["ai", "status", "chatgpt", "--vault", str(vault), "--json"]).stdout)
    assert status["state"] == "ready" and status["email"] == "learner@example.com"
    # Plan-first transport T1: the code-default tiers are plan profiles too.
    profile = next(entry for entry in status["profiles"] if entry["name"] == "chatgpt")
    assert profile["ready"]
    assert profile["routes"] == ["source_query_rewrite", "source_rerank"]
    assert "access-" not in json.dumps(status)

    models = runner.invoke(app, ["ai", "models", "chatgpt", "--vault", str(vault), "--profile", "chatgpt", "--json"])
    assert [model["slug"] for model in json.loads(models.stdout)["models"]] == ["gpt-test-fast", "gpt-test-pro"]

    PlanSession().note_usage_limit(code="subscription_sharing_usage_limit_exceeded", request_id=None)
    paused = json.loads(runner.invoke(app, ["ai", "status", "chatgpt", "--json"]).stdout)
    assert paused["state"] == "usage_exhausted" and paused["paused_until"]
    resumed = json.loads(runner.invoke(app, ["ai", "resume", "chatgpt", "--json"]).stdout)
    assert resumed["state"] == "ready"

    out = runner.invoke(app, ["ai", "signout", "chatgpt", "--json"])
    assert json.loads(out.stdout)["revoked"] is True
    assert json.loads(runner.invoke(app, ["ai", "status", "chatgpt", "--json"]).stdout)["state"] == "signed_out"


def test_unknown_provider_is_refused():
    result = runner.invoke(app, ["ai", "status", "claude"])
    assert result.exit_code != 0


def test_latency_dry_run_then_a_timed_run(server, tmp_path):
    sign_in(PlanSession(), server)
    vault = _vault(tmp_path, server, {})
    dry = runner.invoke(app, ["ai", "latency", "--vault", str(vault), "--provider", "chatgpt", "--dry-run", "--json"])
    assert dry.exit_code == 0, dry.output
    (entry,) = json.loads(dry.stdout)["plan"]
    assert entry["billing"] == "subscription" and entry["calls"] == 3
    assert server.requests == []

    metered = runner.invoke(app, ["ai", "latency", "--vault", str(vault), "--provider", "openrouter", "--dry-run", "--json"])
    assert metered.exit_code == 1 and json.loads(metered.stdout)["error"] == "unknown_price"

    for index in (1, 2):
        server.replies.append(Reply(events=completed_events(json.dumps({"ok": True, "n": index}))))
    run = runner.invoke(app, ["ai", "latency", "--vault", str(vault), "--provider", "chatgpt", "--runs", "2", "--json"])
    assert run.exit_code == 0, run.output
    (row,) = json.loads(run.stdout)["results"]
    assert row["ok_calls"] == 2 and row["seconds"]["median"] >= 0
    assert all(call["seconds_to_first_event"] is not None for call in row["runs"])
    assert row["charged"]["calls"] == 2


def test_doctor_warns_when_a_route_uses_a_plan_this_machine_cannot_serve(server, tmp_path):
    vault = _vault(tmp_path, server, {"source_query_rewrite": "chatgpt"})
    # Plan-first transport T1: every vault uses the plan, so the machine's
    # sign-in is checked under `doctor --ai` (not reported for every vault).
    assert "ai:chatgpt_plan_signed_out" not in {issue.code for issue in run_doctor(vault).issues}
    codes = {issue.code for issue in run_doctor(vault, ai=True).issues}
    assert "ai:chatgpt_plan_signed_out" in codes
    sign_in(PlanSession(), server)
    codes = {issue.code for issue in run_doctor(vault, ai=True).issues}
    assert not {code for code in codes if code.startswith("ai:chatgpt_plan")}


def test_doctor_ignores_an_unrouted_plan_profile(server, tmp_path):
    from learnloop.config.schema import DEFAULT_SERVING_TASK_ROUTES

    # Every route the code defaults put on the plan moved elsewhere.
    vault = _vault(tmp_path, server, {task: "openrouter" for task in DEFAULT_SERVING_TASK_ROUTES})
    path = vault / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["ai"]["active_provider"] = "openrouter"
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    codes = {issue.code for issue in run_doctor(vault, ai=True).issues}
    assert not {code for code in codes if code.startswith("ai:chatgpt_plan")}


# -- Codex review (2026-10-12): one dollar cap across every metered provider --


class _MeteredProbe:
    """A metered stand-in that answers the latency probe and reports the planned usage."""

    provider_type = "openrouter"

    def __init__(self, name: str) -> None:
        from learnloop.ai.usage import TokenUsage

        self.provider_name = name
        self.model = "metered-test"
        self._usage = TokenUsage()
        self.calls = 0

    def supports(self, capability: str) -> bool:
        from learnloop.ai.transport import BOUNDED_STRUCTURED_COMPLETION, STRUCTURED_COMPLETION

        return capability in {STRUCTURED_COMPLETION, BOUNDED_STRUCTURED_COMPLETION}

    def complete(self, request):
        import re

        from learnloop.ai.usage import TokenUsage

        self.calls += 1
        self._usage = TokenUsage(input_tokens=400, output_tokens=64)
        index = int(re.search(r"probe (\d+)", request.prompt).group(1))
        return request.result_model.model_validate({"ok": True, "n": index})

    def consume_usage(self):
        from learnloop.ai.usage import TokenUsage

        usage, self._usage = self._usage, TokenUsage()
        return usage


def _two_metered(tmp_path, server, monkeypatch, extra=("openrouter_b",)):
    import types

    vault = _vault(tmp_path, server, {})
    path = vault / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    # The probe asks for each profile's output budget under the shared policy
    # (T6 follow-up merge); a 64-token profile maximum keeps 464 tokens a call.
    document["ai"]["providers"]["openrouter"]["max_tokens"] = 64
    for name in extra:
        profile = tomlkit.table()
        for key, value in {"type": "openrouter", "model": f"metered/{name}", "api_key_env": "OPENROUTER_API_KEY",
                           "max_tokens": 64}.items():
            profile[key] = value
        document["ai"]["providers"][name] = profile
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    clients: dict[str, _MeteredProbe] = {}

    def client_for(_root, _config, name, **_kwargs):
        return clients.setdefault(name, _MeteredProbe(name))

    monkeypatch.setattr("learnloop.ai.routing.client_for_provider", client_for)
    monkeypatch.setattr("learnloop.ai.routing.runtime_for_provider",
                        lambda _root, _config, _name, **_kwargs: types.SimpleNamespace(ready=True, message="ready"))
    return vault, clients


def test_latency_keeps_every_metered_provider_inside_one_dollar_cap(server, tmp_path, monkeypatch):
    vault, clients = _two_metered(tmp_path, server, monkeypatch)
    # 464 tokens at $100/M is $0.0464 per call: one provider fits $0.05, two do not.
    args = ["ai", "latency", "--vault", str(vault), "--provider", "openrouter", "--provider", "openrouter_b",
            "--runs", "1", "--price-per-million", "100", "--max-cost-usd", "0.05", "--json"]
    dry = runner.invoke(app, [*args, "--dry-run"])
    assert dry.exit_code == 1, dry.output
    report = json.loads(dry.stdout)
    assert report["admissible"] is False and report["metered_estimated_usd"] == pytest.approx(0.0928)
    run = runner.invoke(app, args)
    assert run.exit_code == 1, run.output
    assert json.loads(run.stdout)["error"] == "over_budget"
    assert sum(client.calls for client in clients.values()) == 0  # refused before any call

    within = runner.invoke(app, [*args[:-5], "--price-per-million", "100", "--max-cost-usd", "0.1", "--json"])
    assert within.exit_code == 0, within.output
    rows = json.loads(within.stdout)["results"]
    assert [row["ok_calls"] for row in rows] == [1, 1]
    charged = sum(row["charged"]["estimated_usd"] for row in rows)
    assert charged == pytest.approx(0.0928) and charged <= 0.1


def test_latency_stops_a_later_metered_provider_once_the_shared_cap_is_spent(server, tmp_path, monkeypatch):
    vault, clients = _two_metered(tmp_path, server, monkeypatch)
    answer = _MeteredProbe.complete

    def overspend(self, request):
        from learnloop.ai.usage import TokenUsage

        result = answer(self, request)
        self._usage = TokenUsage(input_tokens=600, output_tokens=64)  # more than estimated
        return result

    monkeypatch.setattr(_MeteredProbe, "complete", overspend)
    # The plan fits ($0.0928 <= $0.095); the first provider's actual use leaves too little for the second.
    run = runner.invoke(app, ["ai", "latency", "--vault", str(vault), "--provider", "openrouter",
                              "--provider", "openrouter_b", "--runs", "1", "--price-per-million", "100",
                              "--max-cost-usd", "0.095", "--json"])
    assert run.exit_code == 0, run.output
    first, second = json.loads(run.stdout)["results"]
    assert first["ok_calls"] == 1
    assert second["ok_calls"] == 0 and "spend caps" in second["error"]
    assert clients["openrouter_b"].calls == 0
    total = first["charged"]["estimated_usd"] + (second["charged"]["estimated_usd"] or 0)
    assert total <= 0.095


def test_latency_admits_a_metered_plan_exactly_at_the_shared_cap(server, tmp_path, monkeypatch):
    # Review F8: three metered providers at $0.464 each total exactly $1.392.
    # A float sum gives 1.3920000000000001 and refused the plan; the shared
    # SpendBudget sums in decimal and admits the same three calls.
    vault, clients = _two_metered(tmp_path, server, monkeypatch, extra=("openrouter_b", "openrouter_c"))
    args = ["ai", "latency", "--vault", str(vault), "--provider", "openrouter", "--provider", "openrouter_b",
            "--provider", "openrouter_c", "--runs", "1", "--price-per-million", "1000", "--max-cost-usd", "1.392",
            "--json"]
    dry = runner.invoke(app, [*args, "--dry-run"])
    assert dry.exit_code == 0, dry.output
    report = json.loads(dry.stdout)
    assert report["admissible"] is True and report["reason"] is None
    assert report["metered_estimated_usd"] == 1.392
    run = runner.invoke(app, args)
    assert run.exit_code == 0, run.output
    payload = json.loads(run.stdout)
    assert [row["ok_calls"] for row in payload["results"]] == [1, 1, 1]
    assert sum(client.calls for client in clients.values()) == 3
    assert payload["metered_charged_usd"] == 1.392

    over = runner.invoke(app, [*args[:-3], "--max-cost-usd", "1.391", "--json"])
    assert over.exit_code == 1, over.output
    assert json.loads(over.stdout)["error"] == "over_budget"
    assert sum(client.calls for client in clients.values()) == 3  # the refused plan made no call
