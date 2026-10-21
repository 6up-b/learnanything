"""Every Codex turn LearnLoop starts is locked down (security stage 2026-10-21).

Found by a read-only investigation (docs/reviews/security-codex-tool-lockdown.md):

1. ``thread_start`` omitted ``approval_mode``, so the SDK started every thread
   ``on_request`` with the Guardian reviewer (a typed thread override beats the
   ``-c approval_policy="never"``), and the SDK's default handler ACCEPTS every
   command and file-change approval: an escalated command could run unsandboxed;
2. ``PaidCalls.call``, ``tutor_qa`` and every other caller that did not pass
   ``isolated=True`` ran on Codex in the vault directory with the user's whole
   Codex configuration (MCP servers, connectors, web search, sub-agents);
3. isolated turns still kept ``apply_patch``, sub-agents and ``request_user_input``;
4. the admission gate saw one call per turn, not sub-agent threads, Guardian
   reviews or tool round trips.

Now: one locked-down profile for every turn (empty temp cwd, permission
profile, every tool-bearing feature off, no MCP/apps/web, no sub-agents, no
user input); ``approval_mode=deny_all`` on thread and turn plus a decline-all
approval handler; a cached, fail-closed launch check over features, MCP and the
bundled model metadata; any non-text turn item, sub-agent, Guardian review or
second request refuses the answer and stops the turn; every thread's tokens
are counted. Fakes only: no model call.
"""

from __future__ import annotations

import ast
import json
import threading
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from learnloop.ai.errors import AIProviderUnavailable, CodexUnavailable
from learnloop.ai.execution import observe_model_calls
from learnloop.ai.providers.codex import SdkCodexClient, isolated_turn_overrides
from learnloop.ai.providers.codex_lockdown import catalog_pin_path
from learnloop.ai.transport import StructuredRequest, execute_structured_operation
from learnloop.config import CodexConfig
from learnloop.diagnosis.offline_review.judge import LinkJudgment

from tests.codex_cli_fakes import (
    FEATURES,
    FakeApprovalMode,
    FakeSdkClient,
    bundled_catalog,
    fake_codex_calls,
    stub_isolation_probe,
    write_fake_codex,
)
from tests.project_support import install_fake_codex_sdk

SRC = Path(__file__).resolve().parents[1] / "src"
try:
    from learnloop.ai.providers.codex_lockdown import LOCKDOWN_DISABLED_FEATURES as _OFF
except ImportError:  # before the security stage (fail-first run): the module did not exist
    _OFF = ("apps", "plugins", "multi_agent", "multi_agent_v2", "browser_use", "computer_use", "sleep_tool")
ANSWER = '{"links": []}'
TEXT_ITEMS = [{"type": "userMessage"}, {"type": "reasoning"}, {"type": "agentMessage", "text": ANSWER}]


def _lockdown():
    from learnloop.ai.providers import codex_lockdown

    return codex_lockdown


def _usage(total: int, last: int | None = None, *, input_tokens: int | None = None) -> SimpleNamespace:
    def breakdown(tokens: int) -> SimpleNamespace:
        inputs = input_tokens if input_tokens is not None else tokens - 10
        return SimpleNamespace(input_tokens=inputs, output_tokens=tokens - inputs, total_tokens=tokens,
                               cached_input_tokens=0, reasoning_output_tokens=0)

    return SimpleNamespace(total=breakdown(total), last=breakdown(total if last is None else last))


def _fake_sdk(monkeypatch, *, items=None, usage=None, on_run=None, approval_mode_in_sdk=True,
              thread_start_takes_approval=True, seams=True, raise_when_stopped=False) -> dict[str, Any]:
    """An ``openai_codex`` stand-in whose turn can emit notifications and server requests."""

    captured: dict[str, Any] = {"turns": [], "constructed": 0}

    class FakeTurn:
        id = "turn_parent"

        def __init__(self, codex):
            self.codex = codex
            self.stopped = threading.Event()

        def run(self):
            if on_run is not None:
                on_run(self.codex._client, self)
            if raise_when_stopped and self.stopped.is_set():
                raise RuntimeError("turn interrupted")
            return SimpleNamespace(final_response=ANSWER, items=list(TEXT_ITEMS if items is None else items),
                                   usage=usage)

        def interrupt(self):
            captured["interrupted"] = True
            self.stopped.set()

    class FakeThread:
        id = "thr_parent"

        def __init__(self, codex):
            self.codex = codex

        def turn(self, prompt, **kwargs):
            captured["turns"].append({"prompt": prompt, **kwargs})
            return FakeTurn(self.codex)

    class FakeCodex:
        def __init__(self, config):
            captured["constructed"] += 1
            captured["app_config"] = config.kwargs
            if seams:
                self._client = FakeSdkClient()
                captured["sdk_client"] = self._client

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def close(self):
            return None

        if thread_start_takes_approval:
            def thread_start(self, **kwargs):
                captured["thread_start"] = kwargs
                return FakeThread(self)
        else:
            def thread_start(self, *, cwd=None, model=None, service_name=None):
                captured["thread_start"] = {"cwd": cwd, "model": model, "service_name": service_name}
                return FakeThread(self)

    class SdkAppConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    from enum import Enum

    class ReasoningEffort(Enum):
        low = "low"
        medium = "medium"
        high = "high"

    module = ModuleType("openai_codex")
    module.Codex = FakeCodex
    module.CodexConfig = SdkAppConfig
    if approval_mode_in_sdk:
        module.ApprovalMode = FakeApprovalMode
    types_module = ModuleType("openai_codex.types")
    types_module.Personality = SimpleNamespace(pragmatic="pragmatic")
    types_module.ReasoningEffort = ReasoningEffort
    types_module.ReasoningSummary = SimpleNamespace(model_validate=lambda value: value)
    import sys

    monkeypatch.setitem(sys.modules, "openai_codex", module)
    monkeypatch.setitem(sys.modules, "openai_codex.types", types_module)
    return captured


