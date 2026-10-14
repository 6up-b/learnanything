"""Chat frontend C1a (spec_mcp_frontend_c1): the MCP tools through the SDK's in-process client.

* **Surface**: six tools with structured outputs and honest annotations (the
  five views read-only; ``find_sources`` records exposure, so it is not).
* **Telemetry**: every call, failed ones included, is one ``chat_tool_call``
  row in ``interaction_events`` (origin ``chat_host``, surface ``chat_mcp``,
  host, tool, argument and result hashes, salience-only); a call that cannot
  be recorded returns nothing.
* **Leakage (G5)**: no answer key, contract key, exam text, cold-check stem
  or passage, reserved stem, probe stem or held score in any payload; a held
  grade reads "held for review".
* **Shared latent state**: ``learning_context`` returns the misconceptions,
  candidates, hypotheses (evidence for and against, repairs tried),
  recurrence groups, answer traces, open gaps and retention risks the app has.
* **Grounding**: ``find_sources`` withholds exam material, reference solutions
  and passages held for a check, returns full blocks with citations, and
  records the shown passages as exposure first: an item built on a shown
  passage is no longer an unexposed independent check (as in the Reader).
* ``today`` reads the stored plan and writes nothing to it.
"""

from __future__ import annotations

import json

import anyio
import pytest
from mcp import Client

from learnloop.attempts.salience_firewall import SalienceEvidenceRejected, reject_salience
from learnloop.remote.runtime import RemoteRuntime
from learnloop_mcp.hosts import detect_host
from learnloop_mcp.server import build_server
from tests.mcp_world import (
    CANDIDATE,
    COLD_PASSAGE,
    GAP_TEXT,
    HYPOTHESIS,
    INJECTION,
    KEY,
    MISCONCEPTION,
    OWN_ANSWER,
    PINNED_STEM,
    PROTECTED,
    build_world,
    hold_att_held,
    no_model_calls,
    payload_text,
    table_count,
)

TOOLS = {"status", "today", "progress", "library", "find_sources", "learning_context"}


def _call_all(server, calls: list[tuple[str, dict]]) -> list:
    async def main():
        results = []
        async with Client(server) as client:
            for name, arguments in calls:
                results.append(await client.call_tool(name, arguments))
        return results

    return anyio.run(main)


def _tools(server) -> list:
    async def main():
        async with Client(server) as client:
            return (await client.list_tools()).tools

    return anyio.run(main)


def _events(repository) -> list[dict]:
    return repository.reader_interaction_events(kind="chat_tool_call")


@pytest.fixture
def paid_routes(monkeypatch):
    return no_model_calls(monkeypatch)


@pytest.fixture
def world(tmp_path, monkeypatch, paid_routes):
    hold_att_held(monkeypatch)
    return build_world(tmp_path / "w")


@pytest.fixture
def server(world):
    return build_server(RemoteRuntime.attach(world.root, load_environment=False))


def test_tool_surface_schemas_and_honest_annotations(server):
    tools = {tool.name: tool for tool in _tools(server)}
    assert set(tools) == TOOLS
    for name, tool in tools.items():
        assert tool.description and tool.output_schema and tool.output_schema.get("properties"), name
        read_only = tool.annotations.read_only_hint
        assert read_only is (name != "find_sources"), name
        assert tool.annotations.destructive_hint is False and tool.annotations.open_world_hint is False
    query = tools["find_sources"].input_schema["properties"]["query"]
    assert query["maxLength"] == 1000 and query["minLength"] == 2
    assert tools["find_sources"].input_schema["properties"]["intent"]["enum"] == [
        "explain", "remediate", "alternative", "worked_example"]
    assert set(tools["learning_context"].output_schema["properties"]) >= {
        "misconceptions", "misconception_candidates", "open_hypotheses", "recurrence_groups",
        "recent_answer_traces", "open_learner_text_gaps", "retention_risks"}
    # No tool takes a path, SQL, a caller kind or a policy: the server derives them.
    for tool in tools.values():
        assert not {"path", "sql", "caller", "policy", "vault"} & set(tool.input_schema.get("properties") or {})


