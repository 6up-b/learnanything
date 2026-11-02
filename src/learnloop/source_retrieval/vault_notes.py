"""Curriculum C2b: the learner's notes are the vault's own (spec_deliverable_curriculum_v1
§10.1 as built).

"Your notes" are, in this vault:

* the learner's **Reader notes and highlights with text** (``source_annotations``: the
  head version of each annotation the learner wrote, its own words in ``learner_text`` and
  ``what_i_think_is_going_on``; a bare highlight with no words, a deleted annotation, a
  disposition and a model's or an author's annotation are not notes);
* their **capture-inbox items** (``capture_inbox``: a capture's text and its note, never
  one the learner dismissed or purged).

Nothing outside the vault is read, and LearnLoop never writes to a note.

**Exam material stays protected.** An annotation anchored on protected material (an exam
unit, a held-out unit, a reading held back until protection is marked: C0a's predicate,
:func:`section_coverage.read_protection`) is no note here: it is never searched, embedded,
linked or sent. With the predicate unreadable no annotation is a note (fail closed);
captures carry no book text and stay.

**Exact words** (always available, no model, no network): the query's terms (the library
search's own tokenizer and stopwords, ``source_block_fts.query_terms``), each matched as a
whole word of a note's title, heading or text; the notes ranked by how many distinct
terms they contain, newest first among equals.

**By meaning** (only while the vault's embeddings are on: ``embedding.enabled`` and
``embedding.backfill_enabled``): the vault's hosted embedding model and route
(``embedding.model``), with the query cache, price and caps of the tutor's hosted query path
(``source_retrieval.queries.embed_query_texts``; record kind ``source_query``; the local
contextual space, ``embedding.local`` / ``embedding.source_space``, indexes book extractions
only and does not cover notes), over ``learner_note/text`` vectors
kept incrementally beside the source blocks' (``ops.embedding_backfill``: content-
addressed, so only a new or changed note is ever embedded; capped per run like a source's
backfill, ``source_vectors.backfill_caps``, at ``source_retrieval.
query_embedding_price_per_million``). Ranked by the Phase 1 mean-centred cosine
(``embedding_vectors.retrieve``) over the notes that have a current vector; a note still
without one is left to exact words (``partial``). With embeddings off the meaning search
is not offered (:func:`meaning_available`, the prompt contract's ``meaning`` flag).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType
from typing import Any, Callable

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import query_terms
from learnloop.vault.embedding_recipes import EmbeddingRecipe, EmbeddingRecord

ORIGIN = "vault"
KIND_ANNOTATION = "annotation"
KIND_CAPTURE = "capture"
REF_KINDS: tuple[str, ...] = (KIND_ANNOTATION, KIND_CAPTURE)
#: ``keep`` (a prompt and display bound, never a model parameter): one note's text at most,
#: as stored and as the judge reads it (C2's bound, unchanged).
NOTE_CHARS = 3000
#: ``keep`` (a display bound): a search hit's snippet.
SNIPPET_CHARS = 200
#: ``keep`` (a display bound): how many notes one search of the Reader's picker lists.
SEARCH_LIMIT = 20
#: The embedding record of a note (kept beside ``source_block/text``).
RECORD_KIND = "learner_note"
RECORD_FIELD = "text"
RECIPE = f"{RECORD_KIND}/{RECORD_FIELD}"
#: The annotation kinds whose words are a note (``disposition`` is a deletion tombstone).
NOTE_ANNOTATION_TYPES = frozenset({"highlight", "question", "confusion", "interpretation"})
#: Capture states that are no longer the learner's (dismissed from the inbox).
DROPPED_CAPTURE_STATES = frozenset({"dismissed"})
CAPTURE_TITLE = "captured note"
ANNOTATION_HEADINGS = {"highlight": "highlight", "question": "question", "confusion": "confusion",
                       "interpretation": "interpretation"}
MODES = ("words", "meaning")
_WORD = re.compile(r"[^\W_]+", re.UNICODE)


class MeaningUnavailable(Exception):
    """A meaning search was asked while it is not available (``reason`` says why)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class VaultNote:
    """One note of the learner's in this vault."""

    ref_kind: str
    ref_id: str
    title: str
    heading: str
    text: str
    truncated: bool
    captured_on: str | None
    #: The annotation's anchor (its reading and first span), for display only.
    extraction_id: str | None = None
    span_id: str | None = None
    #: The note's newest change (for ranking among equals).
    changed_at: str = ""
    #: The whole text (Codex re-review C2b F3): searched, and hashed for change detection;
    #: ``text`` is the bounded one stored and sent.
    full_text: str = ""

    @property
    def note_key(self) -> str:
        return note_key(self.ref_kind, self.ref_id)

    @property
    def content_hash(self) -> str:
        return "text:" + hashlib.sha256(json.dumps([self.title, self.heading, self.full_text or self.text],
                                                   ensure_ascii=False).encode("utf-8")).hexdigest()[:40]

    @property
    def origin(self) -> str:
        return ORIGIN

    @property
    def snippet(self) -> str:
        value = " ".join(self.text.split())
        return value if len(value) <= SNIPPET_CHARS else value[: SNIPPET_CHARS - 1].rstrip() + "…"

    def searchable(self) -> str:
        return "\n".join(part for part in (self.title, self.heading, self.full_text or self.text) if part)

    def view(self) -> dict[str, Any]:
        return {"note_key": self.note_key, "ref_kind": self.ref_kind, "ref_id": self.ref_id, "title": self.title,
                "heading": self.heading, "snippet": self.snippet, "captured_on": self.captured_on,
                "origin": ORIGIN, "content_hash": self.content_hash}


