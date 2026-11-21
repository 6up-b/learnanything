"""A first set of questions from the part of a section the learner has read.

A section's questions used to be written only once the learner finished it. A topic now gets its first set as soon
as every passage it cites has been seen by the learner's own reading (recorded passages, read through
:mod:`learnloop.reader.seen_passages`), whether or not its section is finished. There is no share of a section, no
threshold and no "first few topics": a topic qualifies or it does not.

**Qualification** (:func:`topic_coverage`). A topic's citations are its own provenance references and its facets';
each explicit span id, span locator, timed cue and legacy quote is resolved through the one identity machinery the
section map uses (``section_map.anchor_for_ref``, the alias authority for another reading of the book), across section
boundaries. A topic qualifies when it cites at least one passage, every reference resolves *exactly* to passages of a
reading (a moved passage, an ambiguous quote, a note that is no book of the library, or a book with no reading does
not), every cited passage of every cited book has exact seen evidence, and none of them is held out (the Reader's
checks' protection, ``exam_material.surface_material(..., "reader_checks")``). A topic that fails waits for the
existing route: its section's finish.

**Grounding** (:func:`seen_grounding`). The request's citation bundles are built from the topic's cited passages,
each widened only by neighbours that are themselves seen and contiguous with it (the finished section's bundles take
five neighbours either side, read or not). Nothing the learner has not seen is quoted.

**Reconciliation** (:func:`reconcile_part_read`). For each unfinished section with seen passages whose chapter's
topics have settled (``add_source.section_topics_settled``), the topics that cite it, need questions, are owned by
nobody and qualify are claimed through the same per-topic claims a finish makes
(``section_generation.claim_section_topics``, trigger ``part_read``). It may run any number of times: it claims only
what is newly eligible and unclaimed, and a claimed topic is never claimed again, by a later report or by the
section's finish. Its callers are the progress report, a build that applied topics, the primary's start and its
owed-work drain, and a review that applied held topics; the caller starts the queue after the claim commits.

:func:`assess` is the read both reconciliation and Today use. It is remembered per reading until something it reads
changes (a seen passage anywhere, the queue's revision, which a job's end and every apply bump, the topic claims, the
reading's section progress, or the vault object itself), so the reads that poll Today pay for it once.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from learnloop.content.sources.exam_material import surface_material
from learnloop.content.sources.span_aliases import SpanTranslator, current_reading, reading_source
from learnloop.db.stores.reader import READER_FIRST_SET
from learnloop.reader.reader_progression import _MAX_SOURCE_BUNDLES_PER_LO, _SOURCE_BUNDLE_RADIUS, citation_bundle
from learnloop.reader.section_generation import (
    TOPIC_MANAGED,
    TopicEnqueue,
    claim_section_topics,
    section_generation_candidates,
    section_topic_requests,
)
from learnloop.reader.seen_passages import seen_marker, seen_on, seen_readings
from learnloop.section_map import ANCHOR_CURRENT, anchor_for_ref, canonical_note_ids, extraction_sections
from learnloop.vault.models import LoadedVault, SourceRef, learning_object_facet_union
from learnloop.vault.paths import VaultPaths

__all__ = [
    "BEFORE_BUILD", "NOTHING", "OWED", "READ_FURTHER", "PART_READ", "SectionPartRead", "TopicCoverage", "assess",
    "read_readings", "reconcile_part_read", "seen_grounding", "topic_coverage",
]

#: The trigger a part-read claim is recorded under (``reader_topic_question_work.trigger_event``).
PART_READ = "part_read"

#: What an unfinished section with seen passages can say (:attr:`SectionPartRead.state`).
BEFORE_BUILD = "before_build"  # its chapter's topics are not in yet
OWED = "owed"  # some topic qualifies and nobody has claimed it yet (the phone leaves it to the desktop)
READ_FURTHER = "read_further"  # topics need questions, and none has all its passages seen
NOTHING = "nothing"  # no topic citing it needs questions that nobody writes already

PassageKey = tuple[str, str]

#: References that cite a passage of a reading. Others (an existing entity, a session, manual context) cite none.
_PASSAGE_REFS = frozenset({"canonical_source", "note"})
_TIME_LOCATOR_RE = re.compile(r"^t=(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?$")


@dataclass(frozen=True)
class TopicCoverage:
    """What one topic's grounding cites and how much of it the learner's reading has seen.

    ``cited``: every passage it cites (reading, span), its own references' first, then in reading order;
    ``priority``: 0 for a passage its own references cite, 1 for one only its facets' cite; ``unseen``: those with no
    exact seen evidence; ``unresolved``: how many references could not be resolved exactly; ``held_out``: cited
    passages the Reader's checks must not send to a model."""

    learning_object_id: str
    cited: tuple[PassageKey, ...]
    priority: Mapping[PassageKey, int]
    unseen: tuple[PassageKey, ...]
    unresolved: int
    held_out: tuple[PassageKey, ...]

    @property
    def qualifies(self) -> bool:
        return bool(self.cited) and not self.unseen and not self.unresolved and not self.held_out

    @property
    def reason(self) -> str:
        """Why it qualifies or not, the first exclusion that applies: ``unresolved``, ``no_citation``,
        ``held_out``, ``unseen`` or ``seen``."""

        if self.unresolved:
            return "unresolved"
        if not self.cited:
            return "no_citation"
        if self.held_out:
            return "held_out"
        return "unseen" if self.unseen else "seen"


