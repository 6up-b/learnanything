"""Readings built as production builds them, and the row-deletion oracle (the AD23 redesign round 8,
Option B).

Option B's contract: a reading that holds any withheld block is ABSENT for AD's reading signals.
Its oracle is exact and needs no model of extraction: :func:`delete_reading`, the same vault with
that reading's blocks, units, assets and reading events deleted (its items kept).

The builders are faithful to production, used to show that WHICH blocks are withheld (their text,
position, count) changes nothing:

* :func:`marker_ir`: Marker's blocks on several pages with ``metadata.table_of_contents`` as Marker
  builds it (one entry per SectionHeader present, with title, level and page), through
  ``marker.chunk_output_to_ir`` (its page-range units included);
* :func:`glm_ir`: GLM-OCR's title and text regions, through ``glm_ocr.responses_to_ir``;
* :func:`markdown_ir`: Markdown source text, through ``normalizers.markdown_to_ir``.

Span ids are production's own ``s{n}``: nothing is renamed.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Sequence

import yaml

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository

from tests.helpers import write_yaml

T0 = datetime(2026, 10, 12, 9, 0, tzinfo=UTC)
MARKER, GLM, MARKDOWN, GLM_OUTLINE = "marker", "glm", "markdown", "glm_outline"
STYLES = (MARKER, GLM, MARKDOWN, GLM_OUTLINE)


@dataclass(frozen=True)
class Element:
    kind: str  # "header" or "text"
    text: str
    level: int = 1
    page: int = 0


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def marker_ir(elements: Sequence[Element]) -> Any:
    from learnloop.ingest.extractors import marker

    counters: dict[tuple[int, str], int] = {}
    stack: dict[int, str] = {}
    blocks, toc = [], []
    for element in elements:
        block_type = "SectionHeader" if element.kind == "header" else "Text"
        index = counters.get((element.page, block_type), 0)
        counters[(element.page, block_type)] = index + 1
        block_id = f"/page/{element.page}/{block_type}/{index}"
        if element.kind == "header":
            stack = {level: value for level, value in stack.items() if level < element.level}
            stack[element.level] = block_id
            toc.append({"title": element.text, "heading_level": element.level, "page_id": element.page})
        html = f"<h{element.level + 1}>{element.text}</h{element.level + 1}>" if element.kind == "header" \
            else f"<p>{element.text}</p>"
        blocks.append({"id": block_id, "block_type": block_type, "html": html, "page": element.page,
                       "section_hierarchy": {str(level): value for level, value in sorted(stack.items())}})
    return marker.chunk_output_to_ir(blocks=blocks, metadata={"table_of_contents": toc}, extractor_version="1")


def glm_ir(elements: Sequence[Element], *, outline: bool = False) -> Any:
    from learnloop.ingest.extractors import glm_ocr

    pages = sorted({element.page for element in elements}) or [0]
    layout: dict[int, list[dict[str, Any]]] = {page: [] for page in pages}
    for index, element in enumerate(elements):
        top = 60 + 60 * len(layout[element.page])
        region = {"index": index, "label": "text", "content": element.text, "bbox_2d": [100, top, 1100, top + 40],
                  "width": 1224, "height": 1584}
        if element.kind == "header":
            region.update({"native_label": "paragraph_title", "level": element.level + 1})
        layout[element.page].append(region)
    result = {"layout_details": [layout[page] for page in pages],
              "data_info": {"pages": [{"width": 1224, "height": 1584} for _ in pages]}}
    # ``outline``: the PDF's embedded bookmarks, one per header present (the placer then ranks
    # headings by them, as for a book with an outline).
    bookmarks = [{"title": element.text, "heading_level": element.level, "page_id": element.page}
                 for element in elements if element.kind == "header"] if outline else []
    return glm_ocr.responses_to_ir([(result, pages)], sizes=[(612.0, 792.0)] * (max(pages) + 1), outline=bookmarks,
                                   version="v")


def markdown_ir(elements: Sequence[Element]) -> Any:
    from learnloop.ingest.extractors.normalizers import markdown_to_ir

    lines = []
    for element in elements:
        lines.append(f"{'#' * element.level} {element.text}" if element.kind == "header" else element.text)
        lines.append("")
    return markdown_to_ir("\n".join(lines), title="Book", extractor_name="markdown")


BUILDERS = {MARKER: marker_ir, GLM: glm_ir, MARKDOWN: markdown_ir,
            GLM_OUTLINE: lambda elements: glm_ir(elements, outline=True)}


def ingest_ir(elements: Sequence[Element], *, style: str) -> Any:
    return BUILDERS[style](elements)


def build_vault(root, readings: dict[str, tuple[str, Sequence[Element]]], *, learning_object: str,
                cite: Sequence[tuple[str, str]] = (), viewed: Sequence[tuple[str, str]] = (),
                completed: Sequence[tuple[str, str]] = (), items: Sequence[str] = ("pi_m1a",),
                books: dict[str, str] | None = None):
    """A vault whose sources have ``readings`` (extraction id -> (style, elements)), each persisted
    from the production converter as a reading of its book (``books``: extraction id -> book; by
    default one book, so its readings are readings of one revision); ``learning_object`` cites
    ``cite`` (extraction, span id as ingest numbered it), the Reader viewed ``viewed`` and completed
    the sections ``completed``."""

    from tests.ad23_fakes import ad23_vault
    from tests.test_source_inventory import _persist

    paths = ad23_vault(root, items=tuple(items))
    made = _iso(T0 - timedelta(days=7))
    book_of = {extraction: (books or {}).get(extraction, "pr") for extraction in readings}
    with closing(connect(paths.sqlite_path)) as connection:
        for book in sorted(set(book_of.values())):
            connection.execute("INSERT INTO source_artifacts(id, acquisition_kind, canonical_uri, created_at, "
                               "updated_at) VALUES (?, 'pdf', ?, ?, ?)", (f"src_{book}", f"file:///{book}.pdf", made, made))
            connection.execute("INSERT INTO source_revisions(id, source_id, asset_hash, created_at) VALUES (?, ?, ?, ?)",
                               (f"rev_{book}", f"src_{book}", f"sha256:{book}", made))
        connection.commit()
    repository = Repository(paths.sqlite_path)
    for version, (extraction, (style, elements)) in enumerate(readings.items(), start=1):
        ir = ingest_ir(elements, style=style)
        ir = ir.model_copy(update={"extractor_version": f"{ir.extractor_version}.{version}"})
        _persist(repository, ir, revision_id=f"rev_{book_of[extraction]}", extraction_id=extraction)
    if cite:
        path = paths.learning_object_path("linear-algebra", learning_object)
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        payload["provenance"] = {"origin": "human", "source_refs": [{
            "ref_type": "canonical_source", "ref_id": f"src_{book_of[extraction]}", "source_id": f"src_{book_of[extraction]}",
            "extraction_id": extraction, "span_ids": [span], "locator": f"span:{extraction}/{span}"}
            for extraction, span in cite]}
        write_yaml(path, payload)
    for number, (extraction, span) in enumerate(viewed):
        repository.insert_source_exposure_event(
            {"context": "reader", "extraction_id": extraction, "span_id": span, "revision_id": f"rev_{book_of[extraction]}",
             "source_id": f"src_{book_of[extraction]}", "entity_type": "reader", "entity_id": f"visit_pr_{number}",
             "created_at": _iso(T0 - timedelta(hours=5, minutes=number))})
    for extraction, section in completed:
        repository.upsert_reader_section_progress(extraction_id=extraction, section_id=section, spans_seen=1,
                                                  span_count=1, completed=True)
    return paths


#: Reading tables keyed by their reading, and the extraction column naming it.
_BY_EXTRACTION = (
    ("source_document_blocks", "extraction_id"), ("source_document_units", "extraction_id"),
    ("source_document_assets", "extraction_id"), ("source_exposure_events", "extraction_id"),
    ("reader_section_progress", "extraction_id"), ("reader_authored_questions", "extraction_id"),
    ("source_span_reanchors", "from_extraction_id"), ("source_span_reanchors", "to_extraction_id"),
)


def delete_reading(sqlite_path, extraction_id: str) -> None:
    """THE ORACLE: the reading's blocks, units, assets and reading events deleted, its items kept
    (a row deletion; test-only, so the tables' append-only triggers are dropped around it and
    recreated as they were)."""

    with closing(sqlite3.connect(sqlite_path)) as connection:
        tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        touched = sorted({table for table, _column in _BY_EXTRACTION} | {
            "question_events", "ad_dose_offers", "ad_reading_opportunities", "interaction_events"})
        triggers = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'trigger' AND tbl_name IN (%s)"
            % ",".join("?" for _ in touched), touched).fetchall()
        for name, _sql in triggers:
            connection.execute(f"DROP TRIGGER {name}")
        for table, column in _BY_EXTRACTION:
            if table in tables:
                connection.execute(f"DELETE FROM {table} WHERE {column} = ?", (extraction_id,))
        like = f'%"{extraction_id}"%'
        if "question_events" in tables:
            # Reading questions only: a practice or feedback question is attempt evidence, kept with
            # the items (round 8 follow-up, F1).
            connection.execute("DELETE FROM question_events WHERE context IN ('reader', 'library') AND "
                               "(note_id LIKE ? OR source_context_json LIKE ?)", (f"span:{extraction_id}/%", like))
        if "interaction_events" in tables:
            connection.execute("DELETE FROM interaction_events WHERE (kind LIKE 'reader\\_%' ESCAPE '\\' OR "
                               "kind LIKE 'library\\_%' ESCAPE '\\') AND (payload_json LIKE ? OR locator_json LIKE ?)",
                               (like, like))
        if "ad_dose_offers" in tables:
            drawn = [row[0] for row in connection.execute(
                "SELECT id FROM ad_dose_offers WHERE extraction_id = ?", (extraction_id,))]
            for draw in drawn:
                connection.execute("DELETE FROM ad_dose_offers WHERE draw_id = ?", (draw,))
            connection.execute("DELETE FROM ad_dose_offers WHERE extraction_id = ?", (extraction_id,))
        if "ad_reading_opportunities" in tables:
            connection.execute("DELETE FROM ad_reading_opportunities WHERE source_id LIKE ?", (f"{extraction_id}/%",))
            for source_table in ("source_exposure_events", "question_events", "reader_authored_questions"):
                if source_table in tables:
                    connection.execute(
                        f"DELETE FROM ad_reading_opportunities WHERE source_table = ? AND source_id NOT IN "
                        f"(SELECT id FROM {source_table})", (source_table,))
        for _name, sql in triggers:
            connection.execute(sql)
        connection.commit()


__all__ = ["BUILDERS", "Element", "GLM", "GLM_OUTLINE", "MARKDOWN", "MARKER", "STYLES", "T0", "build_vault", "delete_reading",
           "glm_ir", "ingest_ir", "markdown_ir", "marker_ir"]
