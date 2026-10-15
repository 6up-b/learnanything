"""The one alias authority for a book read again (re-read safety, 2026-10-14).

A book read again (text recognition, another engine, the same pages) gets a new
top-level reading on the same revision, with its own span ids: ``s57`` in the
new reading is not ``s57`` in the old one. Everything that names a span of the
old reading (LO, facet and item links, YAML source refs, source-object
citations, annotations, the saved reading place) is resolved through this
module and nowhere else:

* the aliases are ``reanchor_spans`` (spec_source_ingestion_v2 §2.4), persisted
  in ``source_span_reanchors`` when a re-read completes
  (:func:`record_aliases`); a pair of readings of one source with no persisted
  aliases (a re-read made before this module) is computed here, in memory,
  never written from a read path;
* an exact content-hash alias (or a learner's manual one) is the same text:
  the reference resolves there, ``current``;
* a geometry/section alias is the same place with changed text:
  ``needs_reanchor``, shown flagged, never as if it were the cited text;
* no alias at all: ``stale``, with no span. Never "the current reading + the
  old span id" (the GLM-OCR live check found 7/7 and 13/13 citations resolving
  to other blocks that way);
* protection (exam and held-out material) never takes an approximate alias
  as the whole answer: :class:`SpanCarrier` carries a protected span to every
  block that may hold its words, verified, or to nothing (the caller then
  protects the whole reading; Codex re-review F1, F2).

A reference is resolved against the reading it was made on first: a link's
locator names its extraction; a source-object citation names a revision and is
pinned to a reading by its ``block_content_hash`` when recorded, else by the
reading that was current on that revision when it was made
(:func:`cited_reading`; when it was made is its first copy's time,
:data:`CITATION_MADE_AT_SQL`).
"""

from __future__ import annotations

import re
import threading
from collections import OrderedDict
from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock
from learnloop.db.connection import connect
from learnloop.ingest.reanchor import EXACT_HASH, MANUAL, reanchor_spans

STATUS_CURRENT = "current"
STATUS_NEEDS_REANCHOR = "needs_reanchor"
STATUS_STALE = "stale"

#: Match kinds that name the same text (the rest name the same place only).
SAME_TEXT_KINDS = frozenset({EXACT_HASH, MANUAL})

SpanKey = tuple[str, str]
_Alias = tuple[str, str, float | None]  # (to span, match kind, confidence)


@dataclass(frozen=True)
class SpanResolution:
    """Where one span of one reading lands in another reading of its book."""

    from_extraction_id: str
    from_span_id: str
    extraction_id: str
    span_id: str | None
    status: str
    match_kind: str | None = None

    @property
    def exact(self) -> bool:
        return self.status == STATUS_CURRENT and self.span_id is not None

    @property
    def key(self) -> SpanKey | None:
        return (self.extraction_id, self.span_id) if self.span_id is not None else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "from_extraction_id": self.from_extraction_id,
            "from_span_id": self.from_span_id,
            "extraction_id": self.extraction_id,
            "span_id": self.span_id,
            "status": self.status,
            "match_kind": self.match_kind,
        }


# --- readings ---------------------------------------------------------------------------


def completed_readings(repository: Any, revision_id: str) -> list[dict[str, Any]]:
    """The revision's completed top-level readings, oldest first."""

    return [
        run
        for run in repository.extraction_runs_for_revision(revision_id)
        if run.get("status") == "completed" and run.get("parent_extraction_id") is None
    ]


def source_readings(repository: Any, source_id: str) -> list[dict[str, Any]]:
    """Every completed top-level reading of a source, oldest first."""

    readings: list[dict[str, Any]] = []
    for revision in repository.source_revisions_for(source_id):
        readings.extend(completed_readings(repository, str(revision["id"])))
    return sorted(readings, key=lambda run: (str(run.get("completed_at") or run.get("created_at") or ""),
                                             str(run["id"])))


def current_reading(repository: Any, source_id: str) -> str | None:
    """The reading the Reader opens for a source (its current revision's latest)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id

    return resolve_extraction_id(repository, source_id)


def reading_source(repository: Any, extraction_id: str) -> str | None:
    run = repository.get_extraction_run(extraction_id)
    if run is None:
        return None
    revision = repository.get_source_revision(str(run.get("revision_id") or ""))
    return str(revision["source_id"]) if revision else None


def previous_readings(repository: Any, extraction_id: str) -> list[str]:
    """The completed top-level readings of the same revision made before
    ``extraction_id``, newest first: what a re-read's references were made on."""

    run = repository.get_extraction_run(extraction_id)
    if run is None or run.get("parent_extraction_id") is not None:
        return []
    earlier: list[str] = []
    for other in completed_readings(repository, str(run["revision_id"])):
        if other["id"] == extraction_id:
            break
        earlier.append(str(other["id"]))
    return list(reversed(earlier))