class _Reading:
    """One reading's readable passages, in order, with their sections and blocks, its book, and what of it was seen."""

    def __init__(self, vault: LoadedVault, repository: Any, extraction_id: str) -> None:
        self.extraction_id = str(extraction_id)
        run = repository.get_extraction_run(self.extraction_id)
        self.revision = repository.get_source_revision(str(run.get("revision_id") or "")) if run else None
        self.source_id = str(self.revision["source_id"]) if self.revision and self.revision.get("source_id") else None
        ir = repository.load_document_ir(self.extraction_id) if run else None
        rows, block_by_span, span_to_section = extraction_sections(ir) if ir is not None else ([], {}, {})
        self.sections = {str(row["id"]): list(row["span_ids"]) for row in rows}
        self.order = [span for row in rows for span in row["span_ids"]]
        self.index = {span: position for position, span in enumerate(self.order)}
        self.block_by_span = block_by_span
        self.section_of = span_to_section
        self.blocks = [block_by_span[span] for span in self.order]
        self.translator = SpanTranslator(repository, self.extraction_id)
        self.seen = frozenset(seen_on(repository, self.extraction_id))
        artifact = repository.get_source_artifact(self.source_id) if self.source_id else None
        self.note_ids = canonical_note_ids(vault, artifact or {})
        self.path = _raw_path(vault, self.revision) if self.revision else None


def _raw_path(vault: LoadedVault, revision: Mapping[str, Any]) -> str | None:
    raw = VaultPaths(vault.root, vault.config).canonical_source_raw_path(str(revision.get("asset_hash") or ""))
    return raw.relative_to(vault.root).as_posix() if raw.is_file() else None


class _Library:
    """The readings a set of topics cites, loaded once each: the reading being read, and any other book's current one."""

    def __init__(self, vault: LoadedVault, repository: Any, extraction_id: str) -> None:
        self.vault, self.repository = vault, repository
        self.base = _Reading(vault, repository, extraction_id)
        self._by_source: dict[str, _Reading | None] = {}
        if self.base.source_id:
            self._by_source[self.base.source_id] = self.base
        self._note_sources: dict[str, str] | None = None
        self.material = surface_material(vault, repository, "reader_checks")

    def reading_of(self, source_id: str) -> _Reading | None:
        if source_id not in self._by_source:
            extraction_id = current_reading(self.repository, source_id)
            self._by_source[source_id] = (_Reading(self.vault, self.repository, extraction_id)
                                          if extraction_id else None)
        return self._by_source[source_id]

    def source_of(self, ref: SourceRef) -> str | None:
        """The book a reference cites: its source, or for a note the library book the note stands for."""

        if ref.source_id:
            return str(ref.source_id)
        if ref.ref_type == "canonical_source":
            return str(ref.ref_id) if self.repository.get_source_artifact(str(ref.ref_id)) else None
        if self._note_sources is None:
            self._note_sources = {}
            for artifact in self.repository.all_source_artifacts():
                for note_id in canonical_note_ids(self.vault, artifact):
                    self._note_sources.setdefault(note_id, str(artifact["id"]))
        return self._note_sources.get(str(ref.ref_id))


