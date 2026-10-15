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

F4 rounds 3-5 (the verifies of ``4493140a2``, ``f6c6c73b8`` and ``223d27ef2``)
planted an unpinned historical answer's key in every text a model writes
downstream of it. Their reproductions are kept here; since the narrow stage
(owner decision 2026-10-14, ``tests/test_mcp_c1a_narrow.py``) every such text
is held back until a write-time record says what it was written from, so each
asserts no leak and the entry kept.
"""

from __future__ import annotations

import os
from typing import Any

import anyio
import pytest
from mcp import Client

from learnloop.learner_context import (
    HELD_BACK,
    KEY_WITHHELD,
    REVISION_UNKNOWN_BEHIND,
    TOPIC_WITHHELD,
    WITHHELD_UNKNOWN_ITEM,
    WITHHELD_UNREADABLE,
    ContextLimits,
    WriteProvenance,
    group_alias,
    learning_context,
)
from learnloop.remote.runtime import RemoteRuntime
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml
from learnloop_mcp.server import build_server
from tests.helpers import NOW_ISO
from tests.mcp_world import (
    CANDIDATE,
    EDITED_OLD_PROMPT,
    GENERATED_TITLE,
    HISTORICAL_KEY,
    HYPOTHESIS,
    HYPOTHESIS_COLD,
    LEGACY_KEY,
    MISCONCEPTION,
    OWN_ANSWER,
    PEER,
    PEER_ANSWER,
    PROTECTED,
    build_world,
    c4_receipt,
    candidate_row,
    error_event,
    gap_row,
    generated_world,
    group_row,
    hold_att_held,
    hypothesis_row,
    legacy_answer,
    live_diagnosis,
    misconception_row,
    no_model_calls,
    payload_text,
    pinned_answer,
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


#: An alias key for direct reads, so a test can name a group by its shown key.
ALIAS_KEY = b"k" * 32
#: A complete write-time record naming only the pinned answer and its topic (rule (c)).
SAFE = WriteProvenance(complete=True, answers=("att_own",), topics=("lo_matrices",))


def _recorded(_connection, _kind, _record_id):
    return SAFE


def test_a_recurrence_group_rooted_in_a_protected_hypothesis_keeps_no_statement(world, server, monkeypatch):
    (result,) = _call_all(server, [("learning_context", {"topic": "matrix"})])
    assert all(group["statement"] is None for group in result.structured_content["recurrence_groups"])
    assert HYPOTHESIS_COLD not in payload_text(result.structured_content)
    # Even with a safe record for the root's statement, the group rooted in the
    # cold check's hypothesis keeps none: its member answers are checked too.
    vault = load_vault(world.root)
    context = learning_context(vault, world.repository, topic="matrix", alias_key=ALIAS_KEY, provenance=_recorded)
    groups = {group["group_key"]: group for group in context["recurrence_groups"]}
    assert groups[group_alias("grp_swap", ALIAS_KEY)]["statement"] == HYPOTHESIS
    cold = groups[group_alias("grp_cold", ALIAS_KEY)]
    assert cold["statement"] is None and "check waiting in the app" in cold["statement_note"]
    assert HYPOTHESIS_COLD not in payload_text(context)
    import learnloop.content.sources.exam_material as exam_material

    def broken(*_args, **_kwargs):
        raise RuntimeError("source sets unreadable")

    monkeypatch.setattr(exam_material, "exam_material", broken)
    closed = learning_context(vault, world.repository, topic="matrix", alias_key=ALIAS_KEY, provenance=_recorded)
    assert all(group["statement"] is None for group in closed["recurrence_groups"])


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
    assert edited["diagnosis"]["summary"] is None and edited["diagnosis"]["summary_note"] == HELD_BACK
    assert edited["diagnosis"]["hypotheses"] == []
    statement = next(h for h in context["open_hypotheses"] if h.get("attempt_id") == "att_edited")
    assert statement["statement"] is None and statement["statement_note"] == HELD_BACK
    # No pinned contract and the key has changed since: which key it answered is unknown.
    unpinned = traces["att_unpinned"]
    assert unpinned["answer"] is None and "revision" in unpinned["answer_note"]
    assert HISTORICAL_KEY not in payload_text(context)
    _no_protected([result])
    # A write-time record does not lift the key filter: the summary and the
    # hypothesis restate the key the edited item had when it was graded.
    edited_record = WriteProvenance(complete=True, answers=("att_edited",))
    recorded = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30),
                                provenance=lambda _c, _k, _r: edited_record)
    trace = next(t for t in recorded["recent_answer_traces"] if t["attempt_id"] == "att_edited")
    assert trace["diagnosis"]["summary"] is None and trace["diagnosis"]["summary_note"] == KEY_WITHHELD
    hypothesis = next(h for h in recorded["open_hypotheses"] if h.get("attempt_id") == "att_edited")
    assert hypothesis["statement"] is None and hypothesis["statement_note"] == KEY_WITHHELD
    assert HISTORICAL_KEY not in payload_text(recorded)


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
    assert trace["diagnosis"]["summary_note"] == HELD_BACK and trace["diagnosis"]["hypotheses"] == []
    hypothesis = next(h for h in context["open_hypotheses"] if h.get("attempt_id") == "att_legacy")
    assert hypothesis["statement"] is None and hypothesis["statement_note"] == HELD_BACK
    assert all(group["statement"] is None for group in context["recurrence_groups"])
    assert LEGACY_KEY not in _text(result)
    # A pinned answer still shows (the learner's own words, its graded question).
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER
    _no_protected([result])
    # A record naming the unpinned answer releases nothing drawn from it.
    record = WriteProvenance(complete=True, answers=("att_legacy",))
    recorded = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30),
                                alias_key=ALIAS_KEY, provenance=lambda _c, _k, _r: record)
    hypothesis = next(h for h in recorded["open_hypotheses"] if h.get("attempt_id") == "att_legacy")
    assert hypothesis["statement"] is None and hypothesis["statement_note"] == REVISION_UNKNOWN_BEHIND
    group = next(g for g in recorded["recurrence_groups"] if g["group_key"] == group_alias("grp_legacy", ALIAS_KEY))
    assert group["statement"] is None and group["statement_note"] == REVISION_UNKNOWN_BEHIND
    assert LEGACY_KEY not in payload_text(recorded)


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




# -- F4 rounds 3-5: their reproductions, held back -------------------------------------------
#
# Each world below made the output-side provenance chase release an unpinned
# answer's key (or a drafted topic name). Under the narrow rule none of that
# text is released without a write-time record, so each asserts no leak, the
# entry kept with its counts and status, and the learner's own pinned answer
# still shown.


def _legacy_world(world) -> None:
    """F4 round 3: ``att_legacy``'s key propagated into a recorded misconception
    (statement and correction, through an error event), a candidate (the same
    event and its item), the gaps drawn from that answer (its diagnosis and its
    stuck text) and the beliefs they were matched to; a candidate a gap on it
    created, a misconception promoted from a candidate drawn from it, a pinned
    answer's diagnosis whose context showed it, and a question asked on its
    item outside any attempt."""

    legacy_answer(world)
    with world.repository.connection() as connection:
        error_event(connection, "ev_legacy", "att_legacy", f"Believes {LEGACY_KEY} in every case", "mc_legacy")
        misconception_row(connection, "mc_legacy", f"Believes {LEGACY_KEY} in every case", '["ev_legacy"]',
                          f"Correct: {LEGACY_KEY} only for one swap")
        candidate_row(connection, "mcand_legacy", f"Thinks {LEGACY_KEY} twice", events='["ev_legacy"]',
                      items='["pi_rewritten"]', count=3)
        gap_row(connection, "gap_legacy_diag", source_kind="diagnosis", source_id="diag_legacy",
                attempt_id="att_legacy", item_id="pi_rewritten", text=f"I wrote: {LEGACY_KEY}", target_kind="durable",
                target_id="mc_legacy")
        gap_row(connection, "gap_legacy_stuck", source_kind="stuck_answer", source_id="att_legacy",
                attempt_id="att_legacy", item_id="pi_rewritten", text=f"stuck: is it {LEGACY_KEY}?",
                target_kind="candidate", target_id="mcand_legacy")
        gap_row(connection, "gap_item_question", source_kind="tutor_question", source_id="q_item", attempt_id=None,
                item_id="pi_rewritten", text=f"why is it {LEGACY_KEY}?", target_kind="candidate",
                target_id="mcand_legacy")
        gap_row(connection, "gap_legacy_created", source_kind="tutor_question", source_id="q_created",
                attempt_id="att_legacy", item_id="pi_rewritten", text="is the sign rule the same for columns?",
                target_kind="candidate", target_id="mcand_from_gap", action="belief_candidate")
        candidate_row(connection, "mcand_from_gap", f"Thinks the sign rule is {LEGACY_KEY}")
        candidate_row(connection, "mcand_promoted", f"Expects {LEGACY_KEY} for columns too", events='["ev_legacy"]',
                      items='["pi_rewritten"]', status="promoted", promoted="mc_promoted")
        misconception_row(connection, "mc_promoted", f"Expects {LEGACY_KEY} for columns too", "[]", None)
        connection.commit()
    live_diagnosis(world.repository, "att_own", f"As before, the learner wrote {LEGACY_KEY}.",
                   receipt={"failure_attempt_ids": ["att_legacy"]})


def test_text_drawn_from_an_unpinned_answer_is_withheld_in_every_section(world):
    _legacy_world(world)
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context = result.structured_content
    assert LEGACY_KEY not in _text(result)
    misconceptions = {m["misconception_id"]: m for m in context["misconceptions"]}
    for misconception_id in ("mc_legacy", "mc_promoted", "mc_swap"):
        entry = misconceptions[misconception_id]
        assert entry["statement"] is None and entry["statement_note"] == HELD_BACK, misconception_id
        assert entry["status"] == "active"
    assert misconceptions["mc_legacy"]["correction"] is None and misconceptions["mc_legacy"]["evidence_count"] == 1
    candidates = {c["candidate_id"]: c for c in context["misconception_candidates"]}
    for candidate_id in ("mcand_legacy", "mcand_from_gap", "mcand_row"):
        assert candidates[candidate_id]["statement"] is None, candidate_id
        assert candidates[candidate_id]["statement_note"] == HELD_BACK, candidate_id
    assert candidates["mcand_legacy"]["evidence_count"] == 3
    gaps = {gap["gap_id"]: gap for gap in context["open_learner_text_gaps"]}
    # Words that are the unpinned answer itself: the answer guard's revision check.
    for gap_id in ("gap_legacy_diag", "gap_legacy_stuck"):
        assert gaps[gap_id]["learner_text"] is None and "revision" in gaps[gap_id]["learner_text_note"], gap_id
    # A question (no pinned answer behind it): held back.
    assert gaps["gap_item_question"]["learner_text"] is None
    assert gaps["gap_item_question"]["learner_text_note"] == HELD_BACK
    for gap_id in ("gap_legacy_diag", "gap_legacy_stuck", "gap_item_question"):
        assert gaps[gap_id]["target"] is None and gaps[gap_id]["target_note"] == HELD_BACK, gap_id
        assert gaps[gap_id]["target_topic"] == "Matrix computations", gap_id
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK
    _no_protected([result])


def test_text_whose_provenance_cannot_be_followed_is_withheld(world):
    with world.repository.connection() as connection:
        misconception_row(connection, "mc_dangling", "Thinks a row swap is a scaling", '["ev_gone"]', None)
        misconception_row(connection, "mc_unreadable", "Thinks a row swap is a shear", "not json", None)
        candidate_row(connection, "mcand_orphan", "Thinks a row swap is a transpose")
        connection.commit()
    live_diagnosis(world.repository, "att_own", "The learner expanded along one row only.", receipt=None)
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
    misconceptions = {m["misconception_id"]: m for m in context["misconceptions"]}
    for misconception_id in ("mc_dangling", "mc_unreadable"):
        entry = misconceptions[misconception_id]
        assert entry["statement"] is None and entry["statement_note"] == HELD_BACK, misconception_id
    assert misconceptions["mc_dangling"]["evidence_count"] == 1 and misconceptions["mc_unreadable"]["evidence_count"] == 0
    orphan = next(c for c in context["misconception_candidates"] if c["candidate_id"] == "mcand_orphan")
    assert orphan["statement"] is None and orphan["statement_note"] == HELD_BACK
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER and own["diagnosis"]["status"] == "done"
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK


def test_a_diagnosis_s_cause_and_every_belief_drawn_from_it_are_held_back(world):
    """F4 round 4, F1: a pinned answer's diagnosis was shown ``att_legacy`` and
    copied its key into a cause the overlay lays on the pinned answer's event;
    a hypothesis, its group, a misconception, a candidate and a candidate a gap
    on the diagnosis created carry it on."""

    legacy_answer(world)
    cause = f"Believes {LEGACY_KEY} for every matrix"
    with world.repository.connection() as connection:
        error_event(connection, "ev_own", "att_own", None)
        connection.commit()
    diagnosis_id = live_diagnosis(
        world.repository, "att_own", "The learner mixed up two row operations.",
        view={"events": {"ev_own": {"misconception_statement": cause, "is_misconception": True}}},
        receipt={"failure_attempt_ids": ["att_legacy"]})
    hypothesis_id = hypothesis_row(world, "ep_diag", "att_own", cause, event_id="ev_own")
    with world.repository.connection() as connection:
        group_row(connection, "grp_diag", "ep_diag", cause)
        misconception_row(connection, "mc_diag", cause, '["ev_own"]', f"Correct: never {LEGACY_KEY}")
        candidate_row(connection, "mcand_diag", cause, events='["ev_own"]', items='["pi_own"]', count=2)
        gap_row(connection, "gap_diag", source_kind="diagnosis", source_id=diagnosis_id, attempt_id="att_own",
                item_id="pi_own", text=OWN_ANSWER, target_kind="candidate", target_id="mcand_gap_diag",
                action="belief_candidate")
        candidate_row(connection, "mcand_gap_diag", cause)
        connection.commit()
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context = result.structured_content
    assert LEGACY_KEY not in _text(result)
    diag = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_diag")
    assert diag["statement"] is None and diag["correction"] is None and diag["statement_note"] == HELD_BACK
    assert diag["status"] == "active" and diag["evidence_count"] == 1
    candidates = {c["candidate_id"]: c for c in context["misconception_candidates"]}
    assert candidates["mcand_diag"]["statement"] is None and candidates["mcand_diag"]["evidence_count"] == 2
    assert candidates["mcand_gap_diag"]["statement"] is None
    hypothesis = next(h for h in context["open_hypotheses"] if h.get("hypothesis_id") == hypothesis_id)
    assert hypothesis["statement"] is None and hypothesis["statement_note"] == HELD_BACK
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER and own["diagnosis"]["summary"] is None
    assert own["diagnosis"]["hypotheses"] == [] and own["diagnosis"]["hypotheses_note"] == HELD_BACK
    gap = next(g for g in context["open_learner_text_gaps"] if g["gap_id"] == "gap_diag")
    # The gap's words are the pinned answer itself (b); what it was matched to is held back.
    assert gap["learner_text"] == OWN_ANSWER and gap["target"] is None and gap["target_note"] == HELD_BACK
    _no_protected([result])


def test_a_joint_grader_s_cause_is_held_back_with_or_without_its_receipt(world):
    """F4 round 4, F1 (the joint grader) and Q14 (its receipt not written)."""

    legacy_answer(world)
    cause = f"Thinks {LEGACY_KEY} as graded jointly"
    with world.repository.connection() as connection:
        error_event(connection, "ev_joint", "att_own", cause)
        misconception_row(connection, "mc_joint", cause, '["ev_joint"]', None)
        connection.commit()
    hypothesis_id = hypothesis_row(world, "ep_joint", "att_own", cause, event_id="ev_joint")
    for receipt in (False, True):
        if receipt:
            with world.repository.connection() as connection:
                c4_receipt(connection, "att_own", ["att_legacy"])
                connection.commit()
        context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
        assert LEGACY_KEY not in payload_text(context), receipt
        joint = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_joint")
        assert joint["statement"] is None and joint["statement_note"] == HELD_BACK
        hypothesis = next(h for h in context["open_hypotheses"] if h.get("hypothesis_id") == hypothesis_id)
        assert hypothesis["statement"] is None and hypothesis["statement_note"] == HELD_BACK


def test_a_provenance_cycle_releases_nothing(world):
    """F4 round 4, F1 (cycles): two pinned answers' diagnoses were each shown
    the other's hypothesis, one of them also the unpinned answer."""

    legacy_answer(world)
    pinned_answer(world, "att_peer", PEER_ANSWER, "2026-09-21T09:00:00Z")
    own = hypothesis_row(world, "ep_own_cycle", "att_own", f"Applies the column sign rule: {LEGACY_KEY}")
    peer = hypothesis_row(world, "ep_peer_cycle", "att_peer", f"Applies the row sign rule: {LEGACY_KEY}")
    live_diagnosis(world.repository, "att_own", "Seen with the peer's cause.", receipt={"hypothesis_ids": [peer]})
    live_diagnosis(world.repository, "att_peer", f"Seen with an old answer: {LEGACY_KEY}.",
                   receipt={"hypothesis_ids": [own], "failure_attempt_ids": ["att_legacy"]})
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
    assert LEGACY_KEY not in payload_text(context)
    statements = {h["hypothesis_id"]: h for h in context["open_hypotheses"] if h.get("hypothesis_id")}
    for hypothesis_id in (own, peer):
        assert statements[hypothesis_id]["statement"] is None, hypothesis_id
        assert statements[hypothesis_id]["statement_note"] == HELD_BACK, hypothesis_id
    traces = {t["attempt_id"]: t for t in context["recent_answer_traces"]}
    assert traces["att_peer"]["answer"] == PEER_ANSWER and traces["att_own"]["answer"] == OWN_ANSWER


