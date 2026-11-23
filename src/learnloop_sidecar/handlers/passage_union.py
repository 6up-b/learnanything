"""Reader workbench v2 RPC: ``passage.union_range`` (spec §3.4, §7.6), everything tied to each
passage of one visible range. Batched per range, never per span on hover; goal-independent.

Desktop only (pinned in tests/test_mobile_allowlist.py). Read only; no model call.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from learnloop.passage_union.content import passage_content
from learnloop.passage_union.union import UnionError, union_range
from learnloop.source_retrieval import note_links as NL
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
PASSAGE_UNION_RPCS: tuple[str, ...] = ("passage.union_range",)
#: RD4's fix round (pinned desktop-only).
PASSAGE_CONTENT_RPCS: tuple[str, ...] = ("passage.content",)


class UnionRangeInput(ParamsModel):
    extraction_id: str = Field(min_length=1)
    from_span_id: str | None = None
    to_span_id: str | None = None
    t0: float | None = Field(default=None, ge=0)
    t1: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _one_range(self) -> UnionRangeInput:
        spans = self.from_span_id is not None and self.to_span_id is not None
        times = self.t0 is not None and self.t1 is not None
        partial = (self.from_span_id is None) != (self.to_span_id is None) or (self.t0 is None) != (self.t1 is None)
        if spans == times or partial:
            raise ValueError("a range is two passages (from_span_id, to_span_id) or two times (t0, t1)")
        return self


@method("passage.union_range", UnionRangeInput)
def passage_union_range_handler(ctx: SidecarContext, params: UnionRangeInput) -> dict[str, Any]:
    """``{extraction_id, spans: [{span_id, …everything tied to it}], sections}``."""

    vault, repository = ctx.require_vault()
    # The notes linked beside each passage (curriculum C2's marks, while notes.enabled): the sidecar reads
    # the notes' code, so the union read below it never does.
    notes_by_span = ({mark["span_id"]: mark["notes"] for mark in NL.marks(vault, repository, params.extraction_id)}
                     if NL.enabled(vault) and repository.get_extraction_run(params.extraction_id) is not None else {})
    try:
        return versioned(union_range(vault, repository, extraction_id=params.extraction_id,
                                     from_span_id=params.from_span_id, to_span_id=params.to_span_id, t0=params.t0,
                                     t1=params.t1, notes_by_span=notes_by_span))
    except UnionError as exc:
        raise SidecarError(exc.code, str(exc)) from exc


@method("passage.content", UnionRangeInput)
def passage_content_handler(ctx: SidecarContext, params: UnionRangeInput) -> dict[str, Any]:
    """One range of a reading as the source has it: ``{extraction_id, source_id, title, withheld, spans: [{span_id,
    text, page, t0, t1, section_id, section_label, withheld}]}`` (a ``source_piece``'s words, location and time)."""

    vault, repository = ctx.require_vault()
    try:
        return versioned(passage_content(vault, repository, extraction_id=params.extraction_id,
                                         from_span_id=params.from_span_id, to_span_id=params.to_span_id,
                                         t0=params.t0, t1=params.t1))
    except UnionError as exc:
        raise SidecarError(exc.code, str(exc)) from exc


# -- RD5: the split menu's promoted rows and What this knows (spec §9.1, §9.2) -------------------------------------

#: RD5's (pinned desktop-only).
MENU_RPCS: tuple[str, ...] = ("passage.promoted", "passage.promoted_job", "passage.promoted_cancel", "passage.knows")
PROMOTED_KIND = "passage.promoted"
_PROMOTED_REGISTRY = "promoted_jobs"


class MenuObjectInput(ParamsModel):
    """The object a menu was opened on (§9.1 "invocation"): a passage, a transcript cue (its span or a time), a
    highlight or margin note (its annotation and the passage it sits on), a window header (the passage in view), or
    a pad line (its block)."""

    object_kind: Literal["passage", "cue", "highlight", "note", "window", "pad_line"]
    extraction_id: str | None = None
    span_id: str | None = None
    t: float | None = Field(default=None, ge=0)
    annotation_id: str | None = None
    block_id: str | None = None
    window_id: str | None = None
    desk_id: str | None = None

    @model_validator(mode="after")
    def _names_its_object(self) -> MenuObjectInput:
        if self.object_kind == "pad_line":
            if not self.block_id:
                raise ValueError("a pad line names its block_id")
        elif not self.extraction_id or (self.span_id is None and not (self.object_kind == "cue" and self.t is not None)):
            raise ValueError("a passage, cue, highlight, note or window names its extraction_id and span_id (a cue "
                             "may give its time t instead)")
        if self.object_kind in ("highlight", "note") and not self.annotation_id:
            raise ValueError("a highlight or a margin note names its annotation_id")
        return self


def _menu_places(vault: Any, repository: Any, params: MenuObjectInput) -> tuple[str, list[tuple[str, str]], str,
                                                                                    list[str]]:
    """The object's key, its passages, the words to search by, and the sources it sits in."""

    from learnloop.content.sources.span_aliases import reading_source
    from learnloop.db.stores import pad_reads
    from learnloop.pads.emission import passages_of
    from learnloop.passage_union import promoted as P
    from learnloop.passage_union.union import _range

    if params.object_kind == "pad_line":
        with repository.connection() as connection:
            head = pad_reads.head(connection, str(params.block_id))
            if head is None or head["tombstone"]:
                raise SidecarError("block_not_found", "That pad line is gone.")
            places = [(str(e), str(s)) for e, s in passages_of(connection, head)]
        text = str(head["body_md"] or "")
        key = P.object_key("pad_line", block_id=params.block_id)
    else:
        extraction_id = str(params.extraction_id)
        ir = repository.load_document_ir(extraction_id)
        if ir is None:
            raise SidecarError("extraction_not_found", f"No reading {extraction_id!r}.")
        span_id = params.span_id
        if span_id is None:
            try:
                spans = _range(ir, from_span_id=None, to_span_id=None, t0=params.t, t1=params.t)
            except UnionError as exc:
                raise SidecarError(exc.code, str(exc)) from exc
            if not spans:
                raise SidecarError("span_not_found", "No cue at that time.")
            span_id = spans[0]
        block = next((b for b in ir.blocks if b.span_id == span_id), None)
        if block is None:
            raise SidecarError("span_not_found", "That passage is not in this reading.")
        places, text = [(extraction_id, str(span_id))], str(block.text or "")
        key = P.object_key(params.object_kind, extraction_id=extraction_id, span_id=str(span_id),
                           annotation_id=params.annotation_id, window_id=params.window_id)
    sources = sorted({source for extraction_id, _span in places
                      if (source := reading_source(repository, extraction_id)) is not None})
    return key, places, text, sources


def _union_entries(vault: Any, repository: Any, places: list[tuple[str, str]]) -> list[tuple[str, str, dict]]:
    out = []
    for extraction_id, span_id in places:
        try:
            union = union_range(vault, repository, extraction_id=extraction_id, from_span_id=span_id, to_span_id=span_id)
        except UnionError:
            continue
        out.extend((extraction_id, span_id, entry) for entry in union["spans"])
    return out


def _dismissed(repository: Any, rows: list[Any]) -> set[str]:
    from learnloop.db.stores import pad_reads
    from learnloop.passage_union import promoted as P

    with repository.connection() as connection:
        return P.dismissed_rows(pad_reads.labels_for(connection, "promoted_row", [row.row_id for row in rows]))


@method("passage.knows", MenuObjectInput)
def passage_knows_handler(ctx: SidecarContext, params: MenuObjectInput) -> dict[str, Any]:
    """What this knows (§9.1 ``i``), as one read: the object's passages, each with everything the union read ties to
    it (each row with its anchor quality and alias)."""

    from learnloop.source_retrieval.corpus import block_roles

    vault, repository = ctx.require_vault()
    key, places, _text, sources = _menu_places(vault, repository, params)
    with repository.connection() as connection:
        # A passage's effective role ("exercise", "solution", ...): Make it practice imports an exercise and authors
        # a question otherwise (§9.1).
        roles = block_roles(connection, places)
    return versioned({"object_key": key, "source_ids": sources,
                      "places": [{"extraction_id": extraction_id, "span_id": span_id,
                                  "role": roles.get((extraction_id, span_id)), "knows": entry}
                                 for extraction_id, span_id, entry in _union_entries(vault, repository, places)]})


@method("passage.promoted", MenuObjectInput)
def passage_promoted_handler(ctx: SidecarContext, params: MenuObjectInput) -> dict[str, Any]:
    """The menu's promoted rows at once (the cheap ones, ranked, at most four) and the job finding the judged ones:
    ``{object_key, rows, cap, pending_job: {job_id} | null, paid: {searched_by_meaning, verified, reason}}``."""

    from learnloop.ai import model_use
    from learnloop.ids import new_ulid
    from learnloop.passage_union import elsewhere as E
    from learnloop.passage_union import promoted as P
    from learnloop_sidecar import polled_jobs as PJ

    vault, repository = ctx.require_vault()
    key, places, text, sources = _menu_places(vault, repository, params)
    with repository.connection() as connection:
        linked = E.by_passage_links(repository, connection, places)
    cheap = P.cheap_rows(key, _union_entries(vault, repository, places), linked)
    rows = P.rank(cheap, dismissed=_dismissed(repository, cheap))
    retrieval = bool(getattr(vault.config.source_retrieval, "enabled", False))
    waiting = model_use.waiting(vault.root)
    paid = {"searched_by_meaning": retrieval and not waiting, "verified": retrieval and not waiting,
            "reason": None if retrieval and not waiting else (
                "waiting for your OK to use AI" if waiting else "source retrieval is off")}

    def work(job: PJ.PolledJob) -> dict[str, Any]:
        findings = E.by_correspondents(vault, repository, places, search_fallback=True,
                                       embedder=getattr(ctx, "coverage_embedder", None))
        if retrieval:
            findings += E.by_search(vault, repository, text, exclude_sources=sources, exclude_places=places,
                                    deep=paid["searched_by_meaning"], verify=paid["verified"],
                                    owner_id=f"{PROMOTED_KIND}:{job.job_id}", pick_at_most=P.CAP)
        judged = P.finding_rows(key, findings)
        everything = cheap + judged
        return {"rows": [row.wire() for row in P.rank(everything, dismissed=_dismissed(repository, everything))]}

    job = PJ.registry(ctx, _PROMOTED_REGISTRY).start(
        ctx, kind=PROMOTED_KIND, job_id=f"prom_{new_ulid()}", work=work,
        supersede_key=f"menu:{params.desk_id or ''}")
    return versioned({"object_key": key, "rows": [row.wire() for row in rows], "cap": P.CAP,
                      "pending_job": {"job_id": job.job_id}, "paid": paid})


class PromotedJobInput(ParamsModel):
    job_id: str = Field(min_length=1)


def _promoted_job_payload(ctx: SidecarContext, job_id: str) -> dict[str, Any]:
    from learnloop.ai import plan_fallback
    from learnloop_sidecar import polled_jobs as PJ

    jobs = PJ.registry(ctx, _PROMOTED_REGISTRY)
    job = jobs.get(job_id)
    if job is None:
        if jobs.receipt(job_id) is None:
            raise SidecarError("job_not_found", "That menu is no longer kept; open it again.",
                               details={"job_id": job_id})
        return versioned({"job_id": job_id, "status": PJ.EXPIRED, "done": True, "rows": [], "error": None})
    state = job.state()
    if state["finished"]:
        plan_fallback.relay_job_offer(job)
    status = state["status"]
    error = state["error"] if status == PJ.FAILED else None
    return versioned({
        "job_id": job_id, "status": status, "done": bool(state["finished"]),
        # A cancelled or superseded menu delivers nothing, even when its work finished.
        "rows": (state["result"] or {}).get("rows", []) if status == PJ.DONE else [],
        "error": None if error is None else {"code": error.code, "message": error.message,
                                             "retryable": error.retryable},
    })


@method("passage.promoted_job", PromotedJobInput)
def passage_promoted_job_handler(ctx: SidecarContext, params: PromotedJobInput) -> dict[str, Any]:
    """The judged rows' job at once (never a wait): when done, every row ranked again, cheap and judged, at most
    four."""

    ctx.require_vault()
    return _promoted_job_payload(ctx, params.job_id)


@method("passage.promoted_cancel", PromotedJobInput)
def passage_promoted_cancel_handler(ctx: SidecarContext, params: PromotedJobInput) -> dict[str, Any]:
    """Cancel the judged rows' job (the menu closed): its next paid request is refused; a finished job keeps its
    outcome."""

    from learnloop_sidecar import polled_jobs as PJ

    ctx.require_vault()
    PJ.registry(ctx, _PROMOTED_REGISTRY).cancel(params.job_id)
    return _promoted_job_payload(ctx, params.job_id)
