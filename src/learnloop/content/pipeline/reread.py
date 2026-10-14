"""Reading a book again, safely (re-read safety, 2026-10-14).

The GLM-OCR live check on backup copies of the owner's books found that the
card's "Read it again with text recognition" broke a studied book today,
whatever the engine (docs/reviews/reread-safety.md):

* **E1.** The re-read read whatever sat at the book's ``canonical_uri`` (on
  the owner's machine, a git-LFS pointer), registered it as a new revision and
  made that revision current before extracting it; the extraction failed and
  the book could no longer be opened from the Library.
* **E2.** With the right bytes, the new reading dropped what the learner had
  on the old one: section progress, the Guide's passages, LO highlights, the
  study-map selection (and with it any held-out exam marks), annotations, and
  silently moved source-object citations and the saved reading place.

This module holds the import side of the fix:

* :func:`original_bytes`: an import naming an existing book reads its current
  revision's own bytes (the originals store first, then the recorded files),
  verified against the revision's hash, and refuses plainly otherwise;
* :func:`adopt_revision`: a book's current revision moves only to a revision
  with a completed reading (``register_source_revision`` no longer moves it
  for a book that has one);
* :func:`carry_over`: after a completed reading on a revision that already had
  one, the aliases are recorded (``content.sources.span_aliases``, the one
  authority every reader of old span ids routes through), and section
  progress, the unit selection (exam use modes included) and annotations
  move to the new reading;
* :func:`unread_current_revision` / :func:`restore_readable_revision`: the E1
  state and its one-tap repair;
* :func:`reread_plan`: what a re-read will read, cost and carry, for the
  card's confirmation.

Nothing here changes persisted meaning: replay reads none of these tables
(``rebuild --shadow`` was identical before and after a re-read).
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.content.sources import span_aliases
from learnloop.ingest.hashing import asset_hash
from learnloop.reader.annotations import AnnotationError, reanchor_annotation
from learnloop.reader.reader_guidance import extraction_sections

logger = logging.getLogger(__name__)

ORIGINAL_CHANGED_CODE = "original_changed"
ORIGINAL_CHANGED_MESSAGE = (
    "The file this book came from has changed or is missing, so it can't be read again. "
    "The reading you have stays as it is."
)


# --- E1: the bytes a re-read reads ----------------------------------------------------


def _local_path(uri: str | None) -> Path | None:
    if not uri or uri.startswith(("http://", "https://")):
        return None
    candidate = uri[7:] if uri.startswith("file://") else uri
    path = Path(candidate).expanduser()
    return path if path.is_file() else None


def current_revision(repository: Any, source_id: str) -> dict[str, Any] | None:
    artifact = repository.get_source_artifact(source_id)
    if artifact is None:
        return None
    revision_id = artifact.get("current_revision_id")
    if revision_id:
        revision = repository.get_source_revision(revision_id)
        if revision is not None:
            return revision
    revisions = repository.source_revisions_for(source_id)
    return revisions[-1] if revisions else None


def original_bytes(repository: Any, vault_root: Path, source_id: str, *, fetch_url=None,
                   clock: Clock | None = None) -> Any | None:
    """The current revision's own bytes for an import that names an existing
    book, as ``FetchedBytes``; ``None`` when the book (or its revision) does
    not exist yet, so the import fetches as before (:func:`revision_bytes`)."""

    artifact = repository.get_source_artifact(source_id)
    revision = current_revision(repository, source_id) if artifact is not None else None
    if artifact is None or revision is None:
        return None
    return revision_bytes(vault_root, revision, artifact, fetch_url=fetch_url, clock=clock)


def revision_bytes(vault_root: Path, revision: Mapping[str, Any], artifact: Mapping[str, Any] | None, *,
                   fetch_url=None, clock: Clock | None = None) -> Any:
    """One revision's own bytes, as ``FetchedBytes``.

    Read from the originals store first, then the revision's ``original_uri``
    and the book's ``canonical_uri`` when they are local files, then (a link)
    ``fetch_url(canonical_uri)``; the first whose hash is the revision's wins.
    Nothing else is ever read or registered: bytes that changed (a git-LFS
    pointer where the PDF was) or went missing refuse plainly."""

    from learnloop.content.pipeline.runner import FetchedBytes, IngestRunnerError
    from learnloop.ingest.originals import stored_original_path

    digest = str(revision.get("asset_hash") or "")
    original_uri = str(revision.get("original_uri") or "") or None
    canonical_uri = str((artifact or {}).get("canonical_uri") or "") or None
    candidates: list[Path] = []
    for path in (stored_original_path(vault_root, digest), _local_path(original_uri), _local_path(canonical_uri)):
        if path is not None and path not in candidates:
            candidates.append(path)
    for path in candidates:
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if asset_hash(raw) == digest:
            return FetchedBytes(
                raw_bytes=raw, content_type=None,
                original_uri=original_uri or path.resolve().as_uri(),
                retrieved_at=str(revision.get("retrieved_at") or utc_now_iso(clock)),
            )
    link = next((uri for uri in (canonical_uri, original_uri) if uri and uri.startswith(("http://", "https://"))),
                None)
    if fetch_url is not None and link:
        fetched = fetch_url(link)
        if fetched is not None and asset_hash(fetched.raw_bytes) == digest:
            return fetched
    raise IngestRunnerError(
        ORIGINAL_CHANGED_MESSAGE, code=ORIGINAL_CHANGED_CODE, retryable=False,
        details={"source_id": (artifact or {}).get("id") or revision.get("source_id"),
                 "revision_id": revision.get("id"), "looked_in": len(candidates)},
    )


def has_completed_reading(repository: Any, source_id: str) -> bool:
    return any(span_aliases.completed_readings(repository, str(revision["id"]))
               for revision in repository.source_revisions_for(source_id))


def adopt_revision(repository: Any, source_id: str, revision_id: str, *, clock: Clock | None = None) -> bool:
    """Make ``revision_id`` current once it has a completed reading: when the
    current one has none, or ``revision_id`` is newer. A failed import never
    gets here, so the previous revision stays current."""

    if not span_aliases.completed_readings(repository, revision_id):
        return False
    artifact = repository.get_source_artifact(source_id) or {}
    current_id = artifact.get("current_revision_id")
    if current_id == revision_id:
        return False
    order = [str(revision["id"]) for revision in repository.source_revisions_for(source_id)]
    current_read = bool(current_id) and bool(span_aliases.completed_readings(repository, str(current_id)))
    newer = current_id not in order or (revision_id in order and order.index(revision_id) > order.index(current_id))
    if current_read and not newer:
        return False
    repository.set_source_current_revision(source_id, revision_id, clock=clock)
    return True


# --- E1: the state and its repair ------------------------------------------------------


def unread_current_revision(repository: Any, source_id: str) -> dict[str, Any] | None:
    """The E1 state: the current revision has no completed reading while an
    older one has. ``{"current_revision_id", "readable_revision_id"}`` or None."""

    artifact = repository.get_source_artifact(source_id)
    current_id = (artifact or {}).get("current_revision_id")
    if not current_id or span_aliases.completed_readings(repository, str(current_id)):
        return None
    readable = [revision for revision in repository.source_revisions_for(source_id)
                if revision["id"] != current_id and span_aliases.completed_readings(repository, str(revision["id"]))]
    if not readable:
        return None
    return {"current_revision_id": str(current_id), "readable_revision_id": str(readable[-1]["id"])}


def restore_readable_revision(repository: Any, source_id: str, *, clock: Clock | None = None) -> str | None:
    """The one-tap repair: the book's newest revision with a completed reading
    becomes current again (nothing is deleted). Returns it, or None."""

    state = unread_current_revision(repository, source_id)
    if state is None:
        return None
    repository.set_source_current_revision(source_id, state["readable_revision_id"], clock=clock)
    return state["readable_revision_id"]


def unread_current_revisions(repository: Any) -> list[dict[str, Any]]:
    found = []
    for artifact in repository.all_source_artifacts():
        state = unread_current_revision(repository, str(artifact["id"]))
        if state is not None:
            found.append({"source_id": str(artifact["id"]), **state})
    return found


# --- E2: carrying what the old reading had ---------------------------------------------


def _label(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def unit_map(old_ir: Any, new_ir: Any, aliases: Mapping[str, tuple[str, str, float | None]]) -> dict[str, str | None]:
    """Each old unit's unit in the new reading (``None``: unresolved).

    The same unit id with the same label (both outline units, say), then
    ``reanchor_units`` (unit id + semantic hash, a unique semantic hash), then
    a unique label, then the new unit holding most of the old unit's spans
    through the aliases (more than half of them), then the new unit holding
    most of the old unit's pages (more than half of its blocks lie on pages
    only that unit holds: a coarser reading, one block per page, say)."""

    from learnloop.content.synthesis.source_unit_selection import reanchor_units

    new_by_id = {unit.unit_id: unit for unit in new_ir.units}
    new_by_label: dict[str, list[str]] = {}
    for unit in new_ir.units:
        new_by_label.setdefault(_label(unit.label), []).append(unit.unit_id)
    unit_of_span = {span: unit.unit_id for unit in new_ir.units for span in unit.span_ids}
    old_page = {block.span_id: block.page for block in old_ir.blocks if block.page is not None}
    new_page = {block.span_id: block.page for block in new_ir.blocks if block.page is not None}
    units_on_page: dict[int, set[str]] = {}
    for unit in new_ir.units:
        for span in unit.span_ids:
            if span in new_page:
                units_on_page.setdefault(new_page[span], set()).add(unit.unit_id)
    reanchored = reanchor_units(old_ir, new_ir)
    found: dict[str, str | None] = {}
    for unit in old_ir.units:
        same = new_by_id.get(unit.unit_id)
        if same is not None and _label(same.label) == _label(unit.label):
            found[unit.unit_id] = unit.unit_id
            continue
        if reanchored.get(unit.unit_id) is not None:
            found[unit.unit_id] = reanchored[unit.unit_id]
            continue
        labelled = new_by_label.get(_label(unit.label), []) if _label(unit.label) else []
        if len(labelled) == 1:
            found[unit.unit_id] = labelled[0]
            continue
        landed = Counter(unit_of_span[aliases[span][0]] for span in unit.span_ids
                         if span in aliases and aliases[span][0] in unit_of_span)
        top = landed.most_common(2)
        if top and top[0][1] * 2 > len(unit.span_ids) and (len(top) == 1 or top[1][1] < top[0][1]):
            found[unit.unit_id] = top[0][0]
            continue
        paged = Counter(next(iter(units_on_page[old_page[span]])) for span in unit.span_ids
                        if span in old_page and len(units_on_page.get(old_page[span], ())) == 1)
        top = paged.most_common(2)
        if top and top[0][1] * 2 > len(unit.span_ids) and (len(top) == 1 or top[1][1] < top[0][1]):
            found[unit.unit_id] = top[0][0]
        else:
            found[unit.unit_id] = None
    return found


def carry_progress(repository: Any, old_extraction_id: str, new_extraction_id: str, old_ir: Any, new_ir: Any,
                   units: Mapping[str, str | None], *, clock: Clock | None = None) -> dict[str, int]:
    """Section progress onto the new reading's sections. A new section is
    complete when every old section that lands in it was; how far it was read
    is the share of the spans of every old section landing in it (read or
    not) that were seen."""

    rows = repository.reader_section_progress_for(old_extraction_id)
    if not rows:
        return {"sections": 0, "carried": 0, "completed": 0}
    new_sections = {row["id"]: row for row in extraction_sections(new_ir)[0]}
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        target = units.get(str(row["section_id"]))
        if target is not None and target in new_sections:
            grouped.setdefault(target, []).append(row)
    # A new section is complete only if every old section landing there was;
    # one landed in by an old section never read counts as partly read.
    old_sections = {row["id"]: len(row["span_ids"]) for row in extraction_sections(old_ir)[0]}
    landing: Counter[str] = Counter(units[section] for section in old_sections if units.get(section) is not None)
    landing_spans: Counter[str] = Counter()
    for section, spans in old_sections.items():
        if units.get(section) is not None:
            landing_spans[str(units[section])] += max(spans, 1)
    carried: list[dict[str, Any]] = []
    for section_id, contributors in grouped.items():
        span_count = len(new_sections[section_id]["span_ids"])
        seen = sum(min(int(row.get("spans_seen") or 0), max(int(row.get("span_count") or 0), 1))
                   for row in contributors)
        total = max(landing_spans[section_id],
                    sum(max(int(row.get("span_count") or 0), 1) for row in contributors))
        complete = len(contributors) >= max(landing[section_id], 1) and all(row.get("completed_at") for row in contributors)
        stamps = sorted(str(row["completed_at"]) for row in contributors if row.get("completed_at"))
        revealed = sorted(str(row["revealed_at"]) for row in contributors if row.get("revealed_at"))
        batches = [row["generation_batch_id"] for row in contributors if row.get("generation_batch_id")]
        carried.append({
            "section_id": section_id,
            # Rounded down: a section partly read never shows as read through.
            "spans_seen": span_count if complete else min(span_count, span_count * min(seen, total) // total),
            "span_count": span_count,
            "revealed_at": revealed[0] if revealed else None,
            "completed_at": stamps[-1] if complete else None,
            "generation_batch_id": batches[0] if batches else None,
        })
    repository.carry_reader_section_progress(new_extraction_id, carried, clock=clock)
    return {"sections": len(rows), "carried": sum(len(group) for group in grouped.values()),
            "completed": sum(1 for row in carried if row["completed_at"])}


def carry_selection(repository: Any, old_extraction_id: str, new_extraction_id: str,
                    units: Mapping[str, str | None], *, clock: Clock | None = None) -> dict[str, Any] | None:
    """The study-map unit selection, its exam use modes included, onto the new
    reading. A unit that does not resolve is flagged ``needs_review``; a
    held-out mark on it stays in force through the old selection, which
    ``exam_material`` reads for every reading of the book (by label, and the
    whole reading when the label does not resolve: fail closed)."""

    if repository.get_unit_selection(new_extraction_id) is not None:
        return None
    stored = repository.get_unit_selection(old_extraction_id)
    if stored is None:
        return None
    needs_review: list[str] = list(stored.get("needs_review") or [])
    selected: list[str] = []
    for unit_id in stored.get("selected_unit_ids") or []:
        target = units.get(str(unit_id))
        if target is None:
            needs_review.append(str(unit_id))
        elif target not in selected:
            selected.append(target)
    overrides: list[dict[str, Any]] = []
    for override in stored.get("boundary_overrides") or []:
        target = units.get(str(override.get("unit_id")))
        if target is None:
            needs_review.append(str(override.get("unit_id")))
            continue
        moved = {key: value for key, value in dict(override).items() if key != "at_span_id"}
        moved["unit_id"] = target
        overrides.append(moved)
    modes: dict[str, str] = {}
    for unit_id, mode in (stored.get("exam_use_modes") or {}).items():
        target = units.get(str(unit_id))
        if target is None:
            needs_review.append(str(unit_id))
            continue
        # Two old units landing in one new unit: the more protective mode wins.
        if modes.get(target) != "held_out_evaluation":
            modes[target] = mode
    run = repository.get_extraction_run(new_extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    repository.upsert_unit_selection(
        extraction_id=new_extraction_id, source_id=revision.get("source_id"), revision_id=run.get("revision_id"),
        selected_unit_ids=selected, boundary_overrides=overrides, needs_review=list(dict.fromkeys(needs_review)),
        exam_use_modes=modes, exam_paper_metadata=stored.get("exam_paper_metadata") or {},
        role_override=stored.get("role_override"), clock=clock,
    )
    return {"selected": len(selected), "exam_use_modes": len(modes), "needs_review": len(set(needs_review))}


def carry_annotations(repository: Any, source_id: str, new_extraction_id: str, *,
                      clock: Clock | None = None) -> dict[str, int]:
    """Re-anchor every annotation of the book not yet on the new reading."""

    statuses: Counter[str] = Counter()
    cache: dict[str, Any] = {}
    for head in repository.annotations_for_source(source_id):
        anchor = (head or {}).get("anchor")
        if not anchor or anchor.get("extraction_id") == new_extraction_id:
            continue
        try:
            result = reanchor_annotation(repository, annotation_id=head["annotation"]["id"],
                                         new_extraction_id=new_extraction_id, clock=clock, block_results=cache)
        except AnnotationError:
            statuses["needs_reanchor"] += 1
            continue
        statuses[str(result["status"])] += 1
    return dict(statuses)


def carry_over(repository: Any, new_extraction_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
    """After a completed top-level reading on a revision that already had one:
    record the aliases from every earlier reading of the revision, then carry
    section progress, the unit selection and annotations from the reading the
    Reader showed until now. Idempotent (a retried import runs it again)."""

    previous = span_aliases.previous_readings(repository, new_extraction_id)
    if not previous:
        return None
    source_id = span_aliases.reading_source(repository, new_extraction_id)
    summary: dict[str, Any] = {"from_extraction_id": previous[0], "aliases": {}}
    for old in previous:
        counts = span_aliases.record_aliases(repository, old, new_extraction_id, clock=clock)
        if old == previous[0]:
            summary["aliases"] = counts
    old_ir = repository.load_document_ir(previous[0])
    new_ir = repository.load_document_ir(new_extraction_id)
    if old_ir is not None and new_ir is not None:
        aliases = span_aliases.alias_map(repository, previous[0], new_extraction_id)
        units = unit_map(old_ir, new_ir, aliases)
        summary["progress"] = carry_progress(repository, previous[0], new_extraction_id, old_ir, new_ir, units,
                                             clock=clock)
        summary["selection"] = carry_selection(repository, previous[0], new_extraction_id, units, clock=clock)
    if source_id is not None:
        summary["annotations"] = carry_annotations(repository, source_id, new_extraction_id, clock=clock)
    return summary


# --- the card's confirmation -----------------------------------------------------------


def page_label(pages: Sequence[int]) -> str:
    """0-based page indices as the learner counts them: "pages 14–39"."""

    ordered = sorted(set(int(page) for page in pages))
    runs: list[tuple[int, int]] = []
    for page in ordered:
        if runs and page == runs[-1][1] + 1:
            runs[-1] = (runs[-1][0], page)
        else:
            runs.append((page, page))
    parts = [f"{start + 1}" if start == end else f"{start + 1}–{end + 1}" for start, end in runs]
    return ("page " if len(ordered) == 1 else "pages ") + ", ".join(parts)


def cost_phrase(usd: float | None) -> str:
    if usd is None:
        return "cost unknown until the file is read"
    if usd <= 0:
        return "free"
    if usd < 0.01:
        return "less than $0.01"
    return f"about ${usd:.2f}"


def study_state(repository: Any, source_id: str, extraction_id: str | None) -> dict[str, int]:
    """What the learner has on this book that a re-read must carry."""

    from contextlib import closing

    from learnloop.db.connection import connect

    revisions = [str(revision["id"]) for revision in repository.source_revisions_for(source_id)]
    readings = [str(run["id"]) for run in span_aliases.source_readings(repository, source_id)]
    progress = [row for row in repository.reader_section_progress_for(extraction_id)] if extraction_id else []
    selection = repository.get_unit_selection(extraction_id) if extraction_id else None
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        def count(sql: str, values: Sequence[str]) -> int:
            if not values:
                return 0
            marks = ",".join("?" for _ in values)
            return int(connection.execute(sql.format(marks=marks), tuple(values)).fetchone()[0])

        links = count("SELECT COUNT(*) FROM entity_source_links WHERE extraction_id IN ({marks})", readings)
        citations = count("SELECT COUNT(*) FROM source_object_citations WHERE revision_id IN ({marks})", revisions)
    annotations = len(repository.annotations_for_source(source_id))
    return {
        "sections_read": sum(1 for row in progress if int(row.get("spans_seen") or 0) > 0 or row.get("completed_at")),
        "sections_completed": sum(1 for row in progress if row.get("completed_at")),
        "annotations": annotations,
        "links": links,
        "citations": citations,
        "selected_units": len((selection or {}).get("selected_unit_ids") or []),
        "held_out_units": sum(1 for mode in ((selection or {}).get("exam_use_modes") or {}).values()
                              if mode == "held_out_evaluation"),
    }


def _plural(count: int, noun: str, plural: str | None = None) -> str:
    return f"{count} {noun if count == 1 else (plural or noun + 's')}"


def reread_plan(vault: Any, repository: Any, source_id: str, *, glm: bool, upload_ok: bool,
                title: str | None = None) -> dict[str, Any]:
    """What reading this book again will read, cost and carry, in plain words.

    ``glm``: GLM-OCR (z.ai) reads it; else text recognition on this computer.
    ``needs_confirmation`` when the book has study state, or when z.ai would
    read it with the OK already given (no OK line would show the cost)."""

    from learnloop.content.pipeline.add_source import _completed_extraction
    from learnloop.ingest.extractors.glm_ocr import estimate
    from learnloop.ingest.originals import stored_original_path

    resolved = _completed_extraction(repository, source_id)
    extraction_id = resolved[1] if resolved else None
    run = repository.get_extraction_run(extraction_id) if extraction_id else None
    page_selection = list((run or {}).get("page_selection") or []) or None
    revision = current_revision(repository, source_id) or {}
    pages: int | None = len(page_selection) if page_selection else None
    if pages is None:
        path = stored_original_path(vault.root, str(revision.get("asset_hash") or ""))
        if path is not None:
            from learnloop.content.pipeline.jobs import _pdf_page_count

            pages = _pdf_page_count(path.read_bytes())
    settings = vault.config.ingest.pdf.glm_ocr.model_dump()
    priced = estimate(pages, settings, backend="api" if glm else "local")
    state = study_state(repository, source_id, extraction_id)
    has_state = any(state.values())
    scope = (f"{page_label(page_selection)} ({_plural(len(page_selection), 'page')}), as before"
             if page_selection else (f"all {_plural(pages, 'page')}" if pages else "the whole file"))
    who = (f"z.ai (GLM-OCR) reads it: {cost_phrase(priced['estimated_usd'])}" if glm
           else "Read on this computer: free")
    lines = [f"{scope[0].upper()}{scope[1:]}.", f"{who}."]
    kept: list[str] = []
    if state["sections_read"]:
        kept.append(f"your progress ({_plural(state['sections_read'], 'section')})")
    if state["annotations"]:
        kept.append(_plural(state["annotations"], "note"))
    if state["links"] or state["citations"]:
        kept.append("the passages your questions and notes cite")
    if state["selected_units"]:
        kept.append("your study-map chapters" + (" and held-out exam parts" if state["held_out_units"] else ""))
    if kept:
        joined = kept[0] if len(kept) == 1 else ", ".join(kept[:-1]) + " and " + kept[-1]
        lines.append(f"{joined[0].upper()}{joined[1:]} move to the new reading. "
                     "Anything that can't be matched is marked so you can place it again.")
    name = title or "this book"
    return {
        "source_id": source_id,
        "extraction_id": extraction_id,
        "page_selection": page_selection,
        "pages": pages,
        "estimated_usd": priced["estimated_usd"],
        "estimate": priced,
        "engine": "glm_ocr" if glm else "local",
        "study_state": state,
        "needs_confirmation": has_state or (glm and upload_ok),
        "title": f"Read {name} again with text recognition?",
        "lines": lines,
        "confirm_label": "Read it again",
        "cancel_label": "Not now",
    }
