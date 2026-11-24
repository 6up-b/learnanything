"""The goal lens's reads (Reader workbench v2 §12): everything ``curriculum.goal_lens`` (the pure level
rules) is computed from, gathered from the real model and never computed a second time.

* The deliverable's path as the learner sees it now (``deliverable_path.effective_lines`` over its
  current or latest judgment, with the learner's overrides), its inputs and its view.
* The goal's LOs: the needed ones, the prerequisites at the chosen depth (the path's own closure,
  demonstrated and assumed ones included so their sections show as already shown), and those needed
  only at a deeper depth (the closure's reach grows with the depth: ``deliverable_path.CLOSURE_DEPTH``).
* Coverage: the standing rows (``section_coverage.standing``) for every LO any row names in a reading,
  and the goal LOs whose coverage has not been judged for their current statement.
* The learner's choices on sections for this goal (``goal_lens_choices``).

The caller supplies what this package may not read: the due checks and today's answers (serving's
check state), AD's labelled prediction, and which unjudged LOs the background coverage already tried.
Read only: no model call, no write.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.curriculum import goal_lens as GL
from learnloop.db.repositories import Repository
from learnloop.db.stores import section_coverage as coverage_store
from learnloop.section_map import extraction_sections, range_span_ids
from learnloop.source_retrieval import deliverable_path as DP
from learnloop.source_retrieval import deliverables as DL
from learnloop.source_retrieval import goal_lens_choices as choices
from learnloop.source_retrieval import reading_paths as RP
from learnloop.source_retrieval import section_coverage as SC

#: AD's labelled prediction for one LO (injected; this package never imports adaptive difficulty):
#: ``{"likely": bool, "line": str}`` or None while AD does not predict it.
LikelyReader = Callable[[str], Mapping[str, Any] | None]


@dataclass
class GoalModel:
    """One goal's lens inputs, read once per request."""

    goal: Any
    #: The path's status (``deliverable_path.PATH_STATUSES``), or ``not_a_deliverable``.
    status: str
    depth: str | None
    reads: GL.GoalReads | None = None
    inputs: DP.PathInputs | None = None
    library: SC.Library | None = None
    lines: list[DP.EffectiveLine] = field(default_factory=list)
    #: The path's view (``deliverable_path.path_view``), read from the same inputs.
    view: dict[str, Any] = field(default_factory=dict)
    #: LO -> its kind (needed | prerequisite | later), for every goal LO.
    kinds: dict[str, str] = field(default_factory=dict)
    statuses: dict[str, RP.LoStatus] = field(default_factory=dict)
    #: The LOs of each depth, as the path's closure reaches at that depth (sizes in the path view).
    by_depth: dict[str, list[str]] = field(default_factory=dict)
    #: Coverage treatments per goal LO (primary-eligible first, C0a's order), for primaries off the path.
    treatments: dict[str, tuple[DP.Treatment, ...]] = field(default_factory=dict)
    #: The goal LOs whose coverage has not been judged for their current statement.
    owed: list[str] = field(default_factory=list)
    #: The current judgment's placements: section ref -> the LOs it places there.
    placed: dict[str, list[str]] = field(default_factory=dict)
    choices: dict[str, str] = field(default_factory=dict)
    message: str | None = None


def _closure(vault: Any, needed: Sequence[str], depth: str, background: Mapping[str, set[str]]) -> dict[str, set[str]]:
    closure = DP.prerequisite_closure(vault, needed, depth)
    for lo_id, roots in background.items():
        closure.setdefault(lo_id, set()).update(roots)
    return closure


#: The background work's state for the path at a state key (None: no inputs), as the path view takes it:
#: ``(judging, covering, coverage_failure)``. Read only: it starts nothing.
Progress = Callable[[str | None, str | None], tuple[Mapping[str, Any] | None, bool, Mapping[str, Any] | None]]


def _no_progress(_depth: str | None, _key: str | None) -> tuple[None, bool, None]:
    return None, False, None