def _client(tmp_path: Path, monkeypatch, *, program: str = "/usr/bin/codex-for-test") -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    (vault_root / "state.sqlite").write_text("VAULT", encoding="utf-8")
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=program), vault_root)
    stub_isolation_probe(monkeypatch, client, config_servers=("node_repl",))
    return client


def _plain(client, purpose: str = "tutor_qa"):
    return client.complete(StructuredRequest(purpose=purpose, prompt="p", result_model=LinkJudgment))


# -- 1. every call site that can start a Codex turn ---------------------------------------

def test_every_codex_turn_starter_in_the_source_passes_deny_all_inside_the_locked_down_turn():
    """A new call site that starts a Codex thread or turn without the profile fails here.

    The sweep itself (every module, SDK import aliases, turns on any name, the
    HTTP and subprocess launch paths) is
    ``tests/test_codex_lockdown_round2.py::test_every_codex_turn_app_server_and_transport_in_the_source_is_the_locked_down_one``
    (hardening round 2, L5: this test's earlier sweep had a textual prefilter,
    missed ``sdk.Codex(...)`` and saw ``.turn()`` only on a variable named
    ``thread``). What stays here: the order inside the one turn."""

    codex_py = "learnloop/ai/providers/codex.py"
    source = (SRC / codex_py).read_text(encoding="utf-8")
    # Inside it, the decline handler and notification tap go in before the thread starts.
    body = source[source.index("    def _run_verified_sdk_turn("):source.index("    def _report_turn_usage(")]
    assert body.index("install_on_sdk(codex, lockdown)") < body.index("codex.thread_start(")
    # The launch check runs before the turn, in the function that calls it.
    outer = source[source.index("    def _run_sdk_turn("):source.index("    def _run_verified_sdk_turn(")]
    assert outer.index("self._verified_isolated_overrides(") < outer.index("self._run_verified_sdk_turn(")
    # And the one turn path always asks for the isolated turn.
    run_structured = source[source.index("    def _run_structured("):source.index("    def _run_sdk_turn(")]
    # Round 3: a workspace is inlined and the turn itself never gets one (no shell on any route).
    assert "isolated=True, workspace=None" in run_structured and "self._inline_workspace(" in run_structured
    assert "self.vault_root\n" not in run_structured


# -- 2. every request shape: deny_all, the decline handler, the profile, never the vault ----


def _paid_call(client):
    from learnloop.ai.spend import SpendBudget, SpendCaps
    from learnloop.practice_index.paid import PaidCalls, PaidRoute

    route = PaidRoute(task="source_rerank", provider="codex", profile_type="codex_sdk", model="gpt-5.6-sol",
                      billing="subscription")
    calls = PaidCalls(route=route, budget=SpendBudget(SpendCaps()), price_per_million=None, repository=None,
                      owner_kind="test", owner_id="t")
    return calls.call(client, purpose="library_organizer", prompt="p", result_model=LinkJudgment,
                      output_tokens=512, metadata={})


SHAPES = {
    # The callers that never asked for isolation (finding 2).
    "tutor_qa": lambda client, tmp: execute_structured_operation(
        client, purpose="tutor_qa", prompt="p", result_model=LinkJudgment),
    "paid_calls": lambda client, tmp: _paid_call(client),
    "plain_request": lambda client, tmp: _plain(client, "passage_cue_judge"),
    # The ones that did.
    "isolated": lambda client, tmp: client.complete(StructuredRequest(
        purpose="blind_grading", prompt="p", result_model=LinkJudgment, isolated=True)),
    "workspace": lambda client, tmp: client.complete(StructuredRequest(
        purpose="diagnosis", prompt="p", result_model=LinkJudgment, workspace=tmp)),
}


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_every_request_runs_the_locked_down_profile_with_approvals_denied(tmp_path, monkeypatch, shape):
    captured = _fake_sdk(monkeypatch)
    client = _client(tmp_path, monkeypatch)
    workspace = tmp_path / "snapshot"
    workspace.mkdir()
    (workspace / "INDEX.md").write_text("# history\n", encoding="utf-8")
    SHAPES[shape](client, workspace)

    # Approvals: deny_all on the thread and on the turn.
    assert captured["thread_start"]["approval_mode"] is FakeApprovalMode.deny_all
    assert [turn["approval_mode"] for turn in captured["turns"]] == [FakeApprovalMode.deny_all]
    assert "sandbox" not in captured["thread_start"]
    # The SDK's accept-all handler is replaced by one that declines.
    sdk = captured["sdk_client"]
    assert sdk._approval_handler != FakeSdkClient._default_approval_handler
    assert sdk.server_request("item/commandExecution/requestApproval", {}) == {"decision": "decline"}
    assert sdk.server_request("item/fileChange/requestApproval", {}) == {"decision": "decline"}

    # Never the vault: always an empty directory of its own (round 3: the
    # snapshot workspace is inlined into the prompt, never the turn's cwd).
    roots = {captured["app_config"]["cwd"], captured["thread_start"]["cwd"], captured["turns"][0]["cwd"]}
    (root,) = roots
    root = Path(root)
    assert root != client.vault_root and client.vault_root not in root.parents
    shell = False
    assert root.name.startswith("learnloop-isolated-turn-")
    if shape == "workspace":
        assert '<workspace_file path="INDEX.md">' in captured["turns"][0]["prompt"]
    overrides = list(captured["app_config"]["config_overrides"])
    assert overrides == isolated_turn_overrides(root, shell=shell, mcp_server_ids=("node_repl",),
                                                model_catalog=catalog_pin_path(overrides))
    lockdown = _lockdown()
    for override in ("agents.enabled=false", "tools.experimental_request_user_input.enabled=false",
                     "tools.update_plan.enabled=false", "features.multi_agent=false", "features.multi_agent_v2=false",
                     'web_search="disabled"', "mcp_servers.node_repl.enabled=false",
                     *(f"features.{feature}=false" for feature in lockdown.LOCKDOWN_DISABLED_FEATURES)):
        assert override in overrides, override
    assert ("features.shell_tool=false" in overrides) is (not shell)