@pytest.mark.parametrize("member", [None, "", False, 0, [], "  "], ids=["null", "empty", "false", "zero", "list",
                                                                     "blank"])
def test_a_provenance_list_with_an_unreadable_member_releases_nothing(world, member):
    """F4 round 4, F3: malformed id lists no longer matter to what shows (the
    statements are held back whatever their lists say); the entries stay."""

    import json as _json

    mixed = _json.dumps(["e1", member])
    with world.repository.connection() as connection:
        misconception_row(connection, "mc_mixed", "Thinks a row swap is a reflection", mixed, None)
        candidate_row(connection, "mcand_mixed_events", "Thinks a row swap is a rotation", events=mixed)
        candidate_row(connection, "mcand_mixed_items", "Thinks a row swap is a projection", events='["e1"]',
                      items=_json.dumps(["pi_own", member]))
        connection.commit()
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
    misconceptions = {m["misconception_id"]: m for m in context["misconceptions"]}
    assert misconceptions["mc_mixed"]["statement"] is None
    assert misconceptions["mc_mixed"]["statement_note"] == HELD_BACK
    candidates = {c["candidate_id"]: c for c in context["misconception_candidates"]}
    for candidate_id in ("mcand_mixed_events", "mcand_mixed_items"):
        assert candidates[candidate_id]["statement"] is None, candidate_id
        assert candidates[candidate_id]["statement_note"] == HELD_BACK, candidate_id
    assert "reflection" not in payload_text(context) and "rotation" not in payload_text(context)


