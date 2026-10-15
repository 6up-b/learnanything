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
from typing import Any

from learnloop.db.stores.write_provenance import (
    GRADING,
    Inputs,
    WriteRecord,
    answer_inputs,
    closure,
    fold_topic_records,
)

#: Why what a tutor question's reading named is held back.
TUTOR_UNRECORDED = "the tutor's reading of a question does not record what the tutor read"


def _question_row(connection: Any, event_id: str) -> dict[str, Any] | None:
    columns = {column[1] for column in connection.execute("PRAGMA table_info(question_events)")}
    if not columns:
        return None
    contract = "assessment_contract_version_id" if "assessment_contract_version_id" in columns else "NULL"
    source = "source_context_json" if "source_context_json" in columns else "NULL"
    row = connection.execute(
        f"SELECT practice_item_id, attempt_id, context, created_at, {contract}, {source} FROM question_events "
        "WHERE id = ?", (str(event_id),),
    ).fetchone()
    if row is None:
        return None
    try:
        source_context = json.loads(row[5]) if row[5] else {}
    except (TypeError, ValueError):
        source_context = {}
    return {"item": row[0], "attempt": row[1], "context": row[2], "created_at": row[3], "contract": row[4],
            "source_context": source_context if isinstance(source_context, Mapping) else {}}


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


def text_record(connection: Any, text: Any) -> WriteRecord:
    """What a learner text and its context show any reader of it."""

    topics = tuple(text.anchor_learning_object_ids or ())
    if text.source_kind == "tutor_question":
        return question_record(connection, str(text.question_event_id or text.source_id), topics=topics)
    inputs = answer_inputs(connection, [text.attempt_id]).union(
        Inputs.of(items=[text.practice_item_id], topics=topics))
    if text.source_kind == "diagnosis":
        # The answer, its item, and the diagnosis's causes and quotes.
        return WriteRecord(inputs).join(closure(connection, [("diagnosis", str(text.source_id))]))
    # A stuck answer: the answer, its item's question, its topic and the
    # grader's verbatim quote of the answer.
    return WriteRecord(inputs)


def reading_record(connection: Any, text: Any, reading: Any = None) -> WriteRecord:
    """What wrote a reading's named gap (a belief statement, a prerequisite
    name and line): its reader's inputs (see the module doc)."""

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
    "question_record",
    "reading_record",
    "text_record",
]