def other_readings(repository: Any, extraction_id: str) -> list[str]:
    """Every other completed top-level reading of the reading's book, newest
    first: its reading history, whether or not any alias was recorded
    (a re-read made before aliases were, or one that matched nothing)."""

    source_id = reading_source(repository, extraction_id)
    if source_id is None:
        return []
    return [str(run["id"]) for run in reversed(source_readings(repository, source_id))
            if str(run["id"]) != str(extraction_id)]


def legacy_place_origin(repository: Any, extraction_id: str) -> str | None:
    """The reading a bare span id names when it was saved before places
    recorded their reading (the desktop's ``localStorage``), for a book whose
    Reader now opens ``extraction_id``; ``None`` when that is unknown, and the
    place is then never read as a span of this reading (Codex review F5).

    Known only when one reading can have held it: the book was never read
    again (this reading), or it has exactly one other reading, an earlier one
    of the same revision from which this reading's aliases were recorded (so
    this reading was made by a build that saves every place with its reading:
    the bare place is older than it)."""

    others = other_readings(repository, extraction_id)
    if not others:
        return str(extraction_id)
    if len(others) == 1 and others == previous_readings(repository, extraction_id) \
            and repository.span_reanchors_between(others[0], extraction_id):
        return others[0]
    return None


# --- aliases ----------------------------------------------------------------------------


_MEMO_LIMIT = 64
_memo: OrderedDict[tuple[str, str, str], dict[str, _Alias]] = OrderedDict()
_memo_lock = threading.Lock()


def _memo_key(repository: Any, from_extraction_id: str, to_extraction_id: str) -> tuple[str, str, str]:
    return (str(getattr(repository, "sqlite_path", "")), from_extraction_id, to_extraction_id)


def _computed(repository: Any, from_extraction_id: str, to_extraction_id: str) -> dict[str, _Alias]:
    """Aliases computed in memory for two completed readings of one source.

    A completed reading's IR never changes, so the result is kept (bounded)."""

    key = _memo_key(repository, from_extraction_id, to_extraction_id)
    with _memo_lock:
        if key in _memo:
            _memo.move_to_end(key)
            return _memo[key]
    found: dict[str, _Alias] = {}
    source = reading_source(repository, from_extraction_id)
    from_run = repository.get_extraction_run(from_extraction_id) or {}
    to_run = repository.get_extraction_run(to_extraction_id) or {}
    if (
        source is not None
        and source == reading_source(repository, to_extraction_id)
        and from_run.get("status") == "completed"
        and to_run.get("status") == "completed"
    ):
        from_ir = repository.load_document_ir(from_extraction_id)
        to_ir = repository.load_document_ir(to_extraction_id)
        if from_ir is not None and to_ir is not None:
            result = reanchor_spans(from_ir, to_ir)
            found = {alias.from_span_id: (alias.to_span_id, alias.match_kind, alias.confidence)
                     for alias in result.aliases}
    with _memo_lock:
        _memo[key] = found
        while len(_memo) > _MEMO_LIMIT:
            _memo.popitem(last=False)
    return found


def alias_map(repository: Any, from_extraction_id: str, to_extraction_id: str) -> dict[str, _Alias]:
    """``{old span: (new span, match kind, confidence)}`` from one reading to another:
    the persisted aliases, else (none recorded) the same computation in memory."""

    rows = repository.span_reanchors_between(from_extraction_id, to_extraction_id)
    if rows:
        return {str(row["from_span_id"]): (str(row["to_span_id"]), str(row["match_kind"]), row.get("confidence"))
                for row in rows}
    return _computed(repository, from_extraction_id, to_extraction_id)


def record_aliases(repository: Any, from_extraction_id: str, to_extraction_id: str, *,
                   clock: Clock | None = None) -> dict[str, int]:
    """Re-anchor every span of ``from`` onto ``to`` and persist the aliases."""

    from_ir = repository.load_document_ir(from_extraction_id)
    to_ir = repository.load_document_ir(to_extraction_id)
    if from_ir is None or to_ir is None:
        return {"exact": 0, "moved": 0, "unmatched": 0}
    result = reanchor_spans(from_ir, to_ir)
    repository.record_span_reanchors(
        from_extraction_id, to_extraction_id,
        [(alias.from_span_id, alias.to_span_id, alias.match_kind, alias.confidence) for alias in result.aliases],
        clock=clock,
    )
    with _memo_lock:
        _memo.pop(_memo_key(repository, from_extraction_id, to_extraction_id), None)
    exact = sum(1 for alias in result.aliases if alias.match_kind in SAME_TEXT_KINDS)
    return {"exact": exact, "moved": len(result.aliases) - exact, "unmatched": len(result.needs_reanchor)}


