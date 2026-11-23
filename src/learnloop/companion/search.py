"""Search in context (spec §9.3): the groups found by the learner's words, at once.

This module holds the groups read from the workbench's own tables and the exchanges: **sources in
your library** (titles, with the desks each is open on), **your pads** (standing block text, ink
transcriptions as "your handwriting"), **threads** (Reader exchanges, one row per exchange with the
thread it belongs to), **past companion exchanges** (``companion.history``'s words query) and the
learner-text readings of the notes group (the learner's own words that LearnLoop read for a gap,
outside the exchanges and notes, which have their own groups). The passages and the vault's notes
come from their own services, composed by the sidecar (so nothing here reaches the notes' code).

Every group is bounded (:data:`GROUP_ROWS` rows, and whether more exist) and read on a read-only
connection. Each row names what to open as a ``ContentRef`` (``ref``) plus an optional ``target``
(a span or a pad block), as every workbench result does (§3.4). Nothing here is evidence or writes.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from contextlib import closing
from typing import Any

from learnloop.companion.history import companion_history
from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.db.connection import connect
from learnloop.db.stores import span_projection_reads as spans_reads
from learnloop.substrate.passage_spans import READER_ANSWER_QUESTION_KEY

#: Rows returned per group (the panel shows three and expands; a bound, never a ranking cut-off).
GROUP_ROWS = 12
#: The shortest query searched (one character matches nearly everything).
MIN_QUERY_CHARS = 2
#: The longest query searched (a request-size guardrail).
MAX_QUERY_CHARS = 200
#: How far up a branch a thread's root is looked for (a guard against a corrupt parent chain).
MAX_THREAD_DEPTH = 64
_SNIPPET_RADIUS = 90
_CUE_TIME = re.compile(r"^t=([0-9.]+)-([0-9.]+)$")
#: Gap readings whose words another group shows: a tutor question is an exchange, a linked note's
#: snapshot is a note (and shows only while the notes are on).
_GAP_KINDS_ELSEWHERE = ("tutor_question", "learner_note")
_ANCHOR_RANK = {"exact_selection": 0, "citation": 1, "source_context": 2}

LABELS = {
    "sources": "sources in your library",
    "passages": "passages and moments",
    "notes": "your notes and highlights",
    "pads": "your pads",
    "threads": "threads",
    "exchanges": "past companion exchanges",
}


def words_of(query: str | None) -> str:
    return " ".join(str(query or "").split())[:MAX_QUERY_CHARS]


def _like(words: str) -> str:
    return "%" + words.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def snippet(text: str | None, words: str) -> str:
    flat = " ".join(str(text or "").split())
    at = flat.casefold().find(words.casefold())
    if at < 0:
        return flat[: 2 * _SNIPPET_RADIUS]
    start, end = max(0, at - _SNIPPET_RADIUS), min(len(flat), at + len(words) + _SNIPPET_RADIUS)
    return f"{'…' if start else ''}{flat[start:end]}{'…' if end < len(flat) else ''}"


def _rows(connection: Any, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, tuple(params))
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]


def group(name: str, rows: list[dict[str, Any]], *, more: bool, basis: str = "words") -> dict[str, Any]:
    return {"group": name, "label": LABELS[name], "basis": basis, "status": "ok", "rows": rows, "more": more}


def off_group(name: str, reason: str) -> dict[str, Any]:
    """A group that could not be searched, said so (never shown as "nothing found")."""

    return {"group": name, "label": LABELS[name], "basis": "words", "status": "off", "reason": reason, "rows": [],
            "more": False}


class SourceIds:
    """A reading's source, looked up once per search."""

    def __init__(self, repository: Any) -> None:
        self._repository = repository
        self._found: dict[str, str | None] = {}

    def __call__(self, extraction_id: str) -> str | None:
        if extraction_id not in self._found:
            run = self._repository.get_extraction_run(extraction_id) or {}
            revision = self._repository.get_source_revision(str(run.get("revision_id") or "")) or {}
            self._found[extraction_id] = revision.get("source_id")
        return self._found[extraction_id]


def source_ref(source_id: str | None, extraction_id: str | None) -> dict[str, Any] | None:
    if not source_id or not extraction_id:
        return None
    return {"kind": "source", "source_id": source_id, "extraction_id": extraction_id}


