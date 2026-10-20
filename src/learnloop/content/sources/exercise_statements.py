"""A textbook exercise's region and its statement, read one way (Reader RW4b
fix round 5, R2; canonical sources S1).

* :func:`exercise_regions`: one extraction's exercise regions in document
  order (the lead block and the unhinted body after it), the boundaries S1's
  arm, its exposure rule and the Reader share (``instructional.exercises``
  re-exports them).
* :func:`read_exercise_statement`: THE one reader of an exercise's
  statement. Every path that reads or returns one goes through it: S1's
  import worker and its ``selection_for_region``, the Reader's candidate
  view, its fallback listing, the picked exercise ``workbench.open`` shows,
  every workbench response that carries a picked exercise's statement, and
  the exposure rule's input. At read time it widens the asked spans to
  their complete exercise region(s) and asks the one exam and held-out
  predicate (``exam_material.exam_withheld``) about every one of them, so a
  region held out after it was shown is never read again, not even the part
  a card's preview did not show. It fails closed: a predicate that cannot be
  read, a span that is not there, or spans with no text give None.

It lives beside the predicate (``content.sources``) because S1's import
worker (``content.authoring``) is imported BY the instructional service and
so cannot import it; ``tests/test_library_exercises.py`` pins that no
handler, reader module or S1 path reads a statement another way.
"""
from __future__ import annotations

from collections.abc import Sequence
from contextlib import closing
from dataclasses import dataclass
import re
from typing import Any

from learnloop.content.sources import exam_material as EM
from learnloop.db.connection import connect
from learnloop.db.stores.source_block_fts import (
    MAX_REGION_BLOCKS,
    REGION_BODY_HINTS,
    blocks_by_key,
    extraction_hint_rows,
    section_header_titles,
)
from learnloop.source_retrieval.corpus import effective_hint

#: An exercise label ("Exercise 4.12", "Problem 2") and a bare number ("20 ", "3."),
#: shared with the instructional arm's labelling.
LABEL_RE = re.compile(r"^\s*((?:exercise|problem|question)s?\s*[\dA-Za-z.()\-]*\d[\dA-Za-z.()\-]*)", re.IGNORECASE)
NUMBER_RE = re.compile(r"^\s*(\(?\d+(?:\.\d+)*[.)]?|\([a-z]\))\s")


@dataclass(frozen=True)
class ExerciseRegion:
    extraction_id: str
    span_ids: tuple[str, ...]
    text: str

    @property
    def key(self) -> tuple[str, ...]:
        return (self.extraction_id, *self.span_ids)


def starts_exercise(text: str | None) -> bool:
    """Whether a block's own text opens an exercise: "20 Suppose ...",
    "3. Show ...", "Exercise 4.12", "Problem 2". A sub-part "(a)" does not."""

    value = text or ""
    if LABEL_RE.match(value):
        return True
    number = NUMBER_RE.match(value)
    return number is not None and re.fullmatch(r"\([a-z]\)", number.group(1)) is None


#: Marker's page furniture: never an exercise, never part of one.
PAGE_FURNITURE = frozenset({"PageHeader", "PageFooter"})


def exercise_regions(connection, extraction_id: str) -> list[ExerciseRegion]:
    """One extraction's exercise regions in document order.

    A block whose effective hint is ``exercise`` leads a region; the unhinted
    body after it (prose, equations, tables, figures) joins it, up to the next
    section header, the next lead or ``MAX_REGION_BLOCKS``.
    """

    titles = section_header_titles(connection, extraction_id)
    regions: list[ExerciseRegion] = []
    current: list[Any] = []
    body_left = 0

    def close() -> None:
        if current:
            regions.append(ExerciseRegion(
                extraction_id, tuple(row.span_id for row in current),
                "\n\n".join(" ".join(row.text.split()) for row in current if row.text.strip())))
        current.clear()

    for row in extraction_hint_rows(connection, extraction_id):
        if row.block_type in PAGE_FURNITURE or not (row.text or "").strip():
            # Page headers, footers and empty blocks neither lead nor end a
            # region (an exercise can run across a page break).
            continue
        hint = effective_hint(row, titles)
        if (hint == "exercise" and row.block_type != "SectionHeader" and current and body_left
                and not starts_exercise(row.text)):
            # Under an "Exercises" heading every block carries the heading's
            # hint; only a numbered or labelled block starts a new exercise.
            # The rest ("Find a subspace W ..." after "20 Suppose U = ...", a
            # "Hint:" line) belong to the exercise they follow.
            current.append(row)
            body_left -= 1
        elif hint == "exercise" and row.block_type != "SectionHeader":
            close()
            current.append(row)
            body_left = MAX_REGION_BLOCKS
        elif current and body_left and hint in REGION_BODY_HINTS and row.block_type != "SectionHeader":
            current.append(row)
            body_left -= 1
        else:
            close()
            body_left = 0
    close()
    return regions


