"""Which learning objects a section or span holds: the Reader's mapping, as a dependency-light leaf.

The guide plan, the Reader and data capture's one read of exposures all ask this
(:mod:`learnloop.data_capture.reading_exposures`). It lived in ``reader.reader_guidance`` and
``reader.reader_progression``, which still export these names; the scoreboard and the rebuild must reach it and
cannot import the Reader, so it sits here (landing ruling R7). Vault models, the alias authority and the repository's
reads only.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from learnloop.content.sources.span_aliases import SpanTranslator
from learnloop.vault.models import LoadedVault, SourceRef, learning_object_facet_union

if TYPE_CHECKING:
    from learnloop.db.repositories import Repository

SPAN_LOCATOR_RE = re.compile(r"^span:([^/]+)/(.+)$")
_TIME_LOCATOR_RE = re.compile(r"^t=(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?$")
_FURNITURE_TYPES = {"PageHeader", "PageFooter", "TableOfContents"}


def _extras(value: Any) -> dict[str, Any]:
    extra = getattr(value, "model_extra", None)
    return extra if isinstance(extra, dict) else {}


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").split()).casefold()


def canonical_note_ids(vault: LoadedVault, artifact: dict[str, Any]) -> set[str]:
    """Resolve legacy note-id provenance to the source-library artifact."""

    artifact_uri = str(artifact.get("canonical_uri") or "")
    note_ids: set[str] = set()
    for note in vault.notes.values():
        canonical = _extras(note).get("canonical_source")
        canonical = canonical if isinstance(canonical, dict) else {}
        note_uri = str(canonical.get("canonical_uri") or canonical.get("original_uri") or "")
        if artifact_uri and note_uri == artifact_uri:
            note_ids.add(note.id)
    return note_ids


def _ref_matches_source(ref: SourceRef, source_id: str, note_ids: set[str]) -> bool:
    extra = _extras(ref)
    return (
        str(extra.get("source_id") or "") == source_id
        or (ref.ref_type == "canonical_source" and ref.ref_id == source_id)
        or ref.ref_id in note_ids
    )


def span_for_ref(ref: SourceRef, *, source_id: str, extraction_id: str,
                  note_ids: set[str], blocks: list[Any], translator: Any = None,
                  accept_moved: bool = False) -> str | None:
    """The span of the viewed reading a provenance ref names, or None.

    ``translator`` (a ``span_aliases.SpanTranslator`` onto ``extraction_id``)
    resolves a ref made on another reading of the book (a re-read): the same
    text there, or with ``accept_moved`` the same place with changed text
    (flagged where it is shown, :func:`anchor_for_ref`)."""

    anchor = anchor_for_ref(ref, source_id=source_id, extraction_id=extraction_id, note_ids=note_ids,
                             blocks=blocks, translator=translator)
    if anchor is None or (anchor[1] != ANCHOR_CURRENT and not accept_moved):
        return None
    return anchor[0]


ANCHOR_CURRENT = "current"
ANCHOR_MOVED = "needs_reanchor"


def anchor_for_ref(ref: SourceRef, *, source_id: str, extraction_id: str, note_ids: set[str],
                    blocks: list[Any], translator: Any = None) -> tuple[str, str] | None:
    """``(span id, "current" | "needs_reanchor")`` for a ref on the viewed reading.

    The one alias authority (``content.sources.span_aliases``) resolves a span
    of another reading of the book: an exact alias is ``current``; a
    geometry/section alias (the same place, changed text) is
    ``needs_reanchor``, tried only after the time and quote matches; no alias
    names nothing. Never the viewed reading with the old span id."""

    if not _ref_matches_source(ref, source_id, note_ids):
        return None

    in_view = {block.span_id for block in blocks}
    extra = _extras(ref)
    ref_extraction = str(extra.get("extraction_id") or "")
    locator = str(ref.locator or "")
    match = SPAN_LOCATOR_RE.match(locator)
    moved: str | None = None
    if match is not None and (match.group(1) == extraction_id or ref_extraction == extraction_id):
        span_id = match.group(2)
        if span_id in in_view:
            return span_id, ANCHOR_CURRENT
    elif match is not None and translator is not None:
        resolution = translator.resolve(match.group(1), match.group(2))
        if resolution.span_id is not None and resolution.span_id in in_view:
            if resolution.exact:
                return resolution.span_id, ANCHOR_CURRENT
            moved = resolution.span_id

    # Caption IR keeps the cue locator on extractor_block_id. Match a cited
    # video segment to the first overlapping cue so transcript guidance can use
    # the same goal/latent ranking as text and PDF sources.
    time_match = _TIME_LOCATOR_RE.match(locator)
    if time_match is not None:
        ref_start = float(time_match.group(1))
        ref_end = float(time_match.group(2)) if time_match.group(2) is not None else ref_start
        timed: list[tuple[float, str]] = []
        for block in blocks:
            cue_match = _TIME_LOCATOR_RE.match(str(block.extractor_block_id or ""))
            if cue_match is None:
                continue
            cue_start = float(cue_match.group(1))
            cue_end = float(cue_match.group(2)) if cue_match.group(2) is not None else cue_start
            if cue_end >= ref_start and cue_start <= ref_end:
                timed.append((abs(cue_start - ref_start), block.span_id))
        if timed:
            return min(timed)[1], ANCHOR_CURRENT

    # Older canonical refs carry a quote and a heading-path locator rather than
    # an extraction span.  An unambiguous quote is the safest compatibility path.
    quote = normalize_text(ref.quote)
    if len(quote) >= 8:
        matches = [block.span_id for block in blocks if quote in normalize_text(block.text)]
        if len(matches) == 1:
            return matches[0], ANCHOR_CURRENT
    if moved is not None:
        return moved, ANCHOR_MOVED
    return None


def extraction_sections(ir: Any) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    """Derive the Reader's guide sections from one extraction's IR.

    Returns ``(section_rows, block_by_span, span_to_section)``. Shared by the
    guide plan and the quick-check producer so both agree on what one
    "section" is (readable, non-furniture spans per unit)."""

    blocks = sorted(ir.blocks, key=lambda block: block.ordinal)
    block_by_span = {block.span_id: block for block in blocks}
    span_to_section: dict[str, str] = {}
    section_rows: list[dict[str, Any]] = []

    units = sorted(ir.units, key=lambda unit: unit.ordinal)
    if not units:
        # Valid but unusual IRs may omit units.  Treat the extraction as one
        # section so the Reader still has a coherent progress boundary.
        units = [type("ReaderUnit", (), {
            "unit_id": "whole-source", "label": "This source", "ordinal": 0,
            "span_ids": [block.span_id for block in blocks],
        })()]

    for unit in units:
        readable = [
            span_id for span_id in unit.span_ids
            if span_id in block_by_span and block_by_span[span_id].block_type not in _FURNITURE_TYPES
        ]
        if not readable:
            continue
        for span_id in readable:
            span_to_section[span_id] = unit.unit_id
        section_rows.append({
            "id": unit.unit_id,
            "label": unit.label or "Untitled section",
            "start_span_id": readable[0],
            "end_span_id": readable[-1],
            "span_ids": readable,
        })
    return section_rows, block_by_span, span_to_section


# The mapping comes in two forms (RO2 landing ruling R6). The ``*_in_ir`` functions take the
# extraction's document IR from their caller: adaptive difficulty passes the one its material view
# hands out (``MaterialView.document_ir``, the reading chokepoint, after the withheld rule), because
# a raw ``source_document_*`` read inside AD's operation is refused by AD's guard and rolls back
# every AD write of the serve. The raw-loading versions below them are thin wrappers for callers
# outside AD (the Reader, data capture, the router's reading reads, gap sources).


def section_id_in_ir(ir: Any, span_id: str) -> str | None:
    """The normalized section of ``ir`` holding one reader span."""

    _sections, _block_by_span, span_to_section = extraction_sections(ir)
    section = span_to_section.get(span_id)
    return str(section) if section is not None else None


def section_id_for_span(
    repository: Repository, *, extraction_id: str, span_id: str
) -> str | None:
    """Resolve one reader span to its containing normalized section (loads the IR; outside AD)."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return None
    return section_id_in_ir(ir, span_id)