def test_a_workspace_that_is_the_vault_is_refused(tmp_path, monkeypatch):
    captured = _fake_sdk(monkeypatch)
    client = _client(tmp_path, monkeypatch)
    for workspace in (client.vault_root, client.vault_root.parent):
        with pytest.raises(CodexUnavailable, match="never reads the vault"):
            client.complete(StructuredRequest(purpose="diagnosis", prompt="p", result_model=LinkJudgment,
                                              workspace=workspace))
    assert captured["constructed"] == 0


@pytest.mark.parametrize(
    "method, answer",
    [
        ("item/commandExecution/requestApproval", {"decision": "decline"}),
        ("item/fileChange/requestApproval", {"decision": "decline"}),
        ("item/permissions/requestApproval", {"permissions": {}, "scope": "turn"}),
        ("item/tool/requestUserInput", {"answers": {}}),
        ("mcpServer/elicitation/request", {"action": "decline"}),
        ("item/tool/call", {"contentItems": [], "success": False}),
        ("applyPatchApproval", {"decision": "denied"}),
        ("execCommandApproval", {"decision": "denied"}),
        ("some/future/request", {}),
    ],
)
def test_every_request_the_model_makes_of_the_client_is_declined_and_refuses_the_answer(
    tmp_path, monkeypatch, method, answer,
):
    answers: list[dict[str, Any]] = []

    def ask(sdk, _turn):
        answers.append(sdk.server_request(method, {"threadId": "thr_parent", "turnId": "turn_parent"}))

    _fake_sdk(monkeypatch, on_run=ask)
    with pytest.raises(_lockdown().CodexToolUseRefused, match=f"server request {method}"):
        _plain(_client(tmp_path, monkeypatch))
    assert answers == [answer]


def test_the_clients_own_requests_keep_the_sdk_default_answer(tmp_path, monkeypatch):
    lockdown = _lockdown().TurnLockdown(parent_thread="thr")
    assert lockdown.handle_server_request("account/chatgptAuthTokens/refresh", {}) == {}
    assert lockdown.violations == []


# -- fail closed when the SDK cannot be told ---------------------------------------------


def test_an_sdk_without_approval_mode_refuses_before_anything_starts(tmp_path, monkeypatch):
    captured = _fake_sdk(monkeypatch, approval_mode_in_sdk=False)
    client = _client(tmp_path, monkeypatch)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="ApprovalMode.deny_all"):
        _plain(client)
    assert captured["constructed"] == 0


def test_a_thread_start_that_takes_no_approval_mode_refuses_the_turn(tmp_path, monkeypatch):
    captured = _fake_sdk(monkeypatch, thread_start_takes_approval=False)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="thread_start takes no approval_mode"):
        _plain(_client(tmp_path, monkeypatch))
    assert "thread_start" not in captured and captured["turns"] == []


def test_an_sdk_whose_approval_handler_cannot_be_replaced_refuses_the_turn(tmp_path, monkeypatch):
    captured = _fake_sdk(monkeypatch, seams=False)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="accept-all approval default"):
        _plain(_client(tmp_path, monkeypatch))
    assert "thread_start" not in captured


def test_the_real_sdk_has_the_seams_the_lockdown_replaces():
    """The installed SDK (when importable): ``ApprovalMode.deny_all``, ``thread_start``/``turn``
    taking ``approval_mode``, and a client whose approval handler and router exist."""

    sdk = pytest.importorskip("openai_codex")
    import inspect

    from openai_codex.client import CodexClient

    assert sdk.ApprovalMode.deny_all.value == "deny_all"
    assert "approval_mode" in inspect.signature(sdk.Codex.thread_start).parameters
    assert "approval_mode" in inspect.signature(sdk.Thread.turn).parameters
    client = CodexClient()
    assert callable(client._approval_handler) and callable(client._router.route_notification)
    # The SDK's default ACCEPTS: what the lockdown replaces.
    request = {"id": 1, "method": "item/commandExecution/requestApproval", "params": {}}
    assert client._handle_server_request(request) == {"decision": "accept"}
    lockdown = _lockdown().TurnLockdown(parent_thread="thr_parent")
    _lockdown().install_on_sdk(SimpleNamespace(_client=client), lockdown)
    assert client._handle_server_request(request) == {"decision": "decline"}
    assert lockdown.server_requests == ["item/commandExecution/requestApproval"]
    # Every notification passes the tap first, then the SDK's own routing.
    item = {"type": "mcpToolCall", "id": "i", "server": "s", "tool": "x", "status": "inProgress", "arguments": {}}
    typed = client._coerce_notification("item/started", {"threadId": "thr_parent", "turnId": "t", "item": item,
                                                           "startedAtMs": 1})
    assert type(typed.payload).__name__ == "ItemStartedNotification"
    client._router.route_notification(typed)
    assert "tool item mcptoolcall" in lockdown.violations
    # The typed notifications carry what the early stop reads: the message's
    # phase and the thread's cumulative usage.
    early = _lockdown().TurnLockdown(parent_thread="thr_parent")
    _lockdown().install_on_sdk(SimpleNamespace(_client=client), early)
    breakdown = {"cachedInputTokens": 0, "inputTokens": 100, "outputTokens": 20, "reasoningOutputTokens": 0,
                 "totalTokens": 120}
    for method, params in (
        ("item/completed", {"threadId": "thr_parent", "turnId": "t", "completedAtMs": 2,
                            "item": {"type": "agentMessage", "id": "m", "text": "Trying exec.", "phase": "commentary"}}),
        ("thread/tokenUsage/updated", {"threadId": "thr_parent", "turnId": "t",
                                       "tokenUsage": {"total": breakdown, "last": breakdown}}),
    ):
        notification = client._coerce_notification(method, params)
        assert type(notification.payload).__name__ != "UnknownNotification"
        client._router.route_notification(notification)
    assert early.violations == ["a model response that ended in a tool call (no final answer)"]
    assert early.parent_usage().total_tokens == 120


