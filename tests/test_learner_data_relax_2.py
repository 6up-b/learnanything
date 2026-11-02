"""Learner data-relax 2 (owner principle 2026-11-01: the learner's questions,
answers and history are not private; include them where they help).

* **The figure author gets the learner's state** on the passage's topics
  (``figures.learner_state``): status in words, the open misconception and
  gap statements, at most two recent answers of the learner's own, read
  through ``learner_protection`` so exam, held-out, reserved and
  cold-in-flight work (and anything written from it) never shows. The prompt
  version gains ``+learner-v1`` and the reuse key the state's hash, only when
  the state is non-empty.
* **Switched off** (``figures.author_learner_state``), the payload, the
  prompt and the reuse key are the predecessor's byte for byte; **with no
  state** they are too, so a learner with nothing to say keeps today's keys
  and reuses today's figures.
* **The MCP ledger** keeps each tool call's arguments (bounded) beside their hash.
* **The blind grader's inputs are unchanged.**

Fakes only: the author is injected; no model is reached.
"""

from __future__ import annotations

import dataclasses
import json

import anyio
import pytest
from mcp import Client

from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.figures.learner_state import RECENT_ANSWERS, learner_state, read_learner_state, state_hash
from learnloop.vault.loader import load_vault
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, build_figure_vault, context, flagship, rows, \
    seed_probability_book, set_config, upsert_source_set
from tests.mcp_world import (
    COLD_ANSWER,
    COLD_STEM,
    CONTRACT_KEY,
    EXAM_ANSWER,
    EXAM_CANON_ANSWER,
    EXAM_LOCATOR_ANSWER,
    EXAM_NAMESPACED_ANSWER,
    EXAM_STEM,
    GAP_TEXT,
    LO,
    MISCONCEPTION,
    PROBE_ANSWER,
    PROBE_STEM,
    RESERVED_ANSWER,
    RESERVED_STEM,
    REVERSED_GAP_TEXT,
    UNPINNED_ANSWER,
    _attempt,
    build_world,
    no_model_calls,
)

#: Newer than every ordinary answer, each on protected work: they must be
#: skipped (the two shown answers are older, unprotected ones).
NEWER_EXAM = "NEWER_EXAM_WORK_8812 eigenvalues five and two"
NEWER_COLD = "NEWER_COLD_ANSWER_4471 any row works"
NEWER_RESERVED = "NEWER_RESERVED_ANSWER_3302"
EXAM_DERIVED = "EXAM_DERIVED_MISCONCEPTION_7710 thinks eigenvalues add"
PROTECTED_TEXT = (EXAM_ANSWER, COLD_ANSWER, RESERVED_ANSWER, PROBE_ANSWER, EXAM_CANON_ANSWER, EXAM_LOCATOR_ANSWER,
                  EXAM_NAMESPACED_ANSWER, EXAM_STEM, COLD_STEM, RESERVED_STEM, PROBE_STEM, CONTRACT_KEY,
                  REVERSED_GAP_TEXT, NEWER_EXAM, NEWER_COLD, NEWER_RESERVED, EXAM_DERIVED)
SOURCE_SET = {
    "id": "sset_la", "subject_id": "linear-algebra", "title": "Linear algebra sources",
    "members": [
        {"source_id": "src_book", "revision_id": "rev_book", "default_role": "primary_textbook"},
        {"source_id": "src_exam", "revision_id": "rev_exam", "default_role": "exam"},
        {"source_id": "src_text", "revision_id": "rev_text", "default_role": "primary_textbook"},
        {"source_id": "src_prob", "revision_id": "rev_prob", "default_role": "primary_textbook"},
    ],
}