def _timed(ref: SourceRef, reading: _Reading) -> list[str] | None:
    """Every transcript cue a timed reference's range overlaps, or None when the reference is not timed."""

    match = _TIME_LOCATOR_RE.match(str(ref.locator or ""))
    if match is None:
        return None
    start = float(match.group(1))
    end = float(match.group(2)) if match.group(2) is not None else start
    cues = []
    for block in reading.blocks:
        cue = _TIME_LOCATOR_RE.match(str(block.extractor_block_id or ""))
        if cue is None:
            continue
        cue_start = float(cue.group(1))
        cue_end = float(cue.group(2)) if cue.group(2) is not None else cue_start
        if cue_end >= start and cue_start <= end:
            cues.append(block.span_id)
    return cues


def _resolve(ref: SourceRef, reading: _Reading) -> list[str] | None:
    """The readable passages of ``reading`` a reference cites, each exactly; None when any of it cannot be resolved
    exactly (an explicit span that is not the same text here, or a locator or quote that names no passage, or only a
    moved one)."""

    spans: list[str] = []
    ref_extraction = str(ref.extraction_id or "")
    for span in ref.span_ids:
        if not ref_extraction or ref_extraction == reading.extraction_id:
            if span not in reading.index:
                return None
            spans.append(str(span))
            continue
        resolution = reading.translator.resolve(ref_extraction, str(span))
        if not resolution.exact or resolution.span_id not in reading.index:
            return None
        spans.append(str(resolution.span_id))
    timed = _timed(ref, reading)
    if timed:
        return spans + timed
    if ref.locator or ref.quote:
        anchor = anchor_for_ref(ref, source_id=str(reading.source_id), extraction_id=reading.extraction_id,
                                note_ids=reading.note_ids, blocks=reading.blocks, translator=reading.translator)
        if anchor is not None and anchor[1] == ANCHOR_CURRENT:
            spans.append(anchor[0])
        elif not spans:
            return None
    return spans or None


def _coverage(library: _Library, learning_object: Any) -> TopicCoverage:
    vault = library.vault
    refs: list[tuple[int, SourceRef]] = [(0, ref) for ref in learning_object.provenance.source_refs]
    for facet_id in learning_object_facet_union(learning_object):
        facet = vault.evidence_facets.get(vault.canonical_facet_id(str(facet_id)))
        if facet is not None:
            refs.extend((1, ref) for ref in facet.provenance.source_refs)
    priority: dict[PassageKey, int] = {}
    readings: dict[str, _Reading] = {}
    unresolved = 0
    for rank, ref in refs:
        if ref.ref_type not in _PASSAGE_REFS:
            continue
        source_id = library.source_of(ref)
        reading = library.reading_of(source_id) if source_id else None
        spans = _resolve(ref, reading) if reading is not None else None
        if spans is None:
            unresolved += 1
            continue
        readings[reading.extraction_id] = reading
        for span in spans:
            key = (reading.extraction_id, span)
            priority[key] = min(priority.get(key, rank), rank)
    base = library.base.extraction_id
    cited = tuple(sorted(priority, key=lambda key: (priority[key], key[0] != base, key[0],
                                                    readings[key[0]].index[key[1]])))
    return TopicCoverage(
        learning_object_id=learning_object.id,
        cited=cited,
        priority=priority,
        unseen=tuple(key for key in cited if key[1] not in readings[key[0]].seen),
        unresolved=unresolved,
        held_out=tuple(key for key in cited if library.material.covers(*key)),
    )


def topic_coverage(vault: LoadedVault, repository: Any, extraction_id: str, lo_ids: list[str]
                   ) -> dict[str, TopicCoverage]:
    """Each active topic of ``lo_ids``'s coverage, read against ``extraction_id`` (the reading being read)."""

    library = _Library(vault, repository, extraction_id)
    out = {}
    for lo_id in lo_ids:
        learning_object = vault.learning_objects.get(lo_id)
        if learning_object is not None and learning_object.status == "active":
            out[lo_id] = _coverage(library, learning_object)
    return out


