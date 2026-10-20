"""Keyword (FTS5 BM25) search over source blocks: ``source_block_fts`` (Slice 2 T6).

The index is DERIVED (migration 177): triggers keep it in step with
``source_document_blocks`` and :func:`rebuild_source_block_fts` is the body of
its single registered replayer. Nothing here calls a model or writes evidence.

Queries are never passed to FTS5 verbatim. :func:`match_expression` reduces
free text to quoted word tokens joined by ``OR`` (BM25 ranks documents by how
many and how rare the shared terms are), so learner punctuation, quotes or FTS
operators can never become query syntax or a syntax error.
"""
from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
import json
import re
import sqlite3
import unicodedata

#: Page furniture the library search has always skipped; never indexed.
EXCLUDED_BLOCK_TYPES = ("PageHeader", "PageFooter", "TableOfContents")
#: At most this many distinct terms reach one MATCH expression.
MAX_QUERY_TERMS = 32

_WORD = re.compile(r"[^\W_]+", re.UNICODE)
# Function words that would match nearly every block and only slow the query.
_STOPWORDS = frozenset("""
a about an and are as at be by can could did do does for from had has have how
i if in into is it its me my of on or our so than that the their them then there
these they this to was we were what when where which who why will with would you
your
""".split())


@dataclass(frozen=True)
class BlockMatch:
    extraction_id: str
    span_id: str
    #: FTS5 ``bm25()``: more negative is better. Only its order is used.
    score: float


def query_terms(text: str) -> list[str]:
    """Distinct lowercased word tokens of ``text`` in order, stopwords removed."""

    normalized = unicodedata.normalize("NFKC", text or "").lower()
    terms: list[str] = []
    for token in _WORD.findall(normalized):
        if token in _STOPWORDS or token in terms:
            continue
        terms.append(token)
        if len(terms) >= MAX_QUERY_TERMS:
            break
    return terms


def match_expression(text: str, *, prefix_last: bool = False) -> str | None:
    """A safe FTS5 MATCH expression for free text, or ``None`` when it has no terms.

    Every term is double-quoted (an FTS5 string, so operators are inert) and the
    terms are ORed. ``prefix_last`` makes the final term a prefix query, for a
    search box that runs while the learner is still typing a word.
    """

    terms = query_terms(text)
    if not terms:
        return None
    quoted = ['"' + term.replace('"', '""') + '"' for term in terms]
    if prefix_last and len(terms[-1]) >= 3:
        quoted[-1] += "*"
    return " OR ".join(quoted)


def search_blocks(
    connection: sqlite3.Connection,
    text: str,
    *,
    extraction_ids: Collection[str] | None = None,
    limit: int = 200,
    prefix_last: bool = False,
) -> list[BlockMatch]:
    """BM25-ranked blocks for ``text``, best first, optionally within extractions.

    An empty extraction scope or a query without terms returns ``[]``. Ties keep
    a deterministic order (extraction, then span id).
    """

    expression = match_expression(text, prefix_last=prefix_last)
    if expression is None or limit <= 0:
        return []
    params: list[object] = [expression]
    scope = ""
    if extraction_ids is not None:
        ids = sorted({str(value) for value in extraction_ids if value})
        if not ids:
            return []
        scope = f" AND extraction_id IN ({', '.join('?' for _ in ids)})"
        params.extend(ids)
    params.append(int(limit))
    rows = connection.execute(
        "SELECT extraction_id, span_id, bm25(source_block_fts) AS score "
        "FROM source_block_fts WHERE source_block_fts MATCH ?" + scope
        + " ORDER BY score, extraction_id, span_id LIMIT ?",
        params,
    ).fetchall()
    return [BlockMatch(str(row[0]), str(row[1]), float(row[2])) for row in rows]


def rebuild_source_block_fts(connection: sqlite3.Connection) -> dict[str, int]:
    """Replace the whole index from ``source_document_blocks`` (the replayer body).

    Runs inside the caller's transaction; deterministic for a given block
    ledger. Returns the cleared and written row counts.
    """

    cleared = int(connection.execute("SELECT COUNT(*) FROM source_block_fts").fetchone()[0])
    connection.execute("DELETE FROM source_block_fts")
    marks = ", ".join("?" for _ in EXCLUDED_BLOCK_TYPES)
    cursor = connection.execute(
        "INSERT INTO source_block_fts(rowid, text, extraction_id, span_id) "
        "SELECT rowid, text, extraction_id, span_id FROM source_document_blocks "
        f"WHERE block_type NOT IN ({marks}) ORDER BY rowid",
        EXCLUDED_BLOCK_TYPES,
    )
    return {"cleared": cleared, "written": int(cursor.rowcount if cursor.rowcount >= 0 else 0)}


