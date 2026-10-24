"""Plan-first transport T1 (owner decisions 2026-10-21): properties by construction.

Every serving route uses LearnLoop's own tool-free ChatGPT-plan client (one
``POST /v1/responses`` per admitted request, ``store: false``, no tools); the
Codex agent harness is refused for serving without ``ai.agent_harness_opt_in``
and is never a fallback; an unavailable plan reports "unavailable" and ASKS
about OpenRouter. The numbered sections follow the stage's T1 test list
(docs/reviews/ai-plan-first-transport-t1.md). No test leaves 127.0.0.1.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any, get_args

import pytest
import tomlkit
from typer.testing import CliRunner

from learnloop.ai import plan_fallback
from learnloop.ai.agent_harness import AgentHarnessRefused, is_agent_harness_type
from learnloop.ai.chatgpt_plan.session import PlanSession
from learnloop.ai.chatgpt_plan.workspace import NAMESPACE, ServedWorkspace
from learnloop.ai.client import make_ai_provider_client_from_profile
from learnloop.ai.execution import gate_model_requests
from learnloop.ai.isolation import TOOL_FREE
from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient
from learnloop.ai.routing import (
    DECIDER_TASKS,
    LIST_ROUTE_TASKS,
    AITask,
    fallback_provider_for,
    provider_for_task,
    ready_client_for_task,
)
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import execute_structured_operation
from learnloop.config import LearnLoopConfig, load_config
from learnloop.config.schema import (
    AGENT_HARNESS_PROFILE_TYPES,
    CHATGPT_PLAN_PROVIDER_NAMES,
    CODEX_TO_PLAN_PROFILE,
    DEFAULT_SERVING_TASK_ROUTES,
    LEGACY_CODEX_TASK_ROUTES,
    ChatGPTPlanProviderConfig,
)

from tests.chatgpt_plan_fakes import Reply, completed_events, failed_events, fake_chatgpt, sign_in, tool_call_events
from tests.helpers import create_basic_vault

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TASKS: tuple[str, ...] = get_args(AITask)
#: Tasks whose client is not a chat/structured generation transport.
NON_GENERATION = frozenset({"embedding", "transcription", "video_generation"}) | DECIDER_TASKS
#: The keys a plain plan request may carry (proposal §1.1).
PLAIN_KEYS = frozenset({"model", "instructions", "input", "store", "stream", "text", "reasoning"})
CODEX_NAMES = ("codex", "codex_low", "codex_medium", "codex_luna")


class Answer(WireModel):
    ok: bool
    note: str


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    for name in ("LEARNLOOP_AI_PROVIDER", "LEARNLOOP_AI_FALLBACK", "OPENROUTER_API_KEY", "OPENAI_API_KEY",
                 "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._sleep", lambda _seconds: None)
    plan_fallback.revoke_all()
    yield
    plan_fallback.revoke_all()


#: The action each test's resolutions run as (redesign D: a grant names the action that asked).
LEARNER = "test.learner_request"


@pytest.fixture(autouse=True)
def learner_request():
    """Each test resolves routes as one request of action ``LEARNER`` does (the
    sidecar's dispatch opens ``plan_fallback.request`` per RPC): since redesign D
    a grant counts only in a request of the granted action, or in a unit it
    created (tests/test_plan_first_transport_offer_grants.py pins the property)."""

    with plan_fallback.request(None, LEARNER):
        yield


@pytest.fixture
def no_subprocess(monkeypatch):
    """Any process start fails the test: the refusal must come first."""

    def refuse(*_args: Any, **_kwargs: Any):
        raise AssertionError("a process was started")

    monkeypatch.setattr(subprocess, "Popen", refuse)
    monkeypatch.setattr(subprocess, "run", refuse)
    import os

    monkeypatch.setattr(os, "posix_spawn", refuse, raising=False)
    monkeypatch.setattr(os, "fork", refuse, raising=False)


def _vault(tmp_path: Path, *, opt_in: bool = False, extra: dict[str, Any] | None = None) -> Path:
    root = tmp_path / "vault"
    if not root.exists():
        create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    if opt_in:
        document["ai"]["agent_harness_opt_in"] = True
    for dotted, value in (extra or {}).items():
        table = document
        *parents, leaf = dotted.split(".")
        for part in parents:
            if part not in table:
                table[part] = tomlkit.table()
            table = table[part]
        table[leaf] = value
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def _grant(vault: Path, tasks: list[str]) -> None:
    """The learner answers this action's offer (redesign D: the grant names the action, not tasks)."""

    plan_fallback.grant_origin(vault, LEARNER, tasks)


def _set_state(state: str, server) -> None:
    session = PlanSession()
    if state in {"signed_in", "paused"}:
        sign_in(session, server)
    if state == "paused":
        session.note_usage_limit(code="subscription_sharing_usage_limit_exceeded", request_id="req_t1")


def _assert_never_harness(resolved, task: str, context: str) -> None:
    client = resolved.client
    if client is None:
        return
    provider_type = str(getattr(client, "provider_type", "") or "")
    assert not is_agent_harness_type(provider_type), (task, context, provider_type)
    if task not in NON_GENERATION and provider_type != "decider":
        # (A decider answers typed choice questions only: facet identity and
        # rubric phrasing accept one; it has no tool surface at all.)
        supports = getattr(client, "supports", None)
        assert callable(supports) and supports(TOOL_FREE), (task, context, provider_type)


# -- (1) route resolution ----------------------------------------------------------------------


def test_code_defaults_name_the_plan_tiers_with_the_codex_efforts_and_slugs():
    config = LearnLoopConfig()
    assert config.ai.active_provider == "chatgpt"
    assert config.ai.agent_harness_opt_in is False
    assert config.ai.plan_fallback_profile == "openrouter"
    for codex_name, plan_name in CODEX_TO_PLAN_PROFILE.items():
        codex, plan = config.ai.providers[codex_name], config.ai.providers[plan_name]
        assert plan.type == "chatgpt_plan" and codex.type == "codex_sdk"
        assert (plan.model, plan.reasoning_effort) == (codex.model, codex.reasoning_effort), plan_name
    for task, legacy in LEGACY_CODEX_TASK_ROUTES.items():
        assert DEFAULT_SERVING_TASK_ROUTES[task] == CODEX_TO_PLAN_PROFILE[legacy], task
        assert getattr(config.ai.routing, task) == DEFAULT_SERVING_TASK_ROUTES[task], task
    assert config.ai.providers["chatgpt"].workspace_mode == "inline"
    # The tiers follow the vault's own `chatgpt` slug (one setting for all of them).
    custom = LearnLoopConfig.model_validate({"ai": {"providers": {"chatgpt": {
        "type": "chatgpt_plan", "model": "gpt-owner-slug"}}}})
    for name in ("chatgpt_low", "chatgpt_medium"):
        assert custom.ai.providers[name].model == "gpt-owner-slug"


@pytest.mark.parametrize("state", ["signed_in", "paused", "signed_out"])
@pytest.mark.parametrize("openrouter", [False, True])
def test_every_task_under_code_defaults_resolves_tool_free_and_never_codex(tmp_path, monkeypatch, no_subprocess,
                                                                          state, openrouter):
    if openrouter:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with fake_chatgpt() as server:
        _set_state(state, server)
        vault = _vault(tmp_path)
        config = load_config(vault / "learnloop.toml")
        plan_served = 0
        for task in TASKS:
            resolved = ready_client_for_task(vault, config, task)  # type: ignore[arg-type]
            _assert_never_harness(resolved, task, f"{state}/openrouter={openrouter}")
            if resolved.client is not None and resolved.client.provider_type == "chatgpt_plan":
                plan_served += 1
            if state != "signed_in" and resolved.provider_name in CHATGPT_PLAN_PROVIDER_NAMES:
                # Unavailable, reported through the degrade path; asked, never sent.
                assert not resolved.ready, task
                # Offered only when OpenRouter could do the work as configured (review F2).
                blocked = plan_fallback.offer_blocker(config, task) is not None
                expected = "openrouter" if openrouter and not blocked else None
                assert resolved.runtime.fallback_available == expected, task
                if openrouter and blocked:
                    assert "nothing is offered" in resolved.runtime.message or "isn't offered" in resolved.runtime.message
        if state == "signed_in":
            assert plan_served >= 40  # every chat generation route is served by the plan
        else:
            assert plan_served == 0
        assert server.requests == []  # resolving builds clients; it sends nothing


def _profile_names(config: LearnLoopConfig) -> list[str]:
    return sorted(config.ai.providers)


def test_every_routing_value_for_every_task_never_resolves_to_codex(tmp_path, monkeypatch, no_subprocess):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with fake_chatgpt() as server:
        _set_state("signed_in", server)
        vault = _vault(tmp_path)
        config = load_config(vault / "learnloop.toml")
        names = _profile_names(config)
        assert set(CODEX_NAMES) <= set(names)
        routed_fields = set(type(config.ai.routing).model_fields)
        for task in TASKS:
            if task not in routed_fields:
                continue
            original = getattr(config.ai.routing, task)
            try:
                for name in names:
                    setattr(config.ai.routing, task, [name] if task == "pf_proposers" else name)
                    resolved = ready_client_for_task(vault, config, task)  # type: ignore[arg-type]
                    _assert_never_harness(resolved, task, f"routing={name}")
                    if name in CODEX_NAMES and task not in DECIDER_TASKS and task != "embedding":
                        assert not resolved.ready and "agent harness" in (resolved.runtime.message or ""), (task, name)
            finally:
                setattr(config.ai.routing, task, original)


@pytest.mark.parametrize("state", ["paused", "signed_out"])
def test_every_fallback_provider_and_env_override_never_resolves_to_codex(tmp_path, monkeypatch, no_subprocess,
                                                                          state):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with fake_chatgpt() as server:
        _set_state(state, server)
        vault = _vault(tmp_path)
        config = load_config(vault / "learnloop.toml")
        sample = [task for task in TASKS if task not in NON_GENERATION]
        for name in _profile_names(config):
            config.ai.fallback_provider = name
            for task in sample:
                resolved = ready_client_for_task(vault, config, task)  # type: ignore[arg-type]
                _assert_never_harness(resolved, task, f"fallback={name}")
            selection = provider_for_task(config, "grading")
            if name in CODEX_NAMES:
                assert fallback_provider_for(config, selection) is None
        config.ai.fallback_provider = None
        for name in _profile_names(config):
            monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", name)
            for task in sample:
                resolved = ready_client_for_task(vault, config, task)  # type: ignore[arg-type]
                _assert_never_harness(resolved, task, f"LEARNLOOP_AI_PROVIDER={name}")
        monkeypatch.delenv("LEARNLOOP_AI_PROVIDER")
        assert server.requests == []


def test_the_opt_in_admits_codex_and_codex_is_still_never_a_fallback(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr("learnloop.ai.runtime.check_codex_runtime", lambda *a, **k: SimpleNamespace(
        status="ready", actual_revision=None, message="ok"))
    with fake_chatgpt():
        vault = _vault(tmp_path, opt_in=True, extra={"ai.fallback_provider": "codex", "ai.routing.tutor_qa": "codex_low"})
        config = load_config(vault / "learnloop.toml")
        assert config.ai.agent_harness_opt_in is True
        pinned = ready_client_for_task(vault, config, "tutor_qa")
        assert pinned.ready and pinned.client.provider_type == "codex_sdk"
        # The plan is signed out: the route on it does NOT fall back to Codex.
        grading = ready_client_for_task(vault, config, "grading")
        assert grading.provider_name == "chatgpt_low" and not grading.ready
        assert fallback_provider_for(config, provider_for_task(config, "grading")) is None


# -- (2) admission equals wire and (3) body grammar ----------------------------------------------


class _Log(list):
    """The fake server's request list, also writing one shared, ordered log."""

    def __init__(self, events: list[tuple[str, int]], lock: threading.Lock) -> None:
        super().__init__()
        self.events, self.lock = events, lock

    def append(self, item: Any) -> None:  # noqa: D401 - list protocol
        with self.lock:
            super().append(item)
            self.events.append(("post", len(self)))


class RecordingGate:
    def __init__(self, events: list[tuple[str, int]], lock: threading.Lock) -> None:
        self.events, self.lock, self.admits = events, lock, 0

    def admit(self, client: Any, *, purpose: str, prompt: Any, budget: int | None) -> int:
        with self.lock:
            self.admits += 1
            self.events.append(("admit", self.admits))
            return self.admits

    def settle(self, admission: Any, usage: dict[str, Any]) -> None:
        return None


def _workspace(tmp_path: Path, *, big: int = 0) -> Path:
    root = tmp_path / "workspace"
    (root / "attempts").mkdir(parents=True, exist_ok=True)
    (root / "INDEX.md").write_text("# Index\n- attempts/a.md: lo_x; non_pass\n", encoding="utf-8")
    (root / "attempts" / "a.md").write_text("# Attempt att_a\n- outcome: non_pass\n", encoding="utf-8")
    if big:
        (root / "attempts" / "big.md").write_text("w" * big, encoding="utf-8")
    return root


def _plan_client(server, **profile) -> ChatGPTPlanProviderClient:
    settings = {"model": "gpt-test-fast", "base_url": server.base_url, "timeout_seconds": 10, **profile}
    return ChatGPTPlanProviderClient("chatgpt", ChatGPTPlanProviderConfig(**settings))


def _assert_admitted_then_sent(events: list[tuple[str, int]], gate: RecordingGate, server) -> None:
    posts = [index for kind, index in events if kind == "post"]
    assert len(posts) == len(server.requests) == gate.admits, events
    # Strictly alternating: admit n, then post n, for every n.
    assert events == [entry for n in range(1, gate.admits + 1) for entry in (("admit", n), ("post", n))], events


def _assert_body_grammar(body: dict[str, Any], *, tools_mode: bool) -> None:
    assert body["store"] is False and body["stream"] is True
    if tools_mode and "tools" in body:
        assert set(body) <= PLAIN_KEYS | {"tools", "include"}
        assert body["tools"] == [ServedWorkspace.namespace_tool()]
        assert [tool["name"] for tool in body["tools"]] == [NAMESPACE] == ["workspace"]
        assert all(fn["type"] == "function" for fn in body["tools"][0]["tools"])
        assert body["include"] == ["reasoning.encrypted_content"]
    else:
        assert set(body) <= PLAIN_KEYS, sorted(set(body) - PLAIN_KEYS)


SCENARIOS = ("first_try", "transient_retry", "refresh_401", "json_repair", "inline_workspace", "tool_rounds",
             "inline_overflow_tools", "usage_limit")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_admission_equals_wire_and_every_body_keeps_the_grammar(tmp_path, scenario):
    events: list[tuple[str, int]] = []
    lock = threading.Lock()
    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        server.requests = _Log(events, lock)
        gate = RecordingGate(events, lock)
        workspace = None
        profile: dict[str, Any] = {}
        answer = completed_events('{"ok": true, "note": "done"}')
        if scenario == "first_try":
            server.replies.append(Reply(events=answer))
        elif scenario == "transient_retry":
            server.replies.extend([Reply(status=503, body={"detail": "direct routing unavailable"}),
                                   Reply(events=answer)])
        elif scenario == "refresh_401":
            server.revoke_all_access()
            server.replies.append(Reply(events=answer))
        elif scenario == "json_repair":
            profile = {"response_format": "json_object"}
            server.replies.extend([Reply(events=completed_events('{"ok": true}')), Reply(events=answer)])
        elif scenario == "inline_workspace":
            workspace = _workspace(tmp_path)
            server.replies.append(Reply(events=answer))
        elif scenario == "tool_rounds":
            workspace = _workspace(tmp_path)
            profile = {"workspace_mode": "tools"}
            server.replies.extend([
                Reply(events=tool_call_events([("list_entries", {"directory": None})], response_id="r1")),
                Reply(events=tool_call_events([("read_entry", {"path": "INDEX.md", "start_line": None,
                                                               "max_lines": None})], response_id="r2")),
                Reply(events=answer),
            ])
        elif scenario == "inline_overflow_tools":
            workspace = _workspace(tmp_path, big=20_000)
            profile = {"max_workspace_chars": 10_000}
            server.replies.extend([
                Reply(events=tool_call_events([("read_entry", {"path": "INDEX.md", "start_line": None,
                                                               "max_lines": None})], response_id="r1")),
                Reply(events=answer),
            ])
        elif scenario == "usage_limit":
            server.replies.append(Reply(events=failed_events("subscription_sharing_usage_limit_exceeded",
                                                             after_deltas="{")))
        client = _plan_client(server, **profile)
        kwargs = {"workspace": workspace} if workspace is not None else {}
        with gate_model_requests(gate):
            if scenario == "usage_limit":
                with pytest.raises(Exception, match="usage"):
                    execute_structured_operation(client, purpose="t1", prompt="Say ok", result_model=Answer, **kwargs)
                # Paused: refused locally, neither admitted nor sent.
                with pytest.raises(Exception, match="usage"):
                    execute_structured_operation(client, purpose="t1", prompt="Say ok", result_model=Answer, **kwargs)
            else:
                result = execute_structured_operation(client, purpose="t1", prompt="Say ok", result_model=Answer,
                                                      **kwargs)
                assert result.note == "done"
        _assert_admitted_then_sent(events, gate, server)
        expected_posts = {"first_try": 1, "transient_retry": 2, "refresh_401": 2, "json_repair": 2,
                          "inline_workspace": 1, "tool_rounds": 3, "inline_overflow_tools": 2, "usage_limit": 1}
        assert gate.admits == expected_posts[scenario]
        bodies = [request["body"] for request in server.requests]
        for body in bodies:
            _assert_body_grammar(body, tools_mode=scenario in {"tool_rounds", "inline_overflow_tools"})
        if scenario == "inline_workspace":
            # Diagnosis on the plan is inline by default: one request, no tools.
            assert "tools" not in bodies[0] and "include" not in bodies[0]
            assert '<workspace_file path="INDEX.md">' in bodies[0]["input"][0]["content"]
        if scenario == "inline_overflow_tools":
            assert all("tools" in body for body in bodies)
            assert client.workspace_record()["mode"] == "tools"
            assert client.workspace_record()["inline_overflow"] is True


def test_a_plain_call_never_carries_tools_even_when_asked_for_a_workspace_route():
    """``_respond`` (every non-workspace call and every JSON repair) builds a body without tools."""

    source = (SRC / "learnloop/ai/providers/chatgpt_plan.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    respond = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_respond")
    calls = [node for node in ast.walk(respond) if isinstance(node, ast.Call)
             and getattr(node.func, "id", None) == "request_body"]
    assert len(calls) == 1 and not {kw.arg for kw in calls[0].keywords} & {"tools", "input_items"}


# -- (4) one egress point -------------------------------------------------------------------------


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_responses_stream_is_built_and_sent_only_inside_send_once_under_model_call():
    hits: list[tuple[str, int]] = []
    for path in SRC.rglob("*.py"):
        if path.name == "responses.py" and path.parent.name == "chatgpt_plan":
            continue  # the class itself
        text = path.read_text(encoding="utf-8")
        if "ResponsesStream" not in text:
            continue
        for node in ast.walk(_parse(path)):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "ResponsesStream":
                hits.append((str(path.relative_to(SRC)), node.lineno))
    assert [where for where, _line in hits] == ["learnloop/ai/providers/chatgpt_plan.py"]

    tree = _parse(SRC / "learnloop/ai/providers/chatgpt_plan.py")
    send_once = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_send_once")
    built = [node for node in ast.walk(send_once) if isinstance(node, ast.Call)
             and getattr(node.func, "id", None) == "ResponsesStream"]
    assert len(built) == 1 and built[0].lineno == hits[0][1]
    # Every `.send(` in the module is `stream.send(` inside `with model_call(...)` in _send_once.
    sends = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == "send"]
    assert len(sends) == 1
    guarded = [
        node for node in ast.walk(send_once) if isinstance(node, ast.With)
        and any(isinstance(item.context_expr, ast.Call) and getattr(item.context_expr.func, "id", None) == "model_call"
                for item in node.items)
    ]
    assert len(guarded) == 1
    assert sends[0] in list(ast.walk(guarded[0]))
    assert getattr(sends[0].func.value, "id", None) == "stream"


#: Every module that imports an HTTP client, audited (plan-first T1). The
#: model-inference ones are the plan, the OpenAI-compatible/OpenRouter family
#: and the frozen Codex modules (opt-in only, deleted in T2); the rest fetch
#: sources, run OCR, or talk to local services and send no route's prompt.
HTTP_MODULES = {
    # model inference
    "learnloop/ai/chatgpt_plan/responses.py": "plan: the one Responses stream",
    "learnloop/ai/chatgpt_plan/oauth.py": "plan: sign-in and token refresh (no model request)",
    "learnloop/ai/providers/openai_chat.py": "OpenAI-compatible chat (OpenRouter, DeepSeek)",
    "learnloop/ai/providers/openrouter_catalog.py": "OpenRouter model catalog (no model request)",
    "learnloop/ai/providers/openrouter_video.py": "OpenRouter video generation",
    "learnloop/ai/providers/decider.py": "the Decider on OpenRouter",
    "learnloop/ai/providers/openai_embedding.py": "embeddings on OpenRouter",
    "learnloop/ingest/transcription.py": "OpenRouter/OpenAI transcription",
    "learnloop/ai/providers/codex.py": "FROZEN Codex (opt-in only; T2 deletes)",
    "learnloop/ai/providers/codex_http.py": "FROZEN Codex HTTP adapter (opt-in only; T2 deletes)",
    # not a route's model request
    "learnloop/content/pipeline/source_ingestion.py": "source fetch",
    "learnloop/ingest/extractors/datalab.py": "Datalab OCR",
    "learnloop/ingest/extractors/glm_ocr.py": "GLM OCR",
    "learnloop/ingest/fetchers.py": "web fetch",
}
_HTTP_ROOTS = ("urllib", "http.client", "httpx", "requests", "openai", "aiohttp", "openai_codex")


def _imports_http(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            # `from urllib import request` names the submodule it imports.
            names = ([f"urllib.{alias.name}" for alias in node.names] if node.module == "urllib"
                     else [node.module])
        names = [name for name in names if name not in {"urllib", "urllib.parse"}]  # URL parsing only
        if any(name == root or name.startswith(root + ".") for name in names for root in _HTTP_ROOTS):
            return True
    return False


def test_http_clients_are_imported_only_by_audited_modules():
    found = {
        str(path.relative_to(SRC)) for path in SRC.rglob("*.py")
        if path.parts[-2] != "__pycache__" and _imports_http(_parse(path))
    }
    assert found == set(HTTP_MODULES), {"new": sorted(found - set(HTTP_MODULES)),
                                        "gone": sorted(set(HTTP_MODULES) - found)}


def test_the_plan_bearer_goes_only_to_openai_or_loopback():
    for refused in ("https://example.com/v1", "https://api.openai.com.evil.test/v1", "http://api.openai.com/v1"):
        with pytest.raises(ValueError):
            ChatGPTPlanProviderConfig(model="m", base_url=refused)
    for allowed in ("https://api.openai.com/v1", "http://127.0.0.1:9/v1"):
        ChatGPTPlanProviderConfig(model="m", base_url=allowed)


# -- (5) no serving Codex launch ------------------------------------------------------------------


@pytest.mark.parametrize("profile_type", sorted(AGENT_HARNESS_PROFILE_TYPES))
def test_a_harness_profile_without_the_opt_in_raises_before_any_process(tmp_path, no_subprocess, profile_type):
    config = LearnLoopConfig.model_validate({"ai": {"providers": {"x": {"type": profile_type, "model": "m"}}}})
    profile = config.ai.providers["x"]
    with pytest.raises(AgentHarnessRefused, match="agent harness"):
        make_ai_provider_client_from_profile("x", profile, tmp_path)
    with pytest.raises(AgentHarnessRefused):
        make_ai_provider_client_from_profile("codex", config.ai.providers["codex"], tmp_path)


def test_readiness_of_a_refused_codex_profile_runs_no_health_check(tmp_path, monkeypatch, no_subprocess):
    from learnloop.ai.runtime import check_ai_runtime

    def health(*_args, **_kwargs):
        raise AssertionError("the Codex health check ran")

    monkeypatch.setattr("learnloop.ai.runtime.check_codex_runtime", health)
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    for name in CODEX_NAMES:
        report = check_ai_runtime(vault, config, provider_name=name)
        assert report.status == "provider_unavailable" and "ai.agent_harness_opt_in" in report.message


def test_serving_entry_points_never_load_the_codex_provider(tmp_path):
    """Importing every serving entry point and resolving every task loads no Codex module."""

    home = tmp_path / "home"
    home.mkdir()
    vault = _vault(tmp_path)
    script = f"""
import sys
from typing import get_args
import learnloop.cli.app, learnloop_sidecar.server, learnloop_sidecar.handlers
import learnloop.ops.startup, learnloop.attempts.regrade, learnloop.attempts.attempts
from learnloop.ai.routing import AITask, ready_client_for_task
from learnloop.config import load_config
from pathlib import Path
vault = Path({str(vault)!r})
config = load_config(vault / "learnloop.toml")
for task in get_args(AITask):
    ready_client_for_task(vault, config, task)
for name in ("codex", "codex_low"):
    ready_client_for_task(vault, config, "grading", explicit=name)
loaded = sorted(m for m in sys.modules if m.startswith("learnloop.ai.providers.codex") or m == "openai_codex")
print(loaded)
"""
    env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "CODEX_HOME": str(home / "codex"),
           "LEARNLOOP_CONFIG_DIR": str(home / "config"), "PYTHONPATH": str(ROOT / "src") + ":" + str(ROOT)}
    completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env,
                               cwd=str(tmp_path), timeout=300)
    assert completed.returncode == 0, completed.stderr[-2000:]
    assert completed.stdout.strip().splitlines()[-1] == "[]"


