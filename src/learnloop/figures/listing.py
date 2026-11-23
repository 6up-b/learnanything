"""Which stored figures a source lists now, and the lines for builds still under way.

:func:`list_figures` is the Reader's list for one source: per version chain, the newest version that can be drawn as
configured now (:mod:`.view`), never one held out now (:mod:`.protection`), a figure with no passage once per place
it was asked at, and a pre-built figure nobody pressed for only while figures ahead of need are on and within the
section's cue budget (:func:`_listed`). :func:`section_figures` reads the same rows for the correspondents read,
without re-verifying a sketch (it writes nothing). :func:`rich_pending` lists the rich builds with no quick figure
that have not ended, or ended with code's reason. :func:`prefetch_pending` and :func:`prefetch_plan_waits` tell the
Reader whether a pre-build is coming and which plan waits to retry. :func:`shown_figure` is one figure that may be
shown now (the predictions' and the open path's read). This module imports the view, the request and protection,
nothing of the build: the build imports it.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Collection, Mapping, Sequence
from contextlib import closing
from typing import Any

from learnloop.clock import Clock
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import figures as store
from learnloop.figure_admission import figures_enabled, rich_tiers_enabled
from learnloop.figures import records as FR
from learnloop.figures import rich as RICH
from learnloop.figures import sketch as K
from learnloop.figures import spec as S
from learnloop.figures.protection import figure_homes, item_passages, rich_base_keys, row_withheld, show_me_row
from learnloop.figures.request import FigureRefused, FigureRequest
from learnloop.figures.spec import ALL_SPEC_VERSIONS, RICH_SPEC_VERSIONS, SPEC_VERSIONS
from learnloop.figures.view import (
    SKETCH_OFF_KIND,
    _anchor_span,
    _figure_request,
    _label,
    _prebuilt_pressed,
    _presented_row,
    available_row,
    drawable_now,
    figure_view,
    sketch_rechecked,
    sketch_row,
    source_rejected,
)


# ---------------------------------------------------------------------------
# A source's figures
# ---------------------------------------------------------------------------

def _root(rows_by_id: Mapping[str, Mapping[str, Any]], row: Mapping[str, Any]) -> str:
    current = row
    seen = {current["id"]}
    while current.get("supersedes_id") and current["supersedes_id"] in rows_by_id and current["supersedes_id"] not in seen:
        current = rows_by_id[current["supersedes_id"]]
        seen.add(current["id"])
    return str(current["id"])


def _listed(vault: Any, repository: Repository, extraction_id: str, withheld: list[str] | None = None
            ) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]:
    """The rows :func:`list_figures` presents, with no presentation (RW5d P4a,
    Codex review F3): per version chain, the pick, the chain's length and its
    placements in this source. Read-only: nothing is verified or written; a
    chain left out because its pick is withheld now has the pick's id
    appended to ``withheld`` when given."""

    if not figures_enabled(vault):
        return []
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        if not store.has_tables(connection):
            return []
        rows = store.figures_for_extraction(connection, extraction_id)
    # RW5d P2b: a rich figure that follows a quick one is that figure's fuller
    # version (one line, two versions), never a line of its own.
    rows = [row for row in rows if row["spec_version"] in ALL_SPEC_VERSIONS and not row.get("fuller_of_id")]
    if any(row.get("origin") == "prefetch" for row in rows):
        # RW5d P5: with figures ahead of need switched off, a prebuilt figure
        # nobody pressed for is absent (rev 1 exactly).
        rows = [row for row in rows if row.get("origin") != "prefetch" or _prebuilt_listed(vault, repository, row)]
    by_id = {row["id"]: row for row in rows}
    chains: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        chains.setdefault(_root(by_id, row), []).append(row)
    picks: list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]] = []
    for chain in chains.values():
        shown = [row for row in chain if row["verification"] in store.SHOWN]
        # Codex review F5: with the panels off, the newest version that can
        # still be drawn, before one that would list as "can't draw this yet".
        # RW5c: a version whose stated claim differs is not shown (the failed line only when nothing else is).
        drawable = [row for row in shown if drawable_now(vault, row) and not source_rejected(vault, repository, row)]
        pick = (drawable or shown or chain)[-1]
        if row_withheld(vault, repository, pick) is not None:
            if withheld is not None:
                withheld.append(str(pick["id"]))
            continue
        # RW5d (Codex review F3): a figure with no passage is listed at every
        # paragraph of this source it was asked at (one view per placement),
        # each opening where that request was made.
        homes: list[dict[str, Any] | None] = [
            {"extraction_id": key[0], "span_id": key[1]} for key in figure_homes(repository, pick) or ()
            if key[0] == extraction_id] or [None]
        picks.append((pick, len(chain), homes))
    if any(pick.get("origin") == "prefetch" for pick, _length, _homes in picks):
        picks = _prebuilt_within_budget(vault, repository, extraction_id, picks)
    return picks


def _prebuilt_within_budget(vault: Any, repository: Repository, extraction_id: str,
                            picks: list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]
                            ) -> list[tuple[Mapping[str, Any], int, list[dict[str, Any] | None]]]:
    """RW5d P5 (spec §6.9; Codex review F11): a prebuilt figure nobody pressed for takes its
    place in the Reader's cue budget (``[cues] density``, per section; cues off: none), the
    earliest built first; once pressed it is the learner's like any figure (never cut).

    The count is not shared with that section's margin marks (follow-ups batch 6 (F), recorded
    as not a small change): the marks are ``reader.guide_plan``'s, built from the Guide's plan
    and, with RW3b's discovery on, merged and remembered for the taps (a write) on that read.
    Sharing here would rebuild the Guide's plan and the merge on every ``reader.figures`` read
    (the Reader polls it while a prebuild is coming); sharing in the Reader needs a new
    "unpressed prebuilt" flag on the figure view (pressed is not in it) and a re-cut joining the
    two reads by section on every refresh of either. Worst case today: a section shows its
    marks plus up to the same budget of unpressed prebuilt lines (collapsed "▸" lines)."""

    from learnloop.reader.reader_cues import cue_density, cues_enabled, density_budget
    from learnloop.reader.reader_guidance import extraction_sections

    budget = density_budget(cue_density(vault)) if cues_enabled(vault) else 0
    ir = repository.load_document_ir(extraction_id)
    section_of: dict[str, str] = {}
    if ir is not None:
        for section in extraction_sections(ir)[0]:
            for span in section["span_ids"]:
                section_of.setdefault(str(span), str(section["id"]))
    used: dict[str, int] = {}
    kept = []
    for entry in sorted(picks, key=lambda found: (str(found[0].get("created_at") or ""), str(found[0]["id"]))):
        row = entry[0]
        if row.get("origin") == "prefetch" and not _prebuilt_pressed(repository, row):
            spans = [str(span) for span in row.get("span_ids") or ()]
            section = next((section_of[span] for span in spans if span in section_of), "")
            if used.get(section, 0) >= budget:
                continue
            used[section] = used.get(section, 0) + 1
        kept.append(entry)
    order = {id(entry): index for index, entry in enumerate(picks)}
    return sorted(kept, key=lambda entry: order[id(entry)])


def _prebuilt_listed(vault: Any, repository: Repository, row: Mapping[str, Any]) -> bool:
    """RW5d P5: a prebuilt figure lists while figures ahead of need are on, or
    once a pressed request took it (then it is the learner's like any figure)."""

    from learnloop.figures.power import prefetch_switch

    if _prebuilt_pressed(repository, row):
        return True
    # Codex review F10: unpressed, only a completed (shown) prebuild lists,
    # never a failed or unsupported one (speculation is invisible until useful).
    # RW5c: nor one rejected by its source check, whose only state is a failed line.
    return prefetch_switch(vault) and row.get("verification") in store.SHOWN and not source_rejected(vault, repository, row)


def prefetch_pending(vault: Any, repository: Repository, extraction_id: str, *,
                     pass_running: bool = False) -> bool:
    """RW5d P5 (Codex review F11): whether a prebuild for this source is coming now: the Reader
    then reads its figures again, paced, so a completed prebuild appears without a reopen.
    False with figures ahead of need off (rev 1's payload).

    Codex re-review F18: only active, admissible work counts, so the Reader never polls for
    work no worker will do: nothing on battery (no background build runs there); a decision to
    build with no request yet only while a prefetch pass is running now (``pass_running``: the
    sidecar's drain thread, which builds the waiting decisions first; otherwise it waits for the
    next trigger, which a read does not fire) and today's caps have room (follow-ups batch 7 (A):
    the pass starts nothing past them); a prebuild's rich job only while it is queued or
    running (one waiting for the plan is asked again by the read, :func:`prefetch_plan_waits`,
    and is pending again once requeued)."""

    from learnloop.figures import prefetch_ledger as PL
    from learnloop.figures.power import power_state, prefetch_switch

    if not prefetch_switch(vault) or not power_state().on_mains:
        return False
    if pass_running and PL.capacity_left(vault, repository.sqlite_path):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = "
                                  "'figure_prefetch_decisions'").fetchone() is None:
                return False
            marks = ",".join("?" for _ in PL.BUILD_DECISIONS)
            for raw in connection.execute(
                    "SELECT anchor_json FROM figure_prefetch_decisions WHERE outcome IS NULL AND request_id IS NULL "
                    f"AND decision IN ({marks})", PL.BUILD_DECISIONS):
                try:
                    anchor = json.loads(raw[0] or "null")
                except (TypeError, ValueError):
                    continue
                if isinstance(anchor, dict) and str(anchor.get("extraction_id")) == str(extraction_id):
                    return True
    for job in RICH.rich_jobs(repository):
        payload = job.get("payload") or {}
        if payload.get("build_mode") == "prefetch" and RICH.job_state(job)["state"] == "pending" \
                and str((payload.get("base") or {}).get("extraction_id") or "") == str(extraction_id):
            return True
    return False


