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
    (profile,) = status["profiles"]
    assert profile["name"] == "chatgpt" and profile["ready"]
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
    codes = {issue.code for issue in run_doctor(vault).issues}
    assert "ai:chatgpt_plan_signed_out" in codes
    sign_in(PlanSession(), server)
    codes = {issue.code for issue in run_doctor(vault).issues}
    assert not {code for code in codes if code.startswith("ai:chatgpt_plan")}


def test_doctor_ignores_an_unrouted_plan_profile(server, tmp_path):
    vault = _vault(tmp_path, server, {})
    codes = {issue.code for issue in run_doctor(vault).issues}
    assert not {code for code in codes if code.startswith("ai:chatgpt_plan")}