def read_goal(vault: Any, repository: Repository, goal_id: str, *, held: Iterable[str] = (),
              answered: Iterable[str] = (), settled: Iterable[str] = (), progress: Progress = _no_progress,
              clock: Any = None) -> GoalModel:
    """The goal's model now. ``held``: LOs with a due check; ``answered``: LOs whose check was answered
    today; ``settled``: unjudged LOs the background coverage already tried (no candidate section);
    ``progress``: the background work's state. A goal that is not the learner's own raises
    ``DeliverableError``."""

    goal = DL.goal_of(vault, goal_id)
    depth = DL.depth_of(repository, goal_id)
    model = GoalModel(goal=goal, status="no_scope", depth=depth)
    try:
        library = SC.Library(vault, repository)
        inputs = DP.path_inputs(vault, repository, goal_id, library=library, clock=clock)
    except SC.CoverageError as exc:
        judging, covering, failure = progress(depth, None)
        model.view = DP.path_view(vault, repository, goal_id, judging=judging, covering=covering,
                                  coverage_failure=failure, clock=clock)
        model.status, model.message = model.view["status"], str(exc)
        return model
    judging, covering, failure = progress(depth, inputs.state_key() if inputs is not None else None)
    model.view = DP.path_view(vault, repository, goal_id, judging=judging, covering=covering,
                              coverage_failure=failure, clock=clock, inputs=inputs)
    model.status = str(model.view["status"])
    model.message = model.view.get("message")
    if inputs is None or depth is None:
        return model
    model.inputs, model.library = inputs, library
    needed = [lo.learning_object_id for lo in inputs.los if lo.kind == "needed"]
    # What the needed LOs' primary-eligible sections assume is background at every depth (the path's rule).
    background: dict[str, set[str]] = {}
    for lo in inputs.los:
        if lo.kind != "needed":
            continue
        for treatment in lo.treatments:
            if treatment.primary_eligible:
                for assumed in treatment.assumes:
                    if assumed not in needed and SC._active(vault, assumed):
                        background.setdefault(assumed, set()).add(lo.learning_object_id)
    chosen = _closure(vault, needed, depth, background)
    deeper: set[str] = set()
    for other in RP.DEPTHS[RP.DEPTHS.index(depth) + 1:]:
        deeper |= set(_closure(vault, needed, other, background))
    deeper -= set(chosen) | set(needed)
    kinds = {lo_id: "needed" for lo_id in needed}
    kinds.update({lo_id: "prerequisite" for lo_id in sorted(chosen) if lo_id not in kinds})
    kinds.update({lo_id: "later" for lo_id in sorted(deeper) if lo_id not in kinds})
    statuses = RP.lo_statuses(vault, repository, list(kinds))
    model.kinds, model.statuses = kinds, statuses
    for each in RP.DEPTHS:
        reach = set(_closure(vault, needed, each, background))
        model.by_depth[each] = [*needed, *sorted(lo for lo in reach if lo not in needed
                                                 and not (statuses.get(lo) and (statuses[lo].demonstrated
                                                                                or statuses[lo].assumed)))]
    # Coverage treatments: the path's for its LOs, the standing rows for the rest (deeper ones).
    model.treatments = {lo.learning_object_id: lo.treatments for lo in inputs.los}
    rest = [lo_id for lo_id in kinds if lo_id not in model.treatments]
    for lo_id, entries in SC.standing(vault, repository, library, rest).items():
        model.treatments[lo_id] = DP._treatments(library, entries)
    rows, _fresh = DP._current_rows(repository, inputs)
    model.lines = DP.effective_lines(vault, repository, inputs, rows) if rows else []
    for row in rows:
        ref = f"{row['extraction_id']}/{row['section_id']}"
        model.placed.setdefault(ref, []).append(str(row["learning_object_id"]))
    model.owed = DP.owed_among(vault, repository, [lo.learning_object_id for lo in inputs.los])
    model.choices = choices.section_choices(repository, goal_id)
    held_set, answered_set = set(held), set(answered)
    order = {line.learning_object_id: position for position, line in enumerate(model.lines)}
    ranked = sorted(kinds, key=lambda lo_id: (lo_id not in order, order.get(lo_id, 0),
                                              ("needed", "prerequisite", "later").index(kinds[lo_id]),
                                              needed.index(lo_id) if lo_id in needed else 0, lo_id))
    los = {}
    for ordinal, lo_id in enumerate(ranked):
        status = statuses.get(lo_id)
        los[lo_id] = GL.GoalLo(
            learning_object_id=lo_id, title=getattr(vault.learning_objects.get(lo_id), "title", lo_id),
            kind=kinds[lo_id], ordinal=ordinal, demonstrated=bool(status and status.demonstrated),
            assumed=bool(status and status.assumed), held=lo_id in held_set, answered_today=lo_id in answered_set)
    path = {line.learning_object_id: GL.PathPlace(
        learning_object_id=line.learning_object_id, primary=line.primary.ref,
        alternates=tuple((treatment.ref, difference) for treatment, difference in line.alternates),
        label=line.label, effective=line.effective, reason=line.reason, override=line.override)
        for line in model.lines}
    unsettled = frozenset(model.owed) - frozenset(settled)
    model.reads = GL.GoalReads(goal_title=goal.title, depth=depth, depth_label=RP.DEPTH_LABELS.get(depth, depth),
                               los=los, path=path, unsettled=unsettled)
    return model


