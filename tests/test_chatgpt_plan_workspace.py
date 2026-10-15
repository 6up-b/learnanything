"""The ChatGPT plan's LearnLoop-served read-only workspace, against a fake Responses SSE server.

Covers function-tool rounds (``workspace.list_entries`` / ``workspace.read_entry``
in a namespace, the whole history resent with ``store: false``), served-entry
provenance recorded as each call runs, refused calls, round and character
budgets, cancellation, the deadline, the usage-limit pause, token refresh and
transient retries mid-turn, structured-output validity, the inline mode, a
snapshot diagnosis end to end, and the routing around it (capability, the
caller's deadline, Codex fallback, disclosures). No test leaves 127.0.0.1.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest
import tomlkit

from learnloop.ai.chatgpt_plan.responses import UNSUPPORTED_FIELDS, echo_items
from learnloop.ai.chatgpt_plan.session import ChatGPTPlanUsageExhausted, PlanSession
from learnloop.ai.chatgpt_plan.workspace import (
    INSTRUCTIONS_INLINE,
    INSTRUCTIONS_TOOLS,
    NAMESPACE,
    ServedWorkspace,
    WorkspaceTooLarge,
    normalize_path,
)
from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable, AITurnTimeout
from learnloop.ai.execution import observe_model_calls, single_request
from learnloop.ai.providers.chatgpt_plan import ChatGPTPlanProviderClient, ChatGPTPlanRequestRejected
from learnloop.ai.routing import (
    client_for_provider,
    ready_client_for_task,
    serves_read_only_workspace,
)
from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import READ_ONLY_WORKSPACE, execute_structured_operation
from learnloop.config import load_config
from learnloop.config.schema import ChatGPTPlanProviderConfig

from tests.chatgpt_plan_fakes import (
    REFUSED_FIELDS,
    Reply,
    completed_events,
    failed_events,
    fake_chatgpt,
    run_in_thread,
    served_outputs,
    sign_in,
    tool_call_events,
)
from tests.diagnosis_fakes import prompt_payload
from tests.helpers import create_basic_vault


class Answer(WireModel):
    ok: bool
    note: str


INDEX = "# Index\n- attempts/a.md: lo_x; non_pass\n- attempts/b.md: lo_x; pass\n"
ATTEMPT_A = "# Attempt att_a\n- outcome: non_pass\n"
ATTEMPT_B = "# Attempt att_b\n- outcome: pass\n"


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("LEARNLOOP_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.delenv("LEARNLOOP_AI_PROVIDER", raising=False)
    monkeypatch.setattr("learnloop.ai.providers.chatgpt_plan._sleep", lambda _seconds: None)


@pytest.fixture
def server():
    with fake_chatgpt() as fake:
        sign_in(PlanSession(), fake)
        yield fake


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "workspace"
    (root / "attempts").mkdir(parents=True)
    (root / "INDEX.md").write_text(INDEX, encoding="utf-8")
    (root / "attempts" / "a.md").write_text(ATTEMPT_A, encoding="utf-8")
    (root / "attempts" / "b.md").write_text(ATTEMPT_B, encoding="utf-8")
    return root


def _client(server, **profile) -> ChatGPTPlanProviderClient:
    settings = {"model": "gpt-test-fast", "base_url": server.base_url, "timeout_seconds": 10, **profile}
    return ChatGPTPlanProviderClient("chatgpt", ChatGPTPlanProviderConfig(**settings))


def _ask(client, workspace, **kwargs):
    return execute_structured_operation(client, purpose="diagnosis", prompt="Diagnose from the workspace.",
                                        result_model=Answer, workspace=workspace, **kwargs)


def _read(path: str, start: int | None = None, lines: int | None = None) -> tuple[str, dict]:
    return "read_entry", {"path": path, "start_line": start, "max_lines": lines}


ANSWER = completed_events('{"ok": true, "note": "done"}')


# -- function-tool rounds -------------------------------------------------------------


def test_tool_rounds_serve_files_and_record_each_served_entry(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([("list_entries", {"directory": None}), _read("INDEX.md")], response_id="r1")),
        Reply(events=tool_call_events([_read("attempts/a.md")], response_id="r2")),
        Reply(events=ANSWER),
    ])
    client = _client(server, reasoning_effort="medium")
    events: list[tuple[str, dict]] = []
    with observe_model_calls(lambda action, event: events.append((action, event))):
        assert _ask(client, workspace) == Answer(ok=True, note="done")

    bodies = [request["body"] for request in server.requests]
    assert len(bodies) == 3
    for body in bodies:
        assert body["store"] is False and body["stream"] is True
        assert not set(body) & REFUSED_FIELDS and not set(body) & (UNSUPPORTED_FIELDS - {"tools"})
        assert body["tools"] == [ServedWorkspace.namespace_tool()] and body["tools"][0]["type"] == "namespace"
        assert body["include"] == ["reasoning.encrypted_content"]
        assert body["text"]["format"]["type"] == "json_schema"
        assert body["reasoning"] == {"effort": "medium"}
        assert body["instructions"].endswith(INSTRUCTIONS_TOOLS)
    listing, index = served_outputs(bodies[1])
    assert "attempts/ (2 files)" in listing and f"INDEX.md ({len(INDEX.encode())} bytes)" in listing
    assert index == f"path: INDEX.md (lines 1-3 of 3)\n{INDEX.rstrip()}"
    # Each request resends the whole history; nothing names a stored item.
    kinds = [item.get("type") or item.get("role") for item in bodies[2]["input"]]
    assert kinds == ["user", "reasoning", "function_call", "function_call", "function_call_output",
                     "function_call_output", "reasoning", "function_call", "function_call_output"]
    reasoning = bodies[2]["input"][1]
    assert reasoning == {"type": "reasoning", "summary": [], "encrypted_content": "enc-r1"}
    assert all("id" not in item for item in bodies[2]["input"])
    assert served_outputs(bodies[2])[-1].startswith("path: attempts/a.md (lines 1-2 of 2)")

    # Exact by construction: the files served, once each, in order; a listing is not an input.
    assert client.workspace_activity() == ["INDEX.md", "attempts/a.md"]
    record = client.workspace_record()
    assert record["mode"] == "tools" and record["served_files"] == 2 and record["refused"] == 0
    served = {entry["path"]: entry for entry in record["served"]}
    assert served["INDEX.md"]["sha256"] == hashlib.sha256(INDEX.encode()).hexdigest()
    assert (served["attempts/a.md"]["round"], served["attempts/a.md"]["call_id"]) == (2, "call_r2_0")
    assert [call["outcome"] for call in record["calls"]] == ["listed", "served", "served"]

    # Every round is its own receipt: what it carried, its billing and its usage.
    starts = {event["id"]: event for action, event in events if action == "start"}
    rounds = [event for action, event in events
              if action == "finish" and starts[event["id"]]["purpose"] == "responses_request"]
    plan = [json.loads(event["usage_json"])["chatgpt_plan"] for event in rounds]
    assert [entry["workspace"] for entry in plan] == [
        {"mode": "tools", "round": 1, "carries": []},
        {"mode": "tools", "round": 2, "carries": ["INDEX.md"]},
        {"mode": "tools", "round": 3, "carries": ["attempts/a.md"]},
    ]
    assert {entry["billing"] for entry in plan} == {"subscription"}
    assert [entry.get("function_calls") for entry in plan] == [2, 1, None]
    assert all(event["input_tokens"] for event in rounds)
    assert client.consume_usage().total_tokens == 460 + 460 + 150


def test_dotted_names_and_a_missing_namespace_are_accepted(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([("workspace.read_entry", _read("INDEX.md")[1])], namespace=None)),
        Reply(events=ANSWER),
    ])
    client = _client(server)
    assert _ask(client, workspace).note == "done"
    assert client.workspace_activity() == ["INDEX.md"]


def test_the_terminal_output_may_be_empty_and_unencrypted_reasoning_is_not_resent(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")], encrypted=False, in_terminal_output=False)),
        Reply(events=ANSWER),
    ])
    client = _client(server)
    assert _ask(client, workspace).note == "done"
    second = server.requests[-1]["body"]["input"]
    assert [item.get("type") or item.get("role") for item in second] == ["user", "function_call",
                                                                         "function_call_output"]


# -- provenance: only what is served is recorded ----------------------------------------


def test_refused_calls_serve_nothing_and_are_recorded(server, workspace, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("SECRET OUTSIDE THE WORKSPACE", encoding="utf-8")
    (workspace / "link.md").symlink_to(secret)
    (workspace / "linked").symlink_to(tmp_path, target_is_directory=True)
    server.replies.extend([
        Reply(events=tool_call_events([
            _read("../secret.txt"), _read(str(secret)), _read("link.md"), _read("linked/secret.txt"),
            ("read_entry", "{not json"), ("delete_entry", {"path": "INDEX.md"}), _read("attempts"),
            ("list_entries", {"directory": "INDEX.md"}), _read("INDEX.md", start=99),
        ])),
        Reply(events=tool_call_events([_read("INDEX.md")], namespace="shell", response_id="r2")),
        Reply(events=ANSWER),
    ])
    client = _client(server)
    assert _ask(client, workspace).note == "done"
    outputs = served_outputs(server.requests[-1]["body"])
    assert len(outputs) == 10 and all(output.startswith("error: ") for output in outputs)
    assert "is a directory" in outputs[6] and "is a file" in outputs[7] and "past its end" in outputs[8]
    assert "there is no namespace 'shell'" in outputs[9]
    assert all("SECRET" not in json.dumps(request["body"]) for request in server.requests)
    assert client.workspace_activity() == []
    record = client.workspace_record()
    assert record["refused"] == 10 and record["served"] == []


def test_a_call_without_a_call_id_is_invalid_output(server, workspace):
    events = tool_call_events([_read("INDEX.md")])
    for event in events:
        for item in (event.get("item"), *((event.get("response") or {}).get("output") or [])):
            if isinstance(item, dict) and item.get("type") == "function_call":
                item.pop("call_id", None)
    server.replies.append(Reply(events=events))
    with pytest.raises(AIInvalidOutput, match="call_id"):
        _ask(_client(server), workspace)


def test_a_long_file_is_served_in_parts_and_each_part_recorded(server, workspace):
    long_text = "\n".join(f"line {index:03d} " + "x" * 30 for index in range(1, 101))
    (workspace / "long.md").write_text(long_text, encoding="utf-8")
    server.replies.extend([
        Reply(events=tool_call_events([_read("long.md")], response_id="r1")),
        Reply(respond=lambda body: tool_call_events(
            [_read("long.md", start=int(served_outputs(body)[-1].split("start_line=")[1].split()[0]))],
            response_id="r2")),
        Reply(events=ANSWER),
    ])
    client = _client(server, max_entry_chars=1_000)
    assert _ask(client, workspace).note == "done"
    first = served_outputs(server.requests[1]["body"])[-1]
    assert first.startswith("path: long.md (lines 1-25 of 100); more follows: call workspace.read_entry "
                            "with start_line=26")
    served = client.workspace_record()["served"]
    assert [(entry["start_line"], entry["end_line"]) for entry in served] == [(1, 25), (26, 50)]
    assert all(entry["chars"] <= 1_000 for entry in served)
    assert client.workspace_activity() == ["long.md"]


def test_the_round_budget_asks_for_the_answer_then_fails_closed(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")], response_id="r1")),
        Reply(events=tool_call_events([_read("attempts/a.md")], response_id="r2")),
        Reply(events=ANSWER),
    ])
    client = _client(server, max_tool_rounds=1)
    assert _ask(client, workspace).note == "done"
    assert "answer now" in served_outputs(server.requests[-1]["body"])[-1]
    assert client.workspace_activity() == ["INDEX.md"]  # the refused read served nothing

    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")], response_id="s1")),
        Reply(events=tool_call_events([_read("attempts/a.md")], response_id="s2")),
        Reply(events=tool_call_events([_read("attempts/b.md")], response_id="s3")),
    ])
    with pytest.raises(AIInvalidOutput, match="kept calling"):
        _ask(_client(server, max_tool_rounds=1), workspace)


def test_the_workspace_character_budget_and_the_listing_are_bounded(workspace):
    (workspace / "big.md").write_text("y" * 50 + "\n" + "z" * 50, encoding="utf-8")
    served = ServedWorkspace(workspace, max_entry_chars=1_000, max_workspace_chars=60)
    first = served.call("read_entry", json.dumps({"path": "big.md", "start_line": None, "max_lines": None}),
                        call_id="c1", round_index=1)
    assert first.startswith("path: big.md (lines 1-1 of 2)")
    second = served.call("read_entry", json.dumps({"path": "INDEX.md", "start_line": None, "max_lines": None}),
                         call_id="c2", round_index=1)
    assert second.startswith("path: INDEX.md (lines 1-1 of 3)")  # 10 characters left: one whole line
    third = served.call("read_entry", json.dumps({"path": "attempts/a.md", "start_line": None, "max_lines": None}),
                        call_id="c3", round_index=1)
    assert third == ("path: attempts/a.md (lines 1-1 of 2); line 1 is cut to its first 3 characters; more "
                     "follows: call workspace.read_entry with start_line=2\n# A")
    fourth = served.call("read_entry", json.dumps({"path": "attempts/b.md", "start_line": None, "max_lines": None}),
                         call_id="c4", round_index=1)
    assert fourth.startswith("error: the workspace read budget")
    assert served.activity() == ["big.md", "INDEX.md", "attempts/a.md"] and served.served_chars == 60
    with pytest.raises(WorkspaceTooLarge):
        ServedWorkspace(workspace, max_entry_chars=1_000, max_workspace_chars=60).inline_block()
    for raw, expected in (("/INDEX.md", "INDEX.md"), ("./attempts//a.md", "attempts/a.md"), ("../x", None),
                          ("a/../b", None), ("a\\b", None), ("", None), (None, None)):
        assert normalize_path(raw) == expected


# -- the turn's controls: cancellation, deadline, pause, refresh, retries -------------


def test_an_interrupt_mid_turn_stops_it_and_keeps_what_was_served(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")])),
        Reply(events=ANSWER, stall=5),
    ])
    client = _client(server)
    thread, out = run_in_thread(lambda: _ask(client, workspace))
    for _ in range(200):
        if len(server.requests) == 2:
            break
        time.sleep(0.02)
    time.sleep(0.2)
    client.interrupt()
    thread.join(5)
    assert not thread.is_alive()
    assert isinstance(out.get("error"), AIInterrupted), out
    assert client.workspace_activity() == ["INDEX.md"]


def test_the_deadline_covers_every_round(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")])),
        Reply(events=ANSWER, stall=5),
    ])
    client = _client(server, timeout_seconds=1)
    with pytest.raises(AITurnTimeout):
        _ask(client, workspace)
    assert client.workspace_activity() == ["INDEX.md"]


def test_a_usage_limit_mid_turn_pauses_the_plan(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")])),
        Reply(events=failed_events("subscription_sharing_usage_limit_exceeded")),
    ])
    client = _client(server)
    with pytest.raises(ChatGPTPlanUsageExhausted):
        _ask(client, workspace)
    assert client.workspace_activity() == ["INDEX.md"]
    assert PlanSession().status().readiness()[0] == "usage_exhausted"
    sent = len(server.requests)
    with pytest.raises(ChatGPTPlanUsageExhausted):
        _ask(_client(server), workspace)  # refused locally, before any request
    assert len(server.requests) == sent


def test_a_401_mid_turn_refreshes_and_resends_the_same_round(server, workspace):
    def first_round(_body):
        server.revoke_all_access()  # the next round's token is no longer accepted
        return tool_call_events([_read("INDEX.md")])

    server.replies.extend([Reply(respond=first_round), Reply(events=ANSWER)])
    client = _client(server)
    assert _ask(client, workspace).note == "done"
    assert server.token_requests[-1]["grant_type"] == "refresh_token"
    assert len(server.requests) == 3
    assert server.requests[1]["body"] == server.requests[2]["body"]  # the same round, resent
    assert len(client.workspace_record()["served"]) == 1  # served once, never twice


def test_a_transient_failure_mid_turn_retries_the_round(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")])),
        Reply(status=503, body={"error": {"code": "subscription_sharing_usage_unavailable", "message": "later"}}),
        Reply(events=ANSWER),
    ])
    client = _client(server)
    assert _ask(client, workspace).note == "done"
    assert server.requests[1]["body"] == server.requests[2]["body"]
    assert client.workspace_activity() == ["INDEX.md"]


def test_rejected_workspace_tools_name_the_inline_setting(server, workspace):
    server.replies.append(Reply(status=400, body={"error": {
        "code": "subscription_sharing_unsupported_capability", "message": "tools unsupported", "param": "tools"}}))
    with pytest.raises(ChatGPTPlanRequestRejected) as caught:
        _ask(_client(server), workspace)
    assert 'workspace_mode = "inline"' in str(caught.value)
    assert len(server.requests) == 1


# -- structured output -------------------------------------------------------------------


def test_invalid_final_json_is_repaired_once_without_the_workspace(server, workspace):
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md")])),
        Reply(events=completed_events('{"ok": true}')),  # misses a field
        Reply(events=completed_events('{"ok": true, "note": "repaired"}')),
    ])
    client = _client(server)
    assert _ask(client, workspace).note == "repaired"
    repair = server.requests[-1]["body"]
    assert "tools" not in repair and "include" not in repair
    assert "Repair the following model output" in repair["input"][0]["content"]
    assert repair["text"]["format"]["type"] == "json_schema"


def test_a_workspace_turn_never_runs_under_a_single_request_budget(server, workspace):
    with single_request(), pytest.raises(AIProviderUnavailable, match="one request per round"):
        _ask(_client(server), workspace)
    assert server.requests == []


# -- the inline mode -------------------------------------------------------------------------


def test_inline_mode_sends_every_file_and_records_every_file(server, workspace):
    server.replies.append(Reply(events=ANSWER))
    client = _client(server, workspace_mode="inline")
    events: list[tuple[str, dict]] = []
    with observe_model_calls(lambda action, event: events.append((action, event))):
        assert _ask(client, workspace).note == "done"
    body = server.requests[-1]["body"]
    assert "tools" not in body and body["instructions"].endswith(INSTRUCTIONS_INLINE)
    content = body["input"][0]["content"]
    for path, text in (("INDEX.md", INDEX), ("attempts/a.md", ATTEMPT_A), ("attempts/b.md", ATTEMPT_B)):
        assert f'<workspace_file path="{path}">\n{text}\n</workspace_file>' in content
    assert client.workspace_activity() == ["INDEX.md", "attempts/a.md", "attempts/b.md"]
    finish = [event for action, event in events if action == "finish" and "usage_json" in event][-1]
    assert json.loads(finish["usage_json"])["chatgpt_plan"]["workspace"] == {
        "mode": "inline", "served": ["INDEX.md", "attempts/a.md", "attempts/b.md"]}


def test_inline_mode_refuses_a_workspace_over_its_budget_before_sending(server, workspace):
    (workspace / "big.md").write_text("w" * 20_000, encoding="utf-8")
    client = _client(server, workspace_mode="inline", max_workspace_chars=10_000)
    with pytest.raises(AIProviderUnavailable, match="max_workspace_chars"):
        _ask(client, workspace)
    assert server.requests == [] and client.workspace_activity() == []


# -- a snapshot diagnosis end to end ----------------------------------------------------------


def _diagnosis_answer(body):
    """The fake diagnoser: read INDEX.md, then one failed attempt's file, then answer citing it."""

    outputs = served_outputs(body)
    if not outputs:
        return tool_call_events([_read("INDEX.md")], response_id="d1")
    if len(outputs) == 1:
        path = next(line[2:].split(":")[0] for line in outputs[0].splitlines()
                    if line.startswith("- attempts/") and "att_02_svd_fail" in line)
        return tool_call_events([_read(path)], response_id="d2")
    cited = outputs[-1].splitlines()[1].replace("# Attempt ", "").strip()
    context = prompt_payload(body["input"][0]["content"])["context"]
    events = [{
        "event_index": row["index"], "first_divergence_quote": (row.get("first_divergence") or {}).get("quote"),
        "causal_class": "learner_state",
        "candidate_causes": [{"statement": "The learner leaves V untransposed.", "cause_scope": "learner_state",
                              "prior_weight": 1.0}],
        "registry_match": {"kind": "abstain"}, "history_changed_cause": {"changed": False, "note": ""},
    } for row in context["current_attempt"]["blind_grade"]["error_attributions"]]
    return completed_events(json.dumps({
        "evidence_attempt_ids": [cited], "analysis_md": "The same untransposed factor as before.",
        "event_diagnoses": events, "repair_suggestions": [], "pattern_claims": [],
        "prerequisite_gap_hypotheses": [], "abstentions": [],
    }))