@pytest.mark.parametrize("field", ["failure_attempt_ids", "success_attempt_ids", "hypothesis_ids",
                                   "registry_candidate_ids", "history", "validated_citations"])
@pytest.mark.parametrize("member", [None, "", False], ids=["null", "empty", "false"])
def test_a_diagnosis_receipt_with_an_unreadable_member_releases_nothing(world, field, member):
    """F4 round 4, F3, the diagnosis's context receipt: its contents no longer
    decide anything (a receipt says what was assembled, not everything read)."""

    receipt: dict[str, Any] = {"failure_attempt_ids": ["att_own"]}
    if field == "history":
        receipt["retrieval"] = {"history_attempt_ids": ["att_own", member]}
    elif field == "validated_citations":
        receipt["validated_citations"] = [{"claim_index": 0, "attempt_id": "att_own"},
                                          {"claim_index": 1, "attempt_id": member}]
    else:
        valid = {"hypothesis_ids": world.hypothesis_id, "registry_candidate_ids": "mc_swap"}.get(field, "att_own")
        receipt[field] = [valid, member]
    live_diagnosis(world.repository, "att_own", "The learner expanded along a single row.", receipt=receipt)
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER and own["diagnosis"]["status"] == "done"
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK


def _slug(lo_id: str) -> str:
    return lo_id.split("lo_ltg_", 1)[1].rsplit("_", 1)[0]