# -- 4. an answer from a turn that used a tool is refused ---------------------------------


@pytest.mark.parametrize(
    "kind",
    ["commandExecution", "fileChange", "mcpToolCall", "dynamicToolCall", "collabAgentToolCall", "webSearch",
     "imageView", "imageGeneration", "enteredReviewMode", "hookPrompt", "plan", "someFutureTool"],
)
def test_a_tool_item_refuses_the_answer(tmp_path, monkeypatch, kind):
    _fake_sdk(monkeypatch, items=[*TEXT_ITEMS[:2], {"type": kind}, TEXT_ITEMS[2]])
    with pytest.raises(_lockdown().CodexToolUseRefused) as refused:
        _plain(_client(tmp_path, monkeypatch))
    assert refused.value.violations == [f"turn item {kind.lower()}"]
    assert isinstance(refused.value, AIProviderUnavailable)  # callers treat it as a failed call


def test_a_text_only_turn_returns_its_answer(tmp_path, monkeypatch):
    _fake_sdk(monkeypatch, items=TEXT_ITEMS, usage=_usage(120))
    assert _plain(_client(tmp_path, monkeypatch)) == LinkJudgment(links=[])


def test_an_item_without_a_type_is_never_text(tmp_path, monkeypatch):
    _fake_sdk(monkeypatch, items=[*TEXT_ITEMS, {"path": "/etc/passwd"}])
    with pytest.raises(_lockdown().CodexToolUseRefused, match="turn item unknown"):
        _plain(_client(tmp_path, monkeypatch))


@pytest.mark.parametrize("kind, refused", [("commandExecution", True), ("fileChange", True),
                                           ("collabAgentToolCall", True), ("mcpToolCall", True)])
def test_a_workspace_turn_may_only_add_commands(tmp_path, monkeypatch, kind, refused):
    """Round 3: not even commands any more; a workspace turn is inlined and tool-free like every other."""

    _fake_sdk(monkeypatch, items=[{"type": kind, "command": "cat INDEX.md"}, *TEXT_ITEMS], usage=_usage(300, 100))
    workspace = tmp_path / "snapshot"
    workspace.mkdir()
    request = StructuredRequest(purpose="diagnosis", prompt="p", result_model=LinkJudgment, workspace=workspace)
    client = _client(tmp_path, monkeypatch)
    if refused:
        with pytest.raises(_lockdown().CodexToolUseRefused):
            client.complete(request)
    else:
        assert client.complete(request) == LinkJudgment(links=[])


def test_a_second_model_request_in_a_text_turn_refuses_it(tmp_path, monkeypatch):
    # Code mode's exec leaves no item: the round trip shows as total != last.
    _fake_sdk(monkeypatch, usage=_usage(300, 120))
    with pytest.raises(_lockdown().CodexToolUseRefused, match="second model request"):
        _plain(_client(tmp_path, monkeypatch))


# -- 5. what the SDK reports inside the turn: stopped at the first tool, every token counted --


def test_the_first_tool_item_stops_the_turn(tmp_path, monkeypatch):
    def tool(sdk, turn):
        sdk.notify("item/started", threadId="thr_parent", turnId="turn_parent",
                   item={"type": "fileChange", "id": "i1"})
        assert turn.stopped.wait(5)  # the cap is 0: stopped at once

    captured = _fake_sdk(monkeypatch, on_run=tool, raise_when_stopped=True)
    with pytest.raises(_lockdown().CodexToolUseRefused, match="tool item filechange"):
        _plain(_client(tmp_path, monkeypatch))
    assert captured["interrupted"] is True


def _usage_update(sdk, total: int, thread: str = "thr_parent") -> None:
    sdk.notify("thread/tokenUsage/updated", threadId=thread, turnId="turn_parent",
               tokenUsage={"total": {"inputTokens": total, "outputTokens": 0, "totalTokens": total},
                           "last": {"inputTokens": total, "outputTokens": 0, "totalTokens": total}})


def _message(sdk, phase: str | None) -> None:
    item = {"type": "agentMessage", "id": "m", "text": ANSWER, **({"phase": phase} if phase else {})}
    sdk.notify("item/completed", threadId="thr_parent", turnId="turn_parent", item=item)


def test_a_second_model_request_reported_mid_turn_stops_it(tmp_path, monkeypatch):
    def two_requests(sdk, turn):
        _message(sdk, "final_answer")
        for total in (0, 120, 120, 260):  # a zero update and a rate-limit repeat carry no request
            _usage_update(sdk, total)
        assert turn.stopped.wait(5)

    captured = _fake_sdk(monkeypatch, on_run=two_requests, raise_when_stopped=True)
    with pytest.raises(_lockdown().CodexToolUseRefused, match="second model request"):
        _plain(_client(tmp_path, monkeypatch))
    assert captured["interrupted"] is True


def test_sub_agent_threads_are_refused_and_their_tokens_counted(tmp_path, monkeypatch):
    events: list[tuple[str, dict[str, Any]]] = []

    def sub_agent(sdk, _turn):
        sdk.notify("thread/tokenUsage/updated", threadId="thr_parent", turnId="turn_parent",
                   tokenUsage={"total": {"inputTokens": 100, "outputTokens": 20, "totalTokens": 120}})
        sdk.notify("thread/started", thread={"id": "thr_child"})
        sdk.notify("thread/tokenUsage/updated", threadId="thr_child", turnId="turn_child",
                   tokenUsage={"total": {"inputTokens": 400, "outputTokens": 50, "totalTokens": 450,
                                         "cachedInputTokens": 7}})

    _fake_sdk(monkeypatch, on_run=sub_agent, usage=_usage(120, input_tokens=100))
    client = _client(tmp_path, monkeypatch)
    with observe_model_calls(lambda action, event: events.append((action, dict(event)))), \
            pytest.raises(_lockdown().CodexToolUseRefused, match="sub-agent thread"):
        _plain(client)
    (finish,) = [event for action, event in events if action == "finish" and "usage_json" in event]
    assert finish["input_tokens"] == 100 + 400 and finish["output_tokens"] == 20 + 50
    assert finish["cached_input_tokens"] == 7
    turn = json.loads(finish["usage_json"])["codex_turn"]
    assert turn["threads"] == 2 and turn["model_requests"] == 2
    assert (client._usage_input_tokens, client._usage_output_tokens) == (500, 70)


