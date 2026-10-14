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

The re-review (``26dc3da33..e0fdfef36``):

* F4 (reopened): an answer with no pinned contract shows no answer or
  diagnosis text, even when no key change is recorded (absence of a recorded
  change does not establish the revision it was graded against);
* F11: the dry run's verification plan bounds the live request it plans: the
  same prompt construction and request context, every character at its widest
  encoding, and the retry;
* F12: diagnosed and unresolved causes share the one hypotheses limit, and an
  LO with only unresolved causes keeps its entry.

F4 round 3 (the second re-review's verify, ``4493140a2``):

* every answer-derived text (misconception statements and corrections,
  candidate statements, learner-text gaps' words and targets, hypothesis,
  group, answer and diagnosis text) is released by the one guarded renderer,
  which follows its provenance to the answers behind it and applies the
  answers' own protection and revision check: an unpinned historical answer's
  key, propagated anywhere, is withheld, the entry and its counts kept;
* a link that cannot be followed (an error event not on record, an
  unreadable id list, a diagnosis with no context receipt, a belief with no
  provenance at all) withholds the text too;
* every text field of the output schema is either released by that renderer
  (a ``GuardedText``) or not drawn from an answer by construction.
"""

from __future__ import annotations

import ast
import inspect
import os
import re
from typing import Any

import anyio
import pytest
from mcp import Client

from learnloop.learner_context import (
    ANSWER_DERIVED_FIELDS,
    NON_ANSWER_FIELDS,
    PROVENANCE_MISSING,
    PROVENANCE_UNKNOWN,
    WITHHELD_UNKNOWN_ITEM,
    WITHHELD_UNREADABLE,
    ContextLimits,
    GuardedText,
    learning_context,
)
from learnloop.remote.runtime import RemoteRuntime
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from learnloop_mcp.server import ContextOut, build_server
from tests.helpers import NOW_ISO
from tests.mcp_world import (
    CANDIDATE,
    EDITED_OLD_PROMPT,
    GAP_TEXT,
    HISTORICAL_KEY,
    HYPOTHESIS,
    HYPOTHESIS_COLD,
    MISCONCEPTION,
    OWN_ANSWER,
    PROTECTED,
    build_world,
    hold_att_held,
    no_model_calls,
    payload_text,
)
from tests.practice_index_fakes import _item
from tests.source_service_fakes import set_config

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


def _pin(repository, attempt_id: str, item_id: str, prompt: str, key: str) -> None:
    """Grade ``attempt_id`` against one contract of its item, as the desktop does."""

    import json

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
            "schema_version, created_at) VALUES (?, ?, ?, ?, 1, ?)",
            (f"acv_{attempt_id}", item_id, f"h_{attempt_id}", json.dumps({"prompt": prompt, "expected_answer": key}),
             NOW_ISO))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES (?, ?, 'correct', 0, 1, ?, ?)",
            (f"ge_{attempt_id}", attempt_id, NOW_ISO, f"acv_{attempt_id}"))
        connection.commit()


def test_an_unreadable_practice_item_withholds_its_own_answers_only(world, runtime, server):
    _pin(world.repository, "att_held", "pi_held", "Prove that det(AB) = det(A) det(B).", "multiplicativity proof")
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


# -- re-review F4 (reopened) ---------------------------------------------------------------

#: The key an item had when an older answer (graded before contracts were pinned)
#: was graded: no contract, snapshot or YAML records it any more.
LEGACY_KEY = "LEGACY KEY 8841 a row swap negates the volume"


def test_an_unpinned_answer_shows_no_text_even_when_no_key_change_is_recorded(world):
    payload = _item("pi_rewritten", "lo_matrices", "What does a row swap do to det (rewritten)?",
                    ["facet_determinant"])
    payload["expected_answer"] = "it multiplies the determinant by minus one"
    write_yaml(world.paths.practice_item_path("linear-algebra", "pi_rewritten"), payload)
    statement = f"Thinks {LEGACY_KEY} only for 2x2 matrices"
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_legacy', 'pi_rewritten', 'lo_matrices', 'short_answer', 'independent_attempt', ?, 1.0, 0, "
            "'2026-09-19T09:00:00Z', 'old', 'human', 'desktop_practice')", (f"I wrote: {LEGACY_KEY}",))
        connection.commit()
    world.repository.append_causal_hypothesis(
        episode_key="ep_legacy", attempt_id="att_legacy", learning_object_id="lo_matrices",
        cause_scope="learner_state", statement=statement, statement_normalized=statement.lower(), status="candidate")
    world.repository.insert_attempt_diagnosis(
        attempt_id="att_legacy", diagnosis_prompt_version="test", mode="live", history_mode="full",
        status="completed", proposal={"analysis_md": f"The answer restates {LEGACY_KEY} exactly."},
        causal_view=None, validation_report=None, receipt=None)
    peer = "Mixes up swapping rows with scaling one"
    world.repository.append_causal_hypothesis(
        episode_key="ep_legacy_peer", attempt_id="att_own", learning_object_id="lo_matrices",
        cause_scope="learner_state", statement=peer, statement_normalized=peer.lower(), status="candidate")
    with world.repository.connection() as connection:
        # The group is rooted in the unpinned answer's hypothesis (its peer is a pinned answer's).
        for episode, text, joined in (("ep_legacy", statement, "root"), ("ep_legacy_peer", peer, "judgment")):
            connection.execute(
                "INSERT INTO hypothesis_recurrence_groups(episode_key, statement_normalized, group_key, "
                "root_episode_key, class_count, joined_by, builder_version) VALUES (?, ?, 'grp_legacy', 'ep_legacy', "
                "2, ?, 'test')", (episode, text.lower(), joined))
        connection.commit()
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context = result.structured_content
    trace = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_legacy")
    assert trace["withheld"] is None and trace["result"] == "correct"
    assert trace["stem"] is None and trace["stem_note"] == "question revision not recorded"
    assert trace["answer"] is None and "revision" in trace["answer_note"]
    assert trace["diagnosis"]["status"] == "done" and trace["diagnosis"]["summary"] is None
    assert "revision" in trace["diagnosis"]["summary_note"] and trace["diagnosis"]["hypotheses"] == []
    hypothesis = next(h for h in context["open_hypotheses"] if h.get("attempt_id") == "att_legacy")
    assert hypothesis["statement"] is None and "revision" in hypothesis["statement_note"]
    group = next(g for g in context["recurrence_groups"] if g["group_key"] == "grp_legacy")
    assert group["statement"] is None and "revision" in group["statement_note"]
    assert LEGACY_KEY not in _text(result)
    # A pinned answer still shows (the learner's own words, its graded question).
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER
    _no_protected([result])


# -- re-review F11 -------------------------------------------------------------------------

PRICE = 10.0
#: Mostly three-byte characters, with the query's words so the lexical search finds it.
WIDE_TEXT = "determinant row swap sign " + "行列式交换两行时改变符号，" * 90
WIDE_TITLE = "線形代数の教科書" * 20
WIDE_SECTION = "第三章 行列式と行の交換 " * 20


def test_the_dry_run_bounds_the_live_verification(world, monkeypatch):
    from learnloop.practice_index import paid
    from learnloop.practice_index.listwise import ListwiseOutcome, task_output_tokens
    from learnloop.source_retrieval import find_sources as service
    from tests.source_retrieval_fakes import seed_source

    seed_source(world.repository, source_id="src_wide", revision_id="rev_wide", extraction_id="ext_wide",
                title=WIDE_TITLE, units={"w": (WIDE_SECTION, [(f"{index} {WIDE_TEXT}", 1) for index in range(20)])})
    set_config(world.paths, "ai.providers.metered", type="openrouter", model="metered/judge")
    set_config(world.paths, "ai.routing", source_rerank="metered")
    set_config(world.paths, "source_retrieval", llm_price_per_million=PRICE, rerank_max_cost_usd=50.0)
    sent: list[tuple[str, Any]] = []

    def judged(vault, repository, task, *, prompt, refs, **_kwargs):
        sent.append((prompt, task, len(refs)))
        return ListwiseOutcome("unavailable")

    monkeypatch.setattr(service, "judge_listwise", judged)
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    request = {"query": "determinant row swap sign", "intent": "remediate", "misconception_id": "mc_swap"}
    dry, _live = _call_all(server, [("find_sources", {**request, "dry_run": True}), ("find_sources", request)])
    ((prompt, task, judged_count),) = sent
    assert judged_count == service.VERIFY_POOL
    route = paid.plan_route(load_vault(world.root), "source_rerank")
    output = task_output_tokens(task, route)
    live_tokens = paid.estimated_call_tokens(prompt, task.result_model, output)
    plan = dry.structured_content["plan"]["verification"]
    assert plan["status"] == "would_call" and plan["billing"] == "metered"
    assert plan["estimated_tokens"] >= live_tokens
    # The live worst case: the call, then a truncation retry at twice the output budget.
    assert plan["worst_case_marginal_usd"] >= (2 * live_tokens + output) * PRICE / 1_000_000


def test_no_character_encodes_wider_than_the_dry_runs_filler():
    import json

    from learnloop.source_retrieval.find_sources import WIDEST_CHAR

    def width(char: str) -> int:
        return len(json.dumps(char, ensure_ascii=False).encode("utf-8")) - 2

    sample = [chr(code) for code in range(0x10000) if not 0xD800 <= code <= 0xDFFF]
    sample += [chr(code) for code in (0x10000, 0x1F600, 0x10FFFF)]
    assert max(width(char) for char in sample) == width(WIDEST_CHAR) == 6


# -- re-review F12 -------------------------------------------------------------------------


def test_open_hypotheses_share_one_limit_and_keep_unresolved_only_causes(world):
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_vec', 'pi_independence_1', 'lo_vectors', 'short_answer', 'independent_attempt', "
            "'they are independent', 0.0, 0, '2026-09-20T09:00:00Z', 'old', 'human', 'desktop_practice')")
        for factor, attempt in (("ucf_vec", "att_vec"), ("ucf_own", "att_own")):
            connection.execute(
                "INSERT INTO unresolved_cause_factors(id, attempt_id, candidate_causes_json, status, "
                "algorithm_version, created_at, updated_at) VALUES (?, ?, '[]', 'open', 'test', ?, ?)",
                (factor, attempt, NOW_ISO, NOW_ISO))
        connection.commit()
    vault = load_vault(world.root)
    everything = learning_context(vault, world.repository)["open_hypotheses"]
    kinds = [entry["kind"] for entry in everything]
    assert kinds.count("diagnosed_cause") >= 3 and kinds.count("unresolved_cause") == 2
    for limit in (1, 2, 3, 4):
        entries = learning_context(vault, world.repository, limits=ContextLimits(hypotheses=limit))["open_hypotheses"]
        assert len(entries) == limit, limit
        if limit >= 2:
            # The LO with only an unresolved cause keeps its entry; diagnosed causes keep theirs.
            assert any(e["kind"] == "unresolved_cause" and e["learning_object_id"] == "lo_vectors" for e in entries)
            assert any(e["kind"] == "diagnosed_cause" for e in entries)


# -- F4 round 3 ----------------------------------------------------------------------------


def _error_event(connection, event_id: str, attempt_id: str | None, statement: str,
                 misconception_id: str | None = None) -> None:
    connection.execute(
        "INSERT INTO error_events(id, attempt_id, learning_object_id, error_type, severity, is_misconception, status, "
        "created_at, misconception_id, misconception_statement) VALUES (?, ?, 'lo_matrices', 'misconception', 0.6, 1, "
        "'active', ?, ?, ?)", (event_id, attempt_id, NOW_ISO, misconception_id, statement))


def _gap(connection, gap_id: str, *, source_kind: str, source_id: str, attempt_id: str | None, item_id: str | None,
         text: str, target_kind: str | None, target_id: str | None, action: str = "belief_sighting") -> None:
    connection.execute(
        "INSERT INTO learner_text_gaps(id, source_kind, source_id, attempt_id, practice_item_id, "
        "anchor_learning_object_id, learner_text, chooser, context_judge, kind, action, target_kind, target_id, "
        "algorithm_version, pipeline_version, created_at) VALUES (?, ?, ?, ?, ?, 'lo_matrices', ?, 'decider', ?, "
        "'misconception', ?, ?, ?, 'test', 'test', ?)",
        (gap_id, source_kind, source_id, attempt_id, item_id, text,
         "tutor" if source_kind == "tutor_question" else "diagnoser" if source_kind == "diagnosis" else "gap_reader",
         action, target_kind, target_id, NOW_ISO))


def _misconception(connection, misconception_id: str, statement: str, events: str, correction: str | None) -> None:
    connection.execute(
        "INSERT INTO misconceptions(id, learning_object_id, statement, severity, status, source_error_event_ids_json, "
        "correction_statement, created_at, updated_at) VALUES (?, 'lo_matrices', ?, 0.9, 'active', ?, ?, ?, ?)",
        (misconception_id, statement, events, correction, NOW_ISO, NOW_ISO))


def _candidate(connection, candidate_id: str, statement: str, *, events: str = "[]", items: str = "[]",
               count: int = 1, status: str = "candidate", promoted: str | None = None) -> None:
    connection.execute(
        "INSERT INTO misconception_candidates(id, learning_object_id, statement, statement_normalized, "
        "source_error_event_ids_json, item_ids_json, occurrence_count, status, promoted_misconception_id, created_at, "
        "updated_at) VALUES (?, 'lo_matrices', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (candidate_id, statement, statement.lower(), events, items, count, status, promoted, NOW_ISO, NOW_ISO))


def _diagnose(repository, attempt_id: str, analysis: str, *, failures: list[str] | None = None,
              receipt: bool = True) -> None:
    repository.insert_attempt_diagnosis(
        attempt_id=attempt_id, diagnosis_prompt_version="test", mode="live", history_mode="exact",
        status="completed", proposal={"analysis_md": analysis}, causal_view=None, validation_report=None,
        receipt={"failure_attempt_ids": failures or []} if receipt else None)


def _legacy_world(world) -> None:
    """The verify's reproduction: an unpinned historical answer stating a key
    nothing records any more (``att_legacy``), propagated into a recorded
    misconception (its statement and correction, through an error event), a
    candidate (through the same event and its item), the learner-text gaps
    drawn from that answer (its diagnosis and its stuck text) and the beliefs
    they were matched to; plus the indirect paths to the same answer: a
    candidate a gap on it created, a misconception promoted from a candidate
    drawn from it, a pinned answer's diagnosis whose context showed it, and a
    question asked on its item outside any attempt."""

    payload = _item("pi_rewritten", "lo_matrices", "What does a row swap do to det (rewritten)?",
                    ["facet_determinant"])
    payload["expected_answer"] = "it multiplies the determinant by minus one"
    write_yaml(world.paths.practice_item_path("linear-algebra", "pi_rewritten"), payload)
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_legacy', 'pi_rewritten', 'lo_matrices', 'short_answer', 'independent_attempt', ?, 0.0, 0, "
            "'2026-09-19T09:00:00Z', 'old', 'human', 'desktop_practice')", (f"I wrote: {LEGACY_KEY}",))
        _error_event(connection, "ev_legacy", "att_legacy", f"Believes {LEGACY_KEY} in every case", "mc_legacy")
        _misconception(connection, "mc_legacy", f"Believes {LEGACY_KEY} in every case", '["ev_legacy"]',
                       f"Correct: {LEGACY_KEY} only for one swap")
        _candidate(connection, "mcand_legacy", f"Thinks {LEGACY_KEY} twice", events='["ev_legacy"]',
                   items='["pi_rewritten"]', count=3)
        _gap(connection, "gap_legacy_diag", source_kind="diagnosis", source_id="diag_legacy", attempt_id="att_legacy",
             item_id="pi_rewritten", text=f"I wrote: {LEGACY_KEY}", target_kind="durable", target_id="mc_legacy")
        _gap(connection, "gap_legacy_stuck", source_kind="stuck_answer", source_id="att_legacy",
             attempt_id="att_legacy", item_id="pi_rewritten", text=f"stuck: is it {LEGACY_KEY}?",
             target_kind="candidate", target_id="mcand_legacy")
        _gap(connection, "gap_item_question", source_kind="tutor_question", source_id="q_item", attempt_id=None,
             item_id="pi_rewritten", text=f"why is it {LEGACY_KEY}?", target_kind="candidate",
             target_id="mcand_legacy")
        # A candidate a gap on the unpinned answer created (no event, no item of its own).
        _gap(connection, "gap_legacy_created", source_kind="tutor_question", source_id="q_created",
             attempt_id="att_legacy", item_id="pi_rewritten", text="is the sign rule the same for columns?",
             target_kind="candidate", target_id="mcand_from_gap", action="belief_candidate")
        _candidate(connection, "mcand_from_gap", f"Thinks the sign rule is {LEGACY_KEY}")
        # A misconception promoted from a candidate drawn from the unpinned answer.
        _candidate(connection, "mcand_promoted", f"Expects {LEGACY_KEY} for columns too", events='["ev_legacy"]',
                   items='["pi_rewritten"]', status="promoted", promoted="mc_promoted")
        _misconception(connection, "mc_promoted", f"Expects {LEGACY_KEY} for columns too", "[]", None)
        connection.commit()
    # A pinned answer's diagnosis whose context showed the unpinned answer.
    _diagnose(world.repository, "att_own", f"As before, the learner wrote {LEGACY_KEY}.", failures=["att_legacy"])


def test_text_drawn_from_an_unpinned_answer_is_withheld_in_every_section(world):
    _legacy_world(world)
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context = result.structured_content
    assert LEGACY_KEY not in _text(result)
    # The misconceptions and candidates are still listed, with their counts and status; their text is not.
    misconceptions = {m["misconception_id"]: m for m in context["misconceptions"]}
    for misconception_id in ("mc_legacy", "mc_promoted"):
        entry = misconceptions[misconception_id]
        assert entry["statement"] is None and "revision" in entry["statement_note"], misconception_id
        assert entry["status"] == "active"
    legacy = misconceptions["mc_legacy"]
    assert legacy["correction"] is None and "revision" in legacy["correction_note"]
    assert legacy["evidence_count"] == 1
    candidates = {c["candidate_id"]: c for c in context["misconception_candidates"]}
    for candidate_id in ("mcand_legacy", "mcand_from_gap"):
        entry = candidates[candidate_id]
        assert entry["statement"] is None and "revision" in entry["statement_note"], candidate_id
    assert candidates["mcand_legacy"]["evidence_count"] == 3
    gaps = {gap["gap_id"]: gap for gap in context["open_learner_text_gaps"]}
    for gap_id in ("gap_legacy_diag", "gap_legacy_stuck", "gap_item_question"):
        gap = gaps[gap_id]
        assert gap["learner_text"] is None and "revision" in gap["learner_text_note"], gap_id
        # The gap's target (the recorded belief or the candidate) goes through the same renderer.
        assert gap["target"] is None and "revision" in gap["target_note"], gap_id
        assert gap["target_topic"], gap_id
    # The pinned answer's own words still show; its diagnosis, drawn also from the unpinned answer, does not.
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER
    assert own["diagnosis"]["summary"] is None and "revision" in own["diagnosis"]["summary_note"]
    # A pinned answer's belief still shows, through the same rule.
    assert misconceptions["mc_swap"]["statement"] == MISCONCEPTION
    _no_protected([result])


def test_text_whose_provenance_cannot_be_followed_is_withheld(world):
    with world.repository.connection() as connection:
        # Error events not on record (replaced, or never written).
        _misconception(connection, "mc_dangling", "Thinks a row swap is a scaling", '["ev_gone"]', None)
        _misconception(connection, "mc_unreadable", "Thinks a row swap is a shear", "not json", None)
        # No error event, item, error hunt or gap behind it.
        _candidate(connection, "mcand_orphan", "Thinks a row swap is a transpose")
        connection.commit()
    # A pinned answer's diagnosis with no context receipt: what it was shown is not recorded.
    _diagnose(world.repository, "att_own", "The learner expanded along one row only.", receipt=False)
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
    misconceptions = {m["misconception_id"]: m for m in context["misconceptions"]}
    for misconception_id in ("mc_dangling", "mc_unreadable"):
        entry = misconceptions[misconception_id]
        assert entry["statement"] is None and entry["statement_note"] == PROVENANCE_MISSING, misconception_id
    assert misconceptions["mc_dangling"]["evidence_count"] == 1
    orphan = next(c for c in context["misconception_candidates"] if c["candidate_id"] == "mcand_orphan")
    assert orphan["statement"] is None and orphan["statement_note"] == PROVENANCE_UNKNOWN
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER and own["diagnosis"]["status"] == "done"
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == PROVENANCE_MISSING


def _schema_text_fields(schema: dict) -> set[str]:
    """Every string field of a JSON schema, by path (``a[].b``; a union entry
    of a list by its ``kind``: ``a[kind].b``). Every object must be closed and
    every leaf typed, so no text field can hide in an open dict."""

    defs = schema.get("$defs", {})

    def resolve(node: dict) -> dict:
        while "$ref" in node:
            node = defs[node["$ref"].rsplit("/", 1)[-1]]
        return node

    found: set[str] = set()

    def walk(node: dict, path: str) -> None:
        node = resolve(node)
        branches = node.get("anyOf") or node.get("oneOf")
        if branches:
            objects = [resolve(branch) for branch in branches if resolve(branch).get("type") == "object"]
            if len(objects) > 1:
                base = path[:-2] if path.endswith("[]") else path
                for branch in objects:
                    walk(branch, f"{base}[{branch['properties']['kind']['const']}]")
                return
            for branch in branches:
                walk(branch, path)
            return
        kind = node.get("type")
        if kind == "string":
            found.add(path)
        elif kind == "array":
            walk(node["items"], f"{path}[]")
        elif kind == "object":
            assert node.get("additionalProperties") is False and node.get("properties"), f"open object at {path!r}"
            for name, child in node["properties"].items():
                walk(child, f"{path}.{name}" if path else name)
        else:
            assert kind in ("integer", "number", "boolean", "null"), f"untyped field at {path!r}: {node}"

    walk(schema, "")
    return found


def _output_leaves(value: Any, path: str, unions: set[str], out: list[tuple[str, Any]]) -> None:
    if isinstance(value, dict):
        for name, child in value.items():
            _output_leaves(child, f"{path}.{name}" if path else name, unions, out)
    elif isinstance(value, list):
        for child in value:
            label = f"{path}[{child['kind']}]" if path in unions and isinstance(child, dict) else f"{path}[]"
            _output_leaves(child, label, unions, out)
    elif isinstance(value, str):
        out.append((path, value))


def _guarded_everywhere(world) -> list[str]:
    """Every answer-derived field released at least once: a second belief with
    a correction, a diagnosis with its context receipt, an unresolved cause.
    Returns the answer-derived texts planted."""

    correction = "Swapping two rows multiplies the determinant by one sign change"
    summary = "The learner expanded along a single row and lost track of signs."
    with world.repository.connection() as connection:
        _error_event(connection, "ev_scale", "att_own", "Thinks scaling a row leaves det fixed", "mc_scale")
        _misconception(connection, "mc_scale", "Thinks scaling a row leaves det fixed", '["ev_scale"]', correction)
        connection.execute(
            "INSERT INTO unresolved_cause_factors(id, attempt_id, candidate_causes_json, status, algorithm_version, "
            "created_at, updated_at) VALUES ('ucf_own', 'att_own', '[]', 'open', 'test', ?, ?)", (NOW_ISO, NOW_ISO))
        connection.commit()
    _diagnose(world.repository, "att_own", summary, failures=["att_own"])
    return [OWN_ANSWER, MISCONCEPTION, CANDIDATE, HYPOTHESIS, GAP_TEXT, correction, summary,
            "Thinks scaling a row leaves det fixed"]


def test_every_text_field_of_the_output_is_guarded_or_not_answer_derived(world, server):
    """F4 round 3's one rule, checked against the output schema itself: each
    text field of ``learning_context`` is released only by the guarded renderer
    (a ``GuardedText``) or is not drawn from an answer by construction."""

    async def advertised():
        async with Client(server) as client:
            return {tool.name: tool for tool in (await client.list_tools()).tools}

    schema = anyio.run(advertised)["learning_context"].output_schema
    fields = _schema_text_fields(schema)
    assert fields == _schema_text_fields(ContextOut.model_json_schema())
    assert not ANSWER_DERIVED_FIELDS & set(NON_ANSWER_FIELDS)
    assert fields == ANSWER_DERIVED_FIELDS | set(NON_ANSWER_FIELDS), (
        sorted(fields - ANSWER_DERIVED_FIELDS - set(NON_ANSWER_FIELDS)),
        sorted((ANSWER_DERIVED_FIELDS | set(NON_ANSWER_FIELDS)) - fields))

    planted = _guarded_everywhere(world)
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
    unions = {path.split("[", 1)[0] for path in fields if re.match(r"^\w+\[[a-z_]+\]\.", path)}
    leaves: list[tuple[str, Any]] = []
    _output_leaves(context, "", unions, leaves)
    released: set[str] = set()
    for path, value in leaves:
        assert path in fields, path
        if path in ANSWER_DERIVED_FIELDS:
            assert isinstance(value, GuardedText), (path, value)
            released.add(path)
        else:
            assert not isinstance(value, GuardedText), path
            assert not [text for text in planted if text in value], (path, value)
    # Every renderer-owned field was exercised (released at least once on this world).
    assert released == ANSWER_DERIVED_FIELDS, sorted(ANSWER_DERIVED_FIELDS - released)
    # The output is checked against that schema before it is recorded, and reaches the host unchanged.
    ContextOut.model_validate(context)


def test_only_the_renderer_releases_answer_derived_text():
    with pytest.raises(TypeError):
        GuardedText("an answer", object())
    import learnloop.learner_context as module

    tree = ast.parse(inspect.getsource(module))
    calls = [node for node in ast.walk(tree)
             if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "GuardedText"]
    render = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "render")
    assert calls and all(any(call is node for node in ast.walk(render)) for call in calls)
