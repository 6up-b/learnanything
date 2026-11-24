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
from learnloop_sidecar.workbench_protection import VERB_SURFACES, block_places, withheld_verbs

#: Every RPC this module registers (pinned desktop-only).
PASSAGE_UNION_RPCS: tuple[str, ...] = ("passage.union_range",)
#: RD4's fix round (pinned desktop-only).
PASSAGE_CONTENT_RPCS: tuple[str, ...] = ("passage.content",)


def _notes_by_span(vault: Any, repository: Any, extraction_id: str) -> dict[str, list[dict[str, Any]]]:
    """The notes linked beside each passage of a reading (curriculum C2's marks, while notes.enabled): the sidecar
    reads the notes' code, so the union read below it never does. Every union read here hands them in."""

    if not NL.enabled(vault) or repository.get_extraction_run(extraction_id) is None:
        return {}
    return {mark["span_id"]: mark["notes"] for mark in NL.marks(vault, repository, extraction_id)}


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
            raise ValueError("Select the passage or caption again.")
        return self


@method("passage.union_range", UnionRangeInput)
def passage_union_range_handler(ctx: SidecarContext, params: UnionRangeInput) -> dict[str, Any]:
    """``{extraction_id, spans: [{span_id, …everything tied to it}], sections}``."""

    vault, repository = ctx.require_vault()
    try:
        union = union_range(vault, repository, extraction_id=params.extraction_id, from_span_id=params.from_span_id,
                            to_span_id=params.to_span_id, t0=params.t0, t1=params.t1,
                            notes_by_span=_notes_by_span(vault, repository, params.extraction_id),
                            include_word_origins=True)
    except UnionError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    # A stored quote, authored question or other row whose words came from exam or held-out material is withheld
    # here as in the menu's reads, whenever the material was marked (the union read stores words, not verdicts).
    _withhold_rows(vault, repository, union["spans"])
    return versioned(union)


class PassageContentInput(UnionRangeInput):
    #: The menu verb the words are read for: its destination's set decides what is withheld (Make it practice's
    #: exercise sheet reads with the import's); none, all exam material (a source piece copied into a pad).
    for_verb: Literal["make_practice"] | None = None


@method("passage.content", PassageContentInput)
def passage_content_handler(ctx: SidecarContext, params: PassageContentInput) -> dict[str, Any]:
    """One range of a reading as the source has it: ``{extraction_id, source_id, title, withheld, spans: [{span_id,
    text, page, t0, t1, section_id, section_label, withheld}]}`` (a ``source_piece``'s words, location and time)."""

    vault, repository = ctx.require_vault()
    surface = VERB_SURFACES[params.for_verb][0] if params.for_verb else None
    try:
        return versioned(passage_content(vault, repository, extraction_id=params.extraction_id,
                                         from_span_id=params.from_span_id, to_span_id=params.to_span_id,
                                         t0=params.t0, t1=params.t1, surface=surface))
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
    span_ids: list[str] = Field(default_factory=list)
    t: float | None = Field(default=None, ge=0)
    annotation_id: str | None = None
    block_id: str | None = None
    block_ids: list[str] = Field(default_factory=list)
    window_id: str | None = None
    desk_id: str | None = None
    #: passage.knows only: the menu verb it is read for (Make it practice reads the passage's section and role), so
    #: its destination's own set decides the refusal, as the menu's per-verb verdict does.
    for_verb: Literal["make_practice"] | None = None

    @model_validator(mode="after")
    def _names_its_object(self) -> MenuObjectInput:
        if self.object_kind == "pad_line":
            if not self.block_id:
                raise ValueError("Select the pad line again.")
        elif not self.extraction_id or (self.span_id is None and not (self.object_kind == "cue" and self.t is not None)):
            raise ValueError("Select the passage or caption again.")
        if self.object_kind in ("highlight", "note") and not self.annotation_id:
            raise ValueError("Reopen the menu on the highlight or margin note.")
        return self


class PromotedInput(MenuObjectInput):
    """The menu's object and, from a client that may retry, its request id: a repeat answers with the job the
    first request started (its work runs once); the same id for another object is refused."""

    request_id: str | None = Field(default=None, min_length=1)