def _link(repository, lo_id: str = LO, span_id: str = "p3") -> None:
    """The passage teaches ``lo_id`` (a current primary source link)."""

    from learnloop.ingest.locators import format_block_span

    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO entity_source_links (id, entity_type, entity_id, source_id, revision_id, locator, relation, "
            "extraction_id, status, created_at) VALUES (?, 'learning_object', ?, 'src_prob', 'rev_prob', ?, "
            "'primary', ?, 'current', '2026-09-01T00:00:00Z')",
            (f"esl_{lo_id}_{span_id}", lo_id, format_block_span(EXTRACTION, span_id), EXTRACTION))
        connection.commit()


def _history_world(tmp_path, *, switch: bool | None = None, rich: bool = False):
    """The chat frontend's seeded world (protected work planted with
    distinctive strings) plus the probability book, whose §5.4 equation
    block teaches its LO; newer protected answers and an exam-derived
    misconception on top."""

    world = build_world(tmp_path / "w")
    paths, repository = world.paths, world.repository
    values = {"sketch_enabled": False, "rich_tiers_enabled": rich}
    if rich:
        values["manim_opt_in"] = "standing"
    if switch is not None:
        values["author_learner_state"] = switch
    set_config(paths, "figures", **values)
    seed_probability_book(repository)
    upsert_source_set(paths.root, SOURCE_SET)
    _link(repository)
    with repository.connection() as connection:
        _attempt(connection, "att_new_exam", "pi_own", "2026-09-20T09:00:00Z", answer=NEWER_EXAM, correctness=1.0,
                 attempt_type="exam_attempt")
        _attempt(connection, "att_new_cold", "pi_cold", "2026-09-21T09:00:00Z", answer=NEWER_COLD, correctness=1.0)
        _attempt(connection, "att_new_reserved", "pi_reserved", "2026-09-22T09:00:00Z", answer=NEWER_RESERVED,
                 correctness=1.0)
        connection.execute(
            "INSERT INTO error_events(id, attempt_id, learning_object_id, error_type, severity, is_misconception, "
            "status, created_at, misconception_id, misconception_statement) VALUES ('e_exam', 'att_exam', ?, "
            "'misconception', 0.7, 1, 'active', '2026-09-23T00:00:00Z', 'mc_exam', ?)", (LO, EXAM_DERIVED))
        connection.execute(
            "INSERT INTO misconceptions(id, learning_object_id, statement, severity, status, "
            "source_error_event_ids_json, created_at, updated_at) VALUES ('mc_exam', ?, ?, 0.7, 'active', "
            "'[\"e_exam\"]', '2026-09-23T00:00:00Z', '2026-09-23T00:00:00Z')", (LO, EXAM_DERIVED))
        connection.commit()
    return world


def _plain_vault(tmp_path, *, switch: bool | None = None):
    """The figure tests' vault (no answers, no statements) with the same link."""

    paths, repository = build_figure_vault(tmp_path / "plain")
    if switch is not None:
        set_config(paths, "figures", author_learner_state=switch)
    _link(repository)
    return paths, repository


# ---------------------------------------------------------------------------
# The state, read through the protection
# ---------------------------------------------------------------------------