@dataclass(frozen=True)
class BlockRow:
    extraction_id: str
    span_id: str
    block_type: str
    text: str
    page: int | None
    section_path_json: str | None
    ordinal: int
    extractor_block_id: str | None = None


_BLOCK_COLUMNS = ("extraction_id, span_id, block_type, text, page, section_path_json, ordinal, "
                  "extractor_block_id")


def _block(row) -> BlockRow:
    return BlockRow(str(row[0]), str(row[1]), str(row[2]), str(row[3] or ""),
                    None if row[4] is None else int(row[4]), row[5], int(row[6]),
                    None if row[7] is None else str(row[7]))


def section_header_titles(connection: sqlite3.Connection, extraction_id: str) -> dict[str, str]:
    """``{extractor block id: header text}`` of one extraction's section headers.

    Marker records a block's section path as its headers' block ids
    (``/page/16/SectionHeader/2``); this resolves them to their text.
    """

    return {str(row[0]): " ".join(str(row[1] or "").split()) for row in connection.execute(
        "SELECT extractor_block_id, text FROM source_document_blocks WHERE extraction_id = ? "
        "AND block_type = 'SectionHeader' AND extractor_block_id IS NOT NULL", (extraction_id,),
    ) if str(row[1] or "").strip()}


def extraction_blocks(connection: sqlite3.Connection, extraction_id: str) -> list[BlockRow]:
    """Every block of one extraction in document order (page furniture included)."""

    return [_block(row) for row in connection.execute(
        f"SELECT {_BLOCK_COLUMNS} FROM source_document_blocks WHERE extraction_id = ? "
        "ORDER BY ordinal, span_id", (extraction_id,),
    )]


def blocks_by_key(connection: sqlite3.Connection,
                  keys: Iterable[tuple[str, str]]) -> dict[tuple[str, str], BlockRow]:
    """The named blocks, keyed ``(extraction_id, span_id)``; missing keys are absent."""

    wanted: dict[str, set[str]] = {}
    for extraction_id, span_id in keys:
        wanted.setdefault(str(extraction_id), set()).add(str(span_id))
    found: dict[tuple[str, str], BlockRow] = {}
    for extraction_id, spans in sorted(wanted.items()):
        ordered = sorted(spans)
        for start in range(0, len(ordered), 500):
            chunk = ordered[start:start + 500]
            for row in connection.execute(
                f"SELECT {_BLOCK_COLUMNS} FROM source_document_blocks WHERE extraction_id = ? "
                f"AND span_id IN ({', '.join('?' for _ in chunk)})", (extraction_id, *chunk),
            ):
                block = _block(row)
                found[(block.extraction_id, block.span_id)] = block
    return found


def extraction_fingerprint(connection: sqlite3.Connection, extraction_id: str) -> tuple[int, int]:
    """``(block count, max rowid)``: changes whenever a run's blocks are replaced."""

    row = connection.execute(
        "SELECT COUNT(*), COALESCE(MAX(rowid), 0) FROM source_document_blocks WHERE extraction_id = ?",
        (extraction_id,),
    ).fetchone()
    return int(row[0]), int(row[1])


def extraction_fingerprints(connection: sqlite3.Connection,
                            extraction_ids: Iterable[str]) -> dict[str, tuple[int, int]]:
    """:func:`extraction_fingerprint` of many extractions in one grouped query
    (an extraction without blocks is ``(0, 0)``)."""

    ids = sorted({str(value) for value in extraction_ids if value})
    found = {extraction_id: (0, 0) for extraction_id in ids}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for extraction_id, count, max_rowid in connection.execute(
            "SELECT extraction_id, COUNT(*), COALESCE(MAX(rowid), 0) FROM source_document_blocks "
            f"WHERE extraction_id IN ({', '.join('?' for _ in chunk)}) GROUP BY extraction_id", chunk,
        ):
            found[str(extraction_id)] = (int(count), int(max_rowid))
    return found