def test_every_call_is_recorded_with_its_origin_and_is_never_evidence(world, server):
    calls = [("status", {}), ("today", {}), ("progress", {}), ("library", {"query": "matrix"}),
             ("learning_context", {"topic": "matrix"}), ("find_sources", {"query": "determinant row swap"}),
             ("status", {})]
    results = _call_all(server, calls)
    assert all(not result.is_error for result in results), [r.content for r in results if r.is_error]
    events = _events(world.repository)
    assert [event["subject_id"] for event in events] == [name for name, _ in calls]
    for event in events:
        payload = event["payload"]
        assert event["origin"] == "chat_host" and event["actor"] == "chat_host_model"
        assert event["client_id"] == "unknown" and payload["host"] == "unknown"
        assert payload["surface"] == "chat_mcp" and payload["transport"] == "in_process"
        assert payload["status"] == "ok" and payload["result_hash"].startswith("sha256:")
        assert payload["authority_class"] == "salience_only"
        with pytest.raises(SalienceEvidenceRejected):
            reject_salience(event)
    # Same arguments, same hash; the policy version is the vault's algorithm version.
    assert events[0]["payload"]["arguments_hash"] == events[-1]["payload"]["arguments_hash"]
    assert events[0]["policy_version"] and events[0]["payload_schema_version"] == "chat-tool-call-v1"
    context_event = events[4]["payload"]
    assert context_event["summary"]["misconceptions"] == 1 and "lo_matrices" in context_event["learning_object_ids"]


def test_no_protected_text_reaches_any_payload(world, server):
    calls = [
        ("status", {}), ("today", {}), ("progress", {}), ("library", {}),
        ("learning_context", {}), ("learning_context", {"topic": "matrix computations", "max_traces": 30}),
        ("learning_context", {"learning_object_ids": ["lo_matrices"]}),
        ("find_sources", {"query": "compute the eigenvalues of the matrix and justify them"}),
        ("find_sources", {"query": "cofactor expansion computes a determinant along any row"}),
        ("find_sources", {"query": "subtracting gives the eigenvalue", "limit": 12}),
        ("find_sources", {"query": "eigenvalues determinant", "intent": "alternative"}),
    ]
    results = _call_all(server, calls)
    for (name, _arguments), result in zip(calls, results):
        assert not result.is_error, (name, result.content)
        text = payload_text(result.structured_content) + "".join(getattr(c, "text", "") for c in result.content)
        leaked = [planted for planted in PROTECTED if planted in text]
        assert not leaked, (name, leaked)
    context = results[4].structured_content
    traces = {trace["attempt_id"]: trace for trace in context["recent_answer_traces"]}
    assert traces["att_held"]["result"] == "held_for_review"
    assert context["labels"]["held_for_review"] == "a held grade has no score yet"