def test_a_prerequisite_drafted_from_an_unpinned_answer_shows_neither_its_title_nor_its_id(world):
    """F4 round 4, F2: a drafted prerequisite's title and id are withheld
    wherever the LO appears, its id an opaque alias accepted back, and a topic
    search cannot find it by its words. Since the narrow stage every generated
    name is withheld (the control drafted from the pinned answer too)."""

    los = generated_world(world)
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    text = _text(result)
    assert "8841" not in text and _slug(los["tainted"]) not in text and los["tainted"] not in text
    assert GENERATED_TITLE not in text and "Permutation parity basics" not in text
    context = result.structured_content
    gaps = {gap["gap_id"]: gap for gap in context["open_learner_text_gaps"]}
    alias = gaps["gap_gen"]["learning_object_id"]
    assert alias.startswith("lo_withheld_") and alias in context["scope"]["learning_object_ids"]
    found: dict[str, list[dict]] = {}
    for section in ("misconceptions", "misconception_candidates", "open_hypotheses", "recent_answer_traces",
                    "open_learner_text_gaps", "retention_risks"):
        found[section] = [entry for entry in context[section] if entry.get("learning_object_id") == alias]
    found["recurrence_groups"] = [g for g in context["recurrence_groups"] if alias in g["learning_object_ids"]]
    assert all(found.values()), {section: len(entries) for section, entries in found.items()}
    for section, entries in found.items():
        for entry in entries:
            topics = entry["topics"] if section == "recurrence_groups" else [entry["topic"]]
            assert all(topic.startswith(TOPIC_WITHHELD) for topic in topics), section
    assert any(e["kind"] == "unresolved_cause" for e in found["open_hypotheses"])
    assert gaps["gap_gen"]["learner_text"] is None
    for gap_id in ("gap_gen_safe", "gap_gen_later"):
        assert gaps[gap_id]["learning_object_id"].startswith("lo_withheld_"), gap_id
        assert gaps[gap_id]["target_topic"].startswith(TOPIC_WITHHELD), gap_id
    named, searched, control = _call_all(server, [
        ("learning_context", {"learning_object_ids": [alias]}),
        ("learning_context", {"topic": "8841 negates"}),
        ("learning_context", {"topic": "permutation parity"}),
    ])
    assert named.structured_content["scope"]["learning_object_ids"] == [alias]
    assert any(m["misconception_id"] == "mc_gen" for m in named.structured_content["misconceptions"])
    assert searched.structured_content["scope"]["learning_object_count"] == 0
    assert control.structured_content["scope"]["learning_object_count"] == 0
    for call in (named, searched, control):
        assert _slug(los["tainted"]) not in _text(call) and los["tainted"] not in _text(call)