def note_key(ref_kind: str, ref_id: str) -> str:
    return f"{ref_kind}:{ref_id}"


def split_key(key: str) -> tuple[str, str] | None:
    kind, _, ref = str(key or "").partition(":")
    return (kind, ref) if kind in REF_KINDS and ref else None


def _bounded(text: str) -> tuple[str, bool]:
    value = text.strip()
    if len(value) <= NOTE_CHARS:
        return value, False
    return value[: NOTE_CHARS - 1].rstrip() + "…", True


def _day(value: Any) -> str | None:
    text = str(value or "")[:10]
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# The corpus: annotations with words, and captures
# ---------------------------------------------------------------------------

def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)).fetchone() is not None


def _protection(vault: Any, repository: Repository) -> Any | None:
    """C0a's predicate as the vault says now, or None when it cannot be read (fail closed)."""

    from learnloop.source_retrieval import section_coverage as SC

    try:
        return SC.read_protection(vault, repository)
    except Exception:  # noqa: BLE001 - unreadable protection: no annotation is a note
        return None


def _source_titles(repository: Repository) -> dict[str, str]:
    from learnloop.source_retrieval.corpus import current_extractions

    try:
        return {extraction.source_id: extraction.title for extraction in current_extractions(repository).values()}
    except Exception:  # noqa: BLE001 - a title is display only
        return {}


def _standing_annotation_ids(repository: Repository) -> set[str]:
    """The annotations the Reader lists (no standing delete): the repository's own rule."""

    return repository.standing_annotation_ids()


def _anchor(connection: Any, annotation_id: str) -> tuple[str | None, list[tuple[str, list[str]]]]:
    """The head anchor's reading and its segments (span id, section path)."""

    anchor = connection.execute(
        "SELECT id, extraction_id FROM source_annotation_anchor_versions WHERE annotation_id = ? "
        "ORDER BY version_ordinal DESC LIMIT 1", (annotation_id,)).fetchone()
    if anchor is None:
        return None, []
    segments: list[tuple[str, list[str]]] = []
    for span_id, path_json in connection.execute(
            "SELECT span_id, section_path_json FROM source_annotation_anchor_segments WHERE anchor_version_id = ? "
            "ORDER BY segment_ordinal", (anchor[0],)):
        try:
            path = [str(part) for part in json.loads(path_json or "[]") if str(part).strip()]
        except (TypeError, ValueError):
            path = []
        segments.append((str(span_id), path))
    return str(anchor[1]), segments


def _out(protection: Any, extraction_id: str, segments: Sequence[tuple[str, list[str]]],
         connection: Any = None) -> bool:
    """Whether an annotation's anchor touches protected material. An anchor with no
    segments (a selection still to be re-anchored) is judged by its reading: out when any
    part of that reading is protected (fail closed). The header block of each anchored
    span's section counts too (Codex review C2b F1: its text would be the note's heading)."""

    if protection.reading_out(extraction_id):
        return True
    if not segments:
        material_spans = getattr(protection.material, "spans", ()) or ()
        return any(key[0] == extraction_id for key in (*protection.excluded_spans, *material_spans))
    if any(protection.span_out(extraction_id, span_id) for span_id, _path in segments):
        return True
    if connection is None:
        return False
    return any(protection.span_out(extraction_id, header) for header in _header_spans(connection, extraction_id, segments))


