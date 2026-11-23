"""Builders for the Reader workbench v2 RD0 tests (spec §7.6, §18.1): readings, and synthetic historical
records for every adapter of the two span projections, plus a client that numbers its write batches.

The migration-head fixture has no rows in the projections' source tables, so these seed them by SQL as the
writers would have (the shapes their readers read), one per supported adapter.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as gap_store
from tests.helpers import NOW, NOW_ISO

T0 = "2026-05-19T09:00:00Z"


def seed_reading(repository: Repository, *, source_id: str, revision_id: str, extraction_id: str, spans: list[str],
                 texts: dict[str, str] | None = None, sections: list[tuple[str, list[str]]] | None = None,
                 timed: bool = False) -> None:
    """One completed reading of a source with the given spans in order (one section unless ``sections``).
    ``timed`` stamps each block as a caption cue (``t=<i*10>-<i*10+10>``)."""

    from learnloop.ingest.hashing import extraction_request_hash, extraction_result_hash
    from learnloop.ingest.ir import IR_SCHEMA_VERSION, DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth

    with repository.connection() as connection:
        if connection.execute("SELECT 1 FROM source_artifacts WHERE id = ?", (source_id,)).fetchone() is None:
            connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, updated_at) "
                               "VALUES (?, 'pdf', ?, ?, ?)", (source_id, f"file:///{source_id}.pdf", NOW_ISO, NOW_ISO))
        if connection.execute("SELECT 1 FROM source_revisions WHERE id = ?", (revision_id,)).fetchone() is None:
            connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?, ?, ?, ?)",
                               (revision_id, source_id, f"sha256:{revision_id}", NOW_ISO))
        connection.commit()
    blocks = []
    for ordinal, span in enumerate(spans, start=1):
        block = DocumentBlock.build(span_id=span, block_type="Caption" if timed else "Text", ordinal=ordinal,
                                    section_path=["root"], text=(texts or {}).get(span, f"The passage {span}."))
        if timed:
            block = block.model_copy(update={"extractor_block_id": f"t={(ordinal - 1) * 10:.1f}-{ordinal * 10:.1f}"})
        blocks.append(block)
    units = [DocumentUnit(unit_id=unit, label=f"Section {unit}", ordinal=index, semantic_hash=f"sha256:{unit}",
                          page_start=1, page_end=1, span_ids=unit_spans)
             for index, (unit, unit_spans) in enumerate(sections or [(f"{extraction_id}_u1", spans)])]
    ir = DocumentIR(extractor="text", extractor_version="1", blocks=blocks, assets=[], health=ExtractionHealth(),
                    units=units)
    request_hash = extraction_request_hash(revision_id=revision_id, extractor=f"text-{extraction_id}",
                                           extractor_version=ir.extractor_version, config=None,
                                           ir_schema_version=IR_SCHEMA_VERSION)
    clock = FrozenClock(NOW)
    repository.insert_extraction_run(id=extraction_id, revision_id=revision_id, extractor=f"text-{extraction_id}",
                                     extractor_version=ir.extractor_version, extraction_request_hash=request_hash,
                                     ir_schema_version=IR_SCHEMA_VERSION, config=None, status="running", clock=clock)
    repository.persist_document_ir(extraction_id, ir)
    repository.complete_extraction_run(extraction_id, extraction_result_hash=extraction_result_hash(request_hash, ir),
                                       clock=clock)


def record_alias(repository: Repository, *, from_extraction_id: str, from_span_id: str, to_extraction_id: str,
                 to_span_id: str, match_kind: str = "exact_hash") -> None:
    with repository.connection() as connection:
        connection.execute(
            "INSERT INTO source_span_reanchors (from_extraction_id, from_span_id, to_extraction_id, to_span_id, "
            "match_kind, confidence, created_at) VALUES (?, ?, ?, ?, ?, 1.0, ?)",
            (from_extraction_id, from_span_id, to_extraction_id, to_span_id, match_kind, NOW_ISO))
        connection.commit()


# -- the projections' sources ------------------------------------------------------------------------


def seed_reader_exchange(connection: Any, *, question_event_id: str, extraction_id: str, anchor: str,
                         selection: list[str] = (), citations: list[dict[str, Any]] = (), event_id: str | None = None,
                         answered: bool = True, created_at: str = T0, question_md: str = "Why does this hold?",
                         answer_md: str = "Because the factors are orthogonal. Then the rest follows.") -> None:
    """A Reader Ask as ``reader_dialogue.ask`` records it: the question row keyed by its anchor, and (once
    answered) the ``reader_answer_submitted`` event with its selection and citations."""

    connection.execute(
        "INSERT INTO question_events (id, context, note_id, question_md, answer_md, created_at, answer_status) "
        "VALUES (?, 'reader', ?, ?, ?, ?, ?)",
        (question_event_id, f"span:{extraction_id}/{anchor}", question_md, answer_md if answered else None,
         created_at, "answered" if answered else "failed"))
    if answered:
        payload = {"question_event_id": question_event_id, "extraction_id": extraction_id, "span_id": anchor,
                   "answer_md": answer_md, "citations": list(citations),
                   "manifest": {"selection": {"span_ids": list(selection), "quote_md": "a quote"},
                                "source_spans": [{"span_id": "neighbour_not_a_citation"}]}}
        connection.execute(
            "INSERT INTO interaction_events (id, kind, subject_type, subject_id, payload_json, origin, created_at) "
            "VALUES (?, 'reader_answer_submitted', 'reader_span', ?, ?, 'system', ?)",
            (event_id or f"ie_{question_event_id}", f"span:{extraction_id}/{anchor}", json.dumps(payload), created_at))


def seed_practice_question(connection: Any, *, question_event_id: str, practice_item_id: str,
                           context: str = "practice", created_at: str = T0) -> None:
    connection.execute(
        "INSERT INTO question_events (id, context, practice_item_id, question_md, answer_md, created_at) "
        "VALUES (?, ?, ?, 'What is the first step?', 'Start from the definition.', ?)",
        (question_event_id, context, practice_item_id, created_at))


def seed_gap(connection: Any, *, gap_id: str, source_kind: str, source_id: str, practice_item_id: str | None = None,
             learning_object_id: str | None = None, kind: str = "prerequisite") -> None:
    gap_store.insert_gap(connection, {
        "id": gap_id, "source_kind": source_kind, "source_id": source_id, "practice_item_id": practice_item_id,
        "anchor_learning_object_id": learning_object_id, "learner_text": "I thought it was the inverse.",
        "chooser": "context_model", "context_judge": "gap_reader", "kind": kind, "action": "signal_only",
        "algorithm_version": "test", "pipeline_version": "test", "created_at": T0,
    })


def seed_authored_question(connection: Any, *, question_id: str, extraction_id: str, spans: list[str],
                           anchors: list[str] | None = None) -> None:
    connection.execute(
        "INSERT INTO reader_authored_questions (id, extraction_id, section_id, question_md, expected_answer_md, "
        "span_ids_json, anchor_span_ids_json, prompt_version, created_at, updated_at) "
        "VALUES (?, ?, 'u1', 'What does it factor?', 'A matrix.', ?, ?, 'test', ?, ?)",
        (question_id, extraction_id, json.dumps(spans), json.dumps(anchors) if anchors is not None else None, T0, T0))


def seed_workbench_stuck(connection: Any, *, step_id: str, session_id: str, extraction_id: str,
                         spans: list[str]) -> None:
    connection.execute(
        "INSERT INTO workbench_sessions (id, stem_md, origin, entry, extraction_id, span_ids_json, created_at, "
        "updated_at) VALUES (?, 'Show the factorization exists.', 'reader', 'work_through', ?, ?, ?, ?)",
        (session_id, extraction_id, json.dumps(spans), T0, T0))
    connection.execute(
        "INSERT INTO workbench_steps (id, session_id, ordinal, kind, body_md, client_idempotency_key, created_at) "
        "VALUES (?, ?, 1, 'stuck', 'I do not see why the columns are orthonormal.', ?, ?)",
        (step_id, session_id, f"key_{step_id}", T0))


def seed_note_link(connection: Any, *, note_id: str, note_key: str, extraction_id: str, span_id: str,
                   link_id: str | None = None, status: str = "accepted", created_at: str = T0) -> None:
    if connection.execute("SELECT 1 FROM learner_notes WHERE id = ?", (note_id,)).fetchone() is None:
        connection.execute(
            "INSERT INTO learner_notes (id, note_key, path, line, content_hash, title, origin, text_md, created_at) "
            "VALUES (?, ?, 'notes/a.org', 1, ?, 'A note', 'tend', 'The columns are orthonormal because.', ?)",
            (note_id, note_key, f"sha256:{note_id}", T0))
    connection.execute(
        "INSERT INTO learner_note_links (id, note_id, note_key, target_kind, target_key, extraction_id, span_id, "
        "authorship, status, created_at) VALUES (?, ?, ?, 'passage', ?, ?, ?, 'learner', ?, ?)",
        (link_id or f"lnk_{note_id}_{span_id}_{status}", note_id, note_key, f"{extraction_id}:{span_id}",
         extraction_id, span_id, status, created_at))


@dataclass
class Item:
    """The parts of a practice item the projections read."""

    id: str
    learning_object_id: str
    canonical_exercise: Any = None
    provenance: Any = field(default_factory=lambda: SimpleNamespace(source_refs=[]))


def stub_vault(*items: Item) -> Any:
    """A vault standing in for the recipes: only its practice items are read."""

    return SimpleNamespace(practice_items={item.id: item for item in items})


def item_with_passages(item_id: str, lo_id: str, extraction_id: str, spans: list[str]) -> Item:
    return Item(item_id, lo_id, canonical_exercise=SimpleNamespace(extraction_id=extraction_id, span_ids=spans))


#: The reading every adapter seed names.
BOOK = "ext_book"


def seed_every_adapter(connection: Any) -> dict[str, Any]:
    """One historical record per adapter of both projections (spec §7.6's table), on reading ``BOOK``."""

    seed_reader_exchange(connection, question_event_id="qe_reader", extraction_id=BOOK, anchor="s2", selection=["s3"],
                         citations=[{"span_id": "s4"}, {"locator": f"span:{BOOK}/s5"}])
    seed_reader_exchange(connection, question_event_id="qe_reader_failed", extraction_id=BOOK, anchor="s6",
                         answered=False)
    seed_practice_question(connection, question_event_id="qe_practice_placed", practice_item_id="pi_placed")
    seed_practice_question(connection, question_event_id="qe_feedback_unplaced", practice_item_id="pi_unplaced",
                           context="feedback")
    connection.execute("INSERT INTO question_events (id, context, note_id, question_md, created_at) "
                       "VALUES ('qe_library', 'library', 'note_x', 'What did I write?', ?)", (T0,))
    seed_authored_question(connection, question_id="raq_1", extraction_id=BOOK, spans=["s1", "s2"], anchors=["s2"])
    seed_workbench_stuck(connection, step_id="ws_1", session_id="wbs_1", extraction_id=BOOK, spans=["s3", "s4"])
    seed_note_link(connection, note_id="ln_1", note_key="tend:a", extraction_id=BOOK, span_id="s5")
    seed_gap(connection, gap_id="g_tutor", source_kind="tutor_question", source_id="qe_reader", kind="misconception")
    seed_gap(connection, gap_id="g_formative", source_kind="reader_formative", source_id="raq_1")
    seed_gap(connection, gap_id="g_workbench", source_kind="workbench_text", source_id="ws_1")
    seed_gap(connection, gap_id="g_note", source_kind="learner_note", source_id="ln_1", learning_object_id="lo_note")
    seed_gap(connection, gap_id="g_stuck", source_kind="stuck_answer", source_id="att_1", practice_item_id="pi_placed")
    seed_gap(connection, gap_id="g_diagnosis", source_kind="diagnosis", source_id="dx_1", practice_item_id="pi_unplaced")
    seed_gap(connection, gap_id="g_hint", source_kind="hint_feedback", source_id="ha_1", practice_item_id="pi_unplaced")
    seed_gap(connection, gap_id="g_lesson", source_kind="lesson", source_id="lt_1", learning_object_id="lo_lesson")
    seed_gap(connection, gap_id="g_chat", source_kind="external_chat", source_id="chat_1")
    return {"vault": stub_vault(item_with_passages("pi_placed", "lo_placed", BOOK, ["s7"]),
                                Item("pi_unplaced", "lo_unplaced"))}


class Batches:
    """A client that numbers its batches (one sequence for desk and pad batches, as the protocol has)."""

    def __init__(self, repository: Repository, client_id: str = "client_a") -> None:
        self.repository = repository
        self.client_id = client_id
        self.seq = 0

    def desk(self, *ops: dict[str, Any]) -> dict[str, Any]:
        from pydantic import TypeAdapter

        from learnloop.desks.workspace import DeskOp, apply_desk_ops

        self.seq += 1
        parsed = [TypeAdapter(DeskOp).validate_python(op) for op in ops]
        return apply_desk_ops(self.repository, client_id=self.client_id, seq=self.seq, ops=parsed)

    def pad(self, pad_id: str, *ops: dict[str, Any]) -> dict[str, Any]:
        from pydantic import TypeAdapter

        from learnloop.pads.blocks import PadOp, apply_pad_ops

        self.seq += 1
        parsed = [TypeAdapter(PadOp).validate_python(op) for op in ops]
        return apply_pad_ops(self.repository, client_id=self.client_id, seq=self.seq, pad_id=pad_id, ops=parsed)


def source_ref(extraction_id: str = BOOK, source_id: str = "src_book") -> dict[str, Any]:
    return {"kind": "source", "source_id": source_id, "extraction_id": extraction_id, "view": "render"}


def _ledger(connection: Any, ledger_id: str) -> str:
    connection.execute(
        "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, judge, judge_model, prompt_version, "
        "input_hash, verdict, rationale) VALUES (?, ?, 'test', 'test', 'x', 'llm', 'm', 'p', 'h', 'ok', 'seeded')",
        (ledger_id, T0))
    return ledger_id


def seed_annotation(repository: Repository, *, annotation_id: str, source_id: str, revision_id: str,
                    extraction_id: str, span_id: str, text: str = "kernel = null space") -> None:
    """A highlight with the learner's words, anchored exactly on one passage (its block's current hash)."""

    block_hash = repository.block_content_hashes(extraction_id)[span_id]
    with repository.connection() as connection:
        connection.execute("INSERT INTO source_annotations (id, source_id, created_at) VALUES (?, ?, ?)",
                           (annotation_id, source_id, T0))
        connection.execute(
            "INSERT INTO source_annotation_versions (id, annotation_id, version_ordinal, annotation_type, learner_text, "
            "created_at) VALUES (?, ?, 1, 'highlight', ?, ?)", (f"{annotation_id}_v1", annotation_id, text, T0))
        connection.execute(
            "INSERT INTO source_annotation_anchor_versions (id, annotation_id, version_ordinal, source_id, revision_id, "
            "extraction_id, status, algo_version, created_at) VALUES (?, ?, 1, ?, ?, ?, 'exact', 'anchor-v1', ?)",
            (f"{annotation_id}_a1", annotation_id, source_id, revision_id, extraction_id, T0))
        connection.execute(
            "INSERT INTO source_annotation_anchor_segments (id, anchor_version_id, segment_ordinal, span_id, "
            "block_content_hash, codepoint_start, codepoint_end, exact_quote, selection_text_hash, created_at) "
            "VALUES (?, ?, 0, ?, ?, 0, 4, 'The ', 'h', ?)",
            (f"{annotation_id}_s0", f"{annotation_id}_a1", span_id, block_hash, T0))
        connection.commit()


def seed_union_kinds(connection: Any, *, extraction_id: str, span_id: str, section_id: str,
                     learning_object_id: str) -> None:
    """Everything else the union read gathers, on one passage: a passage link, a figure, an authored question,
    the passage seen and shown, and its section's coverage."""

    connection.execute(
        "INSERT INTO passage_links (id, extraction_id, span_id, target_kind, target_id, relation, quote, pick_rank, "
        "ledger_id, state_key, model, prompt_version, created_at) VALUES ('pl_1', ?, ?, 'misconception', 'm_1', "
        "'clarifies_distinction', 'The passage.', 1, ?, 'k', 'm', 'p', ?)",
        (extraction_id, span_id, _ledger(connection, "jl_link"), T0))
    connection.execute(
        "INSERT INTO interactive_figures (id, extraction_id, span_ids_json, origin, spec_version, verification, "
        "prompt_version, input_hash, created_at) VALUES ('fig_1', ?, ?, 'show_me', 'v1', 'failed', 'p', 'h', ?)",
        (extraction_id, json.dumps([span_id]), T0))
    seed_authored_question(connection, question_id="raq_union", extraction_id=extraction_id, spans=[span_id])
    connection.execute("INSERT INTO reader_seen_spans (extraction_id, span_id, section_id, first_seen_at, origin) "
                       "VALUES (?, ?, ?, ?, 'desktop')", (extraction_id, span_id, section_id, T0))
    for n in (1, 2):
        connection.execute("INSERT INTO source_exposure_events (id, context, extraction_id, span_id, created_at) "
                           "VALUES (?, 'reader', ?, ?, ?)", (f"see_{n}", extraction_id, span_id, f"2026-05-19T0{n}:00:00Z"))
    connection.execute(
        "INSERT INTO section_coverage (id, extraction_id, section_id, learning_object_id, treatment, origin, "
        "section_hash, lo_hash, state_key, ledger_id, model, prompt_version, created_at) "
        "VALUES ('cov_1', ?, ?, ?, 'introduces', 'provenance', 'h', 'h', 'k', ?, 'm', 'p', ?)",
        (extraction_id, section_id, learning_object_id, _ledger(connection, "jl_cov"), T0))
