"""Which passages the learner's own reading observed, and where it reached a section's end (migration 256).

The Reader's progress report (``reader.mark_section_progress``) names the passages the desktop or the phone saw
during the learner's own scrolling or playback, and whether the section's last readable passage was among them.
:func:`check_report` keeps the ids that are the section's passages on that reading and leaves the rest out (it never
refuses a report: its count and completion land as before); the store appends the kept ones
(``upsert_reader_section_progress``), so reports union and a smaller one removes nothing.

These are generation evidence, never evidence of understanding: no mastery, exposure, scheduling or
reading-credit reader reads them, and a section is finished exactly as before. Their one reader is the first set of
questions from the part of a section read (``learnloop.reader.part_read``), through :func:`seen_on` and
:func:`seen_marker` and :func:`seen_readings`; :func:`section_ends_on` is called by nothing in ``src`` yet
(``tests/test_reader_seen_passages.py`` fails on a new reader).

A count is never turned into passages: the phone's count cannot say which passages were seen.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from learnloop.content.sources.span_aliases import SpanTranslator, other_readings
from learnloop.section_map import extraction_sections

ORIGINS = ("desktop", "phone")


_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckedReport:
    """A report's passages, kept: those that are readable passages of its section, in reading order, once each; the
    section's end when its last passage is seen; and how many named ids were left out."""

    seen_span_ids: tuple[str, ...]
    end_span_id: str | None
    left_out: int = 0


def check_report(repository: Any, *, extraction_id: str, section_id: str, seen_span_ids: list[str] | None,
                 reached_end: bool) -> CheckedReport:
    """Keep the passages a report names that are readable passages of its section on its reading.

    Never refuses: the passages are an optional addition to a report whose count, reveal and completion must land
    exactly as before (a phone's queued passages coalesce with its later completion into one record, and a refused
    record is never sent again). An id that is not one of the section's readable passages
    (``section_map.extraction_sections``, the definition the guide, the phone and the quick checks share), and every
    id on an unknown reading or section, is left out: never recorded, and counted in one warning per report. An end
    is kept only when the section's last readable passage is seen, in this report's kept passages or recorded
    earlier on the same reading: an end is an observation of that passage, never a position."""

    wanted = [str(span_id) for span_id in dict.fromkeys(seen_span_ids or ())]
    if not wanted and not reached_end:
        return CheckedReport((), None)
    ir = repository.load_document_ir(extraction_id) if repository.get_extraction_run(extraction_id) else None
    sections = extraction_sections(ir)[0] if ir is not None else []
    section = next((row for row in sections if row["id"] == section_id), None)
    order = {span_id: index for index, span_id in enumerate(section["span_ids"])} if section is not None else {}
    kept = sorted((span_id for span_id in wanted if span_id in order), key=order.__getitem__)
    end_span_id = None
    if reached_end and section is not None:
        last = str(section["end_span_id"])
        if last in kept or last in {str(row["span_id"]) for row in repository.reader_seen_spans_for(extraction_id)}:
            end_span_id = last
    left_out = len(wanted) - len(kept)
    if left_out or (reached_end and end_span_id is None):
        # Counts only: a client and the host disagreeing on a section's passages shows here, never its ids or text.
        _log.warning("seen passages left out of a progress report: %d of %d ids, end %s (reading known: %s, "
                     "section known: %s)", left_out, len(wanted),
                     "left out" if reached_end and end_span_id is None else "kept" if reached_end else "not reported",
                     ir is not None, section is not None)
    return CheckedReport(tuple(kept), end_span_id, left_out)


@dataclass(frozen=True)
class SeenPassage:
    """One passage of a reading with exact seen evidence: where it was observed (``observed_on``: the reading and
    span the report named), when first and by which device."""

    span_id: str
    first_seen_at: str
    origin: str
    observed_on: tuple[str, str]


def seen_on(repository: Any, extraction_id: str) -> dict[str, SeenPassage]:
    """Every passage of ``extraction_id`` with exact seen evidence, by span id.

    The reading's own rows, and those of the book's other readings whose passage is the same text here: an exact
    alias of the one alias authority (``content.sources.span_aliases``: a content-hash or manual match, ``current``).
    A changed passage (a geometry or section alias, ``needs_reanchor``) or one with no alias carries nothing: the
    learner did not read these words. Nothing is written; the earliest observation of a passage wins."""

    found: dict[str, SeenPassage] = {}
    for row in repository.reader_seen_spans_for(extraction_id):
        span_id = str(row["span_id"])
        found[span_id] = SeenPassage(span_id, str(row["first_seen_at"]), str(row["origin"]),
                                     (str(extraction_id), span_id))
    translator = SpanTranslator(repository, extraction_id)
    for other in other_readings(repository, extraction_id):
        for row in repository.reader_seen_spans_for(other):
            resolution = translator.resolve(other, str(row["span_id"]))
            if not resolution.exact or resolution.span_id is None:
                continue
            passage = SeenPassage(resolution.span_id, str(row["first_seen_at"]), str(row["origin"]),
                                  (str(other), str(row["span_id"])))
            held = found.get(resolution.span_id)
            if held is None or passage.first_seen_at < held.first_seen_at:
                found[resolution.span_id] = passage
    return found


def seen_marker(repository: Any) -> tuple[int, int]:
    """A value that changes whenever a passage of any reading is recorded as seen (the rows are only ever added)."""

    return repository.reader_seen_spans_marker()


def seen_readings(repository: Any) -> list[str]:
    """The readings with any passage recorded as seen (each book's reread carries its evidence through
    :func:`seen_on`, so a reading listed here may be an earlier one of a book)."""

    return repository.reader_seen_readings()


@dataclass(frozen=True)
class SectionEnd:
    """A section of a reading whose last readable passage (``span_id``) the learner's own reading reached."""

    section_id: str
    span_id: str
    first_seen_at: str
    origin: str


def section_ends_on(repository: Any, extraction_id: str) -> list[SectionEnd]:
    """The sections of ``extraction_id`` whose end was reached, on that reading only (another reading's sections
    are other sections)."""

    return [SectionEnd(str(row["section_id"]), str(row["span_id"]), str(row["first_seen_at"]), str(row["origin"]))
            for row in repository.reader_section_ends_for(extraction_id)]