@dataclass(frozen=True)
class AssessmentLink:
    """Where one provenance link points: its extraction, locator, source, revision."""

    extraction_id: str | None
    locator: str
    source_id: str | None
    revision_id: str | None


def _link(row) -> AssessmentLink:
    return AssessmentLink(None if row[0] is None else str(row[0]), str(row[1] or ""),
                          None if row[2] is None else str(row[2]),
                          None if row[3] is None else str(row[3]))


def assessment_link_locators(connection: sqlite3.Connection) -> list[AssessmentLink]:
    """Every current assessment-lane provenance link (``exercise`` and
    ``assessment_alignment``), which never enters a teaching context (ING M8 §9.1).
    """

    return [_link(row) for row in connection.execute(
        "SELECT extraction_id, locator, source_id, revision_id FROM entity_source_links "
        "WHERE relation IN ('exercise', 'assessment_alignment') "
        "AND (status IS NULL OR status = 'current') ORDER BY id",
    )]


def entity_link_locators(connection: sqlite3.Connection, entity_type: str,
                         entity_id: str) -> list[AssessmentLink]:
    """Every provenance link of one entity, whatever its relation or status."""

    return [_link(row) for row in connection.execute(
        "SELECT extraction_id, locator, source_id, revision_id FROM entity_source_links "
        "WHERE entity_type = ? AND entity_id = ? ORDER BY id", (entity_type, entity_id),
    )]


#: Entities whose ``primary`` / ``support`` / ``alternate`` provenance vouches
#: for a source as teaching material (what synthesis grounded them on).
TEACHING_LINK_ENTITY_TYPES = ("learning_object", "facet", "concept")


def teaching_link_locators(connection: sqlite3.Connection) -> list[AssessmentLink]:
    """Every current teaching-relation link of a learning object, facet or concept."""

    marks = ", ".join("?" for _ in TEACHING_LINK_ENTITY_TYPES)
    return [_link(row) for row in connection.execute(
        "SELECT extraction_id, locator, source_id, revision_id FROM entity_source_links "
        "WHERE relation IN ('primary', 'support', 'alternate') "
        f"AND entity_type IN ({marks}) AND (status IS NULL OR status = 'current') ORDER BY id",
        TEACHING_LINK_ENTITY_TYPES,
    )]


def revision_source_ids(connection: sqlite3.Connection, revision_ids: Iterable[str]) -> dict[str, str]:
    """``{revision id: source id}`` for the given revisions."""

    ids = sorted({str(value) for value in revision_ids if value})
    found: dict[str, str] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for revision_id, source_id in connection.execute(
            f"SELECT id, source_id FROM source_revisions WHERE id IN ({', '.join('?' for _ in chunk)})", chunk,
        ):
            found[str(revision_id)] = str(source_id)
    return found


def extraction_source_ids(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> dict[str, str]:
    """``{extraction id: source id}`` through each run's revision."""

    ids = sorted({str(value) for value in extraction_ids if value})
    found: dict[str, str] = {}
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        for extraction_id, source_id in connection.execute(
            "SELECT run.id, revision.source_id FROM source_extraction_runs AS run "
            "JOIN source_revisions AS revision ON revision.id = run.revision_id "
            f"WHERE run.id IN ({', '.join('?' for _ in chunk)})", chunk,
        ):
            found[str(extraction_id)] = str(source_id)
    return found


def existing_spans(connection: sqlite3.Connection,
                   keys: Iterable[tuple[str, str]]) -> set[tuple[str, str]]:
    """Which of ``keys`` (extraction, span) name a block that exists: keys
    only, never a block's text (RW4d fix round 5: a comparison's contributors
    are resolved before its protection is checked)."""

    wanted = sorted({(str(key[0]), str(key[1])) for key in keys if key and key[0] and key[1]})
    by_reading: dict[str, list[str]] = {}
    for extraction_id, span_id in wanted:
        by_reading.setdefault(extraction_id, []).append(span_id)
    found: set[tuple[str, str]] = set()
    for extraction_id, span_ids in by_reading.items():
        for start in range(0, len(span_ids), 500):
            chunk = span_ids[start:start + 500]
            found.update((extraction_id, str(row[0])) for row in connection.execute(
                "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? "
                f"AND span_id IN ({', '.join('?' for _ in chunk)})", (extraction_id, *chunk)))
    return found


def spans_with_content_hashes(connection: sqlite3.Connection, extraction_id: str,
                              content_hashes: Collection[str]) -> list[str]:
    """Span ids of one extraction's blocks whose text hashes to one of ``content_hashes``."""

    hashes = sorted({str(value) for value in content_hashes if value})
    found: list[str] = []
    for start in range(0, len(hashes), 500):
        chunk = hashes[start:start + 500]
        found.extend(str(row[0]) for row in connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = ? "
            f"AND content_hash IN ({', '.join('?' for _ in chunk)}) ORDER BY ordinal, span_id",
            (extraction_id, *chunk),
        ))
    return found