def test_text_a_model_wrote_on_a_generated_topic_is_held_back(world):
    """F4 round 4, F2 with F1: a grader's cause for a pinned answer on a
    generated topic's item, and a reader's belief from words anchored on that
    topic; the pinned answer's own words still show."""

    los = generated_world(world)
    with world.repository.connection() as connection:
        connection.execute(
            "INSERT INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
            "schema_version, created_at) VALUES ('acv_gen', 'pi_gen', 'h_gen', ?, 1, ?)",
            ('{"prompt": "Swap two rows and compare determinants.", "expected_answer": "they differ in sign"}',
             NOW_ISO))
        connection.execute(
            "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, practice_mode, attempt_type, "
            "learner_answer_md, correctness, hints_used, created_at, session_id, evidence_origin, entry_surface) "
            "VALUES ('att_gen_pinned', 'pi_gen', ?, 'short_answer', 'independent_attempt', 'GEN_PINNED_7710 equal', "
            "0.0, 0, '2026-09-22T09:00:00Z', 'old', 'human', 'desktop_practice')", (los["tainted"],))
        connection.execute(
            "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
            "assessment_contract_version_id) VALUES ('ge_gen', 'att_gen_pinned', 'correct', 0, 1, ?, 'acv_gen')",
            (NOW_ISO,))
        error_event(connection, "ev_gen", "att_gen_pinned", "Thinks a swap leaves the value equal", "mc_graded_gen")
        misconception_row(connection, "mc_graded_gen", "Thinks a swap leaves the value equal", '["ev_gen"]', None)
        gap_row(connection, "gap_on_gen", source_kind="stuck_answer", source_id="att_gen_pinned",
                attempt_id="att_gen_pinned", item_id="pi_gen", text="GEN_PINNED_7710 equal",
                target_kind="candidate", target_id="mcand_read_gen", action="belief_candidate", anchor=los["tainted"])
        candidate_row(connection, "mcand_read_gen", "Thinks swapped rows are interchangeable")
        connection.commit()
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30))
    graded = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_graded_gen")
    assert graded["statement"] is None and graded["statement_note"] == HELD_BACK
    read = next(c for c in context["misconception_candidates"] if c["candidate_id"] == "mcand_read_gen")
    assert read["statement"] is None and read["statement_note"] == HELD_BACK
    trace = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_gen_pinned")
    assert trace["answer"] == "GEN_PINNED_7710 equal" and trace["topic"].startswith(TOPIC_WITHHELD)
    assert trace["stem"] is None and trace["stem_note"] == HELD_BACK
    assert "8841" not in payload_text(context)