def _seeded(tmp_path):
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.diagnosis.split.context import current_attempt_from
    from learnloop.diagnosis.split.history import VaultHistoryStore
    from tests.diagnosis_split_helpers import blind_record, build_diagnosis_vault, seed_history

    vault, repository = seed_history(build_diagnosis_vault(tmp_path / "vault"))
    store = VaultHistoryStore(vault, repository)
    attempt = store.attempt("att_06_svd_fail")
    item = vault.practice_items[attempt.practice_item_id]
    record = blind_record(
        score=2, max_points=4, criteria={"setup": 2, "result": 0},
        attributions=[{"error_type": "conceptual_slip", "evidence": "Blind evidence here.",
                       "first_divergence": {"anchor_kind": "span", "criterion_id": "result", "quote": "again"},
                       "target_evidence_families": ["recall"], "resolution_status": "unresolved",
                       "validity_scope": "valid_measurement"}],
    )
    current = current_attempt_from(vault, item, attempt_id=attempt.attempt_id, completed_at=attempt.completed_at,
                                   learner_answer_md=attempt.learner_answer_md, blind_grade=record)
    return vault, store, item, resolved_rubric(vault, item), current


def test_a_snapshot_diagnosis_on_the_plan_records_exactly_what_it_read(server, tmp_path):
    from learnloop.diagnosis.split.diagnoser import run_diagnosis
    from learnloop.diagnosis.split.settings import DiagnosisSettings

    vault, store, item, rubric, current = _seeded(tmp_path)
    server.default_reply = lambda body: Reply(events=_diagnosis_answer(body))
    client = _client(server)
    parent = tmp_path / "snapshots"
    parent.mkdir()
    outcome = run_diagnosis(client, vault=vault, item=item, rubric=rubric, store=store, current=current,
                            settings=DiagnosisSettings(), mode="snapshot", snapshot_parent=parent)
    assert outcome.status == "completed", outcome
    assert outcome.unknown_id_count == 0
    assert outcome.proposal["evidence_attempt_ids"] == ["att_02_svd_fail"]  # known only through the export
    opened = outcome.receipt["snapshot"]["opened"]
    assert outcome.receipt["snapshot"]["opened_reported"] is True
    assert opened[0] == "INDEX.md" and opened[1].startswith("attempts/") and "att_02_svd_fail" in opened[1]
    # The provenance contract: each report is a bare relative path naming an
    # export file, which diagnosis input provenance reads as that file's read.
    assert all(not path.startswith("/") and " " not in path and ".." not in path for path in opened)
    assert len(opened) == 2 < outcome.receipt["snapshot"]["file_count"]
    assert list(parent.iterdir()) == []  # the export (learner text) is deleted afterwards
    assert len(server.requests) == 3