class SpanTranslator:
    """Resolves spans of any reading of a book onto one target reading."""

    def __init__(self, repository: Any, to_extraction_id: str) -> None:
        self.repository = repository
        self.to_extraction_id = str(to_extraction_id)
        self._maps: dict[str, dict[str, _Alias]] = {}

    def aliases_from(self, from_extraction_id: str) -> dict[str, _Alias]:
        if from_extraction_id not in self._maps:
            self._maps[from_extraction_id] = alias_map(self.repository, from_extraction_id, self.to_extraction_id)
        return self._maps[from_extraction_id]

    def resolve(self, from_extraction_id: str, span_id: str) -> SpanResolution:
        from_extraction_id, span_id = str(from_extraction_id), str(span_id)
        if from_extraction_id == self.to_extraction_id:
            return SpanResolution(from_extraction_id, span_id, self.to_extraction_id, span_id, STATUS_CURRENT)
        hit = self.aliases_from(from_extraction_id).get(span_id)
        if hit is None:
            return SpanResolution(from_extraction_id, span_id, self.to_extraction_id, None, STATUS_STALE)
        to_span, kind, _confidence = hit
        status = STATUS_CURRENT if kind in SAME_TEXT_KINDS else STATUS_NEEDS_REANCHOR
        return SpanResolution(from_extraction_id, span_id, self.to_extraction_id, to_span, status, kind)


def resolve_span(repository: Any, from_extraction_id: str, span_id: str, to_extraction_id: str) -> SpanResolution:
    return SpanTranslator(repository, to_extraction_id).resolve(from_extraction_id, span_id)


# --- protection: where protected words may lie on another reading -----------------------

_NOT_WORD = re.compile(r"[\W_]+")
#: A block with at most this many letters and digits is a heading, a page
#: number or a running head: what a re-read may put between the parts of a
#: split passage (a passage that runs over a page). Verification may skip it.
_FURNITURE_WORDS = 40


def _words(text: Any) -> str:
    """A block's letters and digits, case-folded: what a split, a merge or
    another segmentation of the same words keeps."""

    return _NOT_WORD.sub("", str(text or "").casefold())


@dataclass(frozen=True)
class _Layout:
    """One reading's blocks in reading order, with their words."""

    order: tuple[str, ...]
    index: Mapping[str, int]
    words: tuple[str, ...]