def test_a_guardian_review_is_counted_and_refuses_the_answer(tmp_path, monkeypatch):
    events: list[tuple[str, dict[str, Any]]] = []

    def review(sdk, _turn):
        sdk.notify("item/autoApprovalReview/started", threadId="thr_parent", turnId="turn_parent")

    _fake_sdk(monkeypatch, on_run=review, usage=_usage(120))
    with observe_model_calls(lambda action, event: events.append((action, dict(event)))), \
            pytest.raises(_lockdown().CodexToolUseRefused, match="Guardian"):
        _plain(_client(tmp_path, monkeypatch))
    (finish,) = [event for action, event in events if action == "finish" and "usage_json" in event]
    assert json.loads(finish["usage_json"])["codex_turn"]["guardian_reviews"] == 1


@pytest.mark.parametrize("phase", ["commentary", None])
def test_a_response_that_ends_without_an_answer_stops_the_turn_at_once(tmp_path, monkeypatch, phase):
    """Live check 5 (2026-10-21): a code-mode exec call leaves no item; the
    response before it ends with a ``commentary`` message only. Stopped there,
    before the round trip becomes a second request. A model that reports no
    phases is never stopped on this ground (its message may be the answer)."""

    def commentary_then_tool(sdk, turn):
        sdk.notify("item/started", threadId="thr_parent", turnId="turn_parent", item={"type": "reasoning"})
        _message(sdk, phase)
        _usage_update(sdk, 120)
        if phase == "commentary":
            assert turn.stopped.wait(5)

    captured = _fake_sdk(monkeypatch, on_run=commentary_then_tool, raise_when_stopped=True, usage=_usage(120))
    client = _client(tmp_path, monkeypatch)
    if phase == "commentary":
        with pytest.raises(_lockdown().CodexToolUseRefused, match="ended in a tool call"):
            _plain(client)
        assert captured["interrupted"] is True
    else:
        assert _plain(client) == LinkJudgment(links=[])
        assert "interrupted" not in captured


def test_an_ordinary_turn_reports_exactly_what_it_did_before(tmp_path, monkeypatch):
    """Behaviour unchanged for a text-only turn: the same receipt fields, no extras.
    The notification order is the one live check 1 (2026-10-21) recorded."""

    events: list[tuple[str, dict[str, Any]]] = []

    def one_request(sdk, _turn):
        for kind in ("userMessage", "reasoning"):
            sdk.notify("item/started", threadId="thr_parent", turnId="turn_parent", item={"type": kind})
            sdk.notify("item/completed", threadId="thr_parent", turnId="turn_parent", item={"type": kind})
        sdk.notify("item/started", threadId="thr_parent", turnId="turn_parent", item={"type": "agentMessage"})
        _message(sdk, "final_answer")
        sdk.notify("thread/tokenUsage/updated", threadId="thr_parent", turnId="turn_parent",
                   tokenUsage={"total": {"inputTokens": 110, "outputTokens": 10, "totalTokens": 120}})
        sdk.notify("turn/completed", threadId="thr_parent", turn={"id": "turn_parent"})

    _fake_sdk(monkeypatch, on_run=one_request, usage=_usage(120, input_tokens=110))
    with observe_model_calls(lambda action, event: events.append((action, dict(event)))):
        assert _plain(_client(tmp_path, monkeypatch)) == LinkJudgment(links=[])
    turn_finish = [event for action, event in events if action == "finish" and event.get("input_tokens") == 110]
    assert turn_finish and all("usage_json" not in event and "model_requests" not in event for event in turn_finish)


# -- 3. the launch check fails closed (fake codex-cli 0.163.0) ------------------------------


def _check_client(tmp_path: Path, program: Path, model: str = "gpt-5.6-sol") -> SdkCodexClient:
    vault_root = tmp_path / "vault"
    vault_root.mkdir(exist_ok=True)
    return SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"), sdk_codex_bin=str(program),
                                      model=model), vault_root)


def _launched(log: Path) -> list[list[str]]:
    return [call["overrides"] for call in fake_codex_calls(log) if call["command"][:1] == ["app-server"]]


def _probe_count(log: Path) -> int:
    return sum(1 for call in fake_codex_calls(log) if call["command"][:1] != ["app-server"])


def _turn(client: SdkCodexClient):
    return _plain(client)


@pytest.mark.parametrize("feature", sorted(set(_OFF) | {"shell_tool"}))
def test_a_tool_bearing_feature_the_cli_leaves_on_refuses_the_turn(tmp_path, monkeypatch, feature):
    program, log = write_fake_codex(tmp_path / "bin", features=[*FEATURES, feature], ignored_features=[feature])
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match=f"feature .*{feature}"):
        _turn(_check_client(tmp_path, program))
    assert _launched(log) == [] and "app_config" not in captured


@pytest.mark.parametrize("feature", ["apps", "plugins", "multi_agent"])
def test_a_core_feature_the_cli_does_not_list_refuses_the_turn(tmp_path, monkeypatch, feature):
    program, log = write_fake_codex(tmp_path / "bin", missing_features=[feature])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match=feature):
        _turn(_check_client(tmp_path, program))
    assert _launched(log) == []