def test_learning_context_is_the_apps_latent_state(world, server):
    (result,) = _call_all(server, [("learning_context", {"topic": "matrix"})])
    context = result.structured_content
    assert context["scope"]["matched_by"] == "topic" and "lo_matrices" in context["scope"]["learning_object_ids"]
    (misconception,) = context["misconceptions"]
    assert misconception["statement"] == MISCONCEPTION and misconception["evidence_count"] == 2
    # The correction states an item's answer key: withheld, and said so.
    assert misconception["correction"] is None and "answer key" in misconception["correction_note"]
    (candidate,) = context["misconception_candidates"]
    assert candidate["statement"] == CANDIDATE and candidate["status"] == "candidate"
    hypotheses = [h for h in context["open_hypotheses"] if h["kind"] == "diagnosed_cause"]
    swap = next(h for h in hypotheses if h["hypothesis_id"] == world.hypothesis_id)
    assert swap["statement"] == HYPOTHESIS and swap["label"] == "a hypothesis, not a finding"
    assert swap["evidence_for"]["recurrence_class_count"] == 2
    assert [repair["episode_id"] for repair in swap["repairs_tried"]] == ["rem_swap"]
    # The hypothesis on the cold check's own answer keeps no statement.
    cold = next(h for h in hypotheses if h["attempt_id"] == "att_cold")
    assert cold["statement"] is None and "check waiting in the app" in cold["statement_note"]
    (group,) = context["recurrence_groups"]
    assert group["statement"] == HYPOTHESIS and group["episodes"] == 2
    traces = {trace["attempt_id"]: trace for trace in context["recent_answer_traces"]}
    own = traces["att_own"]
    assert own["stem"] == PINNED_STEM and own["answer"] == OWN_ANSWER and own["result"] == "incorrect"
    assert own["evidence_origin"] == "human" and own["entry_surface"] == "desktop_practice"
    assert traces["att_key"]["answer"] is None and "answer key" in traces["att_key"]["answer_note"]
    for attempt_id, reason in (("att_cold", "a check waiting in the app"),
                               ("att_exam", "exam or held-out material"),
                               ("att_reserved", "reserved for an assessment"), ("att_probe", "a diagnostic check")):
        trace = traces[attempt_id]
        assert trace["withheld"] == reason and trace["stem"] is None and trace["answer"] is None, attempt_id
    assert traces["att_held"]["hints_used"] == 1 and traces["att_held"]["result"] == "held_for_review"
    (gap,) = context["open_learner_text_gaps"]
    assert gap["learner_text"] == GAP_TEXT and gap["target"] == CANDIDATE
    (risk,) = context["retention_risks"]
    assert risk["learning_object_id"] == "lo_matrices" and risk["items_due_now"] == 1


def test_read_model_fields_match_the_router_card_for_convergence(world, server):
    """R2a's LearnerStateCardV1 (not on main yet) can adopt this read model:
    its ``recent_work`` and ``open_hypotheses`` entry keys are all here."""

    (result,) = _call_all(server, [("learning_context", {})])
    context = result.structured_content
    card_recent_work = {"attempt_id", "at", "learning_object_id", "topic", "kind", "result", "hints_used",
                        "assisted", "key_status", "withheld", "stem", "stem_note", "answer"}
    card_open_problem = {"kind", "learning_object_id", "topic", "status", "since", "statement"}
    card_diagnosed = card_open_problem | {"hypothesis_id", "attempt_id", "error_event_id", "promoted_misconception_id"}
    assert all(card_recent_work <= set(trace) for trace in context["recent_answer_traces"])
    for entry in context["open_hypotheses"]:
        assert (card_diagnosed if entry["kind"] == "diagnosed_cause" else card_open_problem) <= set(entry)


def test_learning_context_fails_closed_when_protection_cannot_be_read(world, server, monkeypatch):
    import learnloop.content.sources.exam_material as exam_material

    def broken(*_args, **_kwargs):
        raise RuntimeError("source sets unreadable")

    monkeypatch.setattr(exam_material, "exam_material", broken)
    (result,) = _call_all(server, [("learning_context", {})])
    context = result.structured_content
    assert all(trace["stem"] is None and trace["answer"] is None for trace in context["recent_answer_traces"])
    assert OWN_ANSWER not in payload_text(context)
    assert any("protected could not be read" in unknown for unknown in context["unknowns"])


def test_find_sources_grounds_with_citations_and_withholds_protected_passages(world, server):
    results = _call_all(server, [
        ("find_sources", {"query": "cofactor expansion computes a determinant along any row"}),
        ("find_sources", {"query": "compute the eigenvalues of the matrix and justify them"}),
        ("find_sources", {"query": "subtracting gives the eigenvalue", "limit": 12}),
    ])
    cold, exam, solutions = (result.structured_content for result in results)
    assert cold["policy"] == "reading" and "agent caller" in cold["policy_derived_from"]
    assert COLD_PASSAGE not in payload_text(cold) and cold["withheld"]["held_for_a_check"] >= 1
    assert exam["withheld"]["exam_material"] >= 1
    assert solutions["withheld"]["solutions"] >= 1
    passage = next(p for p in cold["passages"])
    citation = passage["citation"]
    assert citation["locator"] == f"span:{citation['extraction_id']}/{citation['span_id']}"
    assert citation["source_title"] and citation["revision_id"] and passage["label"].startswith("source-authored")