def test_no_module_outside_the_codex_provider_starts_a_codex_process():
    """Every process launch whose arguments mention Codex lives in the frozen provider."""

    launchers = {"Popen", "run", "check_output", "check_call", "call", "create_subprocess_exec",
                 "create_subprocess_shell", "spawn", "execv", "execvp", "execve", "posix_spawn"}
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        relative = str(path.relative_to(SRC))
        if relative.startswith("learnloop/ai/providers/codex"):
            continue
        text = path.read_text(encoding="utf-8")
        if "codex" not in text.lower():
            continue
        for node in ast.walk(_parse(path)):
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                if name in launchers and "codex" in ast.unparse(node).lower():
                    offenders.append(f"{relative}:{node.lineno}")
    assert offenders == []


# -- (6) the OpenRouter ask ------------------------------------------------------------------------


def test_unavailable_offers_openrouter_only_when_configured_and_sends_nothing_unasked(tmp_path, monkeypatch):
    from tests.openai_fakes import install_fake_openai

    fake_openai = install_fake_openai(monkeypatch, '{"ok": true, "note": "openrouter"}')
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    # No key: no offer at all.
    with plan_fallback.collecting() as offers:
        resolved = ready_client_for_task(vault, config, "tutor_qa")
    assert not resolved.ready and resolved.runtime.fallback_available is None
    assert offers.hint() is None and "fallback_available" not in resolved.runtime.as_dict()
    # A key: offered (typed, in the runtime and the request's hint), never built or sent.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with plan_fallback.collecting() as offers:
        resolved = ready_client_for_task(vault, config, "tutor_qa")
    assert not resolved.ready and resolved.client is None and resolved.provider_name == "chatgpt_low"
    assert resolved.runtime.fallback_available == "openrouter"
    assert resolved.runtime.as_dict()["fallback_profile"] == "openrouter"
    assert "Use OpenRouter instead" in resolved.runtime.message
    assert offers.hint() == {"fallback_available": "openrouter", "fallback_profile": "openrouter",
                             "fallback_tasks": ["tutor_qa"], "plan_signed_out": True}
    assert fake_openai.instances == []
    # A readiness probe asks nothing.
    with plan_fallback.collecting() as offers, plan_fallback.quiet():
        ready_client_for_task(vault, config, "tutor_qa")
    assert offers.hint() is None
    # The learner's choice (this task, this vault, this session): OpenRouter serves it.
    _grant(vault, ["tutor_qa"])
    chosen = ready_client_for_task(vault, config, "tutor_qa")
    assert chosen.ready and chosen.provider_name == "openrouter" and chosen.fallback_from == "chatgpt_low"
    assert chosen.client.supports(TOOL_FREE)
    # A pinned selection (a named profile, LEARNLOOP_AI_PROVIDER) is never replaced.
    pinned = ready_client_for_task(vault, config, "tutor_qa", explicit="chatgpt_low")
    assert not pinned.ready and pinned.provider_name == "chatgpt_low" and pinned.runtime.fallback_available is None
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "chatgpt")
    assert ready_client_for_task(vault, config, "tutor_qa").provider_name == "chatgpt"
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER")
    with plan_fallback.request(None, "test.another_action"):  # another action: still asked (redesign D)
        other = ready_client_for_task(vault, config, "grading")
    assert not other.ready and other.runtime.fallback_available == "openrouter"
    # A grant is for the feature the learner used, never for background work:
    # startup maintenance (a quiet probe) finds a granted task's plan route
    # unavailable and leaves the deferred-regrade backlog for the plan.
    _grant(vault, ["grading"])
    with plan_fallback.quiet():
        background = ready_client_for_task(vault, config, "grading")
    assert not background.ready and background.provider_name == "chatgpt_low"
    monkeypatch.setenv("LEARNLOOP_AI_FALLBACK", "openrouter")
    with plan_fallback.command_grant(), plan_fallback.quiet():
        assert not ready_client_for_task(vault, config, "grading").ready
    monkeypatch.delenv("LEARNLOOP_AI_FALLBACK")
    plan_fallback.revoke_all()
    # The CLI's one-command choice (read by the CLI's entry point only).
    monkeypatch.setenv("LEARNLOOP_AI_FALLBACK", "openrouter")
    with plan_fallback.command_grant():
        assert ready_client_for_task(vault, config, "grading").provider_name == "openrouter"
    monkeypatch.delenv("LEARNLOOP_AI_FALLBACK")
    # A signed-in plan is always used first, granted or not.
    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        _grant(vault, ["tutor_qa"])
        assert ready_client_for_task(vault, config, "tutor_qa").provider_name == "chatgpt_low"
    assert all(instance.requests == [] for instance in fake_openai.instances)  # built, never called


