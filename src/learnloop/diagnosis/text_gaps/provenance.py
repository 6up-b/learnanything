"""What the learner-text pipeline's writers read (spec_mcp_frontend_c1 §4.8).

Diagnosis input provenance for the gap reader, the belief writer and the
prerequisite drafter: each records, with what it writes, exactly what it was
written from, so the chat frontend can release it once every input is safe.

* **A gap's words** (a question the learner asked; a diagnosis's or a stuck
  answer's gap shows the answer itself, rule (b)): the question, with the
  item contract it was asked about (Q10), its item, the attempt it was asked
  during, the passage a Reader question was asked on, and, when the learner
  could have seen the item's solution before asking (a feedback question, or
  a reveal of the item before it), the item's solution and the grading the
  feedback showed (:func:`question_record`).
* **What a reading named** (a belief statement, a prerequisite's name):
  everything its reader read. A stuck answer's reader read the answer, its
  item's question and its topic; a diagnosis's reading is the diagnosis's
  (its record); a tutor question's reading was written by the tutor, whose
  inputs are not recorded yet, so it is incomplete (:func:`reading_record`).
* **A drafted prerequisite** (a generated topic's title): the reading, the
  learner text and its context, the asking topic and the concept titles of
  its subject the drafter was shown (:func:`drafter_record`).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from types import SimpleNamespace
from typing import Any

from learnloop.content.sources.exam_material import source_ref_keys
from learnloop.db.stores.write_provenance import (
    GRADING,
    Inputs,
    WriteRecord,
    answer_inputs,
    closure,
    fold_topic_records,
    source_ref,
)
from learnloop.ingest.locators import parse_block_span

#: Why what a tutor question's reading named is held back.
TUTOR_UNRECORDED = "the tutor's reading of a question does not record what the tutor read"


def _question_row(connection: Any, event_id: str) -> dict[str, Any] | None:
    columns = {column[1] for column in connection.execute("PRAGMA table_info(question_events)")}
    if not columns:
        return None
    contract = "assessment_contract_version_id" if "assessment_contract_version_id" in columns else "NULL"
    source = "source_context_json" if "source_context_json" in columns else "NULL"
    note = "note_id" if "note_id" in columns else "NULL"
    row = connection.execute(
        f"SELECT practice_item_id, attempt_id, context, created_at, {contract}, {source}, {note} "
        "FROM question_events WHERE id = ?", (str(event_id),),
    ).fetchone()
    if row is None:
        return None
    try:
        source_context = json.loads(row[5]) if row[5] else {}
    except (TypeError, ValueError):
        source_context = None
    # Recorded but unreadable (not JSON, not an object) is not the same as none recorded:
    # :func:`reading_sources` fails closed on it (Codex review F1).
    readable = isinstance(source_context, Mapping)
    return {"item": row[0], "attempt": row[1], "context": row[2], "created_at": row[3], "contract": row[4],
            "source_context": source_context if readable else {}, "source_context_readable": readable,
            # None: no source context was recorded (a Reader question from before
            # migration 117 kept only its ``note_id`` span key).
            "source_context_recorded": row[5] is not None, "note_id": row[6]}


def _revealed_before(connection: Any, item_id: str, at: Any) -> bool:
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'reveal_events'").fetchone()
    if exists is None:
        return False
    return connection.execute(
        "SELECT 1 FROM reveal_events WHERE practice_item_id = ? AND created_at <= ? LIMIT 1",
        (str(item_id), str(at or "")),
    ).fetchone() is not None


def _reader_sources(source_context: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    extraction, span = source_context.get("extraction_id"), source_context.get("span_id")
    if extraction and span:
        refs.append({"extraction_id": extraction, "span_ids": [span]})
    for value in source_context.get("source_spans") or ():
        if isinstance(value, Mapping) and value.get("extraction_id") and value.get("span_id"):
            refs.append({"extraction_id": value["extraction_id"], "span_ids": [value["span_id"]]})
    return refs


def question_record(connection: Any, event_id: str, *, topics: Iterable[Any] = ()) -> WriteRecord:
    """What a learner question's words carry (see the module doc)."""

    row = _question_row(connection, event_id)
    if row is None:
        return WriteRecord.incomplete(f"question {event_id} is not on record")
    item = str(row["item"]) if row["item"] else None
    inputs = Inputs.of(questions={str(event_id): row["contract"]}, items=[item] if item else (),
                       topics=topics, sources=_reader_sources(row["source_context"]))
    refs: list[tuple[str, str]] = []
    if row["attempt"]:
        inputs = inputs.union(answer_inputs(connection, [row["attempt"]]))
    if item and (row["context"] == "feedback" or _revealed_before(connection, item, row["created_at"])):
        # The learner could have seen the item's solution (its feedback, a reveal) before asking.
        inputs = inputs.union(Inputs.of(solution_items=[item]))
        if row["attempt"] and row["context"] == "feedback":
            refs.append((GRADING, str(row["attempt"])))
    record = WriteRecord(inputs)
    if refs:
        record = record.join(closure(connection, refs))
    return record