def test_an_unclassified_feature_is_switched_off_and_checked(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", features=[*FEATURES, "future_tool"])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_check_client(tmp_path, program))
    (launched,) = _launched(log)
    assert "features.future_tool=false" in launched


def test_an_unclassified_feature_that_stays_on_refuses_the_turn(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", features=[*FEATURES, "future_tool"],
                                    ignored_features=["future_tool"])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="future_tool"):
        _turn(_check_client(tmp_path, program))
    assert _launched(log) == []


def test_a_cli_that_rejects_the_sub_agent_switch_refuses_the_turn(tmp_path, monkeypatch):
    # A June-era CLI parses `agents.enabled` as a role and refuses to load.
    program, log = write_fake_codex(tmp_path / "bin", rejects_overrides=["agents.enabled"])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable):
        _turn(_check_client(tmp_path, program))
    assert _launched(log) == []


def test_an_enable_flag_for_an_unclassified_feature_refuses_the_turn(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", features=[*FEATURES, "future_tool"])
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    vault_root = tmp_path / "vault"
    vault_root.mkdir()
    client = SdkCodexClient(CodexConfig(checkout_path=str(tmp_path / "codex"),
                                        sdk_launch_command=f"{program} --enable future_tool app-server"), vault_root)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="future_tool"):
        _turn(client)
    assert _launched(log) == []


@pytest.mark.parametrize(
    "catalog, reason",
    [
        (bundled_catalog("gpt-5.6-sol", tool_mode="browser_mode"), "tool_mode"),
        (bundled_catalog("gpt-5.6-sol", apply_patch_tool_type="anywhere"), "apply_patch_tool_type"),
        (bundled_catalog("gpt-5.6-sol", experimental_supported_tools=["clock", "fetch_url"]), "fetch_url"),
        (bundled_catalog("gpt-5.6-sol", artifact_tool_type="native"), "artifact_tool_type"),
        (bundled_catalog("gpt-5.6-sol", multi_agent_version="v3"), "multi_agent_version"),
        (bundled_catalog("gpt-6-luna"), "not in the bundled catalog"),
        ({"not": "a catalog"}, "did not return a model catalog"),
    ],
)
def test_model_metadata_nothing_neutralizes_refuses_the_turn(tmp_path, monkeypatch, catalog, reason):
    program, log = write_fake_codex(tmp_path / "bin", catalog=catalog)
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match=reason):
        _turn(_check_client(tmp_path, program))
    assert _launched(log) == []


def test_the_0_163_0_metadata_is_neutralized_and_passes(tmp_path, monkeypatch):
    catalog = bundled_catalog("gpt-5.6-sol", "gpt-6-luna", experimental_supported_tools=["send_user_message_async",
                                                                                         "clock"])
    program, log = write_fake_codex(tmp_path / "bin", catalog=catalog)
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    _turn(_check_client(tmp_path, program, model=""))  # no model: every entry is checked
    assert len(_launched(log)) == 1


def test_a_failing_model_listing_refuses_the_turn(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", behaviour={"debug models": "fail"})
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    with pytest.raises(_lockdown().CodexLockdownUnavailable, match="debug models"):
        _turn(_check_client(tmp_path, program))
    assert _launched(log) == []


def test_a_passed_check_is_cached_per_config_fingerprint(tmp_path, monkeypatch):
    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    program, log = write_fake_codex(tmp_path / "bin", config_servers={"node_repl": True})
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    client = _check_client(tmp_path, program)
    _turn(client)
    first = _probe_count(log)
    assert first == 6  # mcp list, mcp list (pinned), features list, debug models --bundled, debug models, prompt-input
    _turn(client)
    assert _probe_count(log) == first  # cached: same CLI, same config layers
    launches = _launched(log)
    assert len(launches) == 2 and "mcp_servers.node_repl.enabled=false" in launches[1]
    assert Path(captured["app_config"]["cwd"]).name.startswith("learnloop-isolated-turn-")
    (home / "config.toml").write_text("# changed\n", encoding="utf-8")
    _turn(client)
    assert _probe_count(log) == first * 2  # a config layer changed: checked again


def test_a_refused_check_is_not_cached(tmp_path, monkeypatch):
    program, log = write_fake_codex(tmp_path / "bin", behaviour={"features list": "fail"})
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    client = _check_client(tmp_path, program)
    for _ in range(2):
        with pytest.raises(_lockdown().CodexLockdownUnavailable):
            _turn(client)
    assert _probe_count(log) == 4  # mcp list, features list (fails), twice


def test_the_features_permitted_on_are_exactly_the_reviewed_non_tool_ones():
    """Pin of the reviewed list (codex-cli 0.163.0, 2026-10-21): adding a feature
    here is a security review, not a refactor."""

    lockdown = _lockdown()
    assert set(lockdown.PERMITTED_FEATURES) & set(lockdown.LOCKDOWN_DISABLED_FEATURES) == set()
    assert set(lockdown.PERMITTED_FEATURES) & set(lockdown.SHELL_FEATURES) == {"unified_exec"}
    toolish = {feature for feature in lockdown.PERMITTED_FEATURES
               for word in ("browser", "computer", "mcp", "plugin", "apps", "agent", "web", "image", "hook",
                            "memor", "skill", "search", "patch") if word in feature}
    # Only names that merely mention a tool: a removed no-op flag and two image budgets.
    assert toolish == {"tool_search_always_defer_mcp_tools", "compaction_image_budget", "resize_all_images"}
    assert lockdown.feature_violations({"apps": False, "plugins": False, "multi_agent": False, "fast_mode": True,
                                        "unified_exec": True}, shell=False) == []
    assert lockdown.feature_violations({"apps": False, "plugins": False, "multi_agent": False, "shell_tool": True},
                                       shell=False) == ["shell_tool"]
    assert lockdown.feature_violations({"apps": False, "plugins": False, "multi_agent": False, "shell_tool": True},
                                       shell=True) == []


# -- 6. Codex review of the stage (2026-10-21, job 20261021-111619-GGirNP) ------------------
#
# F1: a workspace command inherited the app server's whole environment (the
#     API keys LearnLoop loads), so an injected `printenv` could read them;
# F2: the cached launch check fingerprinted only whether the turn directory
#     had a `.codex/`, so a workspace-local MCP server added later (or a
#     sibling workspace's) started without its `enabled=false`;
# F3: tokens the SDK reported before an ordinary failure (timeout, interrupt,
#     closed connection) never reached the receipt or the admission's settle.

import os
import shutil
import subprocess

from learnloop.ai.errors import CodexInterrupted, CodexTurnTimeout
from learnloop.ai.execution import gate_model_requests

_CODEX = shutil.which("codex")
_CANARY = "LLCANARY-f1-synthetic"


def _sandboxed_env(codex_home: Path, cwd: Path, overrides: list[str]) -> subprocess.CompletedProcess:
    """`/usr/bin/env` run by the installed CLI the way a workspace command runs.

    ``codex sandbox`` builds the command's environment with the same
    ``create_env(shell_environment_policy)`` as the shell tool, under the
    turn's permission profile; no model, no network. Its own environment is
    synthetic only: never this process's (which may hold real keys)."""

    environ = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(codex_home.parent / "home"),
        "CODEX_HOME": str(codex_home), "LANG": "C.UTF-8",
        "OPENROUTER_API_KEY": _CANARY, "LEARNLOOP_SYNTHETIC_SECRET": _CANARY, "PLAIN_SETTING": _CANARY,
    }
    args = [_CODEX]
    for override in overrides:
        args += ["-c", override]
    return subprocess.run([*args, "sandbox", "--", "/usr/bin/env"], cwd=cwd, env=environ, capture_output=True,
                          text=True, timeout=60)