@pytest.mark.parametrize("shown", ["failure", "success", "history", "citation", "named", "own"])
def test_a_diagnosis_shown_an_answer_whose_grading_saw_the_unpinned_one_is_held_back(world, shown):
    """F4 round 5, F1: a pinned answer whose joint grader was shown
    ``att_legacy`` (its C4 history), shown to a diagnosis in each list of its
    receipt, named in its text, or the diagnosed answer itself."""

    legacy_answer(world)
    pinned_answer(world, PEER, PEER_ANSWER, "2026-09-21T09:00:00Z")
    with world.repository.connection() as connection:
        c4_receipt(connection, "att_own" if shown == "own" else PEER, ["att_legacy"])
        error_event(connection, "ev_own", "att_own", None)
        connection.commit()
    cause = f"Believes {LEGACY_KEY} for every matrix"
    receipt: dict[str, Any] = {
        "failure": {"failure_attempt_ids": [PEER]},
        "success": {"success_attempt_ids": [PEER]},
        "history": {"retrieval": {"history_attempt_ids": [PEER]}},
        "citation": {"validated_citations": [{"claim_index": 0, "attempt_id": PEER}]},
        "named": {},
        "own": {},
    }[shown]
    live_diagnosis(world.repository, "att_own", f"As in answer {PEER}, the learner wrote {LEGACY_KEY}.",
                   view={"events": {"ev_own": {"misconception_statement": cause, "is_misconception": True}}},
                   receipt=receipt)
    with world.repository.connection() as connection:
        misconception_row(connection, "mc_diag", cause, '["ev_own"]', None)
        connection.commit()
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    context = result.structured_content
    assert LEGACY_KEY not in _text(result)
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["answer"] == OWN_ANSWER
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK
    diag = next(m for m in context["misconceptions"] if m["misconception_id"] == "mc_diag")
    assert diag["statement"] is None and diag["statement_note"] == HELD_BACK
    assert diag["status"] == "active" and diag["evidence_count"] == 1