def _open_windows(connection: Any) -> list[dict[str, Any]]:
    """The content of every open window on an open desk, with its desk."""

    found = []
    for row in _rows(connection, "SELECT w.desk_id, w.spec_json FROM desk_windows AS w JOIN desks AS d "
                                 "ON d.desk_id = w.desk_id WHERE w.closed_at IS NULL AND d.archived_at IS NULL "
                                 "ORDER BY d.position, d.desk_id, w.slot, w.pane"):
        try:
            spec = json.loads(row["spec_json"] or "{}")
        except (TypeError, ValueError):
            continue
        content = spec.get("content") if isinstance(spec, dict) else None
        if isinstance(content, dict):
            found.append({"desk_id": row["desk_id"], "content": content})
    return found


def _source_title(repository: Any, artifact: dict[str, Any]) -> str:
    revision = repository.get_source_revision(str(artifact.get("current_revision_id") or "")) or {}
    return str(artifact.get("display_title") or revision.get("original_uri") or artifact.get("canonical_uri")
               or artifact.get("id"))


def sources_group(repository: Any, connection: Any, words: str, desk_id: str | None) -> dict[str, Any]:
    """Library sources whose title holds the words, with the desks each is open on."""

    needle = words.casefold()
    open_on: dict[str, list[str]] = {}
    for window in _open_windows(connection):
        source_id = window["content"].get("source_id")
        if source_id and window["desk_id"] not in open_on.setdefault(str(source_id), []):
            open_on[str(source_id)].append(window["desk_id"])
    matched = []
    for artifact in repository.all_source_artifacts():
        title = _source_title(repository, artifact)
        if needle in title.casefold():
            matched.append((title, artifact))
    rows = []
    for title, artifact in matched[:GROUP_ROWS]:
        source_id = str(artifact["id"])
        extraction_id = resolve_extraction_id(repository, source_id)
        desks = open_on.get(source_id, [])
        rows.append({"source_id": source_id, "extraction_id": extraction_id, "title": title,
                     "reader_enabled": bool(artifact.get("reader_enabled", 1)), "open_on_desk_ids": desks,
                     "on_this_desk": desk_id is not None and desk_id in desks,
                     "ref": source_ref(source_id, extraction_id), "target": None})
    return group("sources", rows, more=len(matched) > GROUP_ROWS)


def pads_group(connection: Any, words: str, desk_id: str | None) -> dict[str, Any]:
    """Standing pad blocks whose text holds the words (removed blocks and archived pads excluded)."""

    found = _rows(connection, (
        "SELECT v.block_id, v.pad_id, v.kind, v.body_md, v.provenance, v.created_at, p.title, p.home_desk_id "
        "FROM pad_block_versions AS v JOIN pads AS p ON p.pad_id = v.pad_id "
        "WHERE p.archived_at IS NULL AND v.tombstone = 0 AND v.body_md LIKE ? ESCAPE '\\' "
        "AND NOT EXISTS (SELECT 1 FROM pad_block_versions AS c WHERE c.supersedes_id = v.version_id) "
        "ORDER BY v.created_at DESC, v.block_id LIMIT ?"), (_like(words), GROUP_ROWS + 1))
    rows = [{"pad_id": row["pad_id"], "block_id": row["block_id"], "pad_title": row["title"],
             "kind": row["kind"], "provenance": row["provenance"],
             # Transcribed ink is the learner's handwriting, labelled as such (spec §9.3).
             "handwriting": row["provenance"] == "ink_transcription",
             "snippet": snippet(row["body_md"], words), "on_this_desk": desk_id is not None
             and row["home_desk_id"] == desk_id, "created_at": row["created_at"],
             "ref": {"kind": "pad", "pad_id": row["pad_id"]}, "target": {"block_id": row["block_id"]}}
            for row in found[:GROUP_ROWS]]
    return group("pads", rows, more=len(found) > GROUP_ROWS)