#: The learner-text sources written on a reading (followups-nov1c E): a question asked in
#: the Reader (its passage), an active-reading answer or a figure prediction (the book's
#: passage, the expected answer's cited spans, the figure's input spans).
READING_SOURCE_KINDS: tuple[str, ...] = ("tutor_question", "reader_formative")


#: The ``question_events.context`` a question asked in the Reader is recorded under
#: (``tutor_qa.ask_question``: its source context names the passage).
READER_QUESTION_CONTEXT = "reader"


def _question_passages(source_context: Mapping[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    """The passages a question's source context names, and whether every one could
    be placed (Codex review F1). Unlike :func:`_reader_sources` (a question's write
    record), an extraction named without a block is kept as a ref to the whole
    extraction, so the exam predicate checks it conservatively
    (``exam_material.source_ref_keys``); a block named without its extraction, or a
    delivered span that is not an object, cannot be placed."""

    refs: list[dict[str, Any]] = []
    complete = True

    def add(extraction: Any, span: Any) -> None:
        nonlocal complete
        if extraction:
            refs.append({"extraction_id": str(extraction), "span_ids": [str(span)] if span else []})
        elif span:
            complete = False

    add(source_context.get("extraction_id"), source_context.get("span_id"))
    spans = source_context.get("source_spans")
    if spans is not None and not isinstance(spans, list):
        return refs, False
    for value in spans or ():
        if not isinstance(value, Mapping):
            complete = False
            continue
        if value.get("extraction_id"):
            add(value["extraction_id"], value.get("span_id"))
            continue
        # A delivered span with no extraction (orchestrator scoped verify remainder):
        # one that places a book passage some other way (its source or revision, a
        # locator, an ``ext:span`` key) is kept for the exam predicate to check
        # (``exam_material.source_ref_protected``); an identified note is on no
        # book's page; anything else cannot be placed and fails closed.
        located = _located_without_extraction(value)
        if located is not None:
            refs.append(located)
        elif not _identified_note(value):
            complete = False
    return refs, complete


#: The fields that name a note in a delivered span (a vault note, a learner note).
_NOTE_FIELDS = ("note_id", "note_key")


def _identified_note(value: Mapping[str, Any]) -> bool:
    return any(value.get(name) for name in _NOTE_FIELDS) or "note" in (value.get("ref_type"), value.get("kind"))


def _located_without_extraction(value: Mapping[str, Any]) -> dict[str, Any] | None:
    """A delivered span with no ``extraction_id`` that still places a book passage:
    a block the shared parser places (``exam_material.source_ref_keys``: a namespaced
    span id ``ext:span`` or ``ext/span``, a block locator), or a source or revision id
    (checked against every extraction of it); None when nothing places it."""

    ref = source_ref(value)
    if ref is None:
        return None
    keys, whole = source_ref_keys(SimpleNamespace(extraction_id=None, span_ids=ref.get("span_ids"),
                                                  locator=ref.get("locator")))
    if keys or whole or ref.get("source_id") or ref.get("revision_id"):
        return ref
    return None


def _reader_span_key(note_id: Any) -> dict[str, Any] | None:
    """The passage a Reader question's ``note_id`` names (``span:<extraction>/<span>``,
    ``tutor_qa.reader_span_key``), else None (no key, a note id, no block)."""

    placed = parse_block_span(str(note_id or ""))
    if placed is None or not placed[0].strip() or not placed[1].strip():
        return None
    return {"extraction_id": placed[0], "span_ids": [placed[1]]}


def reading_sources(connection: Any, source_kind: str, source_id: str) -> tuple[tuple[Mapping[str, Any], ...], bool]:
    """The passages a learner text was written on, for a reading-derived source
    (:data:`READING_SOURCE_KINDS`), and whether they could all be read: a Reader
    question's passage (``question_events.source_context``; a question asked outside
    the Reader names none), an active-reading answer's or a figure prediction's
    passages (:func:`formative_record`). Any other source reads no passage: ``((), True)``.
    A question or formative record that is gone answers ``((), False)``, as does a
    question whose recorded source context is unreadable, a Reader question that names
    no passage (one with no recorded source context is placed from its ``note_id``
    span key when it has one), or a passage that cannot be placed (:func:`_question_passages`; an
    extraction named without a block is checked whole): the caller fails closed (the
    router card's provenance check, exam material only)."""

    if source_kind == "tutor_question":
        row = _question_row(connection, str(source_id))
        if row is None or not row["source_context_readable"]:
            return (), False
        refs, complete = _question_passages(row["source_context"])
        if str(row["context"] or "") == READER_QUESTION_CONTEXT and not refs:
            # A Reader question is always asked on a passage (tutor_qa records its
            # extraction and span). One recorded with no source context at all is
            # placed from its ``note_id`` span key, which names that passage
            # (``tutor_qa.reader_span_key``); one that names none either way cannot
            # be placed.
            placed = None if row["source_context_recorded"] else _reader_span_key(row["note_id"])
            if placed is None:
                return (), False
            return tuple(Inputs.of(sources=[placed]).sources), True
        return tuple(Inputs.of(sources=refs).sources), complete
    if source_kind == "reader_formative":
        record = formative_record(connection, str(source_id))
        return tuple(record.inputs.sources), record.complete
    return (), True


def text_record(connection: Any, text: Any) -> WriteRecord:
    """What a learner text and its context show any reader of it."""

    topics = tuple(text.anchor_learning_object_ids or ())
    if text.source_kind == "tutor_question":
        return question_record(connection, str(text.question_event_id or text.source_id), topics=topics)
    if text.source_kind == "reader_formative":
        return formative_record(connection, str(text.source_id), topics=topics)
    if text.source_kind in ("hint_feedback", "workbench_text"):
        # RW2b: a workbench text is written beside an open problem and its
        # hints, as a reply to a hint is (the same record).
        return hint_feedback_record(connection, text)
    inputs = answer_inputs(connection, [text.attempt_id]).union(
        Inputs.of(items=[text.practice_item_id], topics=topics))
    if text.source_kind == "diagnosis":
        # The answer, its item, and the diagnosis's causes and quotes.
        return WriteRecord(inputs).join(closure(connection, [("diagnosis", str(text.source_id))]))
    # A stuck answer: the answer, its item's question, its topic and the
    # grader's verbatim quote of the answer.
    return WriteRecord(inputs)


def formative_record(connection: Any, question_id: str, *, topics: Iterable[str] = ()) -> WriteRecord:
    """RW1b: what a missed active-reading answer shows its reader -- the
    learner's answer (not an attempt, so no answer contract), the book's
    passage and the cited spans of the expected answer, and the topics."""

    if str(question_id).startswith("fpr_"):  # an RW5a figure prediction, or its later explanation
        return figure_prediction_record(connection, question_id, topics=topics)
    row = connection.execute(
        "SELECT extraction_id, source_id, span_ids_json, anchor_span_ids_json FROM reader_authored_questions "
        "WHERE id = ?", (question_id,),
    ).fetchone()
    if row is None:
        return WriteRecord.incomplete("the active-reading question is gone", inputs=Inputs.of(topics=topics))
    spans: set[str] = set()
    for raw in (row[2], row[3]):
        try:
            spans.update(str(span) for span in json.loads(raw or "[]"))
        except (TypeError, ValueError):
            continue
    source = {"ref_type": "canonical_source", "ref_id": row[1] or row[0], "source_id": row[1],
              "extraction_id": row[0], "span_ids": sorted(spans)}
    return WriteRecord(Inputs.of(topics=topics, sources=[source]))


def figure_prediction_record(connection: Any, prediction_id: str, *, topics: Iterable[str] = ()) -> WriteRecord:
    """RW5a: what a missed figure prediction shows its reader -- the
    learner's answer (not an attempt), every span the figure was built from
    (the selection, a region's block and the paragraphs the author was sent
    around it: the figure's prediction and readouts derive from all of them;
    Codex review F1), and the topics. The figure's own values are computed by
    code from that passage. A later explanation's source (``...:explained``)
    has its prediction's record."""

    from learnloop.diagnosis.text_gaps.sources import figure_input_keys, figure_input_manifest, figure_prediction_id

    prediction_id, _explained = figure_prediction_id(prediction_id)
    row = connection.execute(
        "SELECT f.extraction_id, f.span_ids_json, f.region_json, f.input_span_ids_json, f.asset_id, "
        "f.input_span_keys_json "
        "FROM figure_predictions AS p JOIN interactive_figures AS f ON f.id = p.figure_id WHERE p.id = ?",
        (prediction_id,),
    ).fetchone()
    if row is None:
        return WriteRecord.incomplete("the figure prediction is gone", inputs=Inputs.of(topics=topics))
    manifest = figure_input_manifest({"span_ids_json": row[1], "region_json": row[2], "input_span_ids_json": row[3],
                                      "asset_id": row[4]})
    keys = figure_input_keys({"input_span_keys_json": row[5]})
    if manifest is None or keys is None:
        return WriteRecord.incomplete("the figure's input spans are unreadable", inputs=Inputs.of(topics=topics))
    # Reader RW5d: a show-me figure's retrieved passages (any source) are inputs too.
    by_extraction: dict[str, set[str]] = {str(row[0]): set(manifest)} if row[0] and (manifest or not keys) else {}
    for extraction_id, spans in keys.items():
        by_extraction.setdefault(extraction_id, set()).update(spans)
    sources = []
    for extraction_id, spans in by_extraction.items():
        source_id = connection.execute(
            "SELECT revision.source_id FROM source_extraction_runs AS run LEFT JOIN source_revisions AS revision "
            "ON revision.id = run.revision_id WHERE run.id = ?", (extraction_id,)).fetchone()
        sources.append({"ref_type": "canonical_source", "ref_id": (source_id[0] if source_id else None) or extraction_id,
                        "source_id": source_id[0] if source_id else None, "extraction_id": extraction_id,
                        "span_ids": sorted(spans)})
    return WriteRecord(Inputs.of(topics=topics, sources=sources))


def hint_feedback_record(connection: Any, text: Any) -> WriteRecord:
    """Adaptive hints H2b: what a reply to a hint shows its reader -- the
    learner's words (no attempt's answer contract while the attempt is
    open), the item's question, and the hint or question it answered. A hint
    is written from the item's solution, so the item's solution is an input:
    nothing the reply names is released before the solution is."""

    topics = tuple(text.anchor_learning_object_ids or ())
    item = [text.practice_item_id] if text.practice_item_id else []
    inputs = Inputs.of(items=item, solution_items=item, topics=topics)
    if text.attempt_id:
        inputs = inputs.union(answer_inputs(connection, [text.attempt_id]))
    return WriteRecord(inputs)


def reading_record(connection: Any, text: Any, reading: Any = None) -> WriteRecord:
    """What wrote a reading's named gap (a belief statement, a prerequisite
    name and line): its reader's inputs (see the module doc)."""

    if text.source_kind == "learner_note":
        # Curriculum C5 (Codex review F1): nothing written from a note's reading carries
        # a provenance record (no holding-pen candidate, no drafted LO); a record here
        # would name only its topics and lose that the words came from a note.
        raise ValueError("a note's reading writes no record that needs write-time provenance")
    record = text_record(connection, text)
    if text.source_kind == "tutor_question":
        record = record.join(WriteRecord.incomplete(TUTOR_UNRECORDED))
    refs = tuple(getattr(reading, "prerequisite_refs", ()) or ()) if reading is not None else ()
    if refs:
        record = record.with_inputs(Inputs.of(topics=refs))
    return fold_topic_records(connection, record)


def drafter_record(connection: Any, vault: Any, text: Any, reading: Any, *, subject_id: str | None,
                   shown_concept_titles: Iterable[str] = ()) -> WriteRecord:
    """What the prerequisite drafter read: the reading, the learner text and
    its context, the asking topic, and the topics whose concept titles it was
    shown (``shown_concept_titles``). Each topic's record is folded only when
    it covers the name the drafter was shown it by (codex review F2): the
    asking topic's title, the named prerequisite (the reading's first ref,
    by the reading's name for it), and each concept title of the subject."""

    titles = set(shown_concept_titles)
    los = getattr(vault, "learning_objects", None) or {}
    shown_names: dict[str, list[str]] = {}
    for lo_id, lo in los.items():
        if subject_id in (lo.subjects or ()) and lo.concept in vault.concepts \
                and vault.concepts[lo.concept].title in titles:
            shown_names.setdefault(str(lo_id), []).append(str(vault.concepts[lo.concept].title))
    anchor = los.get(str(getattr(text, "anchor", None) or ""))
    if anchor is not None:
        shown_names.setdefault(str(anchor.id), []).append(str(anchor.title))
    refs = tuple(getattr(reading, "prerequisite_refs", ()) or ()) if reading is not None else ()
    named = getattr(reading, "prerequisite_name", None) if reading is not None else None
    if refs and named is not None:
        shown_names.setdefault(str(refs[0]), []).append(str(named))
    record = reading_record(connection, text, reading).with_inputs(
        Inputs.of(topics=[*(text.anchor_learning_object_ids or ()), *sorted(shown_names)]))
    return fold_topic_records(connection, record, titles=shown_names)


__all__ = [
    "TUTOR_UNRECORDED",
    "drafter_record",
    "figure_prediction_record",
    "formative_record",
    "hint_feedback_record",
    "question_record",
    "reading_record",
    "text_record",
]