def primary_of(model: GoalModel, lo_id: str) -> DP.Treatment | None:
    """The section a click on the LO opens: its path primary, else the first primary-eligible coverage row."""

    line = next((line for line in model.lines if line.learning_object_id == lo_id), None)
    if line is not None:
        return line.primary
    return next((t for t in model.treatments.get(lo_id, ()) if t.primary_eligible), None)


def depth_sizes(model: GoalModel) -> list[dict[str, Any]]:
    """Each depth with the size of its path (§12.5, decision D3): its LOs, and the distinct primary sections
    they read (the path's choice, else coverage's first eligible one) with their minutes at DL1's pace."""

    out = []
    for depth in RP.DEPTHS:
        refs: dict[str, int] = {}
        for lo_id in model.by_depth.get(depth, ()):
            primary = primary_of(model, lo_id)
            if primary is not None:
                refs[primary.ref] = primary.minutes
        out.append({"id": depth, "label": RP.DEPTH_LABELS[depth], "means": RP.DEPTH_MEANS[depth],
                    "learning_objects": len(model.by_depth.get(depth, ())), "sections": len(refs),
                    "minutes": sum(refs.values())})
    return out


# ---------------------------------------------------------------------------
# One reading's sections through the lens
# ---------------------------------------------------------------------------