def test_shown_passages_are_exposure_for_the_items_built_on_them(world, server):
    from learnloop.instructional.exposure import independent_check_eligibility
    from learnloop.vault.loader import load_vault

    (result,) = _call_all(server, [("find_sources", {"query": "the determinant changes sign when rows are swapped"})])
    shown = [(p["citation"]["extraction_id"], p["citation"]["span_id"]) for p in result.structured_content["passages"]]
    assert ("ext_book", "s7") in shown
    (event,) = _events(world.repository)
    call_id = event["payload"]["call_id"]
    exposures = world.repository.source_exposure_events(entity_type="chat_tool_call", entity_id=call_id)
    assert {(row["extraction_id"], row["span_id"]) for row in exposures} == set(shown)
    assert len(event["payload"]["exposure_event_ids"]) == len(shown)
    # An item built on the shown passage is no longer an unexposed independent check (§5.4 rule 3).
    vault = load_vault(world.root)
    verdict = independent_check_eligibility(
        vault, world.repository, {"practice_item_id": "pi_determinant_2", "extraction_id": "ext_book",
                                  "span_ids": ["s7"]}, intent="retention")
    assert verdict["eligible"] is False and "source_exposed" in verdict["reasons"]


def test_vault_text_comes_back_as_quoted_data_and_changes_nothing(world, server):
    from tests.source_retrieval_fakes import seed_source

    seed_source(world.repository, source_id="src_note", revision_id="rev_note", extraction_id="ext_note",
                title="Determinant notes", units={"n": ("Notes on determinants", [(INJECTION, 1)])})
    tables = ["practice_attempts", "misconceptions", "causal_hypotheses", "learner_text_gaps", "reveal_events",
              "grading_evidence", "practice_item_state"]
    before = {table: table_count(world.repository, table) for table in tables}
    (result,) = _call_all(server, [("find_sources", {"query": "determinant note previous instructions answer key"})])
    texts = [passage["text"] for passage in result.structured_content["passages"]]
    assert INJECTION in texts
    assert {table: table_count(world.repository, table) for table in tables} == before


def test_a_failed_call_is_recorded_and_an_unrecordable_one_returns_nothing(world, server, monkeypatch):
    (missing,) = _call_all(server, [("progress", {"goal_id": "goal_nowhere"})])
    assert missing.is_error and "goal_nowhere" in str(missing.content)
    (event,) = _events(world.repository)
    assert event["payload"]["status"] == "error" and event["payload"]["error_code"] == "not_found"
    import learnloop_mcp.server as server_module

    def refuse(*_args, **_kwargs):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(server_module, "record_tool_call", refuse)
    (unrecorded,) = _call_all(server, [("status", {})])
    assert unrecorded.is_error and "could not record" in str(unrecorded.content)
    assert unrecorded.structured_content is None


def test_verification_runs_only_through_the_services_own_paid_route(world, server, paid_routes):
    (result,) = _call_all(server, [("find_sources", {"query": "the determinant changes sign when two rows are swapped", "verify": True})])
    found = result.structured_content
    # The listwise check asked the source_rerank route (spend caps and receipts
    # are that path's); with no model here it reports unverified, honestly.
    assert paid_routes and set(paid_routes) <= {"source_rerank"}
    assert found["status"].startswith("unverified") and found["passages"] == []


def test_status_reports_readiness_without_probing_a_runtime(world, server, monkeypatch):
    import learnloop.ai.runtime as ai_runtime

    def probe(*_args, **_kwargs):
        raise AssertionError("status must not probe a provider runtime")

    monkeypatch.setattr(ai_runtime, "check_ai_runtime", probe)
    (result,) = _call_all(server, [("status", {})])
    status = result.structured_content
    assert status["database"]["schema_ok"] is True
    assert status["pending"]["grades_held_for_review"] == 1
    routes = status["ai"]["routes"]
    assert routes["grading"]["state"] in {"not_checked", "ready", "needs_key", "manual", "not_configured"}
    assert routes["embedding"] == {"state": "off"}
    assert status["frontend"]["surface"] == "chat_mcp"