def seen_grounding(vault: LoadedVault, repository: Any, extraction_id: str, coverage: TopicCoverage,
                   library: _Library | None = None) -> list[dict[str, Any]]:
    """A qualifying topic's citation bundles: its cited passages (at most four, its own references' first, as the
    finished section's bundles choose them), each widened by up to five neighbours on either side inside its section,
    only while they are seen. Every quoted passage is one the learner's reading observed."""

    if not coverage.qualifies:
        return []
    library = library or _Library(vault, repository, extraction_id)
    anchors = list(coverage.cited)[:_MAX_SOURCE_BUNDLES_PER_LO]
    by_reading: dict[str, list[str]] = {}
    for reading_id, span in anchors:
        by_reading.setdefault(reading_id, []).append(span)
    bundles: list[dict[str, Any]] = []
    for reading_id, spans in by_reading.items():
        reading = library.base if reading_id == library.base.extraction_id else next(
            (held for held in library._by_source.values() if held is not None and held.extraction_id == reading_id),
            None)
        if reading is None or reading.revision is None:
            return []
        intervals: dict[str, list[tuple[int, int]]] = {}
        for span in spans:
            section_id = reading.section_of[span]
            order = reading.sections[section_id]
            at = order.index(span)
            start = end = at
            while start > 0 and at - (start - 1) <= _SOURCE_BUNDLE_RADIUS and order[start - 1] in reading.seen:
                start -= 1
            while (end < len(order) - 1 and (end + 1) - at <= _SOURCE_BUNDLE_RADIUS
                   and order[end + 1] in reading.seen):
                end += 1
            intervals.setdefault(section_id, []).append((start, end))
        for section_id in sorted(intervals, key=lambda section: reading.index[reading.sections[section][0]]):
            order = reading.sections[section_id]
            merged: list[tuple[int, int]] = []
            for start, end in sorted(intervals[section_id]):
                if merged and start <= merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                else:
                    merged.append((start, end))
            for start, end in merged:
                bundles.append(citation_bundle(
                    [reading.block_by_span[span] for span in order[start:end + 1]],
                    extraction_id=reading.extraction_id, learning_object_id=coverage.learning_object_id,
                    path=reading.path, source_id=str(reading.source_id), revision_id=str(reading.revision["id"]),
                    section_id=section_id,
                ))
    return bundles


@dataclass(frozen=True)
class SectionPartRead:
    """One unfinished section with seen passages: whether its chapter's topics are in, the topics citing it that
    need questions and nobody owns (``candidates``), those of them that qualify, with their grounding."""

    section_id: str
    settled: bool
    candidates: tuple[str, ...] = ()
    coverage: Mapping[str, TopicCoverage] = field(default_factory=dict)
    grounding: Mapping[str, list[dict[str, Any]]] = field(default_factory=dict)

    @property
    def qualifying(self) -> tuple[str, ...]:
        return tuple(lo for lo in self.candidates if lo in self.grounding)

    @property
    def state(self) -> str:
        if not self.settled:
            return BEFORE_BUILD
        if self.qualifying:
            return OWED
        return READ_FURTHER if self.candidates else NOTHING


_MEMO: dict[tuple[str, str], tuple[tuple[Any, ...], dict[str, SectionPartRead]]] = {}
_MEMO_LOCK = threading.Lock()


def _fingerprint(vault: LoadedVault, repository: Any, progress: list[dict[str, Any]]) -> tuple[Any, ...]:
    return (
        id(vault),
        seen_marker(repository),
        repository.queue_revision()["revision"],
        len(repository.topic_question_work_rows()),
        tuple((row["section_id"], row.get("completed_at"), row.get("generation_batch_id")) for row in progress),
    )