def test_the_learner_state_reaches_the_author_and_protected_work_never_does(tmp_path, monkeypatch):
    no_model_calls(monkeypatch)
    world = _history_world(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    ctx = context(world.root, author=author)
    build(ctx)
    sent = author.contexts[0]
    state = sent["learner_state"]
    prompt = author.prompts[0]
    # The topic and its status in words.
    assert [entry["topic"] for entry in state["topics"]] == [load_vault(world.root).learning_objects[LO].title]
    assert state["topics"][0]["status"]
    # The open statements: the diagnosed misconception and the learner's own
    # words of an open gap, each labelled; the undone gap and a misconception
    # diagnosed from exam work are absent.
    statements = {entry["statement"]: entry for entry in state["open_questions"]}
    assert MISCONCEPTION in statements and statements[MISCONCEPTION]["written_by"].startswith("LearnLoop")
    assert GAP_TEXT in statements and statements[GAP_TEXT]["written_by"] == "the learner"
    # At most two recent answers, the learner's own, newest unprotected first:
    # the three newer protected answers are skipped.
    answers = state["recent_answers"]
    assert len(answers) == RECENT_ANSWERS == 2
    assert answers[0]["answer"] == UNPINNED_ANSWER and "question" not in answers[0]  # no pinned revision
    assert answers[1]["question"].startswith("EDITED_OLD_PROMPT_8810") and answers[1]["result"] == "correct"
    for text in PROTECTED_TEXT:
        assert text not in prompt, text
    # Its own prompt version and instructions, and a reuse key naming the state.
    assert R.LEARNER_STATE_TEXT in prompt and R.LEARNER_SUFFIX in prompt
    (row,) = rows(world.repository, "interactive_figures")
    assert row["prompt_version"] == R.author_prompt_version(advanced=True, learner=True)
    assert row["prompt_version"].endswith("+learner-v1")
    vault = load_vault(world.root)
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    context_ = FS.source_context(vault, world.repository, request)
    assert row["input_hash"] == FS.request_hash(request, context_, None, advanced=True, learner_state=state)
    assert row["input_hash"] != FS.request_hash(request, context_, None, advanced=True)
    # Figures stay help: no learner-state table gained a row.
    assert learner_state(vault, world.repository, [LO]) == state


def test_protection_unreadable_sends_no_answer_and_no_statement(tmp_path, monkeypatch):
    from learnloop import learner_protection

    no_model_calls(monkeypatch)
    world = _history_world(tmp_path)
    monkeypatch.setattr(learner_protection, "withheld_items",
                        lambda vault, repository: learner_protection.Withheld(available=False))
    state = learner_state(load_vault(world.root), world.repository, [LO])
    # Fail closed: only the topic's status is left (or nothing at all).
    assert state is None or set(state) == {"topics"}


# ---------------------------------------------------------------------------
# Codex review F1: gaps with no answer and no item (reading-derived) are
# checked against what their write-time record says they were written beside
# ---------------------------------------------------------------------------

READ_EXAM_GAP = "READ_EXAM_GAP_6120 thinks the exam passage says rows commute"
READ_TEXT_GAP = "READ_TEXT_GAP_6121 thinks swapping rows keeps the determinant"
UNRECORDED_GAP = "UNRECORDED_GAP_6122 no record of where it was written"


def _source(source_id: str, extraction_id: str, span: str) -> dict:
    return {"ref_type": "canonical_source", "ref_id": source_id, "source_id": source_id,
            "extraction_id": extraction_id, "span_ids": [span]}


def _reading_gaps(world) -> None:
    """Three active-reading (``reader_formative``) gaps on the LO, none with an
    answer or an item: one written beside the exam source's passage, one
    beside an ordinary textbook passage (``src_text``), one with no record."""

    from learnloop.db.stores.write_provenance import Inputs, WriteRecord, record_text_write
    from tests.mcp_world import gap_row

    with world.repository.connection() as connection:
        for gap_id, text, source in (("gap_read_exam", READ_EXAM_GAP, _source("src_exam", "ext_exam", "s2")),
                                     ("gap_read_text", READ_TEXT_GAP, _source("src_text", "ext_text", "t1")),
                                     ("gap_unrecorded", UNRECORDED_GAP, None)):
            gap_row(connection, gap_id, source_kind="reader_formative", source_id=f"raq_{gap_id}", attempt_id=None,
                    item_id=None, text=text, target_kind="learning_object", target_id=LO)
            if source is not None:
                record_text_write(connection, kind="learner_text_gap", record_id=gap_id, text=text,
                                  writer="gap_reader", record=WriteRecord(Inputs.of(topics=[LO], sources=[source])))
        connection.commit()


def _statements(state) -> set[str]:
    return {entry["statement"] for entry in (state or {}).get("open_questions") or ()}


def test_a_reading_derived_gap_is_checked_against_the_passage_it_was_written_beside(tmp_path, monkeypatch):
    """F1: before the fix a gap with no answer and no item was sent whatever
    its passage was: the exam passage's gap and the unrecorded one too."""

    no_model_calls(monkeypatch)
    world = _history_world(tmp_path)
    _reading_gaps(world)
    read = read_learner_state(load_vault(world.root), world.repository, [LO])
    shown = _statements(read.state)
    assert READ_TEXT_GAP in shown
    assert READ_EXAM_GAP not in shown and UNRECORDED_GAP not in shown
    # What it was read from goes with it (the ordinary passage among them).
    assert _source("src_text", "ext_text", "t1")["source_id"] in {
        ref.get("source_id") for ref in read.inputs["sources"]}
    # The ordinary passage's source is reclassified as exam material: its gap is withheld now.
    reclassified = json.loads(json.dumps(SOURCE_SET))
    for member in reclassified["members"]:
        if member["source_id"] == "src_text":
            member["default_role"] = "exam"
    upsert_source_set(world.root, reclassified)
    assert READ_TEXT_GAP not in _statements(learner_state(load_vault(world.root), world.repository, [LO]))


def test_protection_unreadable_withholds_reading_derived_gaps_too(tmp_path, monkeypatch):
    """F1: with ``Withheld(available=False)`` an itemless gap's words used to be sent."""

    from learnloop import learner_protection

    no_model_calls(monkeypatch)
    world = _history_world(tmp_path)
    _reading_gaps(world)
    monkeypatch.setattr(learner_protection, "withheld_items",
                        lambda vault, repository: learner_protection.Withheld(available=False))
    state = learner_state(load_vault(world.root), world.repository, [LO])
    assert state is None or set(state) == {"topics"}
    assert READ_TEXT_GAP not in json.dumps(state)


def test_switched_off_the_payload_prompt_and_key_are_the_predecessors_byte_for_byte(tmp_path, monkeypatch):
    """Off on a learner with history, and on with no state at all, the author
    is sent exactly the same bytes, under the same prompt version and key: the
    predecessor's (``request_hash`` with no learner state)."""

    no_model_calls(monkeypatch)
    world = _history_world(tmp_path, switch=False)
    off_author = AuthorFake([flagship(kind="illustrative")])
    build(context(world.root, author=off_author))
    paths, repository = _plain_vault(tmp_path, switch=True)
    empty_author = AuthorFake([flagship(kind="illustrative")])
    build(context(paths.root, author=empty_author))
    assert "learner_state" not in off_author.contexts[0] and "learner_state" not in empty_author.contexts[0]
    assert R.LEARNER_SUFFIX not in off_author.prompts[0] and R.LEARNER_STATE_TEXT not in off_author.prompts[0]
    assert off_author.prompts[0] == empty_author.prompts[0]
    assert off_author.prompts[0] == R.author_prompt(off_author.contexts[0], advanced=True)
    (off_row,) = rows(world.repository, "interactive_figures")
    (empty_row,) = rows(repository, "interactive_figures")
    assert off_row["prompt_version"] == empty_row["prompt_version"] == R.ADVANCED_PROMPT_VERSION
    vault = load_vault(paths.root)
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    predecessor = FS.request_hash(request, FS.source_context(vault, repository, request), None, advanced=True)
    assert off_row["input_hash"] == empty_row["input_hash"] == predecessor


def test_no_state_keeps_todays_key_so_the_switch_reuses_todays_figure(tmp_path, monkeypatch):
    no_model_calls(monkeypatch)
    paths, repository = _plain_vault(tmp_path, switch=False)
    author = AuthorFake([flagship(kind="illustrative")])
    build(context(paths.root, author=author))
    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    assert "author_learner_state = false" in text
    config.write_text(text.replace("author_learner_state = false", "author_learner_state = true"), encoding="utf-8")
    again = AuthorFake([flagship(kind="illustrative")])
    result = build(context(paths.root, author=again))
    assert again.calls == 0 and result["reused"] is True
    assert len(rows(repository, "interactive_figures")) == 1
    assert learner_state(load_vault(paths.root), repository, [LO]) is None


def test_the_reuse_key_and_prompt_version_name_the_state_only_when_non_empty():
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    context_ = FS.SourceContext()
    base = FS.request_hash(request, context_, None)
    assert FS.request_hash(request, context_, None, learner_state=None) == base
    assert FS.request_hash(request, context_, None, learner_state={}) == base
    one = FS.request_hash(request, context_, None, learner_state={"topics": [{"topic": "t", "status": "learning"}]})
    two = FS.request_hash(request, context_, None, learner_state={"topics": [{"topic": "t", "status": "shown"}]})
    assert len({base, one, two}) == 3
    assert state_hash(None) is None and state_hash({}) is None
    assert R.author_prompt_version() == R.AUTHOR_PROMPT_VERSION
    assert R.author_instructions() == R.AUTHOR_INSTRUCTIONS
    assert R.author_prompt({"x": 1}) == R.author_prompt({"x": 1}, learner=False)
    menu = ("grammar", "sketch", "manim")
    assert R.author_prompt_version(sketch=True, tiers=menu, learner=True) == \
        R.author_prompt_version(sketch=True, tiers=menu) + "+learner-v1"
    assert R.author_instructions(show_me=True, learner=True) == R.author_instructions(show_me=True) + \
        R.LEARNER_STATE_TEXT


def test_the_rich_author_receives_what_the_figure_author_received():
    """The rich job's author context is the figure author's (``_author_context``):
    with state, its learner_state goes with it; without, nothing is added."""

    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=["p3"])
    plain = FS._author_context(request, FS.SourceContext(), None, None, (), request_id="r")
    assert "learner_state" not in plain
    request.learner_state = {"topics": [{"topic": "t", "status": "learning"}]}
    with_state = FS._author_context(request, FS.SourceContext(), None, None, (), request_id="r")
    assert with_state == {**plain, "learner_state": request.learner_state}


