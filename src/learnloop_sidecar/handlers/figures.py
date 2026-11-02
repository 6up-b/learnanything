"""Reader workbench RW5a RPCs: explorable figures (spec_reader_workbench_v1 §8; UX §4.7, W11).

* ``reader.figure_request``: "make this explorable" on a selection (an
  equation, a figure block, a short passage) or a region of a figure; RW5b:
  or on an offer (``origin`` ``library`` | ``tutor`` with ``offer_ref``, the
  block the organizer's or the tutor's stored judgment said was explorable). Checked
  at once on the request path (the switches; exam and held-out material is
  refused before any job or model call, the one predicate); then the build
  runs off the request path as a job (RW4a's runner): reuse by input hash,
  the author (at most two attempts) and verification (structure, invariants,
  shaded areas; no source check in RW5a), every request admitted by the
  build's FiguresGate against the vault loaded now.
* ``reader.figure_revise``: "not right?" with the learner's note, a new
  version superseding the shown one (the earlier one is kept).
* ``reader.figure_job`` / ``reader.figure_job_cancel``: read a build at once
  (never a wait), or cancel it (a cancelled build never answers; a paid call
  already sent finishes and its receipt and row are kept).
* ``reader.figures``: the figures of the open source as the Reader shows them
  (a figure whose passage is held out now is left out).
* ``reader.figure_predict`` / ``reader.figure_explain``: the prediction before
  the first change and its optional "what changed?" (formative only).

* ``figure.request`` (Reader RW5d P1, spec_reader_show_me_figures_v1 §7.1):
  the one request for every host, ``FigureRequestV1``: a goal in the
  learner's words (``goalText``), an optional anchor (today's request), where
  the learner was reading (``readingAt``, the home of a figure with no
  passage), the host references (each verified here; P1's hosts are the
  Reader's) and ``offerRef`` (RW5b's, and the tutor answer whose stored
  ``figure_goal`` a tutor goal must equal). ``goal_author`` is never taken
  from the client, and a client never states its policy: the caller is
  derived here, and a check on your own (``coldActive``, or a cold caller)
  or an attempt host refuses (P3 owns figures in attempts).
  ``reader.figure_request`` stays as a thin wrapper for anchor-only requests.
  The build job is read with ``reader.figure_job`` as before; its origin (T1
  redesign D: the offer is the grant) is the RPC method that started it.

Desktop only (pinned in tests/test_mobile_allowlist.py). Kill switches:
``figures.enabled`` (off: every RPC here refuses, the prompt contract has no
``figures`` key, the intent box has no "make this explorable" and no route
is called), ``figures.predictions_enabled``, ``figures.region_enabled``,
``figures.revisions_enabled``, and RW5b's ``figures.offers_enabled`` (off:
no ``offers`` in the contract and an offered request is refused) and
``figures.advanced_panels_enabled``. Nothing here writes an attempt, evidence,
mastery, certification, FSRS, scheduler state or a plan.
"""
from __future__ import annotations

from contextlib import closing
from typing import Any, Literal

from pydantic import Field

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.figures import service as FS
from learnloop.substrate.activities import log_interaction_event
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.source_identity import require_identity
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
FIGURE_RPCS: tuple[str, ...] = (
    "figure.request",
    "figure.rich_cancel",
    "figure.rich_retry",
    "figure.manim_opt_in",
    "reader.figure_request",
    "reader.figure_revise",
    "reader.figure_job",
    "reader.figure_job_cancel",
    "reader.figures",
    "reader.figure_predict",
    "reader.figure_explain",
)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW5a (absent while off).
    RW5b adds ``offers: true`` only while ``figures.offers_enabled`` is on, so
    with it off the contract is RW5a's, key for key."""

    if not FS.enabled(vault):
        return {}
    figures: dict[str, Any] = {"predictions": FS.predictions_enabled(vault), "region": FS.region_enabled(vault),
                               "revisions": FS.revisions_enabled(vault)}
    if FS.figure_offers_enabled(vault):
        figures["offers"] = True
    if FS.show_me_enabled(vault):
        # RW5d P1: present only while figures.show_me_enabled is on, so off the
        # contract is RW5b's, key for key.
        figures["show_me"] = True
    if FS.sketch_enabled(vault):
        # RW5d P2: present only while the sketch tier is on (and the engine
        # ready), so off the contract is P1's, key for key.
        figures["sketch"] = True
    if FS.rich_enabled(vault) and (state := manim_opt_in_state(vault)) != "unavailable":
        # RW5d P2b: present only while the rich tiers are on and the Manim tier
        # concerns this machine (so off, or where Manim can't run, the contract
        # is P2's key for key), with its opt-in state: "ask" (never asked: the
        # press shows allow · not now once), "standing" or "declined".
        figures["rich"] = {"manim_opt_in": state}
    return {"figures": figures}