def block_content_hashes(connection: sqlite3.Connection, extraction_id: str,
                         span_ids: Collection[str]) -> list[str]:
    """The content hashes of the named blocks of one extraction."""

    ids = sorted({str(value) for value in span_ids if value})
    found: list[str] = []
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        found.extend(str(row[0]) for row in connection.execute(
            "SELECT content_hash FROM source_document_blocks WHERE extraction_id = ? "
            f"AND span_id IN ({', '.join('?' for _ in chunk)}) AND content_hash IS NOT NULL",
            (extraction_id, *chunk),
        ))
    return found


def source_extraction_ids(connection: sqlite3.Connection, *, source_id: str | None = None,
                          revision_id: str | None = None) -> list[str]:
    """Every extraction run of a source (all its revisions), or of one revision."""

    if source_id:
        rows = connection.execute(
            "SELECT run.id FROM source_extraction_runs AS run "
            "JOIN source_revisions AS revision ON revision.id = run.revision_id "
            "WHERE revision.source_id = ? ORDER BY run.created_at, run.id", (source_id,))
    elif revision_id:
        rows = connection.execute(
            "SELECT id FROM source_extraction_runs WHERE revision_id = ? ORDER BY created_at, id",
            (revision_id,))
    else:
        return []
    return [str(row[0]) for row in rows]


@dataclass(frozen=True)
class UnitRow:
    unit_id: str
    label: str
    parent_unit_id: str | None
    span_ids: tuple[str, ...]
    #: The unit's content hash (``ingest.hashing.semantic_hash``).
    semantic_hash: str = ""


def extraction_units(connection: sqlite3.Connection, extraction_id: str) -> list[UnitRow]:
    """One extraction's units in outline order (no block or asset read)."""

    units: list[UnitRow] = []
    for row in connection.execute(
        "SELECT unit_id, label, parent_unit_id, span_ids_json, semantic_hash FROM source_document_units "
        "WHERE extraction_id = ? ORDER BY ordinal, unit_id", (extraction_id,),
    ):
        try:
            span_ids = json.loads(row[3] or "[]")
        except (TypeError, ValueError):
            span_ids = []
        units.append(UnitRow(str(row[0]), " ".join(str(row[1] or "").split()),
                             None if row[2] is None else str(row[2]),
                             tuple(str(span) for span in span_ids or [] if span is not None),
                             str(row[4] or "")))
    return units


#: Role hints that continue a lead's region (a solution's or worked example's
#: body follows a short lead block such as "Solution:"). Any other hint, or a
#: section header, ends it.
REGION_BODY_HINTS = frozenset({None, "", "ordinary_prose", "equation", "table", "figure"})
#: A region never runs past this many blocks after its lead.
MAX_REGION_BLOCKS = 20


@dataclass(frozen=True)
class HintRow:
    """One block's role-hint facts, in document order."""

    extraction_id: str
    span_id: str
    block_type: str
    role_hint: str | None
    text: str
    section_path_json: str | None

    @property
    def key(self) -> tuple[str, str]:
        return (self.extraction_id, self.span_id)


def hinted_extraction_ids(connection: sqlite3.Connection, extraction_ids: Iterable[str],
                          hints: Collection[str]) -> list[str]:
    """The given extractions that have at least one block hinted with ``hints``."""

    wanted = sorted({str(hint) for hint in hints if hint})
    ids = sorted({str(value) for value in extraction_ids if value})
    if not wanted or not ids:
        return []
    marks = ", ".join("?" for _ in wanted)
    found: list[str] = []
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        found.extend(str(row[0]) for row in connection.execute(
            f"SELECT DISTINCT extraction_id FROM source_document_blocks WHERE role_hint IN ({marks}) "
            f"AND extraction_id IN ({', '.join('?' for _ in chunk)}) ORDER BY extraction_id",
            (*wanted, *chunk),
        ))
    return found