def test_the_disclosures_name_the_learner_state():
    from learnloop.ai.disclosures import _WHEN

    for consumer in ("figures", "figures_rich"):
        assert "figures.author_learner_state" in _WHEN[consumer], consumer
        assert "never material held out for an exam" in _WHEN[consumer], consumer
        assert "never evidence" in _WHEN[consumer], consumer


def test_the_blind_grader_inputs_are_unchanged():
    """No field of the blind grader's context could carry a figure, a hint
    draft or the learner's state: its fields are pinned (this stage changes
    no grader input)."""

    from learnloop.attempts.blind_grading import BlindGradingContext

    assert tuple(field.name for field in dataclasses.fields(BlindGradingContext)) == (
        "attempt_id", "practice_item_id", "prompt", "expected_answer", "learner_answer_md", "rubric",
        "evidence_facets", "evidence_weights", "criterion_facet_weights", "trace_contract", "error_taxonomy",
        "facet_registry", "discrimination_profiles", "clarification_exchange", "error_hunt_solution",
        "verifier_observations", "reference_policy", "answer_prompt")


# ---------------------------------------------------------------------------
# The MCP tool-call ledger keeps the arguments
# ---------------------------------------------------------------------------

def _called(kept: dict) -> dict:
    """The arguments as called, from a short call's kept copy (nothing was cut)."""

    return dict(kept)

