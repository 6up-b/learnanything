"""Chat frontend C1a, the Codex review's findings (docs/reviews/mcp-c1a-codex-review.md).

* F1: malformed, truncated or mid-write protection metadata (the source sets,
  a practice item's file) fails closed instead of reading as "no protection";
* F2: a recurrence group rooted in a protected hypothesis keeps no statement;
* F3: exam items are found by every provenance form (canonical exercise, block
  locator, namespaced span id), through the shared item predicate;
* F4: answers and diagnosis text are filtered against the key the attempt was
  graded against (its pinned contract), and withheld when that revision cannot
  be established;
* F5: a check reserved while passages are retrieved withholds them (protection
  is read again, with the exposure written, under one write transaction);
* F6: an unmatched topic or unknown ids return no learner history;
* F7: unresolved causes show without a named hypothesis;
* F8: passages keep their formatting (verbatim);
* F9: ``find_sources`` has a dry run: the paid steps and their estimate, no
  provider, no passage, no exposure;
* F10: a call the SDK rejects (invalid arguments, unknown tool) is recorded
  once, and a successful call still once.
"""

from __future__ import annotations

import os

import anyio
import pytest
from mcp import Client

from learnloop.learner_context import WITHHELD_UNKNOWN_ITEM, WITHHELD_UNREADABLE
from learnloop.remote.runtime import RemoteRuntime
from learnloop.vault.yaml_io import write_yaml
from learnloop_mcp.server import build_server
from tests.helpers import NOW_ISO
from tests.mcp_world import (
    EDITED_OLD_PROMPT,
    HISTORICAL_KEY,
    HYPOTHESIS,
    HYPOTHESIS_COLD,
    OWN_ANSWER,
    PROTECTED,
    build_world,
    hold_att_held,
    no_model_calls,
    payload_text,
)
from tests.practice_index_fakes import _item

EXAM_QUERY = "compute the eigenvalues of the matrix and justify them"
SECTIONS = ("misconceptions", "misconception_candidates", "open_hypotheses", "recurrence_groups",
            "recent_answer_traces", "open_learner_text_gaps", "retention_risks")


def _call_all(server, calls):
    async def main():
        async with Client(server) as client:
            return [await client.call_tool(name, arguments) for name, arguments in calls]

    return anyio.run(main)


def _events(repository):
    return repository.reader_interaction_events(kind="chat_tool_call")


def _text(result) -> str:
    return payload_text(result.structured_content) + "".join(getattr(c, "text", "") for c in result.content)


def _no_protected(results) -> None:
    for result in results:
        leaked = [planted for planted in PROTECTED if planted in _text(result)]
        assert not leaked, leaked


def _changed(path) -> None:
    """Make a desktop edit visible to the fingerprint (and its 2 s cache)."""

    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 5_000_000_000))


@pytest.fixture
def paid_routes(monkeypatch):
    return no_model_calls(monkeypatch)


@pytest.fixture
def world(tmp_path, monkeypatch, paid_routes):
    hold_att_held(monkeypatch)
    return build_world(tmp_path / "w")


@pytest.fixture
def runtime(world):
    return RemoteRuntime.attach(world.root, load_environment=False)


@pytest.fixture
def server(runtime):
    return build_server(runtime)


def _reload(runtime) -> None:
    runtime._checked_at = float("-inf")


# -- F1 ------------------------------------------------------------------------------


def _closed(context: dict) -> None:
    traces = context["recent_answer_traces"]
    assert traces and all(trace["stem"] is None and trace["answer"] is None for trace in traces)
    assert all(trace["withheld"] == WITHHELD_UNREADABLE for trace in traces)
    assert all(group["statement"] is None for group in context["recurrence_groups"])
    assert any("protected could not be read" in unknown for unknown in context["unknowns"])


@pytest.mark.parametrize("text", ["source_sets:\n  - id: [unclosed\n", ""], ids=["malformed", "truncated"])
def test_unreadable_source_sets_fail_closed(world, runtime, server, text):
    path = world.paths.source_sets_path
    path.write_text(text, encoding="utf-8")
    _changed(path)
    _reload(runtime)
    results = _call_all(server, [("learning_context", {"max_traces": 30}),
                                 ("find_sources", {"query": EXAM_QUERY}), ("library", {})])
    context, sources, library = results
    _closed(context.structured_content)
    assert sources.is_error and "protected" in _text(sources)
    assert all(card["exam_material"] for card in library.structured_content["sources"])
    _no_protected(results)