def _menu_places(vault: Any, repository: Any, params: MenuObjectInput) -> tuple[str, list[tuple[str, str]], str,
                                                                                    list[str], bool]:
    """The object's key, its passages, the words to search by, the sources it sits in, and whether any of its
    passages is exam or held-out material. A protected passage's words are never searched by (nor sent to a judge):
    the words are empty then, for a pad line too (its words follow the passages they were written about)."""

    from learnloop.passage_union.elsewhere import withheld_places

    from learnloop.content.sources.span_aliases import reading_source
    from learnloop.db.stores import pad_reads
    from learnloop.passage_union import promoted as P
    from learnloop.passage_union.union import span_range

    if params.object_kind == "pad_line":
        with repository.connection() as connection:
            head = pad_reads.head(connection, str(params.block_id))
            if head is None or head["tombstone"]:
                raise SidecarError("block_not_found", "This pad line is gone. Choose another line.")
        key = P.object_key("pad_line", block_id=params.block_id)
        try:
            places = block_places(vault, repository, [head["block_id"], *params.block_ids])
        except SidecarError as exc:
            if exc.code == "exam_material":
                return key, [], "", [], True
            raise
        text = str(head["body_md"] or "")
    else:
        extraction_id = str(params.extraction_id)
        ir = repository.load_document_ir(extraction_id)
        if ir is None:
            raise SidecarError("extraction_not_found", "Couldn’t find this source. Reopen it from your library.")
        span_id = params.span_id
        if span_id is None:
            try:
                spans = span_range(ir, from_span_id=None, to_span_id=None, t0=params.t, t1=params.t)
            except UnionError as exc:
                raise SidecarError(exc.code, str(exc)) from exc
            if not spans:
                raise SidecarError("span_not_found", "Play the video until a caption appears, then try again.")
            span_id = spans[0]
        block = next((b for b in ir.blocks if b.span_id == span_id), None)
        if block is None:
            raise SidecarError("span_not_found", "That passage is not in this reading.")
        selected = dict.fromkeys([span_id, *params.span_ids])
        if selected.keys() - {block.span_id for block in ir.blocks}:
            raise SidecarError("span_not_found", "A selected passage is not in this reading.")
        places = [(extraction_id, span) for span in selected]
        if params.annotation_id and (head := repository.annotation_head(params.annotation_id)):
            from learnloop.reader.annotations import annotation_placements

            original = (head.get("anchor") or {}).get("extraction_id")
            places.extend((original, segment["span_id"]) for segment in head["segments"] if original)
            placement, = annotation_placements(repository, [head], extraction_id)
            places.extend((extraction_id, segment["span_id"]) for segment in placement["segments"])
            places = list(dict.fromkeys(places))
        text = str(block.text or "")
        key = P.object_key(params.object_kind, extraction_id=extraction_id, span_id=str(span_id),
                           annotation_id=params.annotation_id, window_id=params.window_id)
    sources = sorted({source for extraction_id, _span in places
                      if (source := reading_source(repository, extraction_id)) is not None})
    withheld = bool(withheld_places(vault, repository, places))
    return key, places, "" if withheld else text, sources, withheld


def _union_entries(vault: Any, repository: Any, places: list[tuple[str, str]],
                   row_origins: dict[str, set[tuple[str, str]]] | None = None) -> list[tuple[str, str, dict]]:
    out = []
    notes: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for extraction_id, span_id in places:
        if extraction_id not in notes:
            notes[extraction_id] = _notes_by_span(vault, repository, extraction_id)
        try:
            union = union_range(vault, repository, extraction_id=extraction_id, from_span_id=span_id, to_span_id=span_id,
                                notes_by_span=notes[extraction_id], include_word_origins=True)
        except UnionError:
            continue
        out.extend((extraction_id, span_id, entry) for entry in union["spans"])
    _withhold_rows(vault, repository, [entry for _, _, entry in out], row_origins)
    return out


#: The union read's rows that carry words from a passage (each with its ``_word_origins``).
_WORD_FIELDS = ("annotations", "carried", "exchanges", "authored_questions", "passage_links")