@dataclass(frozen=True)
class ExerciseStatement:
    """A textbook exercise's statement, read now and cleared for showing."""

    extraction_id: str
    #: The spans asked for, in order.
    span_ids: tuple[str, ...]
    #: Every span the check covered: the complete exercise region(s) the asked
    #: spans sit in, and the asked spans themselves.
    checked_span_ids: tuple[str, ...]
    #: The complete verbatim statement: the region's text when the spans are
    #: exactly one region, else the blocks themselves, joined as a region joins them.
    text: str
    #: Each asked span's block text, as stored (S1's selection and its hint).
    blocks: tuple[tuple[str, str], ...]


def exercise_region_spans(connection: Any, extraction_id: str, span_id: str,
                          cache: dict[str, list[ExerciseRegion]] | None = None) -> tuple[str, ...] | None:
    """The span ids of the exercise region a span sits in (boundaries only,
    never its text), or None. ``cache``: regions by extraction, for a list."""

    regions = cache.get(extraction_id) if cache is not None else None
    if regions is None:
        regions = exercise_regions(connection, extraction_id)
        if cache is not None:
            cache[extraction_id] = regions
    region = next((region for region in regions if span_id in region.span_ids), None)
    return tuple(region.span_ids) if region is not None else None


def read_exercise_statement(vault: Any, repository: Any, extraction_id: str,
                            span_ids: Sequence[str]) -> ExerciseStatement | None:
    """THE one reader of a textbook exercise's statement (see the module).
    None when it is exam or held-out material now (its complete region),
    when the predicate cannot be read, or when a span is missing or empty."""

    wanted = tuple(str(span) for span in span_ids)
    if not extraction_id or not wanted:
        return None
    try:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            regions = exercise_regions(connection, extraction_id)
            covering = [region for region in regions if set(region.span_ids) & set(wanted)]
            checked = tuple(dict.fromkeys([*(span for region in covering for span in region.span_ids), *wanted]))
            if EM.exam_withheld(vault, repository, [(extraction_id, span) for span in checked]):
                return None
            found = blocks_by_key(connection, [(extraction_id, span) for span in wanted])
    except Exception:  # noqa: BLE001 - an unreadable predicate never shows the statement (fail closed)
        return None
    if any((extraction_id, span) not in found for span in wanted):
        return None
    blocks = tuple((span, found[(extraction_id, span)].text or "") for span in wanted)
    exact = next((region for region in covering if tuple(region.span_ids) == wanted), None)
    text = exact.text if exact is not None else "\n\n".join(
        " ".join(body.split()) for _span, body in blocks if body.strip())
    if not (text or "").strip():
        return None
    return ExerciseStatement(extraction_id=extraction_id, span_ids=wanted, checked_span_ids=checked, text=text,
                             blocks=blocks)


def selection_nodes(statement: ExerciseStatement) -> dict[str, Any]:
    """A Reader-style selection over the statement's whole blocks (``start =
    0``, ``end = len(text)``): what S1's ``selection_for_region`` returns."""

    return {"nodes": [{"span_id": span, "start": 0, "end": len(body)} for span, body in statement.blocks]}


__all__ = [
    "LABEL_RE",
    "NUMBER_RE",
    "PAGE_FURNITURE",
    "ExerciseRegion",
    "ExerciseStatement",
    "exercise_region_spans",
    "exercise_regions",
    "read_exercise_statement",
    "selection_nodes",
    "starts_exercise",
]