def _header_spans(connection: Any, extraction_id: str, segments: Sequence[tuple[str, list[str]]]) -> set[str]:
    """The span ids of the section header blocks the anchored spans sit under."""

    refs: set[str] = set()
    for span_id, path in segments:
        found = list(path)
        if not found:
            row = connection.execute("SELECT section_path_json FROM source_document_blocks WHERE extraction_id = ? "
                                     "AND span_id = ?", (extraction_id, span_id)).fetchone()
            try:
                found = [str(part) for part in json.loads((row[0] if row else None) or "[]")]
            except (TypeError, ValueError):
                found = []
        refs.update(str(part) for part in found if str(part).strip())
    if not refs:
        return set()
    marks = ", ".join("?" for _ in refs)
    return {str(row[0]) for row in connection.execute(
        f"SELECT span_id FROM source_document_blocks WHERE extraction_id = ? AND extractor_block_id IN ({marks})",
        (extraction_id, *sorted(refs)))}


def _section_title(connection: Any, extraction_id: str, segments: Sequence[tuple[str, list[str]]],
                   headers: dict[str, dict[str, str]]) -> str:
    """The section the annotation sits in, by its header's text (the recorded section
    path names header blocks by id, ``/page/16/SectionHeader/2``)."""

    path = next((path for _span, path in segments if path), [])
    if not path and segments:
        # The anchor recorded no section path: the block's own (the extraction's record).
        row = connection.execute("SELECT section_path_json FROM source_document_blocks WHERE extraction_id = ? "
                                 "AND span_id = ?", (extraction_id, segments[0][0])).fetchone()
        try:
            path = [str(part) for part in json.loads((row[0] if row else None) or "[]") if str(part).strip()]
        except (TypeError, ValueError):
            path = []
    if not path:
        return ""
    if extraction_id not in headers:
        from learnloop.db.stores.source_block_fts import section_header_titles

        try:
            headers[extraction_id] = section_header_titles(connection, extraction_id)
        except Exception:  # noqa: BLE001 - a heading is display only
            headers[extraction_id] = {}
    found = headers[extraction_id]
    last = str(path[-1])
    return found.get(last) or ("" if last.startswith("/") else " ".join(last.split()))


def _annotation_notes(vault: Any, repository: Repository, *, only: Iterable[str] | None = None) -> list[VaultNote]:
    protection = _protection(vault, repository)
    if protection is None:
        return []
    standing = _standing_annotation_ids(repository)
    wanted = None if only is None else {str(value) for value in only}
    titles: dict[str, str] | None = None
    headers: dict[str, dict[str, str]] = {}
    out: list[VaultNote] = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not _table(connection, "source_annotation_versions"):
            return []
        rows = connection.execute(
            "SELECT a.id, a.source_id, a.created_at, v.annotation_type, v.learner_text, v.what_i_think_is_going_on, "
            "v.authorship, v.created_at FROM source_annotations AS a JOIN source_annotation_versions AS v "
            "ON v.annotation_id = a.id AND v.version_ordinal = (SELECT MAX(version_ordinal) FROM "
            "source_annotation_versions WHERE annotation_id = a.id) ORDER BY a.created_at, a.id").fetchall()
        for annotation_id, source_id, created_at, kind, words, thinking, authorship, changed_at in rows:
            annotation_id = str(annotation_id)
            if annotation_id not in standing or (wanted is not None and annotation_id not in wanted):
                continue
            if str(kind) not in NOTE_ANNOTATION_TYPES or str(authorship or "learner") != "learner":
                continue
            text = "\n".join(part.strip() for part in (str(words or ""), str(thinking or "")) if part.strip())
            if not text:
                continue  # a bare highlight: the book's words, not the learner's
            extraction_id, segments = _anchor(connection, annotation_id)
            if extraction_id is None:
                continue
            if _out(protection, extraction_id, segments, connection):
                continue  # beside protected material: never a note here
            if titles is None:
                titles = _source_titles(repository)
            section = _section_title(connection, extraction_id, segments, headers)
            heading = " › ".join(part for part in (section, ANNOTATION_HEADINGS.get(str(kind), "")) if part)
            bounded, truncated = _bounded(text)
            out.append(VaultNote(
                ref_kind=KIND_ANNOTATION, ref_id=annotation_id,
                title=" ".join(str(titles.get(str(source_id)) or "your reading").split()), heading=heading,
                text=bounded, truncated=truncated, captured_on=_day(changed_at) or _day(created_at),
                extraction_id=extraction_id, span_id=segments[0][0] if segments else None,
                changed_at=str(changed_at or created_at or ""), full_text=text))
    return out