class SpanCarrier:
    """Carries protected spans (exam and held-out material) from one reading
    of a book onto another (Codex re-review F1, F2).

    :class:`SpanTranslator` answers one span for one span, for display; a
    split, a merge or a re-segmentation can put a protected passage's words in
    several blocks, so protection asks for *every* block of the other reading
    that may hold them, or ``None`` when that can't be verified (the caller
    then protects the whole reading):

    * a same-text alias carries a span to its block (the same words);
    * any other span (the same place with other words, a split, a merge, no
      alias at all) lies in the stretch of the other reading between the
      images of the nearest same-text anchors around it. The whole stretch is
      carried, with the span's own alias, when it is verified: the anchors
      keep their order there, and the stretch holds the span's words (its
      letters and digits, running on in order: every part of a split, the
      whole of a merge), with or without the stretch's short blocks (a
      heading, a page number or a running head the re-read put between the
      parts; a long block never). A span whose words changed, or moved past
      an anchor, or with no anchor on either side (it could be anywhere),
      can't be followed: ``None``.

    For a scope's unit or a held-out mark's spans, every span is carried this
    way, so a unit whose re-read words changed anywhere withholds the whole
    reading: over-protective, never released (open question 2's default).
    """

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self._layouts: dict[str, _Layout | None] = {}
        self._maps: dict[tuple[str, str], dict[str, _Alias]] = {}
        self._bounds: dict[tuple[str, str], tuple[list[int], list[int]]] = {}
        self._stretches: dict[tuple[str, int, int], tuple[str, str]] = {}

    def _layout(self, extraction_id: str) -> _Layout | None:
        if extraction_id not in self._layouts:
            ir = self.repository.load_document_ir(extraction_id)
            if ir is None:
                self._layouts[extraction_id] = None
            else:
                blocks = sorted(ir.blocks, key=lambda block: (block.ordinal, block.span_id))
                order = tuple(str(block.span_id) for block in blocks)
                self._layouts[extraction_id] = _Layout(
                    order, {span: position for position, span in enumerate(order)},
                    tuple(_words(block.text) for block in blocks))
        return self._layouts[extraction_id]

    def _aliases(self, from_extraction_id: str, to_extraction_id: str) -> dict[str, _Alias]:
        key = (from_extraction_id, to_extraction_id)
        if key not in self._maps:
            self._maps[key] = alias_map(self.repository, from_extraction_id, to_extraction_id)
        return self._maps[key]

    def _anchors(self, key: tuple[str, str], source: _Layout, target: _Layout,
                 same: Mapping[str, str]) -> tuple[list[int], list[int]]:
        """For each source position, the target positions of the nearest
        same-text anchors before and after it (-1 and the end when none)."""

        if key not in self._bounds:
            image = [target.index.get(same[span]) if span in same else None for span in source.order]
            before, after = [-1] * len(image), [len(target.order)] * len(image)
            last = -1
            for position, landed in enumerate(image):
                before[position] = last
                if landed is not None:
                    last = landed
            last = len(target.order)
            for position in range(len(image) - 1, -1, -1):
                after[position] = last
                if image[position] is not None:
                    last = image[position]
            self._bounds[key] = (before, after)
        return self._bounds[key]

    def _stretch(self, to_extraction_id: str, target: _Layout, low: int, high: int) -> tuple[str, str]:
        """The words of the target's blocks strictly between ``low`` and
        ``high``: all of them, and the long ones only (short blocks skipped)."""

        key = (to_extraction_id, low, high)
        if key not in self._stretches:
            words = target.words[low + 1:high]
            self._stretches[key] = ("".join(words),
                                    "".join(word for word in words if len(word) > _FURNITURE_WORDS))
        return self._stretches[key]

    def carry(self, from_extraction_id: str, span_ids: Any, to_extraction_id: str) -> frozenset[str] | None:
        """Every span of ``to`` that may hold the words of ``span_ids`` of
        ``from``; ``None`` when that can't be verified."""

        source_id, target_id = str(from_extraction_id), str(to_extraction_id)
        wanted = {str(span) for span in span_ids if span}
        if source_id == target_id or not wanted:
            return frozenset(wanted)
        aliases = self._aliases(source_id, target_id)
        same = {span: hit[0] for span, hit in aliases.items() if hit[1] in SAME_TEXT_KINDS}
        landed = {same[span] for span in wanted if span in same}
        rest = wanted - same.keys()
        if not rest:
            return frozenset(landed)
        source, target = self._layout(source_id), self._layout(target_id)
        if source is None or target is None:
            return None
        bounds = self._anchors((source_id, target_id), source, target, same)
        for span in sorted(rest):
            position = source.index.get(span)
            if position is None:
                return None  # not a block of that reading: nothing places it
            before, after = bounds[0][position], bounds[1][position]
            if before >= after:
                return None  # the anchors around it are out of order there
            if before < 0 and after >= len(target.order):
                return None  # no anchor at all: anywhere in the reading
            words = source.words[position]
            if not any(words in stretch for stretch in self._stretch(target_id, target, before, after)):
                return None  # its words changed, or a part moved past an anchor
            landed.update(target.order[before + 1:after])
            hit = aliases.get(span)
            if hit is not None:
                landed.add(hit[0])
        return frozenset(landed)