def test_the_mcp_ledger_row_carries_its_arguments(tmp_path, monkeypatch):
    from learnloop.remote.runtime import RemoteRuntime
    from learnloop.remote.telemetry import ARGUMENT_CHARS, ARGUMENT_ITEMS, bounded_arguments, canonical_hash
    from learnloop_mcp.server import build_server

    no_model_calls(monkeypatch)
    world = build_world(tmp_path / "w")
    server = build_server(RemoteRuntime.attach(world.root, load_environment=False))
    calls = [("learning_context", {"topic": "row swaps and the determinant", "learning_object_ids": [LO],
                                   "max_traces": 3}),
             ("find_sources", {"query": "determinant row swap"}),
             ("status", {})]

    async def main():
        async with Client(server) as client:
            return [await client.call_tool(name, arguments) for name, arguments in calls]

    results = anyio.run(main)
    assert all(not result.is_error for result in results)
    events = world.repository.reader_interaction_events(kind="chat_tool_call")
    assert [event["subject_id"] for event in events] == [name for name, _ in calls]
    context_args = events[0]["payload"]["arguments"]
    assert context_args["topic"] == "row swaps and the determinant"
    assert context_args["learning_object_ids"] == [LO] and context_args["max_traces"] == 3
    assert events[1]["payload"]["arguments"]["query"] == "determinant row swap"
    for event in events:
        payload = event["payload"]
        assert payload["arguments_hash"].startswith("sha256:")
        assert payload["authority_class"] == "salience_only"
        assert event["payload_schema_version"] == "chat-tool-call-v2"
    # The hash is still of the arguments as called (the bound changes only the kept copy).
    assert events[1]["payload"]["arguments_hash"] == canonical_hash(_called(events[1]["payload"]["arguments"]))
    # Bounded: long strings, long lists, nesting and non-object arguments.
    bounded = bounded_arguments({"query": "q" * (ARGUMENT_CHARS + 10), "ids": list(range(ARGUMENT_ITEMS + 5)),
                                 "nested": {"deep": {"deeper": "x"}}})
    assert len(bounded["query"]) == ARGUMENT_CHARS and len(bounded["ids"]) == ARGUMENT_ITEMS
    assert isinstance(bounded["nested"]["deep"], str)
    assert bounded_arguments("not an object") == {"value": "not an object"} and bounded_arguments(None) == {}
    json.dumps(bounded)