def test_served_paths_map_to_export_entries_under_input_provenance(server, tmp_path):
    """Once diagnosis input provenance is on main, each served path is one export entry."""

    provenance = pytest.importorskip("learnloop.diagnosis.split.provenance")
    from learnloop.diagnosis.split.snapshot import export_snapshot

    vault, store, _item, _rubric, current = _seeded(tmp_path)
    manifest = export_snapshot(vault, store, current.ref(), tmp_path / "export")
    server.replies.extend([
        Reply(events=tool_call_events([_read("INDEX.md"), ("list_entries", {"directory": "attempts"})])),
        Reply(events=ANSWER),
    ])
    client = _client(server)
    _ask(client, manifest.root)
    how, paths = provenance.served_entries(manifest.entries, client.workspace_activity())
    assert (how, paths) == ("entries", ("INDEX.md",))


# -- routing: capability, deadline, fallback, disclosures ----------------------------------


def _vault(tmp_path, server, *, active: str = "codex", fallback: str = "", routes: dict | None = None):
    root = tmp_path / "vault"
    if not root.exists():
        create_basic_vault(root)
    path = root / "learnloop.toml"
    document = tomlkit.parse(path.read_text(encoding="utf-8"))
    table = tomlkit.table()
    for key, value in {"type": "chatgpt_plan", "model": "gpt-test-fast", "base_url": server.base_url,
                       "timeout_seconds": 10}.items():
        table[key] = value
    document["ai"]["providers"]["chatgpt"] = table
    document["ai"]["active_provider"] = active
    document["ai"]["fallback_provider"] = fallback
    for task, name in (routes or {}).items():
        document["ai"]["routing"][task] = name
    path.write_text(tomlkit.dumps(document), encoding="utf-8")
    return root