def reading_sections(vault: Any, repository: Repository, model: GoalModel, extraction_id: str, *,
                     from_span_id: str | None = None, to_span_id: str | None = None, t0: float | None = None,
                     t1: float | None = None) -> list[tuple[dict[str, Any], GL.SectionReads]]:
    """Each section of the reading that the range touches (every section without a range), with the
    passages of the range it holds and its lens reads. Raises ``section_map.RangeError``."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        return []
    rows, _blocks, _span_to_section = extraction_sections(ir)
    if from_span_id is None and t0 is None:
        wanted: set[str] | None = None
    else:
        wanted = set(range_span_ids(ir, from_span_id=from_span_id, to_span_id=to_span_id, t0=t0, t1=t1))
    library = model.library
    reading = library.reading(extraction_id) if library is not None else None
    with repository.connection() as connection:
        present = coverage_store.table_present(connection)
        named = coverage_store.learning_objects_in_reading(connection, extraction_id) if present else []
        hashes = coverage_store.section_hashes_in_reading(connection, extraction_id) if present else {}
    standing = SC.standing(vault, repository, library, named) if library is not None and reading is not None else {}
    out = []
    for row in rows:
        section_id = str(row["id"])
        spans = [str(span) for span in row["span_ids"] if wanted is None or span in wanted]
        if not spans:
            continue
        ref = f"{extraction_id}/{section_id}"
        protection = None
        if reading is None:
            protection = "left_out"
        elif section_id in reading.withheld:
            protection = "withheld"
        coverage = []
        for lo_id in named:
            entry = standing.get(lo_id, {}).get((extraction_id, section_id))
            if entry is not None:
                coverage.append(GL.Coverage(lo_id, entry.treatment if entry.treatment is not None
                                            else GL.CHAPTER_ABOUT if entry.chapter_id is not None
                                            else GL.LEARNER_ABOUT))
        placed = tuple(lo for lo in dict.fromkeys(model.placed.get(ref, ())) if model.reads and lo in model.reads.los)
        # A goal LO whose rows here were all written against an earlier version of the section (no standing row
        # now): what it says of the section is unknown, never "not about it".
        current = library.section(extraction_id, section_id) if library is not None else None
        stale = tuple(sorted(lo_id for (sid, lo_id), seen in hashes.items()
                             if sid == section_id and model.reads and lo_id in model.reads.los
                             and current is not None and current.section_hash not in seen
                             and not any(entry.learning_object_id == lo_id for entry in coverage)))
        reads = GL.SectionReads(ref=ref, title=str(row["label"]), coverage=tuple(coverage), placed=placed,
                                protection=protection, choice=model.choices.get(ref), stale=stale)
        place = {"section_id": section_id, "title": str(row["label"]), "start_span_id": str(row["start_span_id"]),
                 "span_ids": spans}
        out.append((place, reads))
    return out


# ---------------------------------------------------------------------------
# The replies
# ---------------------------------------------------------------------------

DEMONSTRATED_LINE = "Shown on your own, without help."
UNTESTED_LINE = "Not tested on your own yet."


def goal_view(goal: Any) -> dict[str, Any]:
    """"◎ YOUR GOAL · <KIND> · <deadline> (your words, <date set>)" (§12.2 part 1). Kind is shown, never stored."""

    return {"id": goal.id, "title": goal.title, "sentence": goal.intent_sentence or goal.title,
            "kind": DL.kind_of(goal), "due_at": goal.due_at, "set_at": goal.created_at}


def _readiness(model: GoalModel, lo_id: str, likely: LikelyReader | None) -> tuple[str, str]:
    status = model.statuses.get(lo_id)
    if status is not None and status.demonstrated:
        return "demonstrated", DEMONSTRATED_LINE
    try:
        prediction = likely(lo_id) if likely is not None else None
    except Exception:  # noqa: BLE001 - an unreadable prediction reads as untested, as "Am I ready?" reads it
        prediction = None
    if prediction is not None and prediction.get("likely"):
        return "likely", str(prediction.get("line") or "")
    return "untested", UNTESTED_LINE


def protection(vault: Any, repository: Repository, due: Sequence[Mapping[str, Any]],
               model: GoalModel | None = None) -> GL.Protection:
    """What the replies may not say while checks are due (spec §12.6.1, D15), from every due LO whatever the goal:
    their titles; the sections that treat them (standing coverage about them, their path placements in any goal,
    their checks' hosts); the LOs whose explanations depend on them (prerequisites, or what a section read for an
    LO takes as known). Read only."""

    held = sorted({str(row["lo_id"]) for row in due})
    if not held:
        return GL.Protection()
    titles = [vault.learning_objects[lo_id].title for lo_id in held if lo_id in vault.learning_objects]
    sections = {f"{row['host']['extraction_id']}/{row['host']['section_id']}" for row in due
                if row.get("host") and row["host"].get("extraction_id") and row["host"].get("section_id")}
    library = model.library if model is not None and model.library is not None else None
    try:
        library = library or SC.Library(vault, repository)
        for entries in SC.standing(vault, repository, library, held).values():
            for (extraction_id, section_id), entry in entries.items():
                if entry.treatment is None or entry.treatment in SC.ABOUT:
                    sections.add(f"{extraction_id}/{section_id}")
    except SC.CoverageError:
        pass
    with repository.connection() as connection:
        marks = ",".join("?" * len(held))
        for extraction_id, section_id in connection.execute(
                f"SELECT extraction_id, section_id FROM deliverable_path_sections WHERE learning_object_id IN ({marks})",
                held).fetchall():
            sections.add(f"{extraction_id}/{section_id}")
    held_set = set(held)
    concepts = {vault.learning_objects[lo_id].concept for lo_id in held if lo_id in vault.learning_objects}
    concepts.discard(None)
    depends = {lo_id for lo_id, lo in vault.learning_objects.items()
               if lo_id not in held_set and set(getattr(lo, "prerequisites", ()) or ()) & concepts}
    if model is not None:
        for lo_id, treatments in model.treatments.items():
            if lo_id not in held_set and any(set(treatment.assumes) & held_set for treatment in treatments):
                depends.add(lo_id)
    return GL.Protection.of(held, titles, sections, depends)


def _section_ref(treatment: DP.Treatment | None) -> dict[str, Any] | None:
    if treatment is None:
        return None
    return {"extraction_id": treatment.extraction_id, "section_id": treatment.section_id,
            "start_span_id": treatment.start_span_id, "title": treatment.title, "book": treatment.source_title}


def band_view(vault: Any, repository: Repository, model: GoalModel, *, due: Sequence[Mapping[str, Any]],
              answered: Sequence[Mapping[str, Any]], protection: GL.Protection, likely: LikelyReader | None = None,
              pace: Mapping[str, Any] | None = None, progress: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """``goal.band``: the goal, its LOs as dots, the depth with each depth's size, the next step, pace and
    the path's view, masked by ``protection`` (required: no band leaves here unmasked; D15)."""

    return GL.protect_band(_band_view(vault, repository, model, due=due, answered=answered, likely=likely, pace=pace,
                                      progress=progress), protection)