def extraction_hint_rows(connection: sqlite3.Connection, extraction_id: str) -> list[HintRow]:
    """One extraction's blocks in document order, with what role hinting reads."""

    return [HintRow(str(extraction_id), str(row[0]), str(row[1]), None if row[2] is None else str(row[2]),
                    str(row[3] or ""), row[4])
            for row in connection.execute(
        "SELECT span_id, block_type, role_hint, text, section_path_json FROM source_document_blocks "
        "WHERE extraction_id = ? ORDER BY ordinal, span_id", (extraction_id,),
    )]


#: What :func:`lead_regions` does with one block: ``region`` (take it and open
#: a region after it), ``block`` (take it alone), ``body`` (taken only inside an
#: open region) or ``stop`` (closes any open region).
RegionMark = str


def lead_regions(rows: Iterable[HintRow], mark: Callable[[HintRow], RegionMark]) -> set[tuple[str, str]]:
    """The blocks ``mark`` takes, plus each region's body.

    A region takes the ``body`` blocks after its lead, up to the next section
    header or ``stop`` block and at most ``MAX_REGION_BLOCKS``: Marker gives a
    lead line ("Solution:", "Example 5.2") the hint and leaves the body that
    follows unhinted.
    """

    found: set[tuple[str, str]] = set()
    open_region = 0
    for row in rows:
        kind = mark(row)
        if kind in ("region", "block"):
            found.add(row.key)
            open_region = MAX_REGION_BLOCKS if kind == "region" else 0
        elif kind == "body" and open_region and row.block_type != "SectionHeader":
            found.add(row.key)
            open_region -= 1
        else:
            open_region = 0
    return found


def fts_drift(connection: sqlite3.Connection) -> dict[str, int]:
    """How far ``source_block_fts`` has drifted from ``source_document_blocks``.

    ``stale``: index rows whose rowid no longer names the same block (a block
    deleted while the triggers were missing, or rowids renumbered by a table
    rebuild); ``missing``: indexable blocks without their own index row. Both
    are zero for an index the triggers (or the replayer) maintain.
    """

    marks = ", ".join("?" for _ in EXCLUDED_BLOCK_TYPES)
    stale = connection.execute(
        "SELECT COUNT(*) FROM source_block_fts AS f LEFT JOIN source_document_blocks AS b "
        "ON b.rowid = f.rowid AND b.extraction_id = f.extraction_id AND b.span_id = f.span_id "
        "WHERE b.rowid IS NULL",
    ).fetchone()[0]
    missing = connection.execute(
        "SELECT COUNT(*) FROM source_document_blocks AS b LEFT JOIN source_block_fts AS f "
        "ON f.rowid = b.rowid AND f.extraction_id = b.extraction_id AND f.span_id = b.span_id "
        f"WHERE b.block_type NOT IN ({marks}) AND f.rowid IS NULL",
        EXCLUDED_BLOCK_TYPES,
    ).fetchone()[0]
    return {"stale": int(stale), "missing": int(missing)}


def indexed_block_count(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> int:
    ids = sorted({str(value) for value in extraction_ids if value})
    if not ids:
        return 0
    return int(connection.execute(
        f"SELECT COUNT(*) FROM source_block_fts WHERE extraction_id IN ({', '.join('?' for _ in ids)})",
        ids,
    ).fetchone()[0])


__all__ = [
    "AssessmentLink",
    "BlockMatch",
    "BlockRow",
    "EXCLUDED_BLOCK_TYPES",
    "HintRow",
    "MAX_QUERY_TERMS",
    "MAX_REGION_BLOCKS",
    "REGION_BODY_HINTS",
    "TEACHING_LINK_ENTITY_TYPES",
    "UnitRow",
    "assessment_link_locators",
    "block_content_hashes",
    "blocks_by_key",
    "entity_link_locators",
    "extraction_blocks",
    "extraction_fingerprint",
    "extraction_fingerprints",
    "extraction_hint_rows",
    "extraction_source_ids",
    "extraction_units",
    "fts_drift",
    "hinted_extraction_ids",
    "indexed_block_count",
    "lead_regions",
    "match_expression",
    "query_terms",
    "rebuild_source_block_fts",
    "revision_source_ids",
    "search_blocks",
    "section_header_titles",
    "source_extraction_ids",
    "spans_with_content_hashes",
    "teaching_link_locators",
]