def test_the_plan_serves_a_workspace_and_takes_the_callers_deadline(server, tmp_path):
    vault = _vault(tmp_path, server)
    config = load_config(vault / "learnloop.toml")
    assert serves_read_only_workspace(config, "chatgpt") and serves_read_only_workspace(config, "codex")
    assert not serves_read_only_workspace(config, "openrouter")
    client = client_for_provider(vault, config, "chatgpt", timeout_seconds=900)
    assert client.supports(READ_ONLY_WORKSPACE) and client.profile.timeout_seconds == 900
    assert client_for_provider(vault, config, "chatgpt").profile.timeout_seconds == 10


def test_active_chatgpt_falls_back_to_codex_while_the_plan_is_paused(server, tmp_path, monkeypatch):
    monkeypatch.setattr("learnloop.ai.runtime.check_codex_runtime", lambda *a, **k: SimpleNamespace(
        status="ready", actual_revision=None, message="ok"))
    # The switch-over: the active provider, and the routes a vault's
    # learnloop.toml pins to Codex profiles (the template writes eight).
    pinned_routes = {task: "chatgpt" for task in ("grading", "canonical_ingest", "canonical_ingest_retry",
                                                  "authoring", "tutor_qa", "teach_back", "rung_variant",
                                                  "animation")}
    vault = _vault(tmp_path, server, active="chatgpt", fallback="codex", routes=pinned_routes)
    config = load_config(vault / "learnloop.toml")
    for task in ("grading", "diagnosis", "tutor_qa", "authoring", "router_llm", "same_cause_judge"):
        resolved = ready_client_for_task(vault, config, task, timeout_seconds=300)  # type: ignore[arg-type]
        assert (resolved.provider_name, resolved.fallback_from) == ("chatgpt", None), task
        assert resolved.client.provider_type == "chatgpt_plan"
    PlanSession().note_usage_limit(code="subscription_sharing_usage_limit_exceeded", request_id="r")
    resolved = ready_client_for_task(vault, config, "diagnosis", timeout_seconds=300)
    assert (resolved.provider_name, resolved.fallback_from) == ("codex", "chatgpt")
    assert resolved.client.provider_type == "codex_sdk" and resolved.client.supports(READ_ONLY_WORKSPACE)
    # A route pinned to the plan never falls back.
    pinned = ready_client_for_task(vault, config, "diagnosis", explicit="chatgpt")
    assert not pinned.ready and pinned.fallback_from is None
    PlanSession().resume()
    assert ready_client_for_task(vault, config, "diagnosis").provider_name == "chatgpt"