def prefetch_plan_waits(vault: Any, repository: Repository, extraction_id: str | None,
                        *, request_ids: Collection[str] | None = None, clock: Clock | None = None) -> list[str]:
    """RW5d P5 (Codex re-review F17): this source's speculative prebuild rich jobs waiting for
    the plan, newest per input, whose retry is admissible now: figures ahead of need on, this
    machine on mains, and the passage not held out. They list no line (Codex review F10), so the
    Reader's read asks the plan again for them here, paced as every plan wait is
    (``rich.due_for_plan_retry``); the requeued job's own gate checks the rest before any
    request. A newer job of the same input (a press, or a later prebuild) speaks for it.

    Follow-ups batch 6 (D, P5 F17): ``extraction_id`` None reads every source (the prefetch
    pass's own retries: its ``retry_plan_waits``), and
    ``request_ids``, when given, keeps only the jobs of those figure requests (the pass passes
    the requests of its decisions whose horizon is still open).

    Follow-ups batch 6 Codex review F1, verify V1: a job whose saved context touches an item's own
    passage now (:func:`item_passages`: an item under a live administration, such as a cold check
    started after the job first met the limit, or one a later day plan selected) is not asked
    again, by the Reader's read as by the pass; unreadable protection asks none."""

    from learnloop.figures.power import power_state, prefetch_switch
    from learnloop.figures.protection import _withheld

    if not rich_tiers_enabled(vault) or not prefetch_switch(vault) or not power_state().on_mains:
        return []
    candidates: list[tuple[str, dict[str, Any]]] = []
    seen: set[str] = set()
    for job in RICH.rich_jobs(repository):
        payload = job.get("payload") or {}
        base = payload.get("base") or {}
        if extraction_id is not None and str(base.get("extraction_id") or "") != str(extraction_id):
            continue
        key = str(payload.get("input_hash"))
        if key in seen:
            continue
        seen.add(key)
        if payload.get("build_mode") != "prefetch" or RICH.job_state(job)["state"] != RICH.WAITING_FOR_PLAN:
            continue
        if request_ids is not None and str(payload.get("request_id") or "") not in request_ids:
            continue
        if _withheld(vault, repository, base) is not None:
            continue
        candidates.append((str(job["id"]), base))
    if not candidates:
        return []
    found = item_passages(vault, repository, clock=clock)
    if found is None:
        return []  # fail closed
    spans, whole = found
    return [job_id for job_id, base in candidates
            if not any(key[0] in whole or key in spans for key in rich_base_keys(base))]