class CurrentKeys:
    """Moves span keys onto their book's current reading when they match there
    exactly; any other key stays on the reading it was made on, whose text it
    still names (a reader scoped to current readings then drops it rather
    than show another block)."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self._current: dict[str, str | None] = {}
        self._source: dict[str, str | None] = {}
        self._translators: dict[str, SpanTranslator] = {}

    def current_of(self, extraction_id: str) -> str | None:
        if extraction_id not in self._source:
            self._source[extraction_id] = reading_source(self.repository, extraction_id)
        source = self._source[extraction_id]
        if source is None:
            return None
        if source not in self._current:
            self._current[source] = current_reading(self.repository, source)
        return self._current[source]

    def resolve(self, extraction_id: str, span_id: str) -> SpanResolution:
        current = self.current_of(str(extraction_id)) or str(extraction_id)
        if current not in self._translators:
            self._translators[current] = SpanTranslator(self.repository, current)
        return self._translators[current].resolve(str(extraction_id), str(span_id))

    def key(self, extraction_id: str, span_id: str) -> SpanKey:
        resolution = self.resolve(extraction_id, span_id)
        if resolution.exact and resolution.key is not None:
            return resolution.key
        return (str(extraction_id), str(span_id))


# --- citations --------------------------------------------------------------------------


def _block_hash(repository: Any, extraction_id: str, span_id: str) -> str | None:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = connection.execute(
            "SELECT content_hash FROM source_document_blocks WHERE extraction_id = ? AND span_id = ?",
            (extraction_id, span_id),
        ).fetchone()
    return str(row[0]) if row is not None and row[0] is not None else None


#: When a source-object citation was made, as SQL over ``source_object_citations AS c``
#: joined to its ``source_object_versions AS v``: the earliest copy of the same
#: citation (same object, ordinal, revision and span) across the object's
#: versions. A status-only review copies citations into a new version, which
#: before re-read safety's review stamped them with the review's time; a
#: citation with no block hash is pinned to its reading by when it was made,
#: so a copy reviewed after a re-read named the new reading (Codex review F3).
CITATION_MADE_AT_SQL = (
    "COALESCE((SELECT MIN(origin.created_at) FROM source_object_citations AS origin "
    "JOIN source_object_versions AS origin_version ON origin_version.id = origin.source_object_version_id "
    "WHERE origin_version.source_object_id = v.source_object_id AND origin.citation_ordinal = c.citation_ordinal "
    "AND origin.revision_id = c.revision_id AND origin.span_id = c.span_id), c.created_at)"
)


def cited_reading(repository: Any, *, revision_id: str, span_id: str, block_content_hash: str | None = None,
                  created_at: str | None = None) -> str | None:
    """The reading a source-object citation (revision + span) was made on.

    By its recorded block content hash when it has one (the reading whose block
    has that span and that hash, newest first); else the latest reading of the
    revision completed when the citation was made. ``None`` when nothing fits
    (the citation is then unresolved, never another block)."""

    readings = completed_readings(repository, str(revision_id))
    if not readings:
        return None
    if block_content_hash:
        for run in reversed(readings):
            if _block_hash(repository, str(run["id"]), str(span_id)) == block_content_hash:
                return str(run["id"])
        return None
    if created_at:
        made = [run for run in readings if str(run.get("completed_at") or run.get("created_at") or "") <= created_at]
        if made:
            return str(made[-1]["id"])
    return str(readings[0]["id"]) if len(readings) == 1 else None


class CitationResolver:
    """Source-object citations on their book's current reading (or flagged)."""

    def __init__(self, repository: Any) -> None:
        self.repository = repository
        self.keys = CurrentKeys(repository)

    def resolve(self, citation: Mapping[str, Any]) -> SpanResolution | None:
        """``None`` when the reading the citation was made on is unknown."""

        reading = cited_reading(
            self.repository, revision_id=str(citation.get("revision_id") or ""),
            span_id=str(citation.get("span_id") or ""),
            block_content_hash=citation.get("block_content_hash"), created_at=citation.get("created_at"),
        )
        if reading is None:
            return None
        return self.keys.resolve(reading, str(citation.get("span_id") or ""))

    def current_key(self, citation: Mapping[str, Any]) -> SpanKey | None:
        """The citation on its book's current reading when it matches exactly
        there, else on the reading it was made on (``None``: unknown reading)."""

        resolution = self.resolve(citation)
        if resolution is None:
            return None
        if resolution.exact and resolution.key is not None:
            return resolution.key
        return (resolution.from_extraction_id, resolution.from_span_id)


# --- locators ---------------------------------------------------------------------------

_BARE_SPAN = re.compile(r"^span:([^/]+)$")


def locator_key(repository: Any, *, revision_id: str | None, locator: str | None,
                created_at: str | None = None) -> SpanKey | None:
    """Where a ``span:`` locator opens: on its book's current reading when it
    matches exactly there, else on the reading it was made on (whose text it
    names). ``span:<extraction>/<span>`` names its reading; a bare
    ``span:<span>`` is read against ``revision_id`` like a citation
    (:func:`cited_reading`). ``None``: not a span locator, or its reading is
    unknown (then it is not opened, never opened on another block)."""

    from learnloop.ingest.locators import parse_block_span

    text = str(locator or "").strip()
    parsed = parse_block_span(text)
    if parsed is not None and repository.get_extraction_run(parsed[0]) is not None:
        return CurrentKeys(repository).key(*parsed)
    span_id = parsed[1] if parsed is not None else (match.group(1) if (match := _BARE_SPAN.match(text)) else None)
    if span_id is None or not revision_id:
        return None
    return CitationResolver(repository).current_key(
        {"revision_id": revision_id, "span_id": span_id, "created_at": created_at})


def is_span_locator(locator: str | None) -> bool:
    return str(locator or "").strip().startswith("span:")