def test_disclosures_name_the_plan_when_it_is_the_active_provider(server, tmp_path):
    from learnloop.ai.disclosures import judge_route_disclosures

    vault = _vault(tmp_path, server, active="chatgpt")
    entries = {entry["route"]: entry for entry in judge_route_disclosures(load_config(vault / "learnloop.toml"))}
    assert entries["router_llm"]["provider"] == "chatgpt"
    assert "ChatGPT plan" in entries["router_llm"]["disclosure"]


def test_echo_items_keep_only_what_store_false_can_resend():
    output = [
        {"type": "reasoning", "id": "rs_1", "summary": [{"type": "summary_text", "text": "s"}],
         "content": [{"type": "reasoning_text", "text": "raw"}], "encrypted_content": "enc"},
        {"type": "reasoning", "id": "rs_2", "summary": []},  # no encrypted content: dropped
        {"type": "function_call", "id": "fc_1", "status": "completed", "call_id": "c", "name": "read_entry",
         "namespace": NAMESPACE, "arguments": "{}"},
        {"type": "web_search_call", "id": "ws_1"},
    ]
    assert echo_items(output) == [
        {"type": "reasoning", "summary": [{"type": "summary_text", "text": "s"}], "encrypted_content": "enc"},
        {"type": "function_call", "call_id": "c", "name": "read_entry", "namespace": NAMESPACE, "arguments": "{}"},
    ]


def test_the_profile_validates_its_workspace_settings():
    with pytest.raises(ValueError):
        ChatGPTPlanProviderConfig(model="m", workspace_mode="shell")
    with pytest.raises(ValueError):
        ChatGPTPlanProviderConfig(model="m", max_tool_rounds=0)
    profile = ChatGPTPlanProviderConfig(model="m")
    assert (profile.workspace_mode, profile.max_tool_rounds, profile.max_entry_chars,
            profile.max_workspace_chars) == ("tools", 16, 24_000, 400_000)


def test_the_workspace_never_reaches_outside_its_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "a.md").write_text("a", encoding="utf-8")
    served = ServedWorkspace(root, max_entry_chars=1_000, max_workspace_chars=10_000)
    assert set(served.files) == {"a.md"}
    with pytest.raises(NotADirectoryError):
        ServedWorkspace(Path(root / "a.md"), max_entry_chars=1_000, max_workspace_chars=10_000)