def _band_view(vault: Any, repository: Repository, model: GoalModel, *, due: Sequence[Mapping[str, Any]],
               answered: Sequence[Mapping[str, Any]], likely: LikelyReader | None = None,
               pace: Mapping[str, Any] | None = None, progress: Mapping[str, Any] | None = None) -> dict[str, Any]:

    view = model.view
    base: dict[str, Any] = {
        "goal_id": model.goal.id, "goal": goal_view(model.goal), "status": model.status, "message": model.message,
        "reason": view.get("reason"), "depth": model.depth, "depth_label": RP.DEPTH_LABELS.get(model.depth or ""),
        "depths": [{"id": d, "label": RP.DEPTH_LABELS[d], "means": RP.DEPTH_MEANS[d], "learning_objects": None,
                    "sections": None, "minutes": None} for d in RP.DEPTHS],
        "learning_objects": [], "counts": {"learning_objects": 0, "demonstrated": 0, "likely": 0, "untested": 0},
        "unmatched": list((DL.latest_resolution(repository, model.goal.id) or {}).get("unmatched") or ()),
        "checks": {"due_today": 0, "answered_today": 0, "first": None}, "next": {"kind": "none"},
        "pace": dict(pace) if pace is not None else None,
        "coverage": {"unjudged": [], **(dict(progress) if progress else {})}, "path": None,
    }
    if model.reads is None:
        base["path"] = view or None
        return base
    reads = model.reads
    shown = set(reads.los)
    on_band = [lo_id for lo_id, lo in reads.los.items()
               if lo.kind == "needed" or not (lo.demonstrated or lo.assumed)]
    due_here = [row for row in due if row["lo_id"] in shown]
    answered_here = [row for row in answered if row["lo_id"] in shown]
    band_los = []
    for lo_id in on_band:
        lo = reads.los[lo_id]
        readiness, line = _readiness(model, lo_id, likely)
        band_los.append(GL.BandLo(
            learning_object_id=lo_id, title=lo.title, kind=lo.kind, ordinal=lo.ordinal, readiness=readiness,
            readiness_line=line, primary=_section_ref(primary_of(model, lo_id)),
            checks_due=len({row["commitment_id"] for row in due_here if row["lo_id"] == lo_id}),
            answered_today=len({row["commitment_id"] for row in answered_here if row["lo_id"] == lo_id}),
            held=lo.held))
    done = DP._read(repository)
    held = {lo_id for lo_id, lo in reads.los.items() if lo.held}
    next_lines = [GL.NextLine(line.learning_object_id, line.effective, _section_ref(line.primary) or {},
                              read=done(line.primary.extraction_id, line.primary.section_id),
                              held=line.learning_object_id in held) for line in model.lines]
    first = due_here[0] if due_here else None
    checks_due = len({row["commitment_id"] for row in due_here})
    path = dict(view)
    path["lines"] = [_held_line(line) if line["learning_object_id"] in held else line for line in view.get("lines", ())]
    return {**base,
            "depths": depth_sizes(model),
            "learning_objects": GL.band_learning_objects(band_los),
            "counts": GL.band_counts(band_los),
            # No LO on the ◇: while a check is due its LO is not named beside it (§12.6.1).
            "checks": {"due_today": checks_due, "answered_today": len({row["commitment_id"] for row in answered_here}),
                       "first": {"commitment_id": first["commitment_id"], "host": first.get("host")} if first else None},
            "next": GL.next_for_goal(checks_due, {"commitment_id": first["commitment_id"], "host": first.get("host")}
                                     if first else None, next_lines),
            "coverage": {"unjudged": sorted(reads.unsettled), **(dict(progress) if progress else {})},
            "path": path}


