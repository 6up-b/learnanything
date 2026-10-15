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
  progress, the unit selection and annotations move to the new reading. Exam
  and held-out marks never move (protection redesign, 2026-10-15): a reading
  of a protected book is withheld whole until the owner marks its exam
  material on it (``exam_material`` rule 4, ``exam_marking``);
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
from learnloop.content.sources.exam_material import PROTECTION_MARK_KEY, source_marks
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
    """The study-map unit selection onto the new reading: its chapters and
    boundary overrides (a unit that does not resolve is flagged
    ``needs_review``) and the paper's metadata. Never its exam use modes or
    the owner's protection mark (protection redesign, 2026-10-15): protection
    is marked on each reading by the owner, and until it is, a reading of a
    protected book is withheld whole (``exam_material`` rule 4). A selection
    the owner's marking already made on the new reading (no chapters yet)
    keeps its marks and takes the chapters; one with chapters is left as it
    is (idempotent)."""

    existing = repository.get_unit_selection(new_extraction_id)
    if existing is not None and (existing.get("selected_unit_ids") or existing.get("boundary_overrides")):
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
    # The paper's metadata moves; the old reading's protection mark never does.
    metadata = {key: value for key, value in dict(stored.get("exam_paper_metadata") or {}).items()
                if key != PROTECTION_MARK_KEY}
    kept = existing or {}
    metadata.update(dict(kept.get("exam_paper_metadata") or {}))
    run = repository.get_extraction_run(new_extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    repository.upsert_unit_selection(
        extraction_id=new_extraction_id, source_id=revision.get("source_id"), revision_id=run.get("revision_id"),
        selected_unit_ids=selected, boundary_overrides=overrides, needs_review=list(dict.fromkeys(needs_review)),
        exam_use_modes=dict(kept.get("exam_use_modes") or {}), exam_paper_metadata=metadata,
        role_override=kept.get("role_override") or stored.get("role_override"), clock=clock,
    )
    return {"selected": len(selected), "needs_review": len(set(needs_review))}


def carry_annotations(repository: Any, source_id: str, new_extraction_id: str, *,
                      clock: Clock | None = None) -> dict[str, int]:
    """Re-anchor onto the new reading every annotation of the book anchored on
    an EARLIER reading of its revision. One anchored on a newer reading, or on
    another revision, stays where it is: annotations never move backward
    (Codex review F6)."""

    earlier = set(span_aliases.previous_readings(repository, new_extraction_id))
    statuses: Counter[str] = Counter()
    cache: dict[str, Any] = {}
    for head in repository.annotations_for_source(source_id):
        anchor = (head or {}).get("anchor")
        if not anchor or anchor.get("extraction_id") not in earlier:
            continue
        try:
            result = reanchor_annotation(repository, annotation_id=head["annotation"]["id"],
                                         new_extraction_id=new_extraction_id, clock=clock, block_results=cache)
        except AnnotationError:
            statuses["needs_reanchor"] += 1
            continue
        statuses[str(result["status"])] += 1
    return dict(statuses)


def _newest_with(readings: Sequence[str], has: Any) -> str:
    """The newest of ``readings`` (newest first) that has the state, else the newest."""

    return next((reading for reading in readings if has(reading)), readings[0])


def carry_over(repository: Any, new_extraction_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
    """After a completed top-level reading on a revision that already had one:
    record the aliases from every earlier reading of the revision, then carry
    section progress, the unit selection and annotations onto it. Idempotent
    (a retried import, or the card's "Finish moving them", runs it again).

    Only onto the reading the Reader opens (Codex review F6): an import whose
    extraction cache hands back an older reading carries nothing, so nothing
    moves backward. Progress and the selection come from the newest earlier
    reading that has them (one never shown, say, whose own carry did not
    finish, does not hide the learner's)."""

    previous = span_aliases.previous_readings(repository, new_extraction_id)
    if not previous:
        return None
    source_id = span_aliases.reading_source(repository, new_extraction_id)
    current = span_aliases.current_reading(repository, source_id) if source_id is not None else None
    if current != new_extraction_id:
        return {"skipped": "not_the_current_reading", "current_extraction_id": current}
    summary: dict[str, Any] = {"from_extraction_id": previous[0], "aliases": {}}
    for old in previous:
        counts = span_aliases.record_aliases(repository, old, new_extraction_id, clock=clock)
        if old == previous[0]:
            summary["aliases"] = counts
    new_ir = repository.load_document_ir(new_extraction_id)
    if new_ir is not None:
        for kind, has in (("progress", lambda reading: bool(repository.reader_section_progress_for(reading))),
                          ("selection", lambda reading: repository.get_unit_selection(reading) is not None)):
            origin = _newest_with(previous, has)
            old_ir = repository.load_document_ir(origin)
            if old_ir is None:
                continue
            units = unit_map(old_ir, new_ir, span_aliases.alias_map(repository, origin, new_extraction_id))
            if kind == "progress":
                summary["progress"] = carry_progress(repository, origin, new_extraction_id, old_ir, new_ir, units,
                                                     clock=clock)
            else:
                summary["selection"] = carry_selection(repository, origin, new_extraction_id, units, clock=clock)
    if source_id is not None:
        summary["annotations"] = carry_annotations(repository, source_id, new_extraction_id, clock=clock)
    return summary


# --- a carry-over that did not finish (Codex review F7) --------------------------------

#: The import job's payload names the reading it owes a carry-over (before
#: that reading completes) and, once the carry-over finished, the same reading
#: again: a carry-over that failed or was interrupted stays visible on the
#: book's card and in doctor until it is finished.
CARRY_OWED_KEY = "carry_over_for"
CARRY_DONE_KEY = "carry_over_done"
CARRY_INCOMPLETE_LINE = "Your progress and notes didn't all move to the new reading"
CARRY_INCOMPLETE_ACTION = "Finish moving them"
CARRY_INCOMPLETE_DETAILS = (
    "The new reading is ready, but moving your progress, study map and notes to it didn't finish. "
    "Nothing is lost: they are still on the reading you had."
)


def owes_carry(repository: Any, revision_id: str, extraction_id: str) -> bool:
    """Whether a reading of ``revision_id`` would owe a carry-over: the
    revision has another completed top-level reading."""

    return any(str(run["id"]) != extraction_id for run in span_aliases.completed_readings(repository, revision_id))


def carry_owed(repository: Any, source_id: str) -> dict[str, Any] | None:
    """The carry-over a book still owes its current reading, or None:
    ``{"job_id", "extraction_id"}`` of the import that did not finish it."""

    current = reread_reading(repository, source_id)
    if current is None or not span_aliases.previous_readings(repository, current):
        return None
    for job in repository.ingest_jobs_for_source(("import",), source_id):
        payload = job.get("payload") or {}
        if payload.get(CARRY_OWED_KEY) == current:
            if payload.get(CARRY_DONE_KEY) == current:
                return None
            return {"job_id": str(job["id"]), "extraction_id": current}
    return None


def mark_carried(repository: Any, job_id: str, extraction_id: str) -> None:
    job = repository.get_ingest_job(job_id) or {}
    payload = dict(job.get("payload") or {})
    if payload.get(CARRY_DONE_KEY) != extraction_id:
        repository.update_ingest_job_payload(job_id, {**payload, CARRY_DONE_KEY: extraction_id})


def finish_carry_over(repository: Any, source_id: str, *, clock: Clock | None = None) -> dict[str, Any] | None:
    """The card's "Finish moving them" and ``doctor --fix-state``: run the
    owed carry-over again (idempotent) and record it done. None when nothing
    is owed. Raises what the carry-over raises (still owed then)."""

    owed = carry_owed(repository, source_id)
    if owed is None:
        return None
    summary = carry_over(repository, owed["extraction_id"], clock=clock)
    mark_carried(repository, owed["job_id"], owed["extraction_id"])
    return {"extraction_id": owed["extraction_id"], "carried_over": summary}


# --- the card's confirmation -----------------------------------------------------------

#: The re-read confirmation's line for a book with exam material marked on it.
HELD_BACK_PLAN_LINE = ("Your exam material isn't moved: the new reading stays out of explanations, questions "
                       "and search until you mark its exam material on the book's card.")


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


def reread_reading(repository: Any, source_id: str) -> str | None:
    """The completed top-level reading the Reader opens for a book (the one a
    re-read replaces): never a page repair's child run, whose one page would
    become the whole next reading (Codex review F4)."""

    extraction_id = span_aliases.current_reading(repository, source_id)
    run = repository.get_extraction_run(extraction_id) if extraction_id else None
    if run is None or run.get("status") != "completed" or run.get("parent_extraction_id") is not None:
        return None
    return str(extraction_id)


def _engine_line(backend: str | None, settings: Mapping[str, Any], usd: float | None) -> tuple[str, str]:
    """``(engine, who reads it)`` for the confirmation: hosted GLM-OCR (z.ai),
    the owner's own GLM-OCR server (on this computer or another), or text
    recognition on this computer (Codex review F9)."""

    if backend == "api":
        return "glm_ocr", f"z.ai (GLM-OCR) reads it: {cost_phrase(usd)}"
    if backend == "local":
        from learnloop.ingest.extractors.glm_ocr import LOCAL_URL, is_loopback_url

        here = is_loopback_url(str(settings.get("local_url") or LOCAL_URL))
        return "glm_ocr_local", ("GLM-OCR on this computer reads it: free" if here
                                 else "Your GLM-OCR server reads it: free")
    return "local", "Read on this computer: free"


def reread_plan(vault: Any, repository: Any, source_id: str, *, backend: str | None, upload_ok: bool,
                title: str | None = None) -> dict[str, Any]:
    """What reading this book again will read, cost and carry, in plain words.

    ``backend``: the GLM-OCR backend that reads it (``"api"``: z.ai,
    ``"local"``: the owner's own server; ``glm_ocr.selected_backend``), else
    None: text recognition on this computer. The pages and the study state are
    the reading the Reader opens (:func:`reread_reading`).
    ``needs_confirmation`` when the book has study state, or when z.ai would
    read it with the OK already given (no OK line would show the cost)."""

    from learnloop.ingest.extractors.glm_ocr import estimate
    from learnloop.ingest.originals import stored_original_path

    extraction_id = reread_reading(repository, source_id)
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
    priced = estimate(pages, settings, backend="api" if backend == "api" else "local")
    state = study_state(repository, source_id, extraction_id)
    has_state = any(state.values())
    scope = (f"{page_label(page_selection)} ({_plural(len(page_selection), 'page')}), as before"
             if page_selection else (f"all {_plural(pages, 'page')}" if pages else "the whole file"))
    engine, who = _engine_line(backend, settings, priced["estimated_usd"])
    lines = [f"{scope[0].upper()}{scope[1:]}.", f"{who}."]
    kept: list[str] = []
    if state["sections_read"]:
        kept.append(f"your progress ({_plural(state['sections_read'], 'section')})")
    if state["annotations"]:
        kept.append(_plural(state["annotations"], "note"))
    if state["links"] or state["citations"]:
        kept.append("the passages your questions and notes cite")
    if state["selected_units"]:
        kept.append("your study-map chapters")
    if kept:
        joined = kept[0] if len(kept) == 1 else ", ".join(kept[:-1]) + " and " + kept[-1]
        lines.append(f"{joined[0].upper()}{joined[1:]} move to the new reading. "
                     "Anything that can't be matched is marked so you can place it again.")
    # Exam material never moves to another reading (protection redesign): the
    # new reading waits for the owner to mark it.
    protected = source_id in source_marks(vault, repository)
    if protected:
        lines.append(HELD_BACK_PLAN_LINE)
    name = title or "this book"
    return {
        "source_id": source_id,
        "extraction_id": extraction_id,
        "page_selection": page_selection,
        "pages": pages,
        "estimated_usd": priced["estimated_usd"],
        "estimate": priced,
        "engine": engine,
        "study_state": state,
        "needs_confirmation": has_state or protected or (backend == "api" and upload_ok),
        "title": f"Read {name} again with text recognition?",
        "lines": lines,
        "confirm_label": "Read it again",
        "cancel_label": "Not now",
    }