def test_a_plan_call_that_fails_for_availability_offers_openrouter_for_that_route(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        vault = _vault(tmp_path, extra={"ai.providers.chatgpt.base_url": server.base_url})
        config = load_config(vault / "learnloop.toml")
        server.replies.append(Reply(status=429, body={"error": {
            "code": "subscription_sharing_usage_limit_exceeded", "message": "limit"}}))
        with plan_fallback.collecting() as offers:
            resolved = ready_client_for_task(vault, config, "tutor_qa")
            assert resolved.ready and resolved.client.provider_type == "chatgpt_plan"
            assert offers.hint() is None  # nothing failed yet
            with pytest.raises(Exception, match="usage"):
                execute_structured_operation(resolved.client, purpose="t1", prompt="Say ok", result_model=Answer)
        assert offers.hint()["fallback_tasks"] == ["tutor_qa"]
        assert offers.hint()["plan_signed_out"] is False


def test_the_sidecar_attaches_the_typed_hint_and_ai_use_fallback_records_the_choice(tmp_path, monkeypatch):
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.dto import EmptyParams
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.registry import METHOD_REGISTRY, MethodSpec
    from learnloop_sidecar.server import _handle

    vault = _vault(tmp_path)

    def feature(ctx, _params):
        loaded, _repository = ctx.require_vault()
        resolved = ready_client_for_task(loaded.root, loaded.config, "tutor_qa")
        if not resolved.ready:
            raise SidecarError("ai_unavailable", resolved.runtime.message or "unavailable")
        return {"provider": resolved.provider_name}

    monkeypatch.setitem(METHOD_REGISTRY, "test.t1_feature", MethodSpec("test.t1_feature", EmptyParams, feature))
    ctx = SidecarContext()
    ctx.load(vault)

    def rpc(method_name, params=None):
        return _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method_name, "params": params or {}})

    # No OpenRouter key: unavailable, no offer; the choice is refused.
    response = rpc("test.t1_feature")
    assert response["error"]["data"]["code"] == "ai_unavailable"
    assert "fallback_available" not in response["error"]["data"].get("details", {})
    refused = rpc("ai_use_fallback", {"provider": "openrouter", "offerId": "fo_none"})
    assert refused["error"]["data"]["code"] == "fallback_unavailable"
    # A key: the error carries the typed hint, the offer's id and the action that asked.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    response = rpc("test.t1_feature")
    details = response["error"]["data"]["details"]
    assert (details["fallback_available"], details["fallback_tasks"], details["fallback_profile"]) == (
        "openrouter", ["tutor_qa"], "openrouter")
    assert details["fallback_origin"] == "test.t1_feature" and details["fallback_offer_id"]
    assert "fallback_units" not in details
    # The desktop's "Use OpenRouter instead" answers that offer; an unknown one answers nothing.
    unknown = rpc("ai_use_fallback", {"provider": "openrouter", "offerId": "fo_not_an_offer"})
    assert unknown["error"]["data"]["code"] == "not_offered"
    chosen = rpc("ai_use_fallback", {"provider": "openrouter", "offerId": details["fallback_offer_id"]})
    assert chosen["result"]["grantedActions"] == ["test.t1_feature"] and chosen["result"]["scope"] == "session"
    assert chosen["result"]["grantedTasks"] == ["tutor_qa"]
    assert rpc("test.t1_feature")["result"] == {"provider": "openrouter"}
    stopped = rpc("ai_use_fallback", {"provider": "openrouter", "stop": True})
    assert stopped["result"]["grantedTasks"] == []
    assert rpc("test.t1_feature")["error"]["data"]["code"] == "ai_unavailable"
    # The health line is a probe: it never carries the offer.
    health = rpc("get_runtime_health")
    assert "result" in health and "fallbackAvailable" not in health["result"]


