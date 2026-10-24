"""Desktop "Continue with ChatGPT" RPCs and the Settings payload block."""
from __future__ import annotations

import json
import time

import pytest

from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import EmptyParams
from learnloop_sidecar.handlers import chatgpt_plan as rpc
from learnloop_sidecar.handlers.settings import get_settings
from learnloop_sidecar.registry import METHOD_REGISTRY

from tests.chatgpt_plan_fakes import complete_browser_flow, fake_chatgpt
from tests.helpers import create_basic_vault

RPCS = (
    "chatgpt_plan_status",
    "chatgpt_plan_signin_start",
    "chatgpt_plan_signin_cancel",
    "chatgpt_plan_signout",
    "chatgpt_plan_acknowledge_welcome",
    "chatgpt_plan_resume",
)


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setattr(rpc, "ATTEMPTS", rpc.SignInAttempts())


@pytest.fixture
def server(monkeypatch):
    with fake_chatgpt() as fake:
        original = PlanSession.begin_sign_in

        def against_fake(self, **kwargs):
            return original(self, **{**kwargs, "issuer": fake.issuer, "port": 0})

        monkeypatch.setattr(PlanSession, "begin_sign_in", against_fake)
        yield fake


def _wait_for(ctx, status: str) -> dict:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        payload = rpc.chatgpt_plan_status(ctx, EmptyParams())
        if payload["attempt"] and payload["attempt"]["status"] == status:
            return payload
        time.sleep(0.02)
    raise AssertionError(f"attempt never reached {status}")


def test_rpcs_are_registered():
    for name in RPCS:
        assert name in METHOD_REGISTRY


def test_sign_in_from_the_desktop_without_a_vault(server):
    ctx = SidecarContext()
    started = rpc.chatgpt_plan_signin_start(ctx, rpc.SignInStartParams())
    assert started["authorizeUrl"].startswith(server.issuer + "/api/accounts/authorize?")
    assert started["attempt"]["status"] == "waiting"
    complete_browser_flow(started["authorizeUrl"])
    done = _wait_for(ctx, "succeeded")
    assert done["state"] == "ready" and done["signedIn"] and done["welcomePending"]
    assert done["manageUsageUrl"] == "https://chatgpt.com/settings/usage"
    assert "access-" not in json.dumps(done)
    acknowledged = rpc.chatgpt_plan_acknowledge_welcome(ctx, EmptyParams())
    assert acknowledged["welcomePending"] is False
    out = rpc.chatgpt_plan_signout(ctx, EmptyParams())
    assert out["signedIn"] is False and out["signout"]["revoked"] is True


def test_cancel_and_failure_are_reported(server):
    ctx = SidecarContext()
    rpc.chatgpt_plan_signin_start(ctx, rpc.SignInStartParams())
    cancelled = rpc.chatgpt_plan_signin_cancel(ctx, EmptyParams())
    assert cancelled["cancelled"] is True
    assert cancelled["attempt"]["status"] == "cancelled"  # the reply already reports the end
    assert _wait_for(ctx, "cancelled")["attempt"]["error"]["code"] == "cancelled"
    server.deny = True
    started = rpc.chatgpt_plan_signin_start(ctx, rpc.SignInStartParams())
    complete_browser_flow(started["authorizeUrl"])
    assert _wait_for(ctx, "failed")["attempt"]["error"]["code"] == "access_denied"


def test_resume_clears_a_pause(server):
    ctx = SidecarContext()
    started = rpc.chatgpt_plan_signin_start(ctx, rpc.SignInStartParams())
    complete_browser_flow(started["authorizeUrl"])
    _wait_for(ctx, "succeeded")
    PlanSession().note_usage_limit(code="subscription_sharing_usage_limit_exceeded", request_id="r")
    assert rpc.chatgpt_plan_status(ctx, EmptyParams())["state"] == "usage_exhausted"
    assert rpc.chatgpt_plan_resume(ctx, EmptyParams())["state"] == "ready"


def test_settings_payload_lists_plan_profiles_and_their_routes(tmp_path, server):
    root = tmp_path / "vault"
    create_basic_vault(root)
    config = root / "learnloop.toml"
    text = config.read_text(encoding="utf-8").replace(
        "[ai.routing]\n", '[ai.routing]\nsource_query_rewrite = "chatgpt"\n', 1)
    # The template already holds [ai.providers.chatgpt] (plan-first transport T1).
    text = text.replace('[ai.providers.chatgpt]\ntype = "chatgpt_plan"\nmodel = "gpt-5.6-sol"\n',
                        f'[ai.providers.chatgpt]\ntype = "chatgpt_plan"\nmodel = "gpt-test-fast"\n'
                        f'base_url = "{server.base_url}"\n', 1)
    config.write_text(text, encoding="utf-8")
    ctx = SidecarContext()
    ctx.load(root, maintenance=False)
    settings = get_settings(ctx, EmptyParams())
    block = settings["chatgptPlan"]
    assert block["state"] == "signed_out" and block["usingPlan"] is True
    # Plan-first transport T1: the code-default tiers are listed too.
    assert {entry["name"] for entry in block["profiles"]} >= {"chatgpt", "chatgpt_low", "chatgpt_medium"}
    profile = next(entry for entry in block["profiles"] if entry["name"] == "chatgpt")
    assert profile["routes"] == ["source_query_rewrite"]
    assert "chatgpt" in {provider["name"] for provider in settings["ai"]["providers"]}