def test_a_record_naming_what_a_diagnosis_read_releases_it_only_when_every_answer_is_pinned(world):
    """The hook in place of F4 round 5's control: a diagnosis whose write-time
    record names only pinned answers shows its summary; one whose record
    names the unpinned answer (or whose record is incomplete) does not."""

    legacy_answer(world)
    pinned_answer(world, PEER, PEER_ANSWER, "2026-09-21T09:00:00Z")
    peer_diagnosis = live_diagnosis(world.repository, PEER, "Seen with an old answer.",
                                    receipt={"failure_attempt_ids": ["att_legacy"]})
    summary = "The learner flipped the sign once per swap, as in an earlier answer."
    own_diagnosis = live_diagnosis(world.repository, "att_own", summary, receipt={"failure_attempt_ids": [PEER]})
    records = {
        ("diagnosis", own_diagnosis): WriteProvenance(complete=True, answers=("att_own", PEER)),
        ("diagnosis", peer_diagnosis): WriteProvenance(complete=True, answers=(PEER, "att_legacy")),
    }
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30),
                               provenance=lambda _c, kind, record_id: records.get((kind, record_id)))
    traces = {t["attempt_id"]: t for t in context["recent_answer_traces"]}
    assert traces["att_own"]["diagnosis"]["summary"] == summary
    assert traces[PEER]["diagnosis"]["summary"] is None
    assert traces[PEER]["diagnosis"]["summary_note"] == REVISION_UNKNOWN_BEHIND
    records[("diagnosis", own_diagnosis)] = WriteProvenance(complete=False, answers=("att_own", PEER))
    context = learning_context(load_vault(world.root), world.repository, limits=ContextLimits(traces=30),
                               provenance=lambda _c, kind, record_id: records.get((kind, record_id)))
    own = next(t for t in context["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK


@pytest.mark.parametrize("shown", ["registry_misconception", "registry_candidate", "hypothesis", "named", "safe"])
def test_a_diagnosis_shown_a_belief_on_a_generated_topic_is_held_back(world, shown):
    """F4 round 5, F2: a diagnosis shown a belief (with its generated topic's
    id) or naming the id outright; the ``safe`` control is held back too now
    (no write-time record), and no drafted name or id shows."""

    los = generated_world(world)
    with world.repository.connection() as connection:
        misconception_row(connection, "mc_safe", "Thinks parity ignores the swap count", '["e1"]', None,
                          lo=los["safe"])
        connection.commit()
    with world.repository.connection() as connection:
        episode = str(connection.execute("SELECT id FROM causal_hypotheses WHERE episode_key = 'ep_gen'").fetchone()[0])
    topic = los["safe"] if shown == "safe" else los["tainted"]
    receipt: dict[str, Any] = {"retrieval": {"neighborhood_learning_object_ids": ["lo_matrices"]}}
    receipt.update({
        "registry_misconception": {"registry_candidate_ids": ["mc_gen"]},
        "registry_candidate": {"registry_candidate_ids": ["mcand_gen"]},
        "hypothesis": {"hypothesis_ids": [episode]},
        "named": {},
        "safe": {"registry_candidate_ids": ["mc_safe"]},
    }[shown])
    live_diagnosis(world.repository, "att_own", f"The learner's slip matches the belief recorded on {topic}.",
                   receipt=receipt)
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    (result,) = _call_all(server, [("learning_context", {"max_traces": 30})])
    text = _text(result)
    assert "8841" not in text and _slug(los["tainted"]) not in text and los["tainted"] not in text
    assert los["safe"] not in text
    own = next(t for t in result.structured_content["recent_answer_traces"] if t["attempt_id"] == "att_own")
    assert own["diagnosis"]["summary"] is None and own["diagnosis"]["summary_note"] == HELD_BACK