def test_progress_reports_standing_per_goal(world, server):
    (result,) = _call_all(server, [("progress", {})])
    progress = result.structured_content
    assert set(progress["standing_counts"]) == {"demonstrated", "assumed", "learning", "untested"}
    assert progress["labels"]["assumed"].startswith("taken as known")
    assert all("report" in goal for goal in progress["goals"])


@pytest.mark.parametrize(
    ("headers", "meta", "client", "host", "signal"),
    [
        ({"Origin": "https://claude.ai"}, None, None, "claude", "origin_header"),
        ({"origin": "https://chatgpt.com"}, None, None, "chatgpt", "origin_header"),
        ({"User-Agent": "Claude-User (+https://www.anthropic.com)"}, None, None, "claude", "user_agent"),
        ({"user-agent": "openai-mcp/1.0.0"}, None, None, "chatgpt", "user_agent"),
        ({}, {"openai/subject": "anon"}, None, "chatgpt", "request_meta"),
        (None, None, "claude-ai", "claude", "client_info"),
        ({"User-Agent": "python-httpx/0.28"}, None, "probe", "unknown", "none"),
    ],
)
def test_host_label_comes_from_the_request(headers, meta, client, host, signal):
    origin = detect_host(headers, meta=meta, client_name=client, transport="streamable_http")
    assert (origin.host, origin.host_signal, origin.transport) == (host, signal, "streamable_http")


def test_today_shows_the_stored_plan_and_writes_nothing(tmp_path, monkeypatch):
    from learnloop.daily_plan.engine import build_plan
    from learnloop.remote import views
    from tests.daily_plan_fakes import NOW, MovableClock, make_env, scheduled, seed_due
    from tests.helpers import create_daily_plan_vault

    no_model_calls(monkeypatch)
    paths = create_daily_plan_vault(tmp_path / "plan", learning_objects={"lo_m1": [("pi_m1a", 2.0), ("pi_m1b", 2.0)]})
    clock = MovableClock()
    env = make_env(paths.root, [scheduled("pi_m1a", "lo_m1", forgetting_risk=0.6),
                                scheduled("pi_m1b", "lo_m1", forgetting_risk=0.5)], clock=clock)
    for item in ("pi_m1a", "pi_m1b"):
        seed_due(env.repository, item, due=NOW, last=None)
    build_plan(env, kind="normal", budget=25.0, remembered=25, minutes_source="chip")
    runtime = RemoteRuntime.attach(paths.root, load_environment=False)
    tables = ["daily_plans", "attention_blocks", "attention_block_events", "sessions", "router_decisions",
              "practice_attempts", "scheduler_offer_receipts"]
    present = [table for table in tables if table_count(env.repository, "sqlite_master", "name = ?", (table,))]
    before = {table: table_count(env.repository, table) for table in present}
    view = views.today(runtime, clock=clock)
    assert view["plan_enabled"] is True and view["plan"]["blocks"]
    block = view["plan"]["blocks"][0]
    assert {"minutes", "why", "topics", "lane", "items"} <= set(block)
    assert "Question pi_m1" not in json.dumps(view)  # no question text in a plan view
    server = build_server(runtime, clock=clock)
    (result,) = _call_all(server, [("today", {})])
    assert result.structured_content["plan"]["blocks"] == view["plan"]["blocks"]
    assert {table: table_count(env.repository, table) for table in present} == before


def test_citations_name_the_source_never_a_local_path(world, server):
    from tests.source_retrieval_fakes import seed_source

    seed_source(world.repository, source_id="src_private", revision_id="rev_private", extraction_id="ext_private",
                title="", original_uri="file:///home/learner/private/Gram_Schmidt_Notes.pdf",
                units={"g": ("Gram-Schmidt", [("Gram-Schmidt orthonormalization turns a basis into an "
                                               "orthonormal basis.", 1)])})
    results = _call_all(server, [("find_sources", {"query": "Gram-Schmidt orthonormalization basis"}),
                                 ("library", {})])
    text = payload_text([result.structured_content for result in results])
    assert "file://" not in text and "/home/learner" not in text
    titles = {p["citation"]["source_title"] for p in results[0].structured_content["passages"]}
    assert any("Gram Schmidt Notes" in str(title) for title in titles), titles