def test_a_background_jobs_offer_reaches_the_read_that_finds_it_done(tmp_path, monkeypatch):
    """Hints, library asks, margin notes and reading paths run on worker threads.

    A thread has no RPC collector, so each job keeps its own offers and the
    poll RPC that finds it done relays them into its own hint; a job run
    inline hands them to the enclosing RPC as well.
    """

    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.errors import SidecarError
    from learnloop_sidecar.handlers import hints as hint_rpcs, library_ask as library_rpcs

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    # The hint writer refuses a metered route until its price is set, so it is offered only then (F2).
    vault = _vault(tmp_path, extra={"hints.price_per_million": 1.0})
    ctx = SidecarContext()
    ctx.load(vault)

    def unavailable(task: str):
        def work(*_args):
            loaded, _repository = ctx.require_vault()
            resolved = ready_client_for_task(loaded.root, loaded.config, task)  # type: ignore[arg-type]
            assert not resolved.ready
            raise SidecarError("ai_unavailable", resolved.runtime.message or "unavailable")
        return work

    # Started in a request: the job belongs to that action and asks as it (redesign D).
    if True:
        library_job = library_rpcs.LibraryJobs().start(ctx, "ask", None, unavailable("tutor_qa"))
    if True:
        hint_job = hint_rpcs.HintJobs().start(ctx, "item_1", unavailable("hint_writer"))
    assert library_job.done.wait(10) and hint_job.done.wait(10)
    # Polled from an RPC that resolved nothing itself: the job's offer is relayed.
    with plan_fallback.collecting() as offers:
        with pytest.raises(SidecarError):
            library_rpcs._job_payload(library_job)
    # Relayed as the job's own offer (its action, vault and epoch: round 5), what the dispatch mints.
    assert plan_fallback.take_offer(offers, vault)[0]["fallback_tasks"] == ["tutor_qa"]
    with plan_fallback.collecting() as offers:
        with pytest.raises(SidecarError):
            hint_rpcs._job_payload(ctx, hint_job)
    assert plan_fallback.take_offer(offers, vault)[0]["fallback_tasks"] == ["hint_writer"]
    # Relayed once (review F8): a later read of the same failed job brings no banner back.
    with plan_fallback.collecting() as offers:
        with pytest.raises(SidecarError):
            library_rpcs._job_payload(library_job)
    assert plan_fallback.take_offer(offers, vault) == (None, None)
    # Without a key no job offers anything.
    monkeypatch.delenv("OPENROUTER_API_KEY")
    if True:
        quiet_job = library_rpcs.LibraryJobs().start(ctx, "ask", None, unavailable("tutor_qa"))
    assert quiet_job.done.wait(10) and quiet_job.fallback_offer is None
    # A job no press started (opening margin notes, a suggestion) asks nothing either (round 2).
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with plan_fallback.quiet():  # started by automatic work: it belongs to no action
        unpressed = library_rpcs.LibraryJobs().start(ctx, "ask", None, unavailable("tutor_qa"))
    assert unpressed.done.wait(10) and unpressed.fallback_offer is None
    monkeypatch.delenv("OPENROUTER_API_KEY")
    # A nested collector (a job run inline) hands its offers to the enclosing one.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    with plan_fallback.collecting() as outer:
        with plan_fallback.collecting() as inner:
            plan_fallback.note_unavailable("grading", "openrouter")
        assert inner.hint()["fallback_tasks"] == ["grading"]
    assert outer.hint()["fallback_tasks"] == ["grading"]


