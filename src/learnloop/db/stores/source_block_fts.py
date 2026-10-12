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


def assessment_link_locators(connection: sqlite3.Connection) -> list[tuple[str | None, str]]:
    """``(extraction_id, locator)`` of every current assessment-lane provenance link.

    ``exercise`` and ``assessment_alignment`` links point at assessment material,
    which never enters a teaching context (ING M8 §9.1).
    """

    return [(None if row[0] is None else str(row[0]), str(row[1])) for row in connection.execute(
        "SELECT extraction_id, locator FROM entity_source_links "
        "WHERE relation IN ('exercise', 'assessment_alignment') "
        "AND (status IS NULL OR status = 'current') ORDER BY id",
    )]


def indexed_block_count(connection: sqlite3.Connection, extraction_ids: Iterable[str]) -> int:
    ids = sorted({str(value) for value in extraction_ids if value})
    if not ids:
        return 0
    return int(connection.execute(
        f"SELECT COUNT(*) FROM source_block_fts WHERE extraction_id IN ({', '.join('?' for _ in ids)})",
        ids,
    ).fetchone()[0])


__all__ = [
    "BlockMatch",
    "BlockRow",
    "assessment_link_locators",
    "blocks_by_key",
    "extraction_blocks",
    "extraction_fingerprint",
    "EXCLUDED_BLOCK_TYPES",
    "MAX_QUERY_TERMS",
    "indexed_block_count",
    "section_header_titles",
    "match_expression",
    "query_terms",
    "rebuild_source_block_fts",
    "search_blocks",
]