def _capture_notes(repository: Repository, *, only: Iterable[str] | None = None) -> list[VaultNote]:
    wanted = None if only is None else {str(value) for value in only}
    out: list[VaultNote] = []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not _table(connection, "capture_inbox"):
            return []
        rows = connection.execute(
            "SELECT i.id, i.kind, i.text, i.note, i.url, i.captured_at, i.received_at, r.state "
            "FROM capture_inbox AS i LEFT JOIN capture_routes AS r ON r.capture_id = i.id "
            "WHERE i.purged_at IS NULL ORDER BY i.received_at, i.id").fetchall()
    for capture_id, kind, words, note, url, captured_at, received_at, state in rows:
        capture_id = str(capture_id)
        if wanted is not None and capture_id not in wanted:
            continue
        if state in DROPPED_CAPTURE_STATES:
            continue
        text = "\n".join(part.strip() for part in (str(words or ""), str(note or "")) if part.strip())
        if not text:
            continue  # a photo or link with no words of the learner's
        bounded, truncated = _bounded(text)
        heading = " ".join(str(url or "").split())[:200] if kind == "url" else ""
        out.append(VaultNote(ref_kind=KIND_CAPTURE, ref_id=capture_id, title=CAPTURE_TITLE, heading=heading,
                             text=bounded, truncated=truncated,
                             captured_on=_day(captured_at) or _day(received_at),
                             changed_at=str(captured_at or received_at or ""), full_text=text))
    return out


def beside_protected(vault: Any, repository: Repository, key: str) -> bool:
    """Whether the note ``key`` is an annotation anchored on protected material now (or the
    predicate cannot be read: fail closed). A capture never is (it holds no book text)."""

    ref = split_key(key)
    if ref is None or ref[0] != KIND_ANNOTATION:
        return False
    return bool(protected_keys(vault, repository, [key]))


def protected_keys(vault: Any, repository: Repository, keys: Iterable[str]) -> set[str]:
    """The annotation notes among ``keys`` anchored on protected material now (C0a's
    predicate read once; unreadable: every annotation is, fail closed). Captures never are."""

    annotations = [(key, ref[1]) for key, ref in ((key, split_key(key)) for key in keys)
                   if ref is not None and ref[0] == KIND_ANNOTATION]
    if not annotations:
        return set()
    protection = _protection(vault, repository)
    if protection is None:
        return {key for key, _ref in annotations}
    out: set[str] = set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not _table(connection, "source_annotation_anchor_versions"):
            return set()
        for key, annotation_id in annotations:
            extraction_id, segments = _anchor(connection, annotation_id)
            if extraction_id is not None and _out(protection, extraction_id, segments, connection):
                out.add(key)
    return out


def anchor_sources(repository: Repository, key: str) -> list[tuple[str, tuple[str, ...]]]:
    """Every book span a Reader note's snapshot may carry text from (Codex review C2b round 5
    F2): for each anchor version the annotation ever had (a snapshot was taken from one of
    them), its reading and its anchored spans plus the header blocks of their sections (the
    note's heading is that header's text). An anchor version with no segments names its
    whole reading (no spans: conservative). A capture carries no book text: none."""

    ref = split_key(key)
    if ref is None or ref[0] != KIND_ANNOTATION:
        return []
    out: dict[str, set[str]] = {}
    whole: set[str] = set()
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not _table(connection, "source_annotation_anchor_versions"):
            return []
        versions = connection.execute(
            "SELECT id, extraction_id FROM source_annotation_anchor_versions WHERE annotation_id = ? "
            "ORDER BY version_ordinal", (ref[1],)).fetchall()
        for version_id, extraction_id in versions:
            extraction_id = str(extraction_id)
            segments: list[tuple[str, list[str]]] = []
            for span_id, path_json in connection.execute(
                    "SELECT span_id, section_path_json FROM source_annotation_anchor_segments "
                    "WHERE anchor_version_id = ? ORDER BY segment_ordinal", (version_id,)):
                try:
                    path = [str(part) for part in json.loads(path_json or "[]") if str(part).strip()]
                except (TypeError, ValueError):
                    path = []
                segments.append((str(span_id), path))
            if not segments:
                whole.add(extraction_id)
                continue
            spans = out.setdefault(extraction_id, set())
            spans.update(span for span, _path in segments)
            spans.update(_header_spans(connection, extraction_id, segments))
    found = [(extraction_id, tuple(sorted(spans))) for extraction_id, spans in sorted(out.items())
             if extraction_id not in whole]
    return found + [(extraction_id, ()) for extraction_id in sorted(whole)]