def test_the_cli_json_carries_the_hint(tmp_path, monkeypatch):
    from learnloop.cli.render import _dump

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    with plan_fallback.collecting():
        ready_client_for_task(vault, config, "grading")
        payload = json.loads(_dump({"status": "unavailable"}))
    assert payload["fallback_available"] == "openrouter" and payload["fallback_tasks"] == ["grading"]
    assert "fallback_available" not in json.loads(_dump({"status": "unavailable"}))


# -- (7) doctor --fix -------------------------------------------------------------------------------


def _pinned_vault(tmp_path: Path) -> Path:
    vault = _vault(tmp_path)
    path = vault / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    document["ai"]["active_provider"] = "codex"
    document["ai"]["fallback_provider"] = "codex"
    for task, name in LEGACY_CODEX_TASK_ROUTES.items():
        document["ai"]["routing"][task] = name
    document["ai"]["routing"]["pf_proposers"] = ["codex_low", "openrouter", "codex_medium"]
    path.write_text("# owner comment kept\n" + tomlkit.dumps(document), encoding="utf-8")
    return vault


def test_doctor_reports_each_pinned_codex_setting_and_fix_rewrites_it(tmp_path):
    from learnloop.ops.doctor import run_doctor
    from learnloop.ops.plan_transport import FINDING_CODE, codex_pins, fix_codex_pins

    vault = _pinned_vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    findings = [issue for issue in run_doctor(vault).issues if issue.code == FINDING_CODE]
    settings = {issue.details["setting"] for issue in findings}
    assert settings == {"ai.active_provider", "ai.fallback_provider", "ai.routing.pf_proposers",
                        *(f"ai.routing.{task}" for task in LEGACY_CODEX_TASK_ROUTES)}
    assert all("doctor --fix" in issue.message for issue in findings)
    dry = fix_codex_pins(vault, config, dry_run=True)
    assert dry["dry_run"] is True and len(dry["rewritten"]) == len(findings)
    assert len(codex_pins(vault, load_config(vault / "learnloop.toml"))) == len(findings)  # nothing written
    fix_codex_pins(vault, config)
    text = (vault / "learnloop.toml").read_text(encoding="utf-8")
    assert text.startswith("# owner comment kept\n")
    fixed = load_config(vault / "learnloop.toml")
    assert fixed.ai.active_provider == "chatgpt" and not fixed.ai.fallback_provider
    for task, name in LEGACY_CODEX_TASK_ROUTES.items():
        assert getattr(fixed.ai.routing, task) == CODEX_TO_PLAN_PROFILE[name], task
    assert fixed.ai.routing.pf_proposers == ["chatgpt_low", "openrouter", "chatgpt_medium"]
    assert not [issue for issue in run_doctor(vault).issues if issue.code == FINDING_CODE]
    # Opted in: Codex settings are served as written, so nothing is reported.
    opted = _vault(tmp_path / "opted", opt_in=True, extra={"ai.routing.grading": "codex_low"})
    assert not [issue for issue in run_doctor(opted).issues if issue.code == FINDING_CODE]