def _thread_roots(connection: Any, question_event_ids: list[str]) -> dict[str, tuple[str, str]]:
    """Each Reader exchange's answer event and the root of the branch it is on, by question event id."""

    if not question_event_ids:
        return {}
    marks = ",".join("?" for _ in question_event_ids)
    answers: dict[str, tuple[str, str | None]] = {}
    # Written as migration 264's partial expression index, so each lookup is an index probe.
    for event_id, question_event_id, payload_json in connection.execute(
            "SELECT id, " + READER_ANSWER_QUESTION_KEY + ", payload_json FROM interaction_events "
            "WHERE kind = 'reader_answer_submitted' AND " + READER_ANSWER_QUESTION_KEY + f" IN ({marks})",
            question_event_ids):
        answers.setdefault(str(question_event_id), (str(event_id), _parent(payload_json)))
    roots: dict[str, tuple[str, str]] = {}
    for question_event_id, (event_id, parent) in answers.items():
        root, seen = event_id, {event_id}
        while parent and parent not in seen and len(seen) < MAX_THREAD_DEPTH:
            row = connection.execute("SELECT payload_json FROM interaction_events WHERE id = ? "
                                     "AND kind = 'reader_answer_submitted'", (parent,)).fetchone()
            if row is None:
                break
            root, parent = parent, _parent(row[0])
            seen.add(root)
        roots[question_event_id] = (event_id, root)
    return roots


def _parent(payload_json: Any) -> str | None:
    try:
        payload = json.loads(payload_json or "{}")
    except (TypeError, ValueError):
        return None
    parent = payload.get("parent_exchange_id") if isinstance(payload, dict) else None
    return str(parent) if parent else None


def threads_group(connection: Any, words: str, source_ids: SourceIds) -> dict[str, Any]:
    """Reader exchanges whose question or answer holds the words, each with its thread (§7.8)."""

    like = _like(words)
    found = _rows(connection, (
        "SELECT id, note_id, question_md, answer_md, created_at FROM question_events WHERE context = 'reader' "
        "AND answer_status = 'answered' AND (question_md LIKE ? ESCAPE '\\' OR answer_md LIKE ? ESCAPE '\\') "
        "ORDER BY created_at DESC, id DESC LIMIT ?"), (like, like, GROUP_ROWS + 1))
    page = found[:GROUP_ROWS]
    roots = _thread_roots(connection, [str(row["id"]) for row in page])
    rows = []
    for row in page:
        exchange_id, root = roots.get(str(row["id"]), (None, None))
        reading, _, span = str(row["note_id"] or "").removeprefix("span:").partition("/")
        source_id = source_ids(reading) if reading else None
        text = row["question_md"] if words.casefold() in str(row["question_md"]).casefold() else row["answer_md"]
        rows.append({"question_event_id": row["id"], "exchange_id": exchange_id, "root_exchange_id": root,
                     "question_md": row["question_md"], "snippet": snippet(text, words),
                     "created_at": row["created_at"],
                     "passage": source_ref(source_id, reading if span else None),
                     "ref": {"kind": "thread", "root_exchange_id": root} if root else None,
                     "target": {"span_id": span} if span and source_id else None})
    return group("threads", rows, more=len(found) > GROUP_ROWS)


def exchanges_group(repository: Any, words: str, source_ids: SourceIds) -> dict[str, Any]:
    """Every past exchange whose question or answer holds the words (the history's query), newest first."""

    page = companion_history(repository, query=words)
    exchanges = [(desk["desk_id"], exchange) for day in page["days"] for desk in day["desks"]
                 for exchange in desk["exchanges"]]
    # The history groups a day by desk; a search lists newest first across desks.
    exchanges.sort(key=lambda pair: (str(pair[1]["created_at"]), str(pair[1]["question_event_id"])), reverse=True)
    rows = []
    for desk_id, exchange in exchanges[:GROUP_ROWS]:
        anchor = exchange.get("anchor") or None
        reading = anchor["extraction_id"] if anchor else None
        rows.append({**{key: exchange[key] for key in ("question_event_id", "question_md", "answer_first_sentence",
                                                       "surface", "where", "origin", "created_at")},
                     "desk_id": desk_id,
                     "ref": source_ref(source_ids(reading), reading) if reading else None,
                     "target": {"span_id": anchor["span_id"]} if anchor else None})
    return group("exchanges", rows, more=len(exchanges) > GROUP_ROWS or page["cursor"] is not None)