def notes(vault: Any, repository: Repository) -> list[VaultNote]:
    """Every note of the learner's in this vault, as it is now (annotations, then captures)."""

    return [*_annotation_notes(vault, repository), *_capture_notes(repository)]


def read(vault: Any, repository: Repository, key: str) -> VaultNote | None:
    """One note as it is now, by its key; None when it is gone (deleted, dismissed, purged,
    words removed) or is beside protected material."""

    ref = split_key(key)
    if ref is None:
        return None
    kind, ref_id = ref
    found = (_annotation_notes(vault, repository, only=[ref_id]) if kind == KIND_ANNOTATION
             else _capture_notes(repository, only=[ref_id]))
    return found[0] if found else None


def read_many(vault: Any, repository: Repository, keys: Iterable[str]) -> dict[str, VaultNote]:
    refs = [ref for ref in (split_key(key) for key in keys) if ref is not None]
    annotations = [ref_id for kind, ref_id in refs if kind == KIND_ANNOTATION]
    captures = [ref_id for kind, ref_id in refs if kind == KIND_CAPTURE]
    found: list[VaultNote] = []
    if annotations:
        found += _annotation_notes(vault, repository, only=annotations)
    if captures:
        found += _capture_notes(repository, only=captures)
    return {note.note_key: note for note in found}


# ---------------------------------------------------------------------------
# Exact words
# ---------------------------------------------------------------------------

def _words(text: str) -> set[str]:
    return set(_WORD.findall(unicodedata.normalize("NFKC", text or "").lower()))


def words_search(corpus: Sequence[VaultNote], query: str, *, limit: int) -> list[VaultNote]:
    """The notes holding the query's terms as whole words, most distinct terms first, then
    the newest; none for a query with no terms."""

    terms = query_terms(query)
    if not terms or limit <= 0:
        return []
    found: list[tuple[int, VaultNote]] = []
    for note in corpus:
        count = len(set(terms) & _words(note.searchable()))
        if count:
            found.append((count, note))
    # Newest first, then (stable) most distinct terms first.
    found.sort(key=lambda entry: (entry[1].changed_at, entry[1].note_key), reverse=True)
    found.sort(key=lambda entry: -entry[0])
    return [note for _count, note in found[:limit]]


# ---------------------------------------------------------------------------
# By meaning: the vault's embeddings, incrementally
# ---------------------------------------------------------------------------

def meaning_unavailable(vault: Any) -> str | None:
    """Why a meaning search is not offered now, or None (the vault's embedding switches)."""

    embedding = vault.config.embedding
    if not embedding.enabled:
        return "embedding.enabled is false"
    if not embedding.backfill_enabled:
        return "embedding.backfill_enabled is false"
    return None


def meaning_available(vault: Any) -> bool:
    return meaning_unavailable(vault) is None


def recipe_text(note: VaultNote) -> str:
    """What is embedded for a note: its title and heading line, then its text."""

    head = " › ".join(part for part in (note.title, note.heading) if part)
    return f"{head}\n{note.text}" if head else note.text


def _no_texts(_loaded: Any) -> Any:
    return iter(())


NOTE_RECIPES: Mapping[str, EmbeddingRecipe] = MappingProxyType({
    RECIPE: EmbeddingRecipe(
        RECORD_KIND, RECORD_FIELD, 1,
        "One record per note of the learner's in the vault (curriculum C2b): a Reader note or highlight with "
        f"the learner's own words, or a capture-inbox item; its title and heading line, then its text (at most "
        f"{NOTE_CHARS} characters). Never a note beside protected material. Embedded only by the notes search, "
        "incrementally (never in the default backfill).",
        _no_texts,
    ),
})


def records(corpus: Sequence[VaultNote]) -> list[EmbeddingRecord]:
    recipe = NOTE_RECIPES[RECIPE]
    return [recipe.record(note.note_key, recipe_text(note)) for note in corpus]