def test_cli_doctor_fix_dry_run_then_fix(tmp_path):
    from learnloop.cli import app

    runner = CliRunner()
    vault = _pinned_vault(tmp_path)
    before = (vault / "learnloop.toml").read_text(encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--vault", str(vault), "--fix", "--dry-run"])
    assert "Would set ai.routing.grading: 'codex_low' -> 'chatgpt_low'" in result.output
    assert (vault / "learnloop.toml").read_text(encoding="utf-8") == before
    result = runner.invoke(app, ["doctor", "--vault", str(vault), "--fix", "--json"])
    payload = json.loads(result.output)
    assert {change["setting"] for change in payload["fix"]["rewritten"]} >= {"ai.routing.grading"}
    assert not [issue for issue in payload["issues"] if issue["code"] == "ai:codex_route_pinned"]
    assert runner.invoke(app, ["doctor", "--vault", str(vault), "--dry-run"]).exit_code == 2


def test_doctor_names_a_configured_slug_the_account_does_not_list(tmp_path):
    from learnloop.ai.providers.chatgpt_plan import list_plan_models
    from learnloop.ops.doctor import run_doctor

    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        vault = _vault(tmp_path)
        assert not [i for i in run_doctor(vault).issues if i.code == "ai:chatgpt_plan_model_not_listed"]
        list_plan_models(server.base_url)  # `learnloop ai models chatgpt` remembers the list
        issues = [i for i in run_doctor(vault).issues if i.code == "ai:chatgpt_plan_model_not_listed"]
        assert {issue.details["model"] for issue in issues} == {"gpt-5.6-sol", "gpt-6-luna"}
        assert any("[ai.providers.chatgpt] model" in issue.message for issue in issues)
        fixed = _vault(tmp_path, extra={"ai.providers.chatgpt.model": "gpt-test-fast",
                                        "ai.providers.chatgpt_luna.type": "chatgpt_plan",
                                        "ai.providers.chatgpt_luna.model": "gpt-test-pro"})
        assert not [i for i in run_doctor(fixed).issues if i.code == "ai:chatgpt_plan_model_not_listed"]


# -- (8) prompts and parsing unchanged ---------------------------------------------------------------


def test_the_stage_changes_transport_selection_only():
    """The served model changes (owner-approved); the prompt each route builds does not.

    The plan's instructions and body are the provider's own (unchanged since
    the peer stage); here the same operation's prompt reaches the plan's wire
    verbatim, so a route's prompt builder and parser are what they were.
    """

    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        server.replies.append(Reply(events=completed_events('{"ok": true, "note": "done"}')))
        client = _plan_client(server)
        prompt = "Grade this answer against the rubric. <unchanged route prompt>"
        assert execute_structured_operation(client, purpose="grading_proposal", prompt=prompt,
                                            result_model=Answer).note == "done"
        content = server.requests[-1]["body"]["input"][0]["content"]
        assert content.startswith(prompt)


# -- (9) Codex review fixes (docs/reviews/ai-plan-first-transport-t1-codex-review.md) -------------


def test_f1_a_configured_metered_fallback_provider_is_never_used_silently_for_a_plan_route(tmp_path, monkeypatch):
    """Review F1: `fallback_provider = "openrouter"` once served every unavailable plan route, unasked."""

    from learnloop.ai.routing import configured_fallback
    from learnloop.content.pipeline.add_source import authoring_route_for
    from learnloop.content.proposals.method_phrasing import writer_names
    from learnloop.ops.doctor import run_doctor
    from learnloop.ops.plan_transport import METERED_FALLBACK_CODE
    from learnloop.vault.loader import load_vault
    from tests.openai_fakes import install_fake_openai

    fake_openai = install_fake_openai(monkeypatch, '{"ok": true, "note": "openrouter"}')
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path, extra={"ai.fallback_provider": "openrouter"})
    config = load_config(vault / "learnloop.toml")
    for task in ("grading", "tutor_qa", "diagnosis", "hint_writer", "canonical_ingest"):
        with plan_fallback.collecting() as offers:
            resolved = ready_client_for_task(vault, config, task)  # type: ignore[arg-type]
        assert not resolved.ready and resolved.provider_name in CHATGPT_PLAN_PROVIDER_NAMES, task
        assert resolved.fallback_from is None, task
        if plan_fallback.offer_blocker(config, task) is None:
            # Asked instead, through the plan's offer.
            assert resolved.runtime.fallback_available == "openrouter", task
            assert offers.hint()["fallback_tasks"] == [task]
        # Startup maintenance (quiet) never takes the configured fallback either.
        with plan_fallback.quiet():
            assert not ready_client_for_task(vault, config, task).ready, task  # type: ignore[arg-type]
    assert configured_fallback(config, "chatgpt_low") is None
    # A non-plan primary keeps the owner's fallback as written.
    assert configured_fallback(config, "deepseek_flash") == "openrouter"
    # The direct readers follow the same rule: the question build and the method-phrasing writer.
    route = authoring_route_for(vault, config)
    assert not route.ready and route.provider in CHATGPT_PLAN_PROVIDER_NAMES
    assert "openrouter" not in writer_names(load_vault(vault))
    # Doctor names the setting.
    issues = [issue for issue in run_doctor(vault).issues if issue.code == METERED_FALLBACK_CODE]
    assert len(issues) == 1 and issues[0].details["value"] == "openrouter"
    assert "never sends work to a metered provider without asking" in issues[0].message
    assert fake_openai.instances == []  # no OpenRouter client was even built


def test_f2_openrouter_is_offered_only_when_the_feature_could_use_it(tmp_path, monkeypatch):
    """Review F2: a feature that refuses an unpriced metered route makes no offer; it says what to set."""

    from learnloop.config.schema import LearnLoopConfig as Config

    defaults = Config()
    for task, setting in plan_fallback.METERED_PRICE_SETTINGS.items():
        assert task in TASKS, task
        assert plan_fallback._setting(defaults, setting) is None, setting  # unset by default: refused
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    with plan_fallback.collecting() as offers:
        hint = ready_client_for_task(vault, config, "hint_writer")
    assert not hint.ready and hint.runtime.fallback_available is None and offers.hint() is None
    assert "hints.price_per_million" in hint.runtime.message
    priced = _vault(tmp_path, extra={"hints.price_per_million": 1.0})
    with plan_fallback.collecting() as offers:
        hint = ready_client_for_task(priced, load_config(priced / "learnloop.toml"), "hint_writer")
    assert hint.runtime.fallback_available == "openrouter" and offers.hint()["fallback_tasks"] == ["hint_writer"]
    # A snapshot diagnosis reads a workspace only the plan serves: not offered.
    snapshot = _vault(tmp_path, extra={"diagnosis.history_mode": "snapshot"})
    with plan_fallback.collecting() as offers:
        diagnosis = ready_client_for_task(snapshot, load_config(snapshot / "learnloop.toml"), "diagnosis")
    assert diagnosis.runtime.fallback_available is None and offers.hint() is None
    assert "snapshot" in diagnosis.runtime.message
    # A ready plan route that later fails for availability offers nothing for a blocked task either.
    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        with plan_fallback.collecting() as offers:
            assert ready_client_for_task(vault, config, "hint_writer").ready
            plan_fallback.note_plan_failure()
        assert offers.hint() is None


def test_f3_the_question_build_asks_and_a_grant_serves_it_priced_as_metered(tmp_path, monkeypatch):
    """Review F3: the add-source build's route goes through the offer, and a grant routes and prices it."""

    from learnloop.content.pipeline.add_source import authoring_route_for, is_subscription_route

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    with plan_fallback.collecting() as offers:
        route = authoring_route_for(vault, config)
    assert not route.ready and route.provider in CHATGPT_PLAN_PROVIDER_NAMES and route.subscription
    assert offers.hint()["fallback_tasks"] == ["canonical_ingest"]
    assert "Use OpenRouter instead" in (route.message or "")
    _grant(vault, ["canonical_ingest"])
    granted = authoring_route_for(vault, config)
    assert granted.ready and granted.provider == "openrouter"
    # Priced and consented as the profile that serves it: metered, never "subscription".
    assert granted.subscription is False and not is_subscription_route(config, granted.provider)
    assert granted.consent_key != route.consent_key


def test_f4_grants_are_per_vault_per_offer_and_the_env_grant_is_the_cli_commands_only(tmp_path, monkeypatch):
    """Review F4: the env variable grants nothing outside the CLI's command context; grants are per vault."""

    import contextvars

    from learnloop_sidecar.context import SidecarContext

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    # (a) Exported in the shell that started a long-lived host: grants nothing there.
    monkeypatch.setenv("LEARNLOOP_AI_FALLBACK", "openrouter")
    assert not ready_client_for_task(vault, config, "grading").ready
    with plan_fallback.command_grant(host=True) as chosen:
        assert chosen is False and not ready_client_for_task(vault, config, "grading").ready
    with plan_fallback.command_grant() as chosen:
        assert chosen is True and ready_client_for_task(vault, config, "grading").ready
        # A background thread started in a fresh context does not inherit the command's grant.
        seen: list[bool] = []
        thread = threading.Thread(target=lambda: contextvars.Context().run(
            lambda: seen.append(ready_client_for_task(vault, config, "grading").ready)))
        thread.start()
        thread.join(10)
        assert seen == [False]
    monkeypatch.delenv("LEARNLOOP_AI_FALLBACK")
    # (c) Only an offer the dispatch minted can be answered (redesign D).
    assert plan_fallback.answer_offer(vault, "fo_never_minted") is None
    _grant(vault, ["grading"])
    assert plan_fallback.granted_tasks(vault) == ["grading"]
    # (b) Per vault, and a vault switch clears them.
    other = _vault(tmp_path / "other")
    assert not plan_fallback.is_granted("grading", other)
    ctx = SidecarContext()
    ctx.load(vault)
    _grant(vault, ["grading"])
    ctx.load(other)
    assert plan_fallback.granted_tasks(vault) == [] and plan_fallback.granted_origins(vault) == []


def test_f5_doctor_fix_keeps_the_tier_of_a_legacy_codex_route_value(tmp_path):
    """Review F5: `routing.<task> = "codex"` meant that task's Codex tier (medium for ingest)."""

    from learnloop.ops.plan_transport import codex_pins

    extra = {f"ai.routing.{task}": "codex" for task in LEGACY_CODEX_TASK_ROUTES}
    vault = _vault(tmp_path, extra={**extra, "ai.routing.diagnosis": "codex"})
    pins = {pin.setting: pin.replacement for pin in codex_pins(vault, load_config(vault / "learnloop.toml"))}
    for task, tier in LEGACY_CODEX_TASK_ROUTES.items():
        assert pins[f"ai.routing.{task}"] == CODEX_TO_PLAN_PROFILE[tier], task
    assert pins["ai.routing.canonical_ingest"] == "chatgpt_medium"
    assert pins["ai.routing.diagnosis"] == CODEX_TO_PLAN_PROFILE["codex"]