def assess(vault: LoadedVault, repository: Any, extraction_id: str, *,
           topics_settled: Callable[[str], tuple[bool, str | None]], remember: bool = True
           ) -> dict[str, SectionPartRead]:
    """Every unfinished section of ``extraction_id`` the learner has seen passages of, by section id.

    ``topics_settled(section_id)`` says whether the section's chapter's build has settled
    (``add_source.section_topics_settled``). A section whose chapter has not settled is only that: its topics are
    still being written, and none is claimed from it. ``remember`` False neither reads nor keeps the remembered
    answer (a caller whose ``topics_settled`` is not the shared one)."""

    progress = repository.reader_section_progress_for(extraction_id)
    key = (str(getattr(repository, "sqlite_path", id(repository))), str(extraction_id))
    fingerprint = _fingerprint(vault, repository, progress)
    with _MEMO_LOCK:
        held = _MEMO.get(key) if remember else None
    if held is not None and held[0] == fingerprint:
        return held[1]
    finished = {str(row["section_id"]) for row in progress if row.get("completed_at")}
    library = _Library(vault, repository, extraction_id)
    reading = library.base
    sections: dict[str, SectionPartRead] = {}
    read = [section_id for section_id, spans in reading.sections.items()
            if section_id not in finished and any(span in reading.seen for span in spans)]
    for section_id in read:
        settled, _ended = topics_settled(section_id)
        if not settled:
            sections[section_id] = SectionPartRead(section_id, False)
            continue
        candidates = section_generation_candidates(vault, repository, extraction_id=extraction_id,
                                                   section_id=section_id)
        owned = repository.topic_question_work_for(candidates, purpose=READER_FIRST_SET)
        candidates = [lo for lo in candidates if lo not in owned]
        coverage = {lo: _coverage(library, vault.learning_objects[lo]) for lo in candidates
                    if lo in vault.learning_objects}
        grounding = {lo: bundles for lo, cover in coverage.items() if cover.qualifies
                     for bundles in [seen_grounding(vault, repository, extraction_id, cover, library)] if bundles}
        sections[section_id] = SectionPartRead(section_id, True, tuple(candidates), coverage, grounding)
    if remember:
        with _MEMO_LOCK:
            _MEMO[key] = (fingerprint, sections)
    return sections


def read_readings(repository: Any) -> list[str]:
    """The current reading of every book the learner has seen passages of (on it, or on an earlier reading whose
    passages carry over by exact alias)."""

    out: dict[str, None] = {}
    for extraction_id in seen_readings(repository):
        source_id = reading_source(repository, extraction_id)
        current = current_reading(repository, source_id) if source_id else None
        if current:
            out[str(current)] = None
    return list(out)


def reconcile_part_read(
    vault: LoadedVault,
    repository: Any,
    *,
    extraction_id: str,
    enqueue: TopicEnqueue,
    topics_settled: Callable[[str], tuple[bool, str | None]],
    claim_repository: Any = None,
    remember: bool = True,
) -> list[str]:
    """Claim the topics of ``extraction_id``'s unfinished sections that newly qualify, and queue their first sets.

    Each section's qualifying topics nobody owns are claimed in one transaction with their seen grounding
    (``claim_section_topics``, trigger :data:`PART_READ`); its stamp moves to ``topic_managed`` (it is not finished:
    its later finish claims whatever is left through the same claims). A section finished meanwhile, or stamped
    otherwise, is left to its finish. ``enqueue`` records into ``claim_repository``'s transaction and starts nothing;
    the caller starts the queue. Returns the batches queued (none when nothing newly qualifies)."""

    batches = []
    for section in assess(vault, repository, extraction_id, topics_settled=topics_settled,
                          remember=remember).values():
        if not section.qualifying:
            continue
        row = repository.reader_section_progress_row(extraction_id, section.section_id)
        if row is None or row.get("completed_at"):
            continue
        stamp = row.get("generation_batch_id")
        if stamp not in (None, TOPIC_MANAGED):
            continue
        owned = repository.topic_question_work_for(section.qualifying, purpose=READER_FIRST_SET)
        lo_ids = [lo for lo in section.qualifying if lo not in owned]  # one claimed meanwhile through another section
        if not lo_ids:
            continue
        batch_id = claim_section_topics(
            claim_repository or repository, extraction_id=extraction_id, section_id=section.section_id,
            lo_ids=lo_ids, refs=[bundle for lo in lo_ids for bundle in section.grounding[lo]], enqueue=enqueue,
            from_stamp=stamp, requested=section_topic_requests(vault, repository, lo_ids), trigger=PART_READ,
        )
        if batch_id is not None:
            batches.append(batch_id)
    return batches