def _held_line(line: Mapping[str, Any]) -> dict[str, Any]:
    """A path row whose LO has a due check: its purpose text hidden until the check is answered (§12.6.1)."""

    return {**line, "reason": None, "held": True,
            "alternates": [{**alternate, "difference": ""} for alternate in line.get("alternates", ())]}


def lens_view(vault: Any, repository: Repository, model: GoalModel, extraction_id: str, *, protection: GL.Protection,
              from_span_id: str | None = None, to_span_id: str | None = None, t0: float | None = None,
              t1: float | None = None) -> dict[str, Any]:
    """``goal.lens``: one level per section the range touches (passages inherit it, decision D1), masked by
    ``protection`` (required: no lens leaves here unmasked; D15)."""

    return GL.protect_lens(_lens_view(vault, repository, model, extraction_id, from_span_id=from_span_id,
                                      to_span_id=to_span_id, t0=t0, t1=t1), protection)


def _lens_view(vault: Any, repository: Repository, model: GoalModel, extraction_id: str, *,
               from_span_id: str | None = None, to_span_id: str | None = None, t0: float | None = None,
               t1: float | None = None) -> dict[str, Any]:

    base: dict[str, Any] = {"goal_id": model.goal.id, "extraction_id": extraction_id, "status": model.status,
                            "message": model.message, "depth": model.depth,
                            "depth_label": RP.DEPTH_LABELS.get(model.depth or ""), "mapping": "unmapped",
                            "levels": []}
    if model.reads is None:
        return base
    levels = []
    for place, reads in reading_sections(vault, repository, model, extraction_id, from_span_id=from_span_id,
                                         to_span_id=to_span_id, t0=t0, t1=t1):
        level = GL.section_level(reads, model.reads)
        levels.append({**place, **GL.level_view(level, reads, model.reads)})
    mapped = any(level["mapping"] != "unmapped" for level in levels)
    return {**base, "mapping": "mapped" if mapped else "unmapped", "levels": levels}


__all__ = ["GoalModel", "LikelyReader", "Progress", "band_view", "depth_sizes", "goal_view", "lens_view",
           "primary_of", "protection", "read_goal", "reading_sections"]