def _current(vault: Any) -> Any:
    """The vault as its files say now (switches and protection may have changed since ``vault``
    was loaded); ``vault`` itself when it has no root on disk."""

    from learnloop.vault.loader import load_vault

    try:
        return load_vault(vault.root)
    except Exception:  # noqa: BLE001 - unreadable: nothing is authorized (see the callers)
        return None


def _authorized_now(vault: Any) -> tuple[Any | None, str | None]:
    """``(the vault as it is now, None)``, or ``(None, why not)``: the notes and the vault's
    embeddings must still be on before any embedding request (Codex re-review C2b R3 F2)."""

    current = _current(vault)
    if current is None:
        return None, "the vault's settings could not be read"
    if not bool(current.config.notes.enabled):
        return None, "notes.enabled is false"
    reason = meaning_unavailable(current)
    return (current, None) if reason is None else (None, reason)


def ensure_vectors(vault: Any, corpus: Sequence[VaultNote], *,
                   client_factory: Callable[[], Any] | None = None,
                   repository: Repository | None = None) -> dict[str, Any]:
    """Embed the notes that have no current vector yet (content-addressed: an unchanged note
    is never embedded again), through the vault's embedding backfill: its switches, lock,
    receipts and price, capped per run like a source's backfill. Aggregate report only.

    With ``repository``, the notes go in batches under ONE money cap for the whole run (the
    remaining cap passed to each batch: Codex re-review C2b R3 F3), and before every batch,
    the first included, the vault is read again from its files: a switch turned off stops the
    run, and any annotation that now sits beside protected material is dropped (Codex
    re-reviews C2b F2, R3 F1/F2)."""

    from dataclasses import replace as replace_caps

    from learnloop.ops.embedding_backfill import BackfillLockBusy, backfill_embeddings
    from learnloop.source_retrieval.source_vectors import BATCH_SIZE, backfill_caps

    reason = meaning_unavailable(vault)
    if reason is not None:
        return {"status": "disabled", "reason": reason}
    notes = list(corpus)
    if not notes:
        return {"status": "complete", "records": 0}
    batches = [notes] if repository is None else [notes[start:start + BATCH_SIZE]
                                                  for start in range(0, len(notes), BATCH_SIZE)]
    remaining = backfill_caps(vault.config, records(notes)).max_estimated_usd
    totals: dict[str, Any] = {"status": "complete", "records": 0, "cached": 0, "embedded": 0, "dropped": 0}
    for batch in batches:
        if repository is not None:
            current, why = _authorized_now(vault)
            if current is None:
                return {**totals, "status": "disabled", "reason": why}
            protected = protected_keys(current, repository, [note.note_key for note in batch])
            totals["dropped"] += len(protected)
            batch = [note for note in batch if note.note_key not in protected]
        wanted = records(batch)
        if not wanted:
            continue
        caps = backfill_caps(vault.config, wanted)
        if remaining is not None:
            caps = replace_caps(caps, max_estimated_usd=max(0.0, float(remaining)))
        try:
            result = backfill_embeddings(
                vault, caps=caps, recipes=(RECIPE,), registry=NOTE_RECIPES, records=wanted,
                price_per_million=vault.config.source_retrieval.query_embedding_price_per_million,
                client_factory=client_factory)
        except BackfillLockBusy as exc:
            return {**totals, "status": "busy", "reason": str(exc)}
        except ValueError as exc:
            return {**totals, "status": "blocked", "reason": str(exc)}
        for key in ("records", "cached", "embedded"):
            totals[key] += int(result.get(key) or 0)
        if remaining is not None:
            remaining = float(remaining) - float((result.get("charged") or {}).get("estimated_usd") or 0.0)
        if result.get("status") != "complete":
            return {**totals, "status": result.get("status"), "reason": result.get("reason")}
    return totals