# ---------------------------------------------------------------------------
# Codex review F2: a queued rich job checks the saved learner state again
# ---------------------------------------------------------------------------

def _rich_history_rig(tmp_path, monkeypatch):
    """The history world with Manim figures on (the rich job rig's runner and fakes)."""

    from learnloop.content.pipeline.runner import IngestRunner, RunnerServices
    from tests import rich_fixtures as RF
    from tests.test_figure_rich_job import WHY, _Rig

    world = _history_world(tmp_path, rich=True)
    RF.ready_manim(monkeypatch)
    rig = _Rig.__new__(_Rig)
    rig.paths, rig.repository = world.paths, world.repository
    rig.author = AuthorFake([("rich", "manim", RF.brief(), WHY, flagship(kind="illustrative"))])
    rig.rich_author = RF.RichAuthorFake()
    rig.renders = RF.Renders()
    rig.functions = RF.InProcessRunner()
    rig.ingest = IngestRunner(rig.repository, vault_root=rig.paths.root, worker_id="w1", services=RunnerServices(
        figure_rich_client_factory=lambda ctx: rig.rich_author, figure_rich_renderer=rig.renders,
        figure_function_runner=rig.functions))
    rig.batches = []
    return rig


def _switch_off(paths) -> None:
    """``figures.author_learner_state = false`` in place (the section exists)."""

    config = paths.root / "learnloop.toml"
    text = config.read_text(encoding="utf-8")
    if "author_learner_state = true" in text:
        text = text.replace("author_learner_state = true", "author_learner_state = false")
    else:
        text = text.replace("\n[figures]\n", "\n[figures]\nauthor_learner_state = false\n", 1)
    config.write_text(text, encoding="utf-8")
    assert "author_learner_state = false" in text


