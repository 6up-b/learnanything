"""Which passages the learner's own reading observed, and where it reached a section's end (migration 256).

The Reader's progress report (``reader.mark_section_progress``) names the passages the desktop or the phone saw
during the learner's own scrolling or playback, and whether the section's last readable passage was among them.
:func:`check_report` holds those ids to the reading and the section before anything is written; the store appends
them (``upsert_reader_section_progress``), so reports union and a smaller one removes nothing.

These are generation evidence for a later step, never evidence of understanding: no mastery, exposure, scheduling,
reading-credit or generation reader reads them yet, and a section is finished exactly as before. :func:`seen_on`
and :func:`section_ends_on` are the reads that step will use; nothing in ``src`` calls them yet
(``tests/test_reader_seen_passages.py`` fails on a new reader).

A count is never turned into passages: the phone's count cannot say which passages were seen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.content.sources.span_aliases import SpanTranslator, other_readings
from learnloop.section_map import extraction_sections

ORIGINS = ("desktop", "phone")


class SeenReportRefused(ValueError):
    """A report names a reading, a section or a passage that is not there; nothing of it is written."""


@dataclass(frozen=True)
class CheckedReport:
    """A report's passages, checked: in reading order, once each, and the section's end when it was reached."""

    seen_span_ids: tuple[str, ...]
    end_span_id: str | None


def check_report(repository: Any, *, extraction_id: str, section_id: str, seen_span_ids: list[str] | None,
                 reached_end: bool) -> CheckedReport:
    """Hold a report's passages to the reading and the section it names.

    Each id must be one of the section's readable passages (``section_map.extraction_sections``, the one definition
    the guide, the phone and the quick checks share). An end needs the section's last readable passage seen, in this
    report or an earlier one on the same reading: an end is an observation of that passage, never a position."""

    wanted = [str(span_id) for span_id in dict.fromkeys(seen_span_ids or ())]
    if not wanted and not reached_end:
        return CheckedReport((), None)
    ir = repository.load_document_ir(extraction_id) if repository.get_extraction_run(extraction_id) else None
    if ir is None:
        raise SeenReportRefused(f"No reading {extraction_id!r} to record seen passages on.")
    sections, _blocks, _span_to_section = extraction_sections(ir)
    section = next((row for row in sections if row["id"] == section_id), None)
    if section is None:
        raise SeenReportRefused(f"No section {section_id!r} in reading {extraction_id!r}.")
    order = {span_id: index for index, span_id in enumerate(section["span_ids"])}
    strangers = [span_id for span_id in wanted if span_id not in order]
    if strangers:
        raise SeenReportRefused(f"Not passages of section {section_id!r}: {', '.join(strangers[:5])}.")
    end_span_id = None
    if reached_end:
        last = str(section["end_span_id"])
        recorded = {str(row["span_id"]) for row in repository.reader_seen_spans_for(extraction_id)}
        if last not in wanted and last not in recorded:
            raise SeenReportRefused(f"The end of section {section_id!r} is its last passage, which was not seen.")
        end_span_id = last
    return CheckedReport(tuple(sorted(wanted, key=order.__getitem__)), end_span_id)


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