def list_figures(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]:
    """The figures of one source as the Reader shows them: per version chain,
    the newest shown version (else the newest failed or unsupported one), of
    the current spec version, and never one whose passage is held out now."""

    views = []
    withheld: list[str] = []
    for pick, versions, homes in _listed(vault, repository, extraction_id, withheld):
        try:
            views.extend(figure_view(vault, repository, pick, versions=versions, home=home) for home in homes)
        except (S.SpecError, K.SketchError):
            FR.write_withheld_once(repository, str(pick["id"]), FR.SPEC_UNPARSABLE, where="list")
            continue
    for figure_id in withheld:
        FR.write_withheld_once(repository, figure_id, FR.WITHHELD_PICK, where="list")
    return sorted(views, key=lambda view: view["created_at"])


def section_figures(vault: Any, repository: Repository, extraction_id: str,
                    section_of: Callable[[str], str | None]) -> dict[str, list[dict[str, Any]]]:
    """RW5d P4a (spec §10.2): the kept figures of one reading by the section
    their anchor is in, for the correspondents read (figures follow the
    section). A read of what :func:`list_figures` lists (no copy, no
    ``source_objects`` row, Q8): only what the Reader would list on that
    reading now, held-out figures and figures switched off left out, and of
    those only the shown ones (verified or an illustration; never a failed or
    unsupported line). Read-only (Codex review F3): the rows are presented as
    the list presents them except that a sketch built under another engine is
    not re-verified here (opening it does that, and a figure that fails then
    is not shown). ``section_of`` maps an anchor span to its section (the
    caller's protected library: a withheld section maps to none). Each entry
    is the figure's id, its home (reading and anchor span), its label and kind;
    one entry per figure and section."""

    out: dict[str, list[dict[str, Any]]] = {}
    seen: set[tuple[str, str]] = set()
    picks = sorted(_listed(vault, repository, extraction_id), key=lambda found: str(found[0]["created_at"]))
    for pick, _versions, homes in picks:
        # The list's own presentation without the sketch re-verification (it
        # runs the engine and appends to judgment_ledger, and this read writes
        # nothing): that happens when the figure is opened, through its own
        # book's listing. A failure this process already found is honoured.
        row = _presented_row(vault, repository, pick, reverify=False)
        if row.get("verification") not in store.SHOWN:
            continue
        asked = _figure_request(repository, row)
        for home in homes:
            anchor = _anchor_span(row, asked, home)
            if not anchor:
                continue
            section_id = section_of(str(anchor))
            if section_id is None or (section_id, str(row["id"])) in seen:
                continue
            seen.add((section_id, str(row["id"])))
            out.setdefault(section_id, []).append({
                "figure_id": row["id"], "extraction_id": row["extraction_id"], "anchor_span_id": anchor,
                "label": _label(row), "kind": row.get("kind"), "verification": row["verification"],
                "created_at": row["created_at"],
            })
    return out