def _covered(repository: Repository, model_id: str, corpus: Sequence[VaultNote]) -> dict[str, str]:
    """``{note key: content hash}`` of the notes with a current vector for ``model_id``."""

    from learnloop.ops.embedding_backfill import TASK_PREFIX

    expected = {record.record_id: record.content_hash for record in records(corpus)}
    if not expected:
        return {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not _table(connection, "embedding_vectors"):
            return {}
        # Every stored (record, hash) pair: a note keeps a vector per text it ever had (Codex
        # review C2b F3: a text restored after an edit is still covered).
        found = {(str(record_id), str(content_hash)) for record_id, content_hash in connection.execute(
            "SELECT record_id, content_hash FROM embedding_vectors WHERE record_kind = ? AND field = ? "
            "AND model_id = ? AND task_prefix = ?", (RECORD_KIND, RECORD_FIELD, model_id, TASK_PREFIX))}
    return {key: digest for key, digest in expected.items() if (key, digest) in found}


@dataclass
class MeaningResult:
    notes: list[VaultNote] = field(default_factory=list)
    #: ready (every note has a vector) | partial (some have; the rest are left to words) |
    #: empty (no note has one yet) | unavailable (the query could not be embedded)
    status: str = "empty"
    covered: int = 0
    total: int = 0
    reason: str | None = None


def meaning_search(vault: Any, repository: Repository, corpus: Sequence[VaultNote], queries: Sequence[str], *,
                   limit: int, embedder: Any | None = None, owner_id: str = "notes",
                   index: bool = True) -> MeaningResult:
    """The notes nearest each query by meaning, best first (each note once, the first
    query's ranking first). ``index``: embed the notes still without a vector first.
    Raises :class:`MeaningUnavailable` while the vault's embeddings are off."""

    from learnloop.db.stores.embedding_vectors import retrieve
    from learnloop.ops.embedding_backfill import TASK_PREFIX
    from learnloop.source_retrieval.queries import embed_query_texts

    reason = meaning_unavailable(vault)
    if reason is not None:
        raise MeaningUnavailable(reason)
    result = MeaningResult(total=len(corpus))
    texts = {f"q{index_}": " ".join(str(query or "").split()) for index_, query in enumerate(queries)}
    texts = {key: text for key, text in texts.items() if text}
    if not corpus or not texts or limit <= 0:
        result.status = "empty"
        return result
    if index:
        ensure_vectors(vault, corpus, client_factory=(lambda: embedder) if embedder is not None else None,
                       repository=repository)
    model_id = vault.config.embedding.model
    covered = _covered(repository, model_id, corpus)

    result.covered = len(covered)
    if not covered:
        result.status, result.reason = "empty", "no note has a vector yet"
        return result
    # One query per request, each inside the library retrieval's own query caps (cached by text).
    vectors: dict[str, Any] = {}
    reasons: list[str] = []
    for key, text in texts.items():
        # The switches as they are now, before each query is embedded (Codex re-reviews C2b R3 F2, R4 F3).
        _now, why = _authorized_now(vault)
        if _now is None:
            raise MeaningUnavailable(why or "switched off")
        found, report = embed_query_texts(vault, repository, {key: text}, embedder=embedder, owner_id=owner_id)
        vectors.update(found)
        if not found:
            reasons.append(str(report.get("reason") or report.get("status") or ""))
    if not vectors:
        result.status, result.reason = "unavailable", "; ".join(dict.fromkeys(reasons)) or None
        return result
    by_key = {note.note_key: note for note in corpus}
    ordered: dict[str, VaultNote] = {}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for key in texts:
            vector = vectors.get(key)
            if vector is None:
                continue
            for match in retrieve(connection, record_kind=RECORD_KIND, field=RECORD_FIELD, model_id=model_id,
                                  task_prefix=TASK_PREFIX, query=vector, expected_records=covered, limit=limit):
                note = by_key.get(str(match.record_id))
                if note is not None:
                    ordered.setdefault(note.note_key, note)
                if len(ordered) >= limit:
                    break
            if len(ordered) >= limit:
                break
    result.notes = list(ordered.values())
    result.status = "ready" if len(covered) == len(corpus) else "partial"
    return result


__all__ = [
    "CAPTURE_TITLE",
    "KIND_ANNOTATION",
    "anchor_sources",
    "beside_protected",
    "protected_keys",
    "KIND_CAPTURE",
    "MODES",
    "MeaningResult",
    "MeaningUnavailable",
    "NOTE_CHARS",
    "NOTE_RECIPES",
    "ORIGIN",
    "RECIPE",
    "RECORD_KIND",
    "SEARCH_LIMIT",
    "VaultNote",
    "ensure_vectors",
    "meaning_available",
    "meaning_search",
    "meaning_unavailable",
    "note_key",
    "notes",
    "read",
    "read_many",
    "records",
    "recipe_text",
    "split_key",
    "words_search",
]