def test_f6_codex_is_never_a_fallback_through_the_direct_readers_opt_in_or_not(tmp_path, monkeypatch):
    """Review F6: the question build's route and the method-phrasing writer apply the same rule."""

    from types import SimpleNamespace

    from learnloop.ai.routing import configured_fallback
    from learnloop.content.pipeline.add_source import authoring_route_for
    from learnloop.content.proposals.method_phrasing import writer_names
    from learnloop.vault.loader import load_vault

    monkeypatch.setattr("learnloop.ai.runtime.check_codex_runtime", lambda *a, **k: SimpleNamespace(
        status="ready", actual_revision=None, message="ok"))
    vault = _vault(tmp_path, opt_in=True, extra={"ai.fallback_provider": "codex"})
    config = load_config(vault / "learnloop.toml")
    assert configured_fallback(config, "chatgpt") is None
    route = authoring_route_for(vault, config)
    assert route.provider not in CODEX_NAMES and not route.ready
    assert not any(name in CODEX_NAMES for name in writer_names(load_vault(vault)))


def test_f7_an_explicit_inline_never_sends_tools_and_a_tools_turn_caps_its_resent_input(tmp_path):
    """Review F7: inline as written refuses an oversized export; a tools turn stops at its input cap."""

    from learnloop.ai.errors import AIInvalidOutput, AIProviderUnavailable
    from learnloop.ai.providers.chatgpt_plan import TURN_INPUT_FACTOR

    # Only a value the owner wrote counts as explicit (the code default and other keys do not).
    vault = _vault(tmp_path, extra={"ai.providers.chatgpt.model": "gpt-test-fast"})
    assert "workspace_mode" not in load_config(vault / "learnloop.toml").ai.providers["chatgpt"].model_fields_set
    written = _vault(tmp_path, extra={"ai.providers.chatgpt.workspace_mode": "inline"})
    assert "workspace_mode" in load_config(written / "learnloop.toml").ai.providers["chatgpt"].model_fields_set
    with fake_chatgpt() as server:
        sign_in(PlanSession(), server)
        workspace = _workspace(tmp_path, big=20_000)
        client = _plan_client(server, workspace_mode="inline", max_workspace_chars=10_000)
        with pytest.raises(AIProviderUnavailable, match="max_workspace_chars|too large|exceeds"):
            execute_structured_operation(client, purpose="t1", prompt="Say ok", result_model=Answer,
                                         workspace=workspace)
        assert server.requests == []
        # Tools mode: every round resends the history; past TURN_INPUT_FACTOR x max_workspace_chars
        # the model is asked to answer, long before max_tool_rounds.
        read_big = ("read_entry", {"path": "attempts/big.md", "start_line": None, "max_lines": None})
        server.replies.extend(Reply(events=tool_call_events([read_big], response_id=f"r{n}")) for n in range(20))
        client = _plan_client(server, workspace_mode="tools", max_workspace_chars=10_000, max_tool_rounds=16)
        with pytest.raises(AIInvalidOutput, match="request to answer"):
            execute_structured_operation(client, purpose="t1", prompt="Say ok", result_model=Answer,
                                         workspace=workspace)
        sent = [len(request["body"]["instructions"]) + len(json.dumps(request["body"]["input"], ensure_ascii=False))
                for request in server.requests]
        assert len(sent) < 16
        # Below the cap until the round that crosses it, then one "answer now" round.
        assert sum(sent[:-2]) < TURN_INPUT_FACTOR * 10_000 <= sum(sent[:-1])


def test_f8_an_error_that_is_not_a_sidecar_error_keeps_the_offer(tmp_path, monkeypatch):
    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.dto import EmptyParams
    from learnloop_sidecar.registry import METHOD_REGISTRY, MethodSpec
    from learnloop_sidecar.server import _handle

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)

    def feature(ctx, _params):
        loaded, _repository = ctx.require_vault()
        ready_client_for_task(loaded.root, loaded.config, "tutor_qa")
        raise RuntimeError("a handler that lets an unavailable route escape")

    monkeypatch.setitem(METHOD_REGISTRY, "test.t1_crash", MethodSpec("test.t1_crash", EmptyParams, feature))
    ctx = SidecarContext()
    ctx.load(vault)
    response = _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": "test.t1_crash", "params": {}})
    details = response["error"]["data"]["details"]
    assert details["outcome"] == "unknown" and details["fallback_tasks"] == ["tutor_qa"]
    # So the banner's click can be answered: the offer is minted for the action that crashed.
    assert details["fallback_origin"] == "test.t1_crash"
    assert plan_fallback.answer_offer(vault, details["fallback_offer_id"]).origin == "test.t1_crash"


def test_f9_refused_codex_profiles_are_not_offered_as_grading_providers(tmp_path):
    from learnloop.vault.loader import load_vault
    from learnloop_sidecar.context import available_grading_providers

    plain = available_grading_providers(load_vault(_vault(tmp_path)))
    assert not any(name in CODEX_NAMES for name in plain) and plain[-1] == "manual"
    assert "chatgpt" in plain
    opted = available_grading_providers(load_vault(_vault(tmp_path / "opted", opt_in=True)))
    assert "codex" in opted and "codex_low" in opted


# ---------------------------------------------------------------------------
# Re-review (2026-10-23)
# ---------------------------------------------------------------------------


def test_rr_f1_the_connection_status_never_offers_and_shows_a_granted_build(tmp_path, monkeypatch):
    """Re-review F1: `get_ai_connection` runs on every vault load; it is a status read, not a feature use."""

    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.server import _handle
    from learnloop.content.pipeline.add_source import authoring_route_for

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(vault, maintenance=False)

    def rpc(method_name, params=None):
        return _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method_name, "params": params or {}})

    status = rpc("get_ai_connection")["result"]
    assert status["canAuthor"] is False and "fallbackAvailable" not in status
    # Nothing was offered, so nothing can be granted from it.
    refused = rpc("connect_ai", {"provider": "current"})["error"]["data"]
    assert refused["code"] == "ai_not_connected" and "fallback_available" not in refused.get("details", {})
    # The build itself still asks.
    with plan_fallback.collecting() as offers:
        assert not authoring_route_for(vault, ctx.vault.config).ready
    assert offers.hint()["fallback_tasks"] == ["canonical_ingest"]
    # Once the learner chose OpenRouter for Add (the action whose offer it answered), the
    # status says what Add will use (redesign D).
    plan_fallback.grant_origin(vault, "add_source")
    granted = rpc("get_ai_connection")["result"]
    assert granted["canAuthor"] is True and granted["provider"] == "openrouter"
    assert "fallbackAvailable" not in granted


def test_rr_f2_a_feature_that_needs_its_own_price_is_not_served_by_another_features_grant(tmp_path, monkeypatch):
    """Re-review F2: passage checks and exercise imports ride `canonical_ingest` but refuse an unpriced metered route."""

    from types import SimpleNamespace

    from learnloop.content.pipeline import jobs
    from learnloop.content.pipeline.runner import RunnerServices
    from tests.openai_fakes import install_fake_openai

    fake_openai = install_fake_openai(monkeypatch, '{"ok": true, "note": "openrouter"}')
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    ctx = SimpleNamespace(vault_root=vault, services=RunnerServices(), bind_interruptible=lambda _client: None)
    for resolve, setting in ((jobs._paid_quick_check_client, "reader_inquiry.metered_price_per_million"),
                             (jobs._exercise_import_client, "source_service.llm_price_per_million")):
        # No offer the feature would refuse, and the setting is named.
        with plan_fallback.collecting() as offers, pytest.raises(jobs.IngestRunnerError, match=setting):
            resolve(ctx)
        assert offers.hint() is None, setting
    # The question build's grant serves the build, never these features while their price is unset.
    _grant(vault, ["canonical_ingest"])
    assert ready_client_for_task(vault, config, "canonical_ingest").provider_name == "openrouter"
    for resolve, setting in ((jobs._paid_quick_check_client, "reader_inquiry.metered_price_per_million"),
                             (jobs._exercise_import_client, "source_service.llm_price_per_million")):
        with pytest.raises(jobs.IngestRunnerError, match=setting):
            resolve(ctx)
    # Priced: the grant serves them too (an ordinary metered request under their caps).
    priced = _vault(tmp_path, extra={"reader_inquiry.metered_price_per_million": 1.0,
                                     "source_service.llm_price_per_million": 1.0})
    priced_ctx = SimpleNamespace(vault_root=priced, services=RunnerServices(), bind_interruptible=lambda _c: None)
    for resolve in (jobs._paid_quick_check_client, jobs._exercise_import_client):
        assert resolve(priced_ctx).provider_name == "openrouter"
    assert all(instance.requests == [] for instance in fake_openai.instances)  # built, never called