def _withhold_rows(vault: Any, repository: Any, entries: list[dict[str, Any]],
                   row_origins: dict[str, set[tuple[str, str]]] | None = None) -> None:
    """Drop every row whose words came from exam or held-out material, in place, and the rows' origins with them
    (``row_origins`` collects a kept learner row's origins for a later recheck)."""

    from learnloop.passage_union.elsewhere import withheld_places

    hidden = withheld_places(vault, repository, {place for entry in entries for field in _WORD_FIELDS
                                                 for row in entry[field] for place in row.get("_word_origins", ())})
    for entry in entries:
        for field in _WORD_FIELDS:
            visible = []
            for row in entry[field]:
                origins = row.pop("_word_origins", set())
                if hidden.isdisjoint(origins):
                    visible.append(row)
                    ident = row.get("annotation_id") or row.get("carried_id")
                    if row_origins is not None and ident:
                        row_origins.setdefault(ident, set()).update(origins)
            entry[field] = visible


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
    key, places, _text, sources, withheld = _menu_places(vault, repository, params)
    if params.for_verb is not None:
        withheld = params.for_verb in withheld_verbs(vault, repository, places)
    if withheld:
        raise SidecarError("exam_material", "Details for this material are withheld.")
    with repository.connection() as connection:
        # A passage's effective role ("exercise", "solution", ...): Make it practice imports an exercise and authors
        # a question otherwise (§9.1).
        roles = block_roles(connection, places)
    return versioned({"object_key": key, "source_ids": sources,
                      "places": [{"extraction_id": extraction_id, "span_id": span_id,
                                  "role": roles.get((extraction_id, span_id)), "knows": entry}
                                 for extraction_id, span_id, entry in _union_entries(vault, repository, places)]})


@method("passage.promoted", PromotedInput)
def passage_promoted_handler(ctx: SidecarContext, params: PromotedInput) -> dict[str, Any]:
    """The menu's promoted rows at once (the cheap ones, ranked, at most four) and the job finding the judged ones:
    ``{object_key, rows, cap, withheld, pending_job: {job_id} | null, paid: {searched_by_meaning, verified,
    reason}}``. ``withheld``: a passage of the object is exam or held-out material, so nothing is searched for it
    and no passage elsewhere is promoted from it."""

    from learnloop.ai import model_use
    from learnloop.ids import new_ulid
    from learnloop.passage_union import elsewhere as E
    from learnloop.passage_union import promoted as P
    from learnloop_sidecar import polled_jobs as PJ

    vault, repository = ctx.require_vault()
    key, places, text, sources, withheld = _menu_places(vault, repository, params)
    with repository.connection() as connection:
        linked = [] if withheld else E.by_passage_links(vault, repository, connection, places)
    word_origins: dict[str, set[tuple[str, str]]] = {}
    cheap = P.cheap_rows(key, _union_entries(vault, repository, places, word_origins), linked)
    if withheld:
        cheap = [row for row in cheap if row.kind not in {"note", "carried"}]
    retrieval = bool(getattr(vault.config.source_retrieval, "enabled", False)) and not withheld
    waiting = model_use.waiting(vault.root)
    paid = {"searched_by_meaning": retrieval and not waiting, "verified": retrieval and not waiting,
            "reason": None if retrieval and not waiting else (
                "exam or held-out material: nothing is searched for it" if withheld else
                "waiting for your OK to use AI" if waiting else "source retrieval is off")}

    def kept_rows(candidates: list[P.Row]) -> dict[str, Any]:
        kept = P.rank(candidates, dismissed=_dismissed(repository, candidates))
        row_places = {}
        for row in kept:
            ident = row.action.get("carried_id") or row.action.get("annotation_id")
            if ident in word_origins:
                row_places[row.row_id] = word_origins[ident]
        return {"origins": places, "block_ids": [params.block_id, *params.block_ids] if params.block_id else [],
                "withheld": withheld, "rows": [row.wire() for row in kept], "row_places": row_places}

    def work(job: PJ.PolledJob) -> dict[str, Any]:
        def protected_now() -> bool:
            if withheld:
                return True
            origins = set(places)
            if params.block_id:
                origins.update(block_places(vault, repository, [params.block_id, *params.block_ids]))
            return bool(E.withheld_places(vault, repository, origins))

        findings = [] if protected_now() else E.by_correspondents(
            vault, repository, places, search_fallback=True, embedder=getattr(ctx, "coverage_embedder", None))
        if retrieval and not protected_now():
            findings += E.by_search(vault, repository, text, exclude_sources=sources, exclude_places=places,
                                    deep=paid["searched_by_meaning"], verify=paid["verified"],
                                    owner_id=f"{PROMOTED_KIND}:{job.job_id}", pick_at_most=P.CAP)
        judged = P.finding_rows(key, findings)
        return kept_rows(cheap + judged)

    jobs = PJ.registry(ctx, _PROMOTED_REGISTRY)
    request_key = params.model_dump(mode="json")
    known = jobs.known(PJ.vault_key(ctx), params.request_id) if params.request_id else None
    if known is not None and known.request_key != request_key:
        raise SidecarError("request_reused", "Reopen the passage menu to see suggestions.",
                           details={"request_id": params.request_id})
    job_id = known.job_id if known is not None else jobs.start(
        ctx, kind=PROMOTED_KIND, job_id=params.request_id or f"prom_{new_ulid()}", work=work,
        request_key=request_key, supersede_key=f"menu:{params.desk_id or ''}").job_id
    rows, blocked = _deliver_rows(ctx, kept_rows(cheap))
    # Per verb (``withheld_verbs``): each verb's destination decides by its own set, so a practice exam that is not
    # held out keeps the Ask and practice the Reader offers; ``withheld`` stays the menu's own search's (all exam).
    verbs = sorted(VERB_SURFACES) if blocked and not withheld else withheld_verbs(vault, repository, places)
    return versioned({"object_key": key, "rows": rows, "cap": P.CAP, "withheld": withheld or blocked,
                      "withheld_verbs": verbs, "pending_job": {"job_id": job_id}, "paid": paid})