# ---------------------------------------------------------------------------
# Rich builds still under way
# ---------------------------------------------------------------------------

def _rich_line(request: FigureRequest, job: Mapping[str, Any], state: Mapping[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    base = payload.get("base") or {}
    home = base.get("home") or {}
    spans = list(base.get("span_ids") or ())
    anchor = (spans or [(base.get("region") or {}).get("span_id") or home.get("span_id")])[-1]
    return {"request_id": payload.get("request_id"), "extraction_id": base.get("extraction_id"),
            "anchor_span_id": anchor, "tier": payload.get("tier"), "goal_text": base.get("goal_text"),
            "state": state.get("state"), "phase": state.get("phase"), "reason": state.get("reason"),
            "rich_job_id": job.get("id")}


def rich_pending(vault: Any, repository: Repository, extraction_id: str) -> list[dict[str, Any]]:
    """RW5d P2b (spec §6.8): the rich builds with no quick figure for this
    source that have not ended (pending, or waiting for the plan), each as
    the pending line under its passage; empty while the rich tiers are off.
    A build whose passage is held out now is left out.

    Codex review F9: a build that ended with no row (interrupted when
    LearnLoop stopped, or stopped with code's reason) stays as a ``failed``
    line with that reason and its job (``figure.rich_retry`` requeues it),
    until a later build of the same input replaces it; a cancelled one is
    gone (the learner chose).

    Codex re-review F14: a correction of an animation ("not right?") whose
    job stored a failure lists no line of its own (the earlier animation
    stays the chain's shown version), so it stays as a ``failed`` line with
    the stored reason (``figure.rich_retry`` asks again,
    :func:`rich_revision_retry`), until a later correction of the same
    figure replaces it. Reader follow-ups Nov 1b (P2b ruling R1): such a
    failure is found from the durable rows (the stored failure, its request,
    and that request's job over the whole queue), not only among the jobs
    the queue's recent window returns."""

    if not figures_enabled(vault) or not rich_tiers_enabled(vault):
        return []
    lines = []
    seen: set[str] = set()
    corrected: set[str] = set()
    stored: list[dict[str, Any]] | None = None

    def stored_rows() -> list[dict[str, Any]]:
        nonlocal stored
        if stored is None:
            with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                stored = store.figures_for_extraction(connection, extraction_id) \
                    if store.has_tables(connection) else []
        return stored

    def failed_corrections() -> list[dict[str, Any]]:
        # P2b ruling R1: the stored failures of animation corrections, newest
        # first, each with its job (by its request, over the whole queue).
        # Codex review F4 (Nov 1b): only while that job is still the newest
        # correction of the figure over the whole queue; a newer one (even a
        # cancelled one, which stores no row) speaks for it, as in the window.
        found = []
        for row in reversed(stored_rows()):
            if row.get("verification") != "failed" or row.get("spec_version") not in RICH_SPEC_VERSIONS \
                    or not row.get("supersedes_id") or not row.get("request_id"):
                continue
            job = RICH.rich_job_for_request(repository, str(row["request_id"]))
            if job is None or (job.get("payload") or {}).get("supersedes_id") != row["supersedes_id"]:
                continue
            newest = RICH.rich_job_for_figure(repository, str(row["supersedes_id"]))
            if newest is not None and str(newest.get("id")) == str(job.get("id")):
                found.append(job)
        return found

    jobs = RICH.rich_jobs(repository)
    windowed = {str(job.get("id")) for job in jobs}
    for job in [*jobs, *(job for job in failed_corrections() if str(job.get("id")) not in windowed)]:
        payload = job.get("payload") or {}
        base = payload.get("base") or {}
        if payload.get("fast_figure_id") or str(base.get("extraction_id") or "") != str(extraction_id):
            continue
        if payload.get("build_mode") == "prefetch":
            # RW5d P5 (Codex review F10): a speculative rich-only prebuild is
            # invisible until a figure exists (no building, waiting or failed
            # line, switch on or off); a press of the same input is its own
            # request with its own line.
            continue
        if str(payload.get("input_hash")) in seen:
            continue
        seen.add(str(payload.get("input_hash")))
        supersedes = payload.get("supersedes_id")
        if supersedes:
            # Jobs come newest first: a newer correction of the same figure
            # speaks for it (its own line, or its stored version).
            if str(supersedes) in corrected:
                continue
            corrected.add(str(supersedes))
        state = RICH.job_state(job)
        failed_correction = _failed_correction(payload, stored_rows()) if supersedes and \
            state["state"] in ("done", "failed") else None
        if failed_correction is not None:
            reason = str((failed_correction.get("verification_report") or {}).get("reason") or "")
            state = {"state": "failed", "reason": reason[:300] or "the job failed", "rich_job_id": job["id"]}
        elif state["state"] not in ("pending", "waiting_for_plan", "failed"):
            continue
        elif state["state"] == "failed" and payload.get("input_hash") in {row["input_hash"] for row in stored_rows()}:
            # A stored row (the figure, or its stored failure) lists itself.
            continue
        from learnloop.figures.protection import _withheld

        if _withheld(vault, repository, base) is not None:
            continue
        lines.append(_rich_line(FigureRequest(extraction_id=extraction_id, span_ids=[]), job, state))
    return lines


def _failed_correction(payload: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """Codex re-review F14: the failure a correction job stored (its request's
    row, ``failed``) while it is still the newest version of the figure it
    corrects: nothing supersedes it and no later correction of that figure
    was stored. None otherwise (it succeeded, stored nothing, or was replaced)."""

    supersedes = payload.get("supersedes_id")
    request_id = payload.get("request_id")
    if not supersedes or not request_id:
        return None
    mine = [row for row in rows if row.get("request_id") == request_id and row.get("supersedes_id") == supersedes]
    if not mine or mine[-1].get("verification") != "failed":
        return None
    failed = mine[-1]
    later = [row for row in rows if row.get("supersedes_id") in (supersedes, failed["id"])]
    if later and later[-1]["id"] != failed["id"]:
        return None
    return failed


# ---------------------------------------------------------------------------
# One figure that may be shown now
# ---------------------------------------------------------------------------

def shown_figure(vault: Any, repository: Repository, figure_id: str) -> tuple[dict[str, Any], Any]:
    """A figure that may be shown now: shown verification, a current spec
    version, its passage not held out. Returns the row and its compiled
    spec (a :class:`~learnloop.figures.spec.CompiledFigure`, or for a sketch
    a :class:`~learnloop.figures.sketch.CompiledSketch`)."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        row = store.figure(connection, figure_id) if store.has_tables(connection) else None
    if row is None:
        raise FigureRefused("not_found", "That figure is no longer kept.")
    if row["verification"] not in store.SHOWN or row["spec_version"] not in SPEC_VERSIONS or not row.get("spec_json"):
        # A rich figure (RW5d P2b) has no predictions and is shown through its view only.
        raise FigureRefused("not_found", "That figure is not shown.")
    available = available_row(vault, row)
    if available is not row and available.get("unsupported_kind") == SKETCH_OFF_KIND:
        raise FigureRefused("sketch_disabled", "That figure is a simulation, and the sketch engine can't run here.")
    if available is not row:
        raise FigureRefused("not_found", "That figure can't be drawn here.")
    if sketch_row(row):
        # Codex review F9: the rechecked row is the one delivered and
        # predicted on (its dropped predictions are this engine's).
        row = dict(sketch_rechecked(row, repository))
        if row.get("verification") not in store.SHOWN:
            raise FigureRefused("not_found", "That simulation couldn't run under this version.")
    if show_me_row(row) and not figures_enabled(vault):
        raise FigureRefused("figures_disabled", "Explorable figures are switched off (figures.enabled).")
    if row_withheld(vault, repository, row) is not None:
        raise FigureRefused("exam_material", "That figure's passage is held out now.")
    if source_rejected(vault, repository, row):
        raise FigureRefused("not_found", "That figure is not shown.")
    if sketch_row(row):
        return row, K.parse_sketch(row["spec_json"])
    return row, S.parse_spec(row["spec_json"])


__all__ = [
    "list_figures",
    "prefetch_pending",
    "prefetch_plan_waits",
    "rich_pending",
    "section_figures",
    "shown_figure",
]