def _make_exam_material(rig, item_id: str = "pi_edited") -> None:
    """The item the shown answers were on now comes from the exam source."""

    from learnloop.vault.yaml_io import read_yaml, write_yaml

    path = rig.paths.practice_item_path("linear-algebra", item_id)
    item = read_yaml(path)
    item["provenance"] = {"origin": "human", "source_refs": [
        {"ref_type": "canonical_source", "ref_id": "src_exam", "extraction_id": "ext_exam", "span_ids": ["s2"]}]}
    write_yaml(path, item)


def test_a_queued_rich_job_never_sends_an_answer_whose_item_became_exam_material(tmp_path, monkeypatch):
    """F2: before the fix the rich author still received the saved answers and question."""

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    payload = rig.job()["payload"]
    state = payload["author_context"]["learner_state"]
    assert state["recent_answers"] and payload["learner_state_inputs"]["answers"]
    assert "att_unpinned" in payload["learner_state_inputs"]["answers"]
    _make_exam_material(rig)
    rig.ingest.drain()
    job = rig.job()
    assert rig.rich_author.calls == 0
    assert job["status"] == "failed" and job["error"]["code"] == "exam_material", job
    assert len(rows(rig.repository, "interactive_figures")) == 1  # only the quick figure


def test_a_rich_job_stops_when_an_input_becomes_protected_while_it_runs(tmp_path, monkeypatch):
    """F2: protection is checked again before every rich request and before the store (the gate's hold)."""

    from tests import rich_fixtures as RF

    class ProtectingRenders(RF.Renders):
        def __call__(self, scene_code, scene_class, **kwargs):
            _make_exam_material(rig)  # the answer's item becomes exam material while the video renders
            return super().__call__(scene_code, scene_class, **kwargs)

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.renders = ProtectingRenders()
    rig.ingest.services.figure_rich_renderer = rig.renders
    rig.build()
    rig.ingest.drain()
    assert rig.rich_author.calls == 1 and len(rig.renders.calls) == 1
    job = rig.job()
    assert job["status"] == "failed" and job["error"]["code"] == "exam_material", job
    assert len(rows(rig.repository, "interactive_figures")) == 1


def test_a_queued_rich_job_with_learner_state_stops_when_the_switch_goes_off(tmp_path, monkeypatch):
    """F2: the saved state survived ``figures.author_learner_state = false`` and was sent."""

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    assert rig.job()["payload"]["author_context"]["learner_state"]
    _switch_off(rig.paths)
    rig.ingest.drain()
    job = rig.job()
    assert rig.rich_author.calls == 0
    assert job["status"] == "failed" and job["error"]["code"] == "figures_changed", job


def test_a_saved_learner_state_with_no_record_of_its_inputs_is_never_sent(tmp_path, monkeypatch):
    from learnloop.figures import rich as RICH

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    payload = dict(rig.job()["payload"])
    payload.pop("learner_state_inputs")
    with pytest.raises(RICH.RichJobStopped) as stopped:
        RICH.run_rich_job(rig.vault, rig.repository, payload, client=rig.rich_author, renderer=rig.renders,
                          function_runner=rig.functions)
    assert stopped.value.code == "exam_material" and rig.rich_author.calls == 0


def test_the_switch_is_in_the_build_and_rich_keys(tmp_path):
    paths, _repository = _plain_vault(tmp_path, switch=True)
    on = FS.build_key(load_vault(paths.root))
    _switch_off(paths)
    assert FS.build_key(load_vault(paths.root)) != on


# ---------------------------------------------------------------------------
# Codex re-review F2: the stored rich figure keeps what its learner state was
# read from; recovery, delivery and reuse check it again
# ---------------------------------------------------------------------------

def _rich_row(repository) -> dict:
    from learnloop.db.stores import figures as store

    (row,) = [found for found in rows(repository, "interactive_figures") if found["tier"] == "manim"]
    with repository.connection() as connection:
        return store.figure(connection, row["id"])