class PromotedJobInput(ParamsModel):
    job_id: str = Field(min_length=1)


def _deliver_rows(ctx: SidecarContext, result: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    from learnloop.passage_union.elsewhere import withheld_places

    vault, repository = ctx.require_vault()
    origins = set(result["origins"])
    try:
        origins.update(block_places(vault, repository, result["block_ids"]))
    except SidecarError as exc:
        if exc.code in {"block_not_found", "exam_material"}:
            return [], True
        raise
    rows = result["rows"]

    def target(row: dict[str, Any]) -> tuple[str, str] | None:
        action = row["action"]
        extraction = action.get("ref", {}).get("extraction_id")
        span = action.get("target", {}).get("span_id")
        return (extraction, span) if extraction and span else None

    row_places = result["row_places"]
    withheld = withheld_places(vault, repository, origins | {place for row in rows if (place := target(row))}
                               | {place for places in row_places.values() for place in places})
    origin_withheld = not origins.isdisjoint(withheld)
    if origin_withheld and not result["withheld"]:
        return [], True
    return [row for row in rows if target(row) not in withheld and
            withheld.isdisjoint(row_places.get(row["row_id"], ()))], origin_withheld


def _verbs_now(ctx: SidecarContext, result: dict[str, Any]) -> list[str]:
    """The per-verb verdict at a delivery, read again from the object's origins (a mark made since counts); a pad line
    that cannot be read withholds every verb."""

    vault, repository = ctx.require_vault()
    try:
        origins = set(result["origins"]) | set(block_places(vault, repository, result["block_ids"]))
    except SidecarError:
        return sorted(VERB_SURFACES)
    return withheld_verbs(vault, repository, origins)


def _promoted_job_payload(ctx: SidecarContext, job_id: str) -> dict[str, Any]:
    from learnloop.ai import plan_fallback
    from learnloop_sidecar import polled_jobs as PJ

    # Polled jobs are kept per vault: a job id from another vault is not found here.
    jobs = PJ.registry(ctx, _PROMOTED_REGISTRY)
    vault = PJ.vault_key(ctx)
    job = jobs.get(vault, job_id)
    if job is None:
        if jobs.receipt(vault, job_id) is None:
            raise SidecarError("job_not_found", "Suggestions expired. Reopen the passage menu to try again.",
                               details={"job_id": job_id})
        return versioned({"job_id": job_id, "status": PJ.EXPIRED, "done": True, "rows": [], "error": None})
    state = job.state()
    if state["finished"]:
        plan_fallback.relay_job_offer(job)
    status = state["status"]
    error = state["error"] if status == PJ.FAILED else None
    rows, withheld = _deliver_rows(ctx, state["result"]) if status == PJ.DONE else ([], None)
    verbs = None if withheld is None else _verbs_now(ctx, state["result"])
    return versioned({
        "job_id": job_id, "status": status, "done": bool(state["finished"]),
        # A cancelled or superseded menu delivers nothing, even when its work finished.
        "rows": rows, **({"withheld": withheld, "withheld_verbs": verbs} if withheld is not None else {}),
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
    PJ.registry(ctx, _PROMOTED_REGISTRY).cancel(PJ.vault_key(ctx), params.job_id)
    return _promoted_job_payload(ctx, params.job_id)
