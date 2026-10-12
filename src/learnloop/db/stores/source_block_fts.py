"""Keyword (FTS5 BM25) search over source blocks: ``source_block_fts`` (Slice 2 T6).

The index is DERIVED (migration 175): triggers keep it in step with
``source_document_blocks`` and :func:`rebuild_source_block_fts` is the body of
its single registered replayer. Nothing here calls a model or writes evidence.

Queries are never passed to FTS5 verbatim. :func:`match_expression` reduces
free text to quoted word tokens joined by ``OR`` (BM25 ranks documents by how
many and how rare the shared terms are), so learner punctuation, quotes or FTS
operators can never become query syntax or a syntax error.
"""
from __future__ import annotations

from collections.abc import Collection, Iterable
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


@dataclass(frozen=True)
class AssessmentLink:
    extraction_id: str | None
    locator: str
    source_id: str | None
    revision_id: str | None


def assessment_link_locators(connection: sqlite3.Connection) -> list[AssessmentLink]:
    """Every current assessment-lane provenance link (``exercise`` and
    ``assessment_alignment``), which never enters a teaching context (ING M8 §9.1).
    """

    return [AssessmentLink(None if row[0] is None else str(row[0]), str(row[1] or ""),
                           None if row[2] is None else str(row[2]),
                           None if row[3] is None else str(row[3]))
            for row in connection.execute(
        "SELECT extraction_id, locator, source_id, revision_id FROM entity_source_links "
        "WHERE relation IN ('exercise', 'assessment_alignment') "
        "AND (status IS NULL OR status = 'current') ORDER BY id",
    )]


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


def extraction_units(connection: sqlite3.Connection, extraction_id: str) -> list[UnitRow]:
    """One extraction's units in outline order (no block or asset read)."""

    units: list[UnitRow] = []
    for row in connection.execute(
        "SELECT unit_id, label, parent_unit_id, span_ids_json FROM source_document_units "
        "WHERE extraction_id = ? ORDER BY ordinal, unit_id", (extraction_id,),
    ):
        try:
            span_ids = json.loads(row[3] or "[]")
        except (TypeError, ValueError):
            span_ids = []
        units.append(UnitRow(str(row[0]), " ".join(str(row[1] or "").split()),
                             None if row[2] is None else str(row[2]),
                             tuple(str(span) for span in span_ids or [] if span is not None)))
    return units


#: Role hints that continue a solution's region (its body follows a short lead
#: block such as "Solution:"). Any other hint, or a section header, ends it.
_REGION_BODY_HINTS = frozenset({None, "", "ordinary_prose", "equation", "table", "figure"})
#: A region never runs past this many blocks after its lead.
MAX_REGION_BLOCKS = 20


def role_hint_spans(connection: sqlite3.Connection, extraction_ids: Iterable[str],
                    hints: Collection[str], *, region_hints: Collection[str] = ()) -> set[tuple[str, str]]:
    """Blocks whose ``role_hint`` is in ``hints``, within the given extractions.

    A block whose hint is in ``region_hints`` also takes the blocks after it,
    up to the next section header or structural hint (definition, theorem,
    another exercise, ...) and at most ``MAX_REGION_BLOCKS``: Marker gives the
    lead line ("Solution:") the hint and leaves the body that follows unhinted.
    """

    wanted = sorted({str(hint) for hint in hints if hint})
    ids = sorted({str(value) for value in extraction_ids if value})
    if not wanted or not ids:
        return set()
    marks = ", ".join("?" for _ in wanted)
    regions = {str(hint) for hint in region_hints}
    found: set[tuple[str, str]] = set()
    for start in range(0, len(ids), 500):
        chunk = ids[start:start + 500]
        hinted = connection.execute(
            f"SELECT DISTINCT extraction_id FROM source_document_blocks WHERE role_hint IN ({marks}) "
            f"AND extraction_id IN ({', '.join('?' for _ in chunk)}) ORDER BY extraction_id",
            (*wanted, *chunk),
        ).fetchall()
        for (extraction_id,) in hinted:
            open_region = 0
            for span_id, block_type, role_hint in connection.execute(
                "SELECT span_id, block_type, role_hint FROM source_document_blocks "
                "WHERE extraction_id = ? ORDER BY ordinal, span_id", (extraction_id,),
            ):
                if role_hint in wanted:
                    found.add((str(extraction_id), str(span_id)))
                    open_region = MAX_REGION_BLOCKS if role_hint in regions else 0
                elif open_region and block_type != "SectionHeader" and role_hint in _REGION_BODY_HINTS:
                    found.add((str(extraction_id), str(span_id)))
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
    "MAX_REGION_BLOCKS",
    "UnitRow",
    "assessment_link_locators",
    "blocks_by_key",
    "extraction_blocks",
    "extraction_fingerprint",
    "extraction_units",
    "EXCLUDED_BLOCK_TYPES",
    "MAX_QUERY_TERMS",
    "fts_drift",
    "indexed_block_count",
    "role_hint_spans",
    "source_extraction_ids",
    "section_header_titles",
    "match_expression",
    "query_terms",
    "rebuild_source_block_fts",
    "search_blocks",
]