def test_rr_f3_the_plan_status_lists_the_sessions_grants_for_a_lasting_stop(tmp_path, monkeypatch):
    """Re-review F3: Settings shows "Stop using OpenRouter" while any grant exists, not only after granting."""

    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.dto import EmptyParams
    from learnloop_sidecar.handlers import chatgpt_plan as rpc

    vault = _vault(tmp_path)
    ctx = SidecarContext()
    ctx.load(vault, maintenance=False)
    assert rpc.chatgpt_plan_status(ctx, EmptyParams())["openrouterGrantedTasks"] == []
    _grant(vault, ["tutor_qa", "grading"])
    assert rpc.chatgpt_plan_status(ctx, EmptyParams())["openrouterGrantedTasks"] == ["grading", "tutor_qa"]
    plan_fallback.revoke(vault)
    assert rpc.chatgpt_plan_status(ctx, EmptyParams())["openrouterGrantedTasks"] == []


def _rpc_on(root: Path):
    """A loaded sidecar and a JSON-RPC caller that goes through the server (offers attached as the desktop sees them)."""

    from learnloop_sidecar import handlers  # noqa: F401 - populates the registry
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.server import _handle

    ctx = SidecarContext()
    ctx.load(root, maintenance=False)

    def rpc(method_name: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return _handle(ctx, {"jsonrpc": "2.0", "id": 1, "method": method_name, "params": params or {}})

    return ctx, rpc


def _gate_outcome(response: dict[str, Any]) -> tuple[str, str, bool]:
    """(status, message, offered) of a priced feature's RPC gate, whether it raised or degraded."""

    if "error" in response:
        data = response["error"]["data"]
        details = data.get("details") or {}
        return data["code"], response["error"]["message"], "fallback_available" in details
    result = response["result"]
    return str(result["status"]), str(result.get("message") or ""), "fallbackAvailable" in result


@pytest.mark.parametrize("feature", ["exercise_import", "inquiry_quick_check", "selection_question"])
def test_fix_l1_the_rpc_gates_of_priced_features_offer_and_honour_no_grant_their_job_would_refuse(
        tmp_path, monkeypatch, feature):
    """Fix round L1: reader.import_exercise, reader.reconnect_answer (quick check) and
    reader.active_question resolve their gate under their own price, as their jobs do."""

    from types import SimpleNamespace

    from learnloop.content.pipeline.jobs import DurableIngestJobs
    from learnloop.reader import reader_dialogue as RD
    from learnloop_sidecar.handlers import reader as reader_handlers
    from tests.openai_fakes import install_fake_openai
    from tests.test_reader_guidance import _setup as guide_setup
    from tests.test_sidecar_reader import _setup as reader_setup

    fake_openai = install_fake_openai(monkeypatch, '{"ok": true, "note": "openrouter"}')
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    queued: list[str] = []
    for name in ("enqueue_reader_exercise_import", "enqueue_reader_inquiry_check",
                 "enqueue_reader_selection_check"):
        monkeypatch.setattr(DurableIngestJobs, name,
                            lambda self, _name=name, **_kwargs: queued.append(_name) or "batch_fix_l1")
    monkeypatch.setattr(reader_handlers, "ready_tutor_qa_provider",
                        lambda vault: ("stub", SimpleNamespace(ready=True), RD.StubReaderClient()))
    if feature == "selection_question":
        root = guide_setup(tmp_path)[0].root
        setting = "reader_inquiry.metered_price_per_million"
    else:
        root = reader_setup(tmp_path)
        setting = ("source_service.llm_price_per_million" if feature == "exercise_import"
                   else "reader_inquiry.metered_price_per_million")
    asks: list[int] = []

    def call(rpc) -> tuple[str, str, bool]:
        if feature == "exercise_import":
            response = rpc("reader.import_exercise", {"extractionId": "ext1", "rawSelection": {
                "nodes": [{"spanId": "s1", "start": 0, "end": 10}]}})
        elif feature == "selection_question":
            response = rpc("reader.active_question", {"extractionId": "ext1", "spanIds": ["s1"], "style": "why_step"})
        else:
            asks.append(len(asks))
            asked = rpc("reader.ask", {"extractionId": "ext1", "spanId": "s1", "question": f"Root {len(asks)}?"})
            response = rpc("reader.reconnect_answer", {"extractionId": "ext1",
                                                       "exchangeId": asked["result"]["readerAnswerEventId"],
                                                       "answer": "quick_check", "via": "rail"})
        return _gate_outcome(response)

    _ctx, rpc = _rpc_on(root)
    # Unpriced: no "Use OpenRouter instead" the job would refuse, and the setting is named.
    status, message, offered = call(rpc)
    assert status == "provider_unavailable" and not offered, message
    assert setting in message and "can do this instead" not in message, message
    # Even a yes to this very action does not open the gate: the job would refuse it.
    gate = {"exercise_import": "reader.import_exercise", "inquiry_quick_check": "reader.reconnect_answer",
            "selection_question": "reader.active_question"}[feature]
    plan_fallback.grant_origin(root, gate)
    status, message, _offered = call(rpc)
    assert status == "provider_unavailable" and setting in message, message
    assert queued == []
    # Priced: the offer is made, and once granted the gate passes (an ordinary metered request).
    plan_fallback.revoke_all()
    document = tomlkit.parse((root / "learnloop.toml").read_text(encoding="utf-8"))
    section, key = setting.split(".")
    if section not in document:
        document[section] = tomlkit.table()
    document[section][key] = 1.0
    (root / "learnloop.toml").write_text(tomlkit.dumps(document), encoding="utf-8")
    _ctx, rpc = _rpc_on(root)
    status, message, offered = call(rpc)
    assert status == "provider_unavailable" and offered and "can do this instead" in message, message
    plan_fallback.grant_origin(root, gate)  # the learner's yes to this action
    status, message, _offered = call(rpc)
    assert status == "queued" and len(queued) == 1, message
    assert all(instance.requests == [] for instance in fake_openai.instances)  # built, never called


def test_fix_l1_an_exercise_imports_own_authoring_route_is_held_to_its_price(tmp_path, monkeypatch):
    """Fix round L1: a harvest or need import resolves authoring itself (no client passed);
    it makes no offer and takes no grant while source_service.llm_price_per_million is unset."""

    from learnloop.content.authoring import source_exercise_import as SEI
    from tests.openai_fakes import install_fake_openai
    from tests.source_service_fakes import build_textbook_vault, set_config

    fake_openai = install_fake_openai(monkeypatch, '{"ok": true, "note": "openrouter"}')
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    paths, repository, spans = build_textbook_vault(tmp_path / "textbook")
    set_config(paths, "source_service", exercise_verification=False)

    def run(span):
        with plan_fallback.collecting() as offers:
            result = SEI.import_source_exercise(paths.root, repository, extraction_id="ext_text", span_ids=[span],
                                                caller="harvest", clients={})
        return result, offers.hint()

    result, hint = run(spans["exercises"][1])
    assert result["status"] == "failed" and hint is None, (result, hint)
    assert "no authoring route is ready" in result["reason"]
    assert "source_service.llm_price_per_million" in result["reason"]
    _grant(paths.root, ["authoring"])
    result, _hint = run(spans["exercises"][2])
    assert result["status"] == "failed" and "no authoring route is ready" in result["reason"], result
    assert all(instance.requests == [] for instance in fake_openai.instances)


def test_fix_l2_a_quiet_status_read_never_points_at_an_offer_it_did_not_make(tmp_path, monkeypatch):
    """Fix round L2: under quiet() (either kind) the unavailable message carries no
    "Use OpenRouter instead" sentence and the runtime no fallback fields; a real offer keeps both."""

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-never-sent")
    vault = _vault(tmp_path)
    config = load_config(vault / "learnloop.toml")
    sentence = plan_fallback.offer_sentence()
    for quiet in (plan_fallback.quiet(), plan_fallback.status_as(LEARNER)):
        with quiet:
            resolved = ready_client_for_task(vault, config, "canonical_ingest")
        assert not resolved.ready
        assert sentence not in (resolved.runtime.message or "") and "OpenRouter" not in (resolved.runtime.message or "")
        assert resolved.runtime.fallback_available is None and "fallback_available" not in resolved.runtime.as_dict()
    with plan_fallback.collecting() as offers:
        offered = ready_client_for_task(vault, config, "canonical_ingest")
    assert sentence in offered.runtime.message and offered.runtime.fallback_available == "openrouter"
    assert offers.hint()["fallback_tasks"] == ["canonical_ingest"]
    # The connection sheet (a quiet status read on every vault load) says nothing about a banner.
    _ctx, rpc = _rpc_on(vault)
    status = rpc("get_ai_connection")["result"]
    assert status["canAuthor"] is False and "fallbackAvailable" not in status
    assert "OpenRouter" not in (status["message"] or ""), status["message"]