def manim_opt_in_state(vault: Any) -> str:
    from learnloop.figure_admission import manim_opt_in
    from learnloop.figures import rich as RICH

    given = manim_opt_in(vault)
    if given is not None:
        return given
    return "ask" if RICH.manim_opt_in_needed(vault) else "unavailable"


def _require(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    if not FS.enabled(vault):
        raise SidecarError("figures_disabled", "Explorable figures are switched off (figures.enabled).")
    return vault, repository


def _refused(exc: FS.FigureRefused) -> SidecarError:
    return SidecarError(exc.code, exc.message, retryable=exc.code in ("unavailable", "capped", FS.STORAGE_BUSY))


def _event(repository: Any, event: str, payload: dict[str, Any], *, extraction_id: str | None) -> None:
    log_interaction_event(repository, kind="reader_action_invoked", origin="learner",
                          subject_type="reader_extraction", subject_id=extraction_id,
                          payload=salience_payload({"event": event, **payload}))


# ---------------------------------------------------------------------------
# The jobs (never on the request path)
# ---------------------------------------------------------------------------

def _jobs(ctx: SidecarContext) -> Any:
    from learnloop_sidecar.handlers.library_ask import LibraryJobs

    jobs = getattr(ctx, "figure_jobs", None)
    if jobs is None:
        jobs = LibraryJobs()
        ctx.figure_jobs = jobs  # type: ignore[attr-defined]
    return jobs


def deliver_figure(ctx: SidecarContext, result: dict[str, Any]) -> dict[str, Any]:
    """A finished build as it may go out NOW: with the switch off since, or
    its passage held out since, nothing of it is delivered."""

    vault, repository = _require(ctx)
    figure = result.get("figure") or {}
    # Rechecked on the stored row: every span the author was sent, the
    # paragraphs around the selection included (Codex review F1).
    if figure and FS.figure_withheld(vault, repository, str(figure.get("figure_id") or "")):
        return {"figure": None, "reused": False, "withheld": True}
    if figure:
        # Follow-ups Nov 2: the kept view's fuller version is rebuilt from the
        # current rows (rechecked like any figure as it goes out), never the
        # one read when the build finished.
        result = {**result, "figure": FS.redelivered_view(vault, repository, figure)}
    return result


def _wake_gap_worker(ctx: SidecarContext) -> Any:
    """A queued learner-text job wakes the post-attempt worker's ``gaps``
    slot, which starts lazily (Codex review F6)."""

    return lambda _job_id: ctx.post_attempt_worker.notify()


def _rich_spawner(ctx: SidecarContext, vault: Any, *, granted: bool = True) -> Any:
    """RW5d P2b (spec §8.6, SM9): how a build starts its rich job on the
    durable queue. Taken here, in the pressed request: the press's token and
    action when that action is granted for this session (the grant covers
    the job), else none (the job belongs to no action: it makes no offer and
    honours no grant, and waits for the plan when it is down)."""

    from learnloop.ai import plan_fallback

    jobs = getattr(ctx, "ingest_jobs", None)
    if jobs is None or not hasattr(jobs, "enqueue_figure_rich"):
        return None
    # ``granted`` False (Codex review F8: a recovered intent, started from a
    # read): no action's grant, whatever this request carries.
    token = plan_fallback.unit_token(vault.root) if granted else None
    origin = plan_fallback.unit_origin() if token is not None else None

    def spawn(payload: dict[str, Any]) -> str:
        return jobs.enqueue_figure_rich(payload=payload, grant=token, origin=origin)

    return spawn


def _start(ctx: SidecarContext, request: FS.FigureRequest) -> dict[str, Any]:
    from learnloop_sidecar.handlers.library_ask import _job_payload

    vault, _repository = _require(ctx)
    author = getattr(ctx, "figure_author_client", None)
    # RW5d: the grounding retrieval (the sources service's, unset; a fake in tests).
    find = getattr(ctx, "figure_find_sources", None)
    spawn = _rich_spawner(ctx, vault) if FS.rich_enabled(vault) else None

    def work(worker_repo: Any) -> dict[str, Any]:
        try:
            # Every request is admitted against the vault loaded NOW (the
            # build's FiguresGate), not the one captured here.
            outcome = FS.build_figure(vault, worker_repo, request, author_client=author,
                                      live_vault=ctx.loaded_vault, find=find, spawn_rich=spawn)
        except FS.FigureRefused as exc:
            raise _refused(exc) from exc
        result: dict[str, Any] = {"figure": outcome.view, "reused": outcome.reused}
        if outcome.rich is not None:
            # RW5d P2b: only a rich figure is being built (its pending line).
            result["rich"] = outcome.rich
        return result

    job = _jobs(ctx).start(ctx, "figure_build", None, work, deliver=lambda result: deliver_figure(ctx, result))
    return _job_payload(job)


class RegionInput(ParamsModel):
    span_id: str
    bbox: list[float] = Field(min_length=4, max_length=4)


class FigureRequestInput(ParamsModel):
    extraction_id: str
    span_ids: list[str] = Field(default_factory=list, max_length=40)
    region: RegionInput | None = None
    #: RW5b: "make this explorable" pressed on an offer (``library`` | ``tutor``);
    #: ``offer_ref`` names the judgment that offered it (the library question,
    #: or the tutor answer's question event).
    origin: Literal["selection", "library", "tutor"] = "selection"
    offer_ref: str | None = Field(default=None, max_length=200)
    #: Reader follow-ups Nov 1: the passages as ``extraction:span`` keys, formed where
    #: they were taken; each must name this request's reading (None: not sent).
    span_keys: list[str] | None = Field(default=None, max_length=41)


def offered_spans(vault: Any, repository: Any, origin: str, offer_ref: str | None) -> set[tuple[str, str]]:
    """The ``(extraction_id, span_id)`` blocks the judgment ``offer_ref`` said
    were explorable: the library organizer's notes (RW4a) or the Reader tutor's
    answer (RW1c), as stored, each confirmed by the verdict's own
    ``judgment_ledger`` row (Codex review F3: the append-only ledger, not the
    output's JSON alone, says what the judge decided). Read from stored
    outputs only: the press makes no model call, and a block the judge did not
    offer is refused."""

    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.practice_index import judgments_by_ids
    from learnloop.figure_admission import offerable_blocks, tutor_explorable_yes

    if not offer_ref:
        return set()
    if origin == "library":
        from learnloop.source_retrieval import library_ask as LA

        try:
            row = LA.ask_row(repository, offer_ref)
        except LA.LibraryAskError:
            return set()
        notes = [note for note in (row.get("organizer") or {}).get("notes") or ()
                 if isinstance(note, dict) and note.get("explorable") is True and ":" in str(note.get("key") or "")]
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            ledger = judgments_by_ids(connection, [str(note.get("ledger_id") or "") for note in notes
                                                   if note.get("ledger_id")])
        # The note's ledger row is the judgment (fix round 2, F8): the
        # organizer's own task, on this very block, recording yes. Its left id
        # is not compared with this ask: a second identical ask is answered
        # from the ledger (rows keyed by the request, never the ask), and
        # RW4d's fork copies the notes under a new id, so a row's left id is
        # the ask that first paid for the judgment, not every ask showing it.
        said = {(str(note["key"]).split(":", 1)[0], str(note["key"]).split(":", 1)[1]) for note in notes
                if LA.ledger_explorable(found := ledger.get(str(note.get("ledger_id") or "")))
                and found.get("task") == LA.ORGANIZER_TASK.ledger_task
                and found.get("left_kind") == LA.ORGANIZER_TASK.left_kind
                and str(found.get("right_id")) == str(note["key"])}
    else:
        event = repository.question_event(offer_ref)
        view = ((event or {}).get("source_context") or {}).get("reader_tutor") or {}
        said = {(str(entry.get("extraction_id")), str(entry.get("span_id"))) for entry in view.get("explorable") or ()
                if isinstance(entry, dict)}
        said &= tutor_explorable_yes(repository, offer_ref, sorted(said))
    # Code's rule on top of the judgment: only an equation or a figure block.
    return set(offerable_blocks(repository, sorted(said)))


def tutor_figure_goal(repository: Any, offer_ref: str | None) -> dict[str, Any] | None:
    """RW5d: the ``figure_goal`` the Reader tutor's stored answer ``offer_ref``
    wrote (its text and the cited spans it grounds in), read from the stored
    output only (as :func:`offered_spans` reads its explorable blocks): the
    press makes no model call, and a goal the answer did not write is refused
    (G-SM5). Confirmed by the goal's own ``judgment_ledger`` row (Codex review
    F6: the append-only ledger, not the event's JSON alone, says what the
    tutor offered): a view whose goal or grounding differs from it is refused."""

    from learnloop.figure_admission import tutor_figure_goal_offered

    if not offer_ref:
        return None
    event = repository.question_event(offer_ref)
    view = ((event or {}).get("source_context") or {}).get("reader_tutor") or {}
    goal = view.get("figure_goal")
    if not isinstance(goal, dict) or not str(goal.get("text") or "").strip():
        return None
    if not tutor_figure_goal_offered(repository, offer_ref, goal.get("text"), goal.get("span_keys") or ()):
        return None
    return goal


def _same_goal(left: str | None, right: str | None) -> bool:
    return " ".join(str(left or "").split()) == " ".join(str(right or "").split()) != ""


#: P1's hosts are the Reader's: the attempt, workbench and lesson references are P3's and P4's.
_LATER_HOST_REFS = ("item_id", "submission_id", "workbench_session_id", "attempt_id", "lesson_id", "node_id")


def _host_caller(vault: Any, repository: Any, *, origin: str, host_ref: dict[str, Any],
                 offer_ref: str | None) -> Any | None:
    """The caller a request's question-event reference determines, or None
    when it names none (Codex review F2). Every supplied question event, from
    any origin (``hostRef.questionEventId``, and a tutor offer's ``offerRef``),
    is resolved on the server through ``caller_for_question_event``: the
    restriction it was asked under (cold, or bound to an item) is the
    request's, so the caller's policy refuses it below. P1's hosts are the
    Reader's: a question asked anywhere else is refused here."""

    from dataclasses import replace

    from learnloop.instructional.policy import caller_for_question_event
    from learnloop.source_retrieval.policy import PolicyRefused

    named = [str(ref) for ref in (host_ref.get("question_event_id"), offer_ref if origin == "tutor" else None) if ref]
    if not named:
        return None
    if len(set(named)) > 1:
        raise SidecarError("validation_error", "The request names two different answers.")
    event = repository.question_event(named[0])
    if event is None:
        raise SidecarError("not_found", "That answer is no longer kept.")
    if str(event.get("context") or "") != "reader":
        raise SidecarError("validation_error", "Figures on practice, feedback or lessons come in a later version.")
    try:
        caller = caller_for_question_event(vault, repository, named[0])
    except PolicyRefused as exc:
        raise SidecarError("not_found", str(exc)) from exc
    # The caller kind follows the origin (spec §7.2): the tutor's for a tutor
    # press, the Reader's otherwise; the event's restriction is kept either way.
    return caller if origin == "tutor" else replace(caller, kind="reader")


def _request_figure(ctx: SidecarContext, *, origin: str, extraction_id: str | None, span_ids: list[str],
                    region: dict[str, Any] | None, goal_text: str | None, reading_at: dict[str, Any] | None,
                    offer_ref: str | None, host_ref: dict[str, Any], cold_active: bool,
                    span_keys: list[str] | None = None) -> dict[str, Any]:
    """One figure request, from either RPC: validated, its caller derived and
    its held-out material refused here, on the request path, before any job or
    model call; then a build job."""

    from learnloop.source_retrieval.policy import derive_policy
    from learnloop_sidecar.handlers.library_ask import reader_caller

    vault, repository = _require(ctx)
    # Reader CA6b fix round 5: the anchor's passages and the reading place are
    # their readings' own (fail closed, before any job).
    if extraction_id:
        require_identity(repository, extraction_id=extraction_id,
                         span_ids=[*span_ids, (region or {}).get("span_id")], reading_span_keys=span_keys)
    if reading_at and reading_at.get("extraction_id"):
        require_identity(repository, extraction_id=str(reading_at["extraction_id"]), span_ids=[reading_at.get("span_id")])
    if origin in FS.RESERVED_ORIGINS:
        raise SidecarError("validation_error", f"Figures with origin {origin!r} are not made here.")
    goal = " ".join(str(goal_text or "").split()) or None
    if goal is not None and not FS.show_me_enabled(vault):
        raise SidecarError("show_me_disabled", "\"Show me\" in your own words is switched off (figures.show_me_enabled).")
    if cold_active:
        # SM4: nothing is shown or built during a check on your own (taking a
        # figure as help there is P3's take step).
        raise SidecarError("cold_check", "Figures aren't shown during a check on your own.")
    later = [name for name in _LATER_HOST_REFS if host_ref.get(name)]
    if later:
        raise SidecarError("validation_error", "Figures on practice, feedback or lessons come in a later version.")
    anchored = bool(span_ids or region)
    home = str(extraction_id) if anchored else str((reading_at or {}).get("extraction_id") or "")
    goal_author = None
    keys: list[tuple[str, str]] | None = None
    if origin == "tutor" and goal is not None:
        # The tutor's goal: only the one its stored answer wrote, grounded in
        # that answer's cited passages; the press is the grant (SM9).
        if not FS.figure_offers_enabled(vault):
            raise SidecarError("offers_disabled", "Offered figures are switched off (figures.offers_enabled).")
        stored = tutor_figure_goal(repository, offer_ref)
        if anchored or stored is None or not _same_goal(stored.get("text"), goal):
            raise SidecarError("not_offered", "That figure goal was not offered by the tutor's answer.")
        goal_author = "tutor"
        keys = [(str(key[0]), str(key[1])) for key in stored.get("span_keys") or () if len(key) == 2]
    elif origin != "selection" and origin != "show_me":
        # RW5b: an offered figure is one block the judgment offered, no region, no goal.
        if not FS.figure_offers_enabled(vault):
            raise SidecarError("offers_disabled", "Offered figures are switched off (figures.offers_enabled).")
        offered = offered_spans(vault, repository, origin, offer_ref)
        wanted = {(str(extraction_id), str(span)) for span in span_ids}
        if goal is not None or region is not None or len(wanted) != 1 or not wanted <= offered:
            raise SidecarError("not_offered", "That passage was not offered as an explorable figure.")
    elif goal is not None:
        goal_author = "learner"
    # The references are validated as supplied (re-review F2): a tutor goal's
    # ``offerRef`` and a different ``hostRef.questionEventId`` are refused
    # together, never one overwritten by the other first.
    caller = _host_caller(vault, repository, origin=origin, host_ref=host_ref, offer_ref=offer_ref)
    if goal_author == "tutor":
        # Only now is the request's host the answer that offered the goal.
        host_ref = {**host_ref, "question_event_id": offer_ref}
    if caller is None:
        caller = reader_caller(vault, repository, extraction_id=home or None)
    policy, _why = derive_policy(caller)
    if policy == "cold_attempt":
        raise SidecarError("cold_check", "Figures aren't shown during a check on your own.")
    if policy != "reading":
        raise SidecarError("validation_error", "Figures on practice, feedback or lessons come in a later version.")
    try:
        request = FS.check_request(vault, repository, FS.FigureRequest(
            extraction_id=str(extraction_id or home), span_ids=list(span_ids), region=region, origin=origin,
            goal_text=goal, goal_author=goal_author, reading_at=reading_at, host_ref=host_ref, caller=caller,
            grounding_keys=keys))
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _event(repository, "figure_requested", {"extraction_id": request.extraction_id,
                                            "span_count": len(request.span_ids), "via": origin},
           extraction_id=request.extraction_id)
    if request.goal_text is not None:
        # RW5d (salience only): never the words, only that they were given and with what.
        _event(repository, "show_me_requested", {"extraction_id": request.extraction_id, "via": origin,
                                                 "anchored": FS.anchored(request),
                                                 "goal_author": request.goal_author},
               extraction_id=request.extraction_id)
    if request.region is not None:
        _event(repository, "figure_region_selected", {"extraction_id": request.extraction_id,
                                                      "span_id": request.region["span_id"]},
               extraction_id=request.extraction_id)
    return _start(ctx, request)


@method("reader.figure_request", FigureRequestInput)
def reader_figure_request(ctx: SidecarContext, params: FigureRequestInput) -> dict[str, Any]:
    """"Make this explorable": refused at once for held-out material or a
    switch that is off; otherwise a build job (read it with reader.figure_job).
    RW5d: a thin wrapper over :func:`figure_request`'s path for an anchor-only
    request (RW5a/b's callers are unchanged)."""

    region = {"span_id": params.region.span_id, "bbox": list(params.region.bbox)} if params.region else None
    return _request_figure(ctx, origin=params.origin, extraction_id=params.extraction_id,
                           span_ids=list(params.span_ids), region=region, goal_text=None, reading_at=None,
                           offer_ref=params.offer_ref, host_ref={}, cold_active=False, span_keys=params.span_keys)


class AnchorInput(ParamsModel):
    extraction_id: str
    span_ids: list[str] = Field(default_factory=list, max_length=40)
    region: RegionInput | None = None
    #: Reader follow-ups Nov 1: the passages as ``extraction:span`` keys, formed where
    #: they were taken; each must name this request's reading (None: not sent).
    span_keys: list[str] | None = Field(default=None, max_length=41)


class ReadingAtInput(ParamsModel):
    extraction_id: str
    span_id: str


class HostRefInput(ParamsModel):
    """References only, each verified on the server (spec §7.1). P1 verifies a
    tutor answer's question event; the rest are P3's and P4's and refused."""

    question_event_id: str | None = Field(default=None, max_length=200)
    item_id: str | None = Field(default=None, max_length=200)
    submission_id: str | None = Field(default=None, max_length=200)
    workbench_session_id: str | None = Field(default=None, max_length=200)
    attempt_id: str | None = Field(default=None, max_length=200)
    lesson_id: str | None = Field(default=None, max_length=200)
    node_id: str | None = Field(default=None, max_length=200)


class FigureRequestV1Input(ParamsModel):
    """``FigureRequestV1`` (spec §7.1). ``goal_author``, the policy and the
    tiers are derived on the server, never sent."""

    goal_text: str | None = Field(default=None, max_length=2000)
    anchor: AnchorInput | None = None
    origin: Literal["selection", "library", "tutor", "show_me", "ask", "teacher", "prefetch"] = "show_me"
    host_ref: HostRefInput | None = None
    reading_at: ReadingAtInput | None = None
    offer_ref: str | None = Field(default=None, max_length=200)
    #: The Reader's own cold flag (a check on your own is open): it only ever narrows.
    cold_active: bool = False


@method("figure.request", FigureRequestV1Input)
def figure_request(ctx: SidecarContext, params: FigureRequestV1Input) -> dict[str, Any]:
    """RW5d P1 "show me": one request for every host (module docstring); a build job."""

    anchor = params.anchor
    region = ({"span_id": anchor.region.span_id, "bbox": list(anchor.region.bbox)}
              if anchor is not None and anchor.region else None)
    reading_at = ({"extraction_id": params.reading_at.extraction_id, "span_id": params.reading_at.span_id}
                  if params.reading_at else None)
    host_ref = {key: value for key, value in (params.host_ref.model_dump() if params.host_ref else {}).items()
                if value}
    return _request_figure(ctx, origin=params.origin, extraction_id=anchor.extraction_id if anchor else None,
                           span_ids=list(anchor.span_ids) if anchor else [], region=region,
                           goal_text=params.goal_text, reading_at=reading_at, offer_ref=params.offer_ref,
                           host_ref=host_ref, cold_active=params.cold_active,
                           span_keys=anchor.span_keys if anchor else None)


class FigureReviseInput(ParamsModel):
    figure_id: str
    note: str = Field(default="", max_length=2000)
    #: RW5d P2b (spec §8.5): on an animation, "try a different kind of figure"
    #: (the note re-runs the tier choice instead of going to the rich author).
    different_kind: bool = False


@method("reader.figure_revise", FigureReviseInput)
def reader_figure_revise(ctx: SidecarContext, params: FigureReviseInput) -> dict[str, Any]:
    """"Not right?": a new version with the learner's note (a build job)."""

    from learnloop.db.connection import connect
    from learnloop.db.stores import figures as store

    vault, repository = _require(ctx)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        base = store.figure(connection, params.figure_id) if store.has_tables(connection) else None
    if base is None:
        raise SidecarError("not_found", "That figure is no longer kept.")
    try:
        # RW5d: a show-me figure keeps its goal, home and grounding.
        revision = FS.revision_request(repository, base, params.note)
        revision.different_kind = bool(params.different_kind)
        request = FS.check_request(vault, repository, revision)
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _event(repository, "figure_revision_requested", {"extraction_id": base["extraction_id"],
                                                     "figure_id": base["id"]}, extraction_id=base["extraction_id"])
    return _start(ctx, request)


class FigureJobInput(ParamsModel):
    job_id: str


@method("reader.figure_job", FigureJobInput)
def reader_figure_job(ctx: SidecarContext, params: FigureJobInput) -> dict[str, Any]:
    """A figure build's state, at once (never a wait on the request path)."""

    from learnloop_sidecar.handlers.library_ask import _job_payload

    _require(ctx)
    job = _jobs(ctx).get(params.job_id)
    if job is None:
        raise SidecarError("not_found", "That figure request is no longer kept; ask again.")
    return _job_payload(job)


@method("reader.figure_job_cancel", FigureJobInput)
def reader_figure_job_cancel(ctx: SidecarContext, params: FigureJobInput) -> dict[str, Any]:
    _require(ctx)
    job = _jobs(ctx).get(params.job_id)
    if job is None:
        raise SidecarError("not_found", "That figure request is no longer kept.")
    with job.lock:
        job.cancelled = True
    return versioned({"job_id": job.job_id, "kind": job.kind, "ask_id": None, "state": "cancelled", "result": None})


class FiguresInput(ParamsModel):
    extraction_id: str


@method("reader.figures", FiguresInput)
def reader_figures(ctx: SidecarContext, params: FiguresInput) -> dict[str, Any]:
    """The open source's figures as the Reader shows them (no model call).
    RW5d P2b: each quick figure carries its fuller version's state, and the
    rich builds with no quick figure are listed as pending lines; a build
    waiting for the plan is asked again (at most once per interval, never an
    offer)."""

    vault, repository = _require(ctx)
    if FS.rich_enabled(vault):
        # Codex review F8: a quick figure whose rich job's intent committed but
        # whose job never started (a stop between the two) starts it now.
        try:
            FS.resume_rich_intents(vault, repository, params.extraction_id,
                                   _rich_spawner(ctx, vault, granted=False))
        except Exception:  # noqa: BLE001 - the fuller line keeps saying it is pending; a later read retries
            pass
    figures = FS.list_figures(vault, repository, params.extraction_id)
    payload: dict[str, Any] = {"extraction_id": params.extraction_id, "figures": figures}
    if FS.rich_enabled(vault):
        pending = FS.rich_pending(vault, repository, params.extraction_id)
        payload["rich_pending"] = pending
        _retry_plan_waits(ctx, [*(line for line in pending), *((figure.get("fuller") or {}) for figure in figures)])
    return versioned(payload)


def _retry_plan_waits(ctx: SidecarContext, lines: list[dict[str, Any]]) -> None:
    from learnloop.figures import rich as RICH

    jobs = getattr(ctx, "ingest_jobs", None)
    if jobs is None or not hasattr(jobs, "retry_figure_rich"):
        return
    for line in lines:
        job_id = line.get("rich_job_id") if line.get("state") == "waiting_for_plan" else None
        if job_id and RICH.due_for_plan_retry(str(job_id)):
            try:
                jobs.retry_figure_rich(str(job_id), error_code=RICH.WAITING_FOR_PLAN)
            except Exception:  # noqa: BLE001 - the line keeps saying it waits
                pass


class RichCancelInput(ParamsModel):
    rich_job_id: str = Field(min_length=1, max_length=200)


@method("figure.rich_cancel", RichCancelInput)
def figure_rich_cancel(ctx: SidecarContext, params: RichCancelInput) -> dict[str, Any]:
    """RW5d P2b: cancel a rich build (the fuller animation, or a rich-only
    figure's pending line). Only the rich job: a quick figure stays. A paid
    call already sent finishes and keeps its receipt; nothing is stored."""

    vault, repository = _require(ctx)
    if not FS.rich_enabled(vault):
        raise SidecarError("rich_disabled", "Rich figures are switched off (figures.rich_tiers_enabled).")
    job = repository.get_ingest_job(params.rich_job_id)
    if job is None or job.get("job_type") != "figure_rich":
        raise SidecarError("not_found", "That animation build is no longer kept.")
    jobs = getattr(ctx, "ingest_jobs", None)
    if jobs is not None:
        jobs.cancel(params.rich_job_id)
    base = (job.get("payload") or {}).get("base") or {}
    _event(repository, "rich_build_cancelled", {"extraction_id": base.get("extraction_id"),
                                                "tier": (job.get("payload") or {}).get("tier")},
           extraction_id=base.get("extraction_id"))
    return versioned({"rich_job_id": params.rich_job_id, "state": "cancelled"})


class RichRetryInput(ParamsModel):
    rich_job_id: str = Field(min_length=1, max_length=200)


@method("figure.rich_retry", RichRetryInput)
def figure_rich_retry(ctx: SidecarContext, params: RichRetryInput) -> dict[str, Any]:
    """RW5d P2b (Codex review F9): try a rich build again that ended with no
    row (interrupted when LearnLoop stopped, or stopped with code's reason).
    The same job is requeued (its payload and request identity: a paid answer
    is recovered, never paid for twice); a cancelled build is not.

    Codex re-review F14: a correction of an animation whose job stored a
    failure is asked again instead: the same correction, a new generation
    (the rich author asked afresh), started here (no author call: it goes
    straight to the rich job, whose id is answered)."""

    vault, repository = _require(ctx)
    revision = FS.rich_revision_retry(vault, repository, params.rich_job_id)
    if revision is not None:
        try:
            outcome = FS.build_figure(vault, repository, revision,
                                      author_client=getattr(ctx, "figure_author_client", None),
                                      live_vault=ctx.loaded_vault, find=getattr(ctx, "figure_find_sources", None),
                                      spawn_rich=_rich_spawner(ctx, vault))
        except FS.FigureRefused as exc:
            raise _refused(exc) from exc
        started = (outcome.rich or {}).get("rich_job_id") or params.rich_job_id
        return versioned({"rich_job_id": started, "state": "pending"})
    try:
        code = FS.retry_rich_job(vault, repository, params.rich_job_id)
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    jobs = getattr(ctx, "ingest_jobs", None)
    if jobs is None or not hasattr(jobs, "retry_figure_rich") or not jobs.retry_figure_rich(
            params.rich_job_id, error_code=code):
        raise SidecarError("unavailable", "LearnLoop couldn't start that animation again just now.")
    return versioned({"rich_job_id": params.rich_job_id, "state": "pending"})


class ManimOptInInput(ParamsModel):
    choice: Literal["allow", "decline"]


@method("figure.manim_opt_in", ManimOptInInput)
def figure_manim_opt_in(ctx: SidecarContext, params: ManimOptInInput) -> dict[str, Any]:
    """RW5d P2b (spec §9b.3, Q17): the standing opt-in for Manim figures,
    asked once inline on a press: "allow" writes ``figures.manim_opt_in =
    "standing"`` with the date; "not now" writes ``"declined"`` (Manim stays
    off the menu and is not asked again; settings can change it, and
    revoke it). Linux with bwrap and Manim only."""

    from learnloop.clock import utc_now_iso
    from learnloop.ops.settings_store import SettingsStoreError, apply_config_updates

    vault, _repository = _require(ctx)
    if not FS.rich_enabled(vault):
        raise SidecarError("rich_disabled", "Rich figures are switched off (figures.rich_tiers_enabled).")
    value = "standing" if params.choice == "allow" else "declined"
    if value == "standing":
        from learnloop.figures import rich as RICH

        if not RICH.manim_runtime_state(vault)["ready"]:
            raise SidecarError("manim_unavailable", "Manim figures need Linux with bubblewrap and Manim installed.")
    try:
        apply_config_updates(vault.root / "learnloop.toml", {("figures", "manim_opt_in"): value,
                                                             ("figures", "manim_opt_in_at"): utc_now_iso(None)[:10]})
    except SettingsStoreError as exc:
        raise SidecarError(exc.code, str(exc)) from exc
    ctx.reload(maintenance=False)
    vault, _repository = _require(ctx)
    return versioned({"manim_opt_in": manim_opt_in_state(vault)})


class FigurePredictInput(ParamsModel):
    figure_id: str
    prediction_index: int = Field(ge=0, le=10)
    answer: str = Field(min_length=1, max_length=200)


@method("reader.figure_predict", FigurePredictInput)
def reader_figure_predict(ctx: SidecarContext, params: FigurePredictInput) -> dict[str, Any]:
    """The learner's prediction: stored, the observed before/after readout
    returned, matched decided by code. Formative: never graded."""

    vault, repository = _require(ctx)
    try:
        found = FS.record_prediction(vault, repository, params.figure_id, params.prediction_index, params.answer,
                                     on_queued=_wake_gap_worker(ctx))
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _event(repository, "figure_predicted", {"figure_id": params.figure_id, "extraction_id": found.get("extraction_id"),
                                            "status": "matched" if found.get("matched") else "missed"},
           extraction_id=found.get("extraction_id"))
    return versioned(found)


class FigureExplainInput(ParamsModel):
    prediction_id: str
    text: str = Field(min_length=1, max_length=2000)


@method("reader.figure_explain", FigureExplainInput)
def reader_figure_explain(ctx: SidecarContext, params: FigureExplainInput) -> dict[str, Any]:
    """"What changed, and why?" (optional, once)."""

    vault, repository = _require(ctx)
    try:
        found = FS.record_explanation(vault, repository, params.prediction_id, params.text,
                                      on_queued=_wake_gap_worker(ctx))
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _event(repository, "figure_explained", {"figure_id": found.get("figure_id"),
                                            "extraction_id": found.get("extraction_id")},
           extraction_id=found.get("extraction_id"))
    return versioned(found)


__all__ = ["FIGURE_RPCS", "deliver_figure", "prompt_contract_fields"]