def gap_rows(connection: Any, words: str, source_ids: SourceIds) -> tuple[list[dict[str, Any]], bool]:
    """The learner's own words LearnLoop read for a gap (stuck answers, workbench text, lesson turns and
    the like), whose words no other group shows. Placed on their best passage when they have one."""

    marks = ",".join("?" for _ in _GAP_KINDS_ELSEWHERE)
    found = _rows(connection, (
        "SELECT id, source_kind, kind, learner_text, created_at FROM learner_text_gaps "
        f"WHERE source_kind NOT IN ({marks}) AND learner_text LIKE ? ESCAPE '\\' "
        "ORDER BY created_at DESC, id DESC LIMIT ?"), (*_GAP_KINDS_ELSEWHERE, _like(words), GROUP_ROWS + 1))
    page = found[:GROUP_ROWS]
    best: dict[str, dict[str, Any]] = {}
    for row in spans_reads.rows_for(connection, "learner_text_gap_spans", [str(gap["id"]) for gap in page]):
        if row["span_id"] is None:
            continue
        current = best.get(row["gap_id"])
        if current is None or _ANCHOR_RANK[row["quality"]] < _ANCHOR_RANK[current["quality"]]:
            best[row["gap_id"]] = row
    rows = []
    for gap in page:
        anchor = best.get(str(gap["id"]))
        reading = anchor["extraction_id"] if anchor else None
        rows.append({"note_kind": "gap_reading", "gap_id": gap["id"], "source_kind": gap["source_kind"],
                     "kind": gap["kind"], "snippet": snippet(gap["learner_text"], words),
                     "created_at": gap["created_at"],
                     "ref": source_ref(source_ids(reading), reading) if reading else None,
                     "target": {"span_id": anchor["span_id"]} if anchor else None})
    return rows, len(found) > GROUP_ROWS


def cue_starts(repository: Any, keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], float]:
    """The start time of each passage that is a transcript cue (its block is ``t=<start>-<end>``), so a
    video result opens at its moment; a book passage has none."""

    wanted = sorted(set(keys))
    if not wanted:
        return {}
    found: dict[tuple[str, str], float] = {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for start in range(0, len(wanted), 200):
            chunk = wanted[start:start + 200]
            clause = " OR ".join("(extraction_id = ? AND span_id = ?)" for _ in chunk)
            for extraction_id, span_id, block_id in connection.execute(
                    f"SELECT extraction_id, span_id, extractor_block_id FROM source_document_blocks WHERE {clause}",
                    [value for key in chunk for value in key]):
                match = _CUE_TIME.match(str(block_id or ""))
                if match:
                    found[(str(extraction_id), str(span_id))] = float(match.group(1))
    return found


def passage_row(hit: dict[str, Any], cue_start: float | None, *, basis: str = "words") -> dict[str, Any]:
    """A library search hit as a result row: a video opens at its cue, a book at its passage."""

    source_id, extraction_id = hit.get("source_id"), hit.get("extraction_id")
    if cue_start is not None and source_id and extraction_id:
        ref: dict[str, Any] | None = {"kind": "video", "source_id": source_id, "extraction_id": extraction_id,
                                      "t": cue_start}
        target: dict[str, Any] = {"span_id": hit.get("span_id"), "t": cue_start}
    else:
        ref, target = source_ref(source_id, extraction_id), {"span_id": hit.get("span_id")}
    return {"source_id": source_id, "source_title": hit.get("source_title"), "extraction_id": extraction_id,
            "span_id": hit.get("span_id"), "section": hit.get("section"), "page": hit.get("page"),
            "snippet": hit.get("snippet"), "by_meaning": basis == "meaning", "ref": ref, "target": target}


def word_groups(repository: Any, words: str, *, desk_id: str | None, scopes: Iterable[str]) -> dict[str, Any]:
    """The groups this module searches, by name, for the scopes asked (``gaps`` is the notes group's part)."""

    wanted = set(scopes)
    source_ids = SourceIds(repository)
    out: dict[str, Any] = {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if "sources" in wanted:
            out["sources"] = sources_group(repository, connection, words, desk_id)
        if "pads" in wanted:
            out["pads"] = pads_group(connection, words, desk_id)
        if "threads" in wanted:
            out["threads"] = threads_group(connection, words, source_ids)
        if "notes" in wanted:
            out["gaps"] = gap_rows(connection, words, source_ids)
    if "exchanges" in wanted:
        out["exchanges"] = exchanges_group(repository, words, source_ids)
    return out


__all__ = ["GROUP_ROWS", "LABELS", "MAX_QUERY_CHARS", "MIN_QUERY_CHARS", "SourceIds", "cue_starts", "group",
           "off_group", "passage_row", "snippet", "source_ref", "word_groups", "words_of"]