def learning_objects_for_span_in_ir(
    vault: LoadedVault,
    repository: Repository,
    ir: Any,
    *,
    extraction_id: str,
    span_id: str,
) -> list[str]:
    """:func:`learning_objects_for_span` over a given IR."""

    section_id = section_id_in_ir(ir, span_id)
    if section_id is None:
        return []
    return learning_objects_for_section_in_ir(vault, repository, ir, extraction_id=extraction_id,
                                              section_id=section_id)


def learning_objects_for_span(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    span_id: str,
) -> list[str]:
    """Provenance-linked Learning Objects available as promotion targets (loads the IR; outside AD)."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return []
    return learning_objects_for_span_in_ir(vault, repository, ir, extraction_id=extraction_id, span_id=span_id)


def learning_objects_for_section(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
    section_id: str,
) -> list[str]:
    """Active Learning Objects whose provenance cites spans inside the section (loads the IR; outside AD).

    See :func:`learning_objects_for_section_in_ir`."""

    if repository.get_extraction_run(extraction_id) is None:
        return []
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return []
    return learning_objects_for_section_in_ir(vault, repository, ir, extraction_id=extraction_id,
                                              section_id=section_id)


def learning_objects_for_section_in_ir(
    vault: LoadedVault,
    repository: Repository,
    ir: Any,
    *,
    extraction_id: str,
    section_id: str,
) -> list[str]:
    """Active Learning Objects whose provenance cites spans inside the section of ``ir``.

    Reuses the guide plan's span resolution (`span_for_ref`) so item passages,
    quick-checks, and progression triggers agree on what belongs to a section.
    Returns a sorted, de-duplicated id list; empty when the section has no
    provenance-linked LOs (thin citation — see the source-finished sweep).
    """

    run = repository.get_extraction_run(extraction_id)
    if run is None:
        return []
    revision = repository.get_source_revision(run["revision_id"])
    source_id = str((revision or {}).get("source_id") or "")
    section_rows, block_by_span, _span_to_section = extraction_sections(ir)
    section = next((row for row in section_rows if row["id"] == section_id), None)
    if section is None:
        return []
    section_spans = set(section["span_ids"])
    blocks = [block_by_span[span_id] for span_id in section["span_ids"] if span_id in block_by_span]

    artifact = repository.get_source_artifact(source_id) or {}
    note_ids = canonical_note_ids(vault, artifact)
    # Refs made on an earlier reading of the book resolve through the one
    # alias authority (re-read safety): the same place counts for which LOs a
    # section holds, even when its text changed.
    translator = SpanTranslator(repository, extraction_id)

    matched: set[str] = set()
    for learning_object in vault.learning_objects.values():
        if learning_object.status != "active":
            continue
        refs = list(learning_object.provenance.source_refs)
        for facet_id in learning_object_facet_union(learning_object):
            facet = vault.evidence_facets.get(vault.canonical_facet_id(str(facet_id)))
            if facet is not None:
                refs.extend(facet.provenance.source_refs)
        for ref in refs:
            span_id = span_for_ref(
                ref,
                source_id=source_id,
                extraction_id=extraction_id,
                note_ids=note_ids,
                blocks=blocks,
                translator=translator,
                accept_moved=True,
            )
            if span_id is not None and span_id in section_spans:
                matched.add(learning_object.id)
                break
    return sorted(matched)


def learning_objects_by_section(
    vault: LoadedVault,
    repository: Repository,
    *,
    extraction_id: str,
) -> dict[str, list[str]]:
    """Every section of an extraction with its provenance-linked Learning Objects.

    The same answer as :func:`learning_objects_for_section` for each section
    (each section's refs resolve against that section's own blocks), with the
    IR, the artifact and the alias translator loaded once. RW6a's "Since last
    time" reads it for the LOs a source teaches. Sections with no linked LO
    are left out.
    """

    run = repository.get_extraction_run(extraction_id)
    if run is None:
        return {}
    revision = repository.get_source_revision(run["revision_id"])
    source_id = str((revision or {}).get("source_id") or "")
    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return {}
    section_rows, block_by_span, _span_to_section = extraction_sections(ir)

    artifact = repository.get_source_artifact(source_id) or {}
    note_ids = canonical_note_ids(vault, artifact)
    translator = SpanTranslator(repository, extraction_id)

    refs_by_lo: list[tuple[str, list[Any]]] = []
    for learning_object in vault.learning_objects.values():
        if learning_object.status != "active":
            continue
        refs = list(learning_object.provenance.source_refs)
        for facet_id in learning_object_facet_union(learning_object):
            facet = vault.evidence_facets.get(vault.canonical_facet_id(str(facet_id)))
            if facet is not None:
                refs.extend(facet.provenance.source_refs)
        if refs:
            refs_by_lo.append((learning_object.id, refs))

    out: dict[str, list[str]] = {}
    for section in section_rows:
        section_spans = set(section["span_ids"])
        blocks = [block_by_span[span_id] for span_id in section["span_ids"] if span_id in block_by_span]
        matched: set[str] = set()
        for learning_object_id, refs in refs_by_lo:
            for ref in refs:
                span_id = span_for_ref(
                    ref,
                    source_id=source_id,
                    extraction_id=extraction_id,
                    note_ids=note_ids,
                    blocks=blocks,
                    translator=translator,
                    accept_moved=True,
                )
                if span_id is not None and span_id in section_spans:
                    matched.add(learning_object_id)
                    break
        if matched:
            out[str(section["id"])] = sorted(matched)
    return out