def test_a_vault_that_changes_while_it_loads_fails_closed(world, runtime, server, monkeypatch):
    import learnloop.remote.runtime as runtime_module

    real = runtime_module.load_vault
    item_path = world.paths.practice_item_path("linear-algebra", "pi_held")

    def written_meanwhile(*args, **kwargs):
        loaded = real(*args, **kwargs)
        # The desktop rewrites a file while this process reads the vault.
        item_path.write_text(item_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        return loaded

    monkeypatch.setattr(runtime_module, "load_vault", written_meanwhile)
    _changed(item_path)
    _reload(runtime)
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    _closed(result.structured_content)
    _no_protected([result])
    # Settled again: the next read loads a consistent snapshot and protection is back.
    monkeypatch.setattr(runtime_module, "load_vault", real)
    _reload(runtime)
    (settled,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    traces = {trace["attempt_id"]: trace for trace in settled.structured_content["recent_answer_traces"]}
    assert traces["att_own"]["answer"] == OWN_ANSWER


def test_an_unreadable_practice_item_withholds_its_own_answers_only(world, runtime, server):
    path = world.paths.practice_item_path("linear-algebra", "pi_own")
    path.write_text("id: [unclosed\n", encoding="utf-8")
    _changed(path)
    _reload(runtime)
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context = result.structured_content
    traces = {trace["attempt_id"]: trace for trace in context["recent_answer_traces"]}
    own = traces["att_own"]
    assert own["withheld"] == WITHHELD_UNKNOWN_ITEM and own["stem"] is None and own["answer"] is None
    assert OWN_ANSWER not in payload_text(context)
    # The rest of the record is still shown.
    assert traces["att_held"]["answer"] == "my proof sketch"
    _no_protected([result])


# -- F2 ------------------------------------------------------------------------------


def test_a_recurrence_group_rooted_in_a_protected_hypothesis_keeps_no_statement(world, server, monkeypatch):
    (result,) = _call_all(server, [("learning_context", {"topic": "matrix"})])
    groups = {group["group_key"]: group for group in result.structured_content["recurrence_groups"]}
    assert groups["grp_swap"]["statement"] == HYPOTHESIS
    cold = groups["grp_cold"]
    assert cold["statement"] is None and "check waiting in the app" in cold["statement_note"]
    assert HYPOTHESIS_COLD not in payload_text(result.structured_content)
    import learnloop.content.sources.exam_material as exam_material

    def broken(*_args, **_kwargs):
        raise RuntimeError("source sets unreadable")

    monkeypatch.setattr(exam_material, "exam_material", broken)
    (closed,) = _call_all(server, [("learning_context", {"topic": "matrix"})])
    assert all(group["statement"] is None for group in closed.structured_content["recurrence_groups"])


# -- F3 ------------------------------------------------------------------------------


def test_exam_items_are_found_by_every_provenance_form(world, server):
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    traces = {trace["attempt_id"]: trace for trace in result.structured_content["recent_answer_traces"]}
    for attempt_id in ("att_exam_canon", "att_exam_locator", "att_exam_ns"):
        trace = traces[attempt_id]
        assert trace["withheld"] == "exam or held-out material", attempt_id
        assert trace["stem"] is None and trace["answer"] is None and trace["result"] == "correct"
    _no_protected([result])


# -- F4 ------------------------------------------------------------------------------


def test_answers_and_diagnoses_are_filtered_against_the_key_they_were_graded_by(world, server):
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context = result.structured_content
    traces = {trace["attempt_id"]: trace for trace in context["recent_answer_traces"]}
    edited = traces["att_edited"]
    # The question as it was graded is shown; the answer restating that revision's key is not.
    assert edited["stem"] == EDITED_OLD_PROMPT
    assert edited["answer"] is None and "answer key" in edited["answer_note"]
    assert edited["diagnosis"]["status"] == "done"
    assert edited["diagnosis"]["summary"] is None and "answer key" in edited["diagnosis"]["summary_note"]
    assert edited["diagnosis"]["hypotheses"] == []
    statement = next(h for h in context["open_hypotheses"] if h.get("attempt_id") == "att_edited")
    assert statement["statement"] is None and "answer key" in statement["statement_note"]
    # No pinned contract and the key has changed since: which key it answered is unknown.
    unpinned = traces["att_unpinned"]
    assert unpinned["answer"] is None and "revision" in unpinned["answer_note"]
    assert HISTORICAL_KEY not in payload_text(context)
    _no_protected([result])


# -- F5 ------------------------------------------------------------------------------


def test_a_check_reserved_while_passages_are_retrieved_withholds_them(world, monkeypatch):
    payload = _item("pi_race", "lo_matrices", "Why does a row swap flip the determinant's sign?",
                    ["facet_determinant"])
    payload["provenance"] = {"origin": "human", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": "src_book", "extraction_id": "ext_book", "span_ids": ["s7"]}]}
    write_yaml(world.paths.practice_item_path("linear-algebra", "pi_race"), payload)
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    import learnloop.instructional.sources as instructional_sources

    real = instructional_sources.propose_sources

    def reserved_meanwhile(*args, **kwargs):
        hits = real(*args, **kwargs)
        assert any((hit["extraction_id"], hit["span_id"]) == ("ext_book", "s7") for hit in hits.hits)
        # The desktop reserves a cold retry on the item built on that passage while retrieval runs.
        with world.repository.connection() as connection:
            connection.execute(
                "INSERT INTO followup_tasks(id, kind, case_kind, case_ref, not_before, status, selected_item_id, "
                "created_at, updated_at) VALUES ('ft_race', 'cold_retry', 'misconception', 'mc_swap', ?, "
                "'pending', 'pi_race', ?, ?)", ("2026-10-30T00:00:00Z", NOW_ISO, NOW_ISO))
            connection.commit()
        return hits

    monkeypatch.setattr(instructional_sources, "propose_sources", reserved_meanwhile)
    (result,) = _call_all(server, [("find_sources", {"query": "the determinant changes sign when rows are swapped"})])
    found = result.structured_content
    shown = {(p["citation"]["extraction_id"], p["citation"]["span_id"]) for p in found["passages"]}
    assert ("ext_book", "s7") not in shown and found["withheld"]["held_for_a_check"] >= 1
    exposed = {(row["extraction_id"], row["span_id"])
               for row in world.repository.source_exposure_events(entity_type="chat_tool_call")}
    assert ("ext_book", "s7") not in exposed and exposed == shown


# -- F6 ------------------------------------------------------------------------------


@pytest.mark.parametrize(("arguments", "note"), [
    ({"topic": "quantum chromodynamics"}, "no topic in the vault matched"),
    ({"learning_object_ids": ["lo_nowhere"]}, "none of the named learning objects"),
])
def test_an_unmatched_scope_returns_no_learner_history(world, server, arguments, note):
    (result,) = _call_all(server, [("learning_context", arguments)])
    context = result.structured_content
    assert context["scope"]["learning_object_count"] == 0
    assert {section: context[section] for section in SECTIONS} == {section: [] for section in SECTIONS}
    assert any(note in unknown for unknown in context["unknowns"])


# -- F7 ------------------------------------------------------------------------------


def test_unresolved_causes_show_without_a_named_hypothesis(world, server):
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_vec', 'pi_independence_1', 'lo_vectors', 'short_answer', 'independent_attempt', "
            "'they are independent', 0.0, 0, '2026-09-20T09:00:00Z', 'old', 'human', 'desktop_practice')")
        connection.execute(
            "INSERT INTO unresolved_cause_factors(id, attempt_id, candidate_causes_json, status, algorithm_version, "
            "created_at, updated_at) VALUES ('ucf_vec', 'att_vec', '[]', 'open', 'test', ?, ?)", (NOW_ISO, NOW_ISO))
        connection.commit()
    (result,) = _call_all(server, [("learning_context", {"learning_object_ids": ["lo_vectors"]})])
    (entry,) = result.structured_content["open_hypotheses"]
    assert entry["kind"] == "unresolved_cause" and entry["learning_object_id"] == "lo_vectors"
    assert entry["statement"] == "1 answer(s) whose cause is not settled"


# -- F8 ------------------------------------------------------------------------------


CODE_BLOCK = ("Sign rule in Python for row swaps:\n"
              "def sign_after(swaps):\n"
              "    if swaps % 2:\n"
              "        return -1\n"
              "    return 1")
TABLE_BLOCK = "| row swaps | sign of det |\n|---|---|\n| 1 | -1 |\n| 2 | +1 |"
MATH_BLOCK = "$$\n\\det(P A) = -\\det(A)\n$$\nfor a single row swap P."


def test_passages_are_verbatim_with_their_formatting(world, server):
    from tests.source_retrieval_fakes import seed_source

    seed_source(world.repository, source_id="src_code", revision_id="rev_code", extraction_id="ext_code",
                title="Sign rule notes", units={"c": ("Sign rule in code", [(CODE_BLOCK, 1), (TABLE_BLOCK, 1),
                                                                             (MATH_BLOCK, 1)])})
    (result,) = _call_all(server, [("find_sources", {"query": "row swaps sign python det", "limit": 12})])
    texts = [passage["text"] for passage in result.structured_content["passages"]]
    assert CODE_BLOCK in texts and TABLE_BLOCK in texts and MATH_BLOCK in texts


# -- F9 ------------------------------------------------------------------------------


def test_find_sources_dry_run_plans_without_a_provider_or_exposure(world, server, paid_routes):
    calls = [("find_sources", {"query": "why does a row swap change the determinant", "intent": "alternative",
                               "dry_run": True}),
             ("find_sources", {"query": "why does a row swap change the determinant", "dry_run": True})]
    alternative, explain = (result.structured_content for result in _call_all(server, calls))
    for found in (alternative, explain):
        assert found["status"] == "dry_run" and found["passages"] == [] and found["chars_returned"] == 0
        plan = found["plan"]
        assert plan["dry_run"] is True and {"rewrite", "query_embedding", "verification"} <= set(plan)
        assert "calls" in plan and "estimated_usd" in plan
    # An alternative is always verified (one listwise call); a plain explain is not.
    assert alternative["plan"]["verification"]["status"] != "not_requested"
    assert explain["plan"]["verification"]["status"] == "not_requested"
    assert paid_routes == []  # no provider was even resolved
    assert world.repository.source_exposure_events(entity_type="chat_tool_call") == []
    events = _events(world.repository)
    assert [event["payload"]["summary"].get("dry_run") for event in events] == [True, True]
    assert all(event["payload"]["exposure_event_ids"] == [] for event in events)


def test_a_subscription_route_is_estimated_from_tokens(world, server, paid_routes):
    """The world's source_rerank route is the Codex profile (the owner's
    ChatGPT plan): its cost is estimated from tokens, never charged to a cap."""

    (result,) = _call_all(server, [("find_sources", {"query": "why does a row swap change the determinant",
                                                     "intent": "alternative", "dry_run": True})])
    plan = result.structured_content["plan"]
    verification = plan["verification"]
    assert verification["status"] == "would_call" and verification["billing"] == "subscription"
    assert verification["cost_basis"] == "estimated_only" and verification["estimated_tokens"] > 0
    assert verification["marginal_usd"] == 0.0 and verification["max_calls_with_retry"] == 2
    assert plan["calls"] == 1 and plan["estimated_tokens"] >= verification["estimated_tokens"]
    assert plan["cost_basis"] == ["estimated_only"] and paid_routes == []


# -- F10 -----------------------------------------------------------------------------


def test_calls_the_sdk_rejects_are_recorded_once(world, server):
    results = _call_all(server, [("find_sources", {"query": "x"}), ("no_such_tool", {"a": 1}), ("status", {})])
    assert results[0].is_error and results[1].is_error and not results[2].is_error
    rows = [(event["subject_id"], event["payload"]["status"], event["payload"]["error_code"])
            for event in _events(world.repository)]
    assert rows == [("find_sources", "error", "invalid_arguments"), ("unknown_tool", "error", "unknown_tool"),
                    ("status", "ok", None)]