@pytest.mark.skipif(_CODEX is None, reason="the Codex CLI is not installed")
@pytest.mark.parametrize("user_config", [
    "",
    '[shell_environment_policy]\ninherit = "all"\nignore_default_excludes = true\n'
    'set = { USER_SET_TOKEN = "LLCANARY-f1-synthetic", PLAIN_SET = "LLCANARY-f1-synthetic" }\n'
    'filters = { "*KEY*" = "include", "PLAIN*" = "include", "*SECRET*" = "include" }\n',
    '[shell_environment_policy]\ninherit = "all"\ninclude_only = ["*"]\nexperimental_use_profile = true\n'
    'set = { USER_SET_TOKEN = "LLCANARY-f1-synthetic" }\n',
], ids=["default-policy", "set-and-filters", "include-all-and-profile"])
def test_a_workspace_command_cannot_see_inherited_credentials(tmp_path, user_config):
    """F1 on the installed binary: synthetic secrets in the app server's
    environment and in a hostile user config never reach a workspace command."""

    home = tmp_path / "codex-home"
    home.mkdir()
    (tmp_path / "home").mkdir()
    (home / "config.toml").write_text(user_config, encoding="utf-8")
    cwd = tmp_path / "snapshot"
    cwd.mkdir()
    (cwd / "INDEX.md").write_text("export\n", encoding="utf-8")
    locked = _sandboxed_env(home, cwd, isolated_turn_overrides(cwd, shell=True))
    assert locked.returncode == 0, locked.stderr
    assert _CANARY not in locked.stdout and _CANARY not in locked.stderr
    names = {line.split("=", 1)[0] for line in locked.stdout.splitlines() if "=" in line}
    assert names - set(_lockdown().SHELL_ENVIRONMENT_ALLOWLIST) <= {"PWD", "CODEX_SANDBOX_NETWORK_DISABLED",
                                                                     "CODEX_SANDBOX", "CODEX_THREAD_ID"}
    assert "PATH" in names
    # The control: the same command under the profile without the policy is
    # what the stage shipped, and it sees the canary.
    unlocked = [override for override in isolated_turn_overrides(cwd, shell=True)
                if not override.startswith("shell_environment_policy.")]
    assert _CANARY in _sandboxed_env(home, cwd, unlocked).stdout


@pytest.mark.parametrize("shell", [False, True])
def test_every_turn_pins_the_command_environment_and_turns_shell_snapshots_off(tmp_path, shell):
    lockdown = _lockdown()
    overrides = isolated_turn_overrides(tmp_path, shell=shell)
    policy = [override for override in overrides if override.startswith("shell_environment_policy.")]
    assert policy == lockdown.shell_environment_overrides()
    assert 'shell_environment_policy.inherit="core"' in policy
    assert "shell_environment_policy.ignore_default_excludes=false" in policy
    assert "shell_environment_policy.experimental_use_profile=false" in policy
    (include_only,) = [override for override in policy if override.startswith("shell_environment_policy.include_only=")]
    allowed = json.loads(include_only.partition("=")[2])
    assert allowed == list(lockdown.SHELL_ENVIRONMENT_ALLOWLIST)
    assert not [name for name in allowed if any(word in name for word in ("KEY", "TOKEN", "SECRET", "*"))]
    assert "features.shell_snapshot=false" in overrides
    on = {"apps": False, "plugins": False, "multi_agent": False, "shell_tool": True, "shell_snapshot": True}
    assert lockdown.feature_violations(on, shell=shell) == (["shell_snapshot"] if shell else
                                                             ["shell_snapshot", "shell_tool"])


def _workspace_turn(client: SdkCodexClient, workspace: Path):
    return client.complete(StructuredRequest(purpose="diagnosis", prompt="p", result_model=LinkJudgment,
                                             workspace=workspace))


def _project_layer(workspace: Path, *servers: str) -> None:
    layer = workspace / ".codex"
    layer.mkdir(parents=True, exist_ok=True)
    (layer / "config.toml").write_text(
        "".join(f'[mcp_servers.{name}]\ncommand = "/bin/true"\n\n' for name in servers), encoding="utf-8")