def test_a_rich_figure_keeps_the_inputs_of_the_learner_state_it_was_written_from(tmp_path, monkeypatch):
    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    inputs = rig.job()["payload"]["learner_state_inputs"]
    rig.ingest.drain()
    assert rig.job()["status"] == "completed", rig.job()
    assert _rich_row(rig.repository)["verification_report"]["learner_state_inputs"] == inputs


def test_a_recovered_rich_job_rechecks_its_stored_figures_learner_state(tmp_path, monkeypatch):
    """Re-review F2: the figure committed, the job was not acknowledged, an
    answer's item became exam material, the job resumed: before the fix the
    stored figure was returned with no protection check."""

    from learnloop.figures import rich as RICH

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    payload = dict(rig.job()["payload"])
    rig.ingest.drain()
    assert rig.rich_author.calls == 1
    # Resumed with the protection unchanged: the stored figure is recovered.
    recovered = RICH.run_rich_job(rig.vault, rig.repository, payload, client=rig.rich_author,
                                  renderer=rig.renders, function_runner=rig.functions)
    assert recovered["reused"] and recovered["figure_id"] == _rich_row(rig.repository)["id"]
    _make_exam_material(rig)
    with pytest.raises(RICH.RichJobStopped) as stopped:
        RICH.run_rich_job(rig.vault, rig.repository, payload, client=rig.rich_author, renderer=rig.renders,
                          function_runner=rig.functions)
    assert stopped.value.code == "exam_material" and rig.rich_author.calls == 1


def test_a_rich_figure_whose_learner_inputs_became_protected_is_not_delivered(tmp_path, monkeypatch):
    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.build()
    rig.ingest.drain()
    rich = _rich_row(rig.repository)
    (line,) = rig.listed()
    assert line["fuller"]["state"] == "ready" and line["fuller"]["figure"]["figure_id"] == rich["id"]
    assert not FS.figure_withheld(rig.vault, rig.repository, rich["id"])
    _make_exam_material(rig)
    assert FS.figure_withheld(rig.vault, rig.repository, rich["id"])
    assert FS.row_withheld(rig.vault, rig.repository, rich) is not None
    (line,) = rig.listed()  # the quick figure stays; its fuller version is not delivered
    assert not (line["fuller"] or {}).get("figure")


def test_a_rich_only_figure_whose_learner_inputs_became_protected_is_never_reused(tmp_path, monkeypatch):
    from learnloop.figures import rich as RICH
    from tests import rich_fixtures as RF
    from tests.test_figure_rich_job import WHY

    rig = _rich_history_rig(tmp_path, monkeypatch)
    rig.author = AuthorFake([("rich", "manim", RF.brief(), WHY)])
    outcome = rig.build()
    assert outcome.view is None and outcome.rich["state"] == "pending"
    rig.ingest.drain()
    rich = _rich_row(rig.repository)
    assert not rich["fuller_of_id"] and rich["verification_report"]["learner_state_inputs"]["answers"]
    with rig.repository.connection() as connection:
        assert FS._reusable(rig.vault, rig.repository, connection, rich["input_hash"], [])["id"] == rich["id"]
    assert [view["figure_id"] for view in rig.listed()] == [rich["id"]]
    _make_exam_material(rig)
    with rig.repository.connection() as connection:
        assert FS._reusable(rig.vault, rig.repository, connection, rich["input_hash"], []) is None
    assert rig.listed() == []
    assert RICH.stored_learner_state_withheld(rig.vault, rig.repository, rich) is not None


def test_a_stored_rich_figure_without_learner_state_is_checked_as_before(tmp_path, monkeypatch):
    from learnloop.figures import rich as RICH

    row = {"verification_report": {"outcome": "illustrative"}}
    assert RICH.stored_learner_state_withheld(None, None, row) is None
    # A recorded learner state whose inputs record is missing fails closed.
    paths, repository = _plain_vault(tmp_path)
    vault = load_vault(paths.root)
    assert RICH.stored_learner_state_withheld(vault, repository, {"verification_report": {
        "learner_state_inputs": None}}) is not None