def test_a_workspaces_own_project_layer_never_reaches_the_turn(tmp_path, monkeypatch):
    """Round 3 supersedes F2 (a workspace-local MCP server and a cached check):
    the workspace is inlined, the turn runs in a fresh scratch directory, so the
    workspace's own `.codex/config.toml` is never a layer of the turn at all."""

    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    program, log = write_fake_codex(tmp_path / "bin")
    captured = install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    client = _check_client(tmp_path, program)
    workspace = tmp_path / "trusted-workspace"
    _project_layer(workspace, "docs", "shell_bridge")
    (workspace / "INDEX.md").write_text("# history\n", encoding="utf-8")
    _workspace_turn(client, workspace)
    root = Path(captured["app_config"]["cwd"])
    assert root.name.startswith("learnloop-isolated-turn-") and root != workspace.resolve()
    assert json.loads(captured["spawned"]["stdout"])["servers_on"] == []
    assert not [override for override in _launched(log)[-1] if "docs" in override or "shell_bridge" in override]
    assert '<workspace_file path="INDEX.md">' in captured["turns"][0]["prompt"]


def test_fresh_workspaces_without_a_project_layer_still_share_one_check(tmp_path, monkeypatch):
    """The cache keeps working for what LearnLoop makes: a new export every turn."""

    home = tmp_path / "codex-home"
    home.mkdir()
    monkeypatch.setenv("CODEX_HOME", str(home))
    program, log = write_fake_codex(tmp_path / "bin")
    install_fake_codex_sdk(monkeypatch, final_response=ANSWER, spawn=True)
    client = _check_client(tmp_path, program)
    for index in range(3):
        export = tmp_path / "exports" / f"learnloop-diagnosis-snapshot-{index}"
        export.mkdir(parents=True)
        _workspace_turn(client, export)
    assert _probe_count(log) == 5  # mcp list, features list, debug models (twice), prompt-input: once


def _gate(settled: list[dict[str, Any]]):
    class Gate:
        def admit(self, client, *, purpose, prompt, budget):
            return purpose

        def settle(self, admission, usage):
            settled.append({"admission": admission, **usage})

    return Gate()


def _finishes(events: list[tuple[str, dict[str, Any]]], purpose: str) -> list[dict[str, Any]]:
    ids = {event["id"] for action, event in events if action == "start" and event.get("purpose") == purpose}
    return [event for action, event in events if action == "finish" and event["id"] in ids]


def _two_command_rounds(sdk) -> None:
    """One answered model request (round 3: every turn is tool-free, so a second request or a
    command would be a violation; F3 is about an ordinary failure, without one)."""

    sdk.notify("item/completed", threadId="thr_parent", turnId="turn_parent",
               item={"type": "agentMessage", "phase": "final_answer", "text": ANSWER})
    sdk.notify("thread/tokenUsage/updated", threadId="thr_parent", turnId="turn_parent",
               tokenUsage={"total": {"inputTokens": 2300, "outputTokens": 120, "totalTokens": 2420,
                                     "cachedInputTokens": 900}})


@pytest.mark.parametrize("ending", ["sdk_timeout", "connection_closed", "learner_interrupt", "request_deadline"])
def test_tokens_reported_before_an_ordinary_failure_reach_the_receipt_and_the_settle(tmp_path, monkeypatch, ending):
    """F3: a turn spends a request, then fails without any lockdown violation."""

    events: list[tuple[str, dict[str, Any]]] = []
    settled: list[dict[str, Any]] = []
    client = _client(tmp_path, monkeypatch)

    def rounds_then_failure(sdk, turn):
        _two_command_rounds(sdk)
        if ending == "sdk_timeout":
            raise TimeoutError("timed out waiting for the app server")
        if ending == "connection_closed":
            raise BrokenPipeError("app-server connection closed")
        if ending == "learner_interrupt":
            client.interrupt()
        assert turn.stopped.wait(5)  # the interrupt or the request's deadline stops the turn
        raise RuntimeError("turn interrupted")

    _fake_sdk(monkeypatch, on_run=rounds_then_failure)
    workspace = tmp_path / "snapshot"
    workspace.mkdir()
    request = StructuredRequest(purpose="diagnosis", prompt="p", result_model=LinkJudgment, workspace=workspace,
                                timeout_seconds=0.5 if ending == "request_deadline" else None)
    expected = {"sdk_timeout": CodexUnavailable, "connection_closed": CodexUnavailable,
                "learner_interrupt": CodexInterrupted, "request_deadline": CodexTurnTimeout}[ending]
    with observe_model_calls(lambda action, event: events.append((action, dict(event)))), \
            gate_model_requests(_gate(settled)), pytest.raises(expected):
        client.complete(request)
    (finish,) = _finishes(events, "diagnosis:sdk_turn")
    assert (finish["input_tokens"], finish["output_tokens"], finish["cached_input_tokens"]) == (2300, 120, 900)
    (settle,) = [entry for entry in settled if entry["admission"] == "diagnosis:sdk_turn"]
    assert (settle["input_tokens"], settle["output_tokens"]) == (2300, 120)
    assert (client._usage_input_tokens, client._usage_output_tokens) == (2300, 120)


def test_a_failure_before_any_usage_reports_nothing_new(tmp_path, monkeypatch):
    """Unchanged: a turn that failed before the SDK reported tokens adds none."""

    events: list[tuple[str, dict[str, Any]]] = []

    def closed(_sdk, _turn):
        raise BrokenPipeError("app-server connection closed")

    _fake_sdk(monkeypatch, on_run=closed)
    client = _client(tmp_path, monkeypatch)
    with observe_model_calls(lambda action, event: events.append((action, dict(event)))), \
            pytest.raises(CodexUnavailable):
        _plain(client)
    (finish,) = _finishes(events, "tutor_qa:sdk_turn")
    assert finish.get("input_tokens") is None and "usage_json" not in finish
    assert (client._usage_input_tokens, client._usage_output_tokens) == (0, 0)
