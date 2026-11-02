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

* RW5d P3 (spec §6.4, §11.2-§11.4, ``figures.help_kind_enabled``): figures
  inside attempts. ``figure.request`` with origin ``ask`` and an attempt
  host (``hostRef.itemId`` with ``submissionId`` and ``sessionId``: the
  practice answer box; ``workbenchSessionId``: a workbench problem;
  ``attemptId``: feedback) is the CA2 Ask panel's *show me*: built under
  ``assisted_practice`` for the item (feedback: the item's post-attempt
  policy), never from its own blocks; on an open attempt the delivered
  figure writes one ``help_assists`` figure row (one hint-equivalent at
  Submit through the hint fold, once per figure per attempt) and, on
  overlap with the key, the ``tutor_answer`` reveal with basis
  ``figure:<id>``, in one transaction with the delivery. ``figure.take_step``
  is a check on your own's take step: it converts the attempt (its row is
  the one hint-equivalent) and answers the token a cold request must carry;
  without it a request is refused under ``cold_attempt``. ``figure.open``
  opens a stored figure on an attempt host (the chooser's
  ``explore_figure`` line), recorded the same way.

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
from dataclasses import dataclass
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
    "figure.take_step",
    "figure.open",
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
    if FS.help_enabled(vault):
        # RW5d P3: present only while figures in attempts are on, so off the
        # contract is P2b's key for key.
        figures["help"] = True
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
    attempt = result.pop("_attempt", None)
    figure = result.get("figure") or {}
    # Rechecked on the stored row: every span the author was sent, the
    # paragraphs around the selection included (Codex review F1).
    if figure and FS.figure_withheld(vault, repository, str(figure.get("figure_id") or "")):
        return {"figure": None, "reused": False, "withheld": True}
    if attempt is not None and figure:
        # RW5d P3: a figure on an attempt host is recorded as it goes out (one
        # hint-equivalent per figure per attempt, and its reveal), or not shown.
        # Codex review F5: with figures in attempts switched off since the
        # build was admitted, nothing of it is delivered (record_attempt_figure
        # rechecks the switch too, for figure.open and the chooser's line).
        if not FS.help_enabled(vault):
            return {"figure": None, "reused": False, "withheld": False, "help": _help_off_line(attempt)}
        help_line = record_attempt_figure(ctx, attempt, str(figure.get("figure_id") or ""))
        if help_line.get("status") == "not_recorded":
            return {"figure": None, "reused": False, "withheld": False, "help": help_line}
        result["help"] = help_line
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


def _start(ctx: SidecarContext, request: FS.FigureRequest, *, attempt: dict[str, Any] | None = None
           ) -> dict[str, Any]:
    from learnloop_sidecar.handlers.library_ask import _job_payload

    vault, _repository = _require(ctx)
    author = getattr(ctx, "figure_author_client", None)
    # RW5d: the grounding retrieval (the sources service's, unset; a fake in tests).
    find = getattr(ctx, "figure_find_sources", None)
    # RW5d P3: an attempt host's figure is a quick one (grammar or sketch): a
    # rich build's pending line lists under a passage, and this figure has none.
    spawn = _rich_spawner(ctx, vault) if FS.rich_enabled(vault) and attempt is None else None

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
        if attempt is not None:
            # RW5d P3: the verified host, read by the delivery (never sent out).
            result["_attempt"] = dict(attempt)
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


#: The lesson references are P4's (the attempt, workbench and feedback ones are P3's: origin ``ask``).
_LATER_HOST_REFS = ("lesson_id", "node_id")


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
                    span_keys: list[str] | None = None, take_step: str | None = None) -> dict[str, Any]:
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
    if origin == "ask" or any(host_ref.get(name) for name in FS.ATTEMPT_HOST_REFS):
        # RW5d P3: the Ask panel on practice, feedback and the workbench.
        if origin != "ask" or extraction_id or span_ids or region:
            raise SidecarError("validation_error", "A figure on practice, feedback or the workbench comes from "
                                                   "the Ask panel's show me, with no passage.")
        return _request_attempt_figure(ctx, vault, repository, goal=goal, host_ref=host_ref,
                                       take_step=take_step)
    if cold_active:
        # SM4: nothing is shown or built during a check on your own (taking a
        # figure as help there is P3's take step, on the practice hosts).
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
    #: RW5d P3: the practice session the answer box's attempt is in (its
    #: hints fold by it, so its figure row carries it).
    session_id: str | None = Field(default=None, max_length=200)
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
    #: RW5d P3: the take step's token (``figure.take_step``) on a check on your own.
    take_step_token: str | None = Field(default=None, max_length=200)


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
                           span_keys=anchor.span_keys if anchor else None, take_step=params.take_step_token)


class FigureReviseInput(ParamsModel):
    figure_id: str
    note: str = Field(default="", max_length=2000)
    #: RW5d P2b (spec §8.5): on an animation, "try a different kind of figure"
    #: (the note re-runs the tier choice instead of going to the rich author).
    different_kind: bool = False
    #: RW5d P3 (Codex review F4): the attempt host the figure is open on now
    #: (the Ask panel or the chooser's line), verified here like a request's;
    #: absent: the host the figure was asked on, as it stands now.
    host_ref: HostRefInput | None = None
    take_step_token: str | None = Field(default=None, max_length=200)


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
    attempt = None
    current = {key: value for key, value in (params.host_ref.model_dump() if params.host_ref else {}).items()
               if value}
    if current and not any(current.get(name) for name in FS.ATTEMPT_HOST_REFS):
        raise SidecarError("validation_error", "A revision's host is an attempt host (practice, feedback or the "
                                               "workbench).")
    try:
        # RW5d: a show-me figure keeps its goal, home and grounding.
        revision = FS.revision_request(repository, base, params.note)
        revision.different_kind = bool(params.different_kind)
        if current or FS.attempt_hosted(revision):
            # RW5d P3: a figure open on an attempt host is revised there, under
            # the host as it stands now (submitted since: free; cold: its take
            # step), and the new version is the same figure for the count.
            # Codex review F4: the host is the one it is open on NOW when the
            # panel names it (a Reader figure opened from the chooser's line),
            # else the one it was asked on.
            from learnloop.source_retrieval.policy import derive_policy

            _help_required(vault)
            stored = current or dict(revision.host_ref or {})
            token = params.take_step_token if current else stored.get("take_step")
            host = _attempt_host(ctx, vault, repository, stored, take_step=token)
            if current and host.counts:
                _refuse_own_blocks(vault, repository, host.item_id, base)
            revision.caller = _attempt_caller(vault, repository, host)
            if derive_policy(revision.caller)[0] == "cold_attempt":
                raise SidecarError(TAKE_STEP_REQUIRED, "On a check on your own, a figure makes this practice with "
                                                       "help: take the step first.")
            revision.host_ref = host.ref()
            attempt = host.record()
        request = FS.check_request(vault, repository, revision)
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _event(repository, "figure_revision_requested", {"extraction_id": base["extraction_id"],
                                                     "figure_id": base["id"]}, extraction_id=base["extraction_id"])
    return _start(ctx, request, attempt=attempt)


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


# ---------------------------------------------------------------------------
# RW5d P3: figures inside attempts (spec §6.4, §11.2-§11.4)
# ---------------------------------------------------------------------------

#: The take step's refusals and lines (§11.3).
TAKE_STEP_REQUIRED = "take_step_required"


@dataclass(frozen=True)
class AttemptHost:
    """An attempt host's verified references (§7.1: each resolved on the
    server, never the client's word): ``practice`` (the answer box: its
    submission key and practice session), ``workbench`` (a problem bound to
    the item) or ``feedback`` (a committed attempt, or a submission that has
    since committed: free). ``cold``: a check on your own is open on the item;
    ``take_step_id``: its take step's row, which a cold request must name."""

    kind: str
    item_id: str
    submission_id: str | None = None
    session_id: str | None = None
    workbench_session_id: str | None = None
    attempt_id: str | None = None
    cold: bool = False
    take_step_id: str | None = None

    @property
    def counts(self) -> bool:
        """An open attempt: a figure here is one hint-equivalent."""

        return self.kind in ("practice", "workbench")

    def ref(self) -> dict[str, Any]:
        """The verified references as the request row keeps them."""

        return {key: value for key, value in {
            "item_id": self.item_id, "submission_id": self.submission_id, "session_id": self.session_id,
            "workbench_session_id": self.workbench_session_id, "attempt_id": self.attempt_id,
            "host": self.kind, "take_step": self.take_step_id}.items() if value}

    def record(self) -> dict[str, Any]:
        return {"kind": self.kind, "item_id": self.item_id, "submission_id": self.submission_id,
                "session_id": self.session_id, "workbench_session_id": self.workbench_session_id,
                "attempt_id": self.attempt_id, "cold": self.cold, "take_step_id": self.take_step_id}

    def cost_line(self) -> str:
        from learnloop.figures.help import COST_LINES

        if not self.counts:
            return COST_LINES["feedback"]
        return COST_LINES["cold"] if self.cold and self.take_step_id is None else COST_LINES["open"]


HELP_OFF_MESSAGE = "Figures on practice, feedback and the workbench are switched off (figures.help_kind_enabled)."


def _help_required(vault: Any) -> None:
    if not FS.help_enabled(vault):
        raise SidecarError("figures_help_disabled", HELP_OFF_MESSAGE)


def _help_off_line(attempt: dict[str, Any]) -> dict[str, Any]:
    """Codex review F5: what a delivery answers when figures in attempts were
    switched off between the request and the delivery (nothing shown, nothing
    recorded)."""

    return {"host": attempt.get("kind"), "status": "disabled", "counts_as_hint": False, "message": HELP_OFF_MESSAGE}


def attempt_aliases(repository: Any, item_id: str, submission_id: str | None,
                    workbench_session_id: str | None) -> tuple[frozenset[str], frozenset[str]]:
    """Codex review F3: every identity of the one attempt in progress
    (Reader CA2's aliases, ``reader.workbench.attempt_identities``): the answer
    box's draft keys handed into Work in Steps and the workbenches they were
    handed into, so a figure is counted once across every host of the
    attempt. A handoff that cannot be read raises (never read as none)."""

    from learnloop.reader import workbench as WB

    return WB.attempt_identities(repository, practice_item_id=item_id, submission_id=submission_id,
                                 workbench_session_id=workbench_session_id)


def _token_row_matches(row: dict[str, Any] | None, *, item_id: str, session_id: str | None, kind: str,
                       submissions: frozenset[str], workbenches: frozenset[str]) -> bool:
    """Whether a take step's row is this attempt's (Codex review F1): the
    same item, unattached, under one of the attempt's identities (its
    aliases included), and, for an answer-box row, in the same practice
    session as the request."""

    if row is None or row.get("practice_item_id") != item_id or row.get("attempt_id") is not None:
        return False
    if not (row.get("submission_id") in submissions or row.get("workbench_session_id") in workbenches):
        return False
    if kind == "practice" and row.get("practice_session_id") not in (None, session_id):
        return False
    return True


def _item_cold(vault: Any, repository: Any, item_id: str) -> bool:
    from learnloop_sidecar.handlers.tutor_qa import _item_cold as tutor_item_cold

    return bool(tutor_item_cold(vault, repository, item_id))


def take_step_available(vault: Any, repository: Any, item_id: str) -> bool:
    """Whether a check on your own on ``item_id`` takes help (the ladder's
    take step, as the hint panel's): a "Check once" served cold with the
    help header, or a due cold follow-up under Reader CA2's conversion rule
    (``ask.cold_help_converts``, mvp-0.34). Never an item reserved for a
    held-out exam, and never a measured view whose safeguards refuse help: a
    figure is then refused, as a hint is."""

    from learnloop.clock import SystemClock
    from learnloop.content.sources.exam_material import exam_reserved
    from learnloop.intent.checks import cold_followup_view, served_check

    try:
        if exam_reserved(repository, item_id):
            return False
        now = SystemClock().now()
        check = served_check(vault, repository, item_id, now=now)
        if check is not None:
            return bool(check.get("cold")) and bool(check.get("help_header"))
        view = cold_followup_view(vault, repository, item_id, now=now)
        return view is not None and bool(view.get("help_header"))
    except Exception:  # noqa: BLE001 - fail closed: no take step
        return False


def _committed(repository: Any, submission_id: str | None) -> bool:
    from learnloop.db.connection import connect
    from learnloop.db.stores import help_assists as HA

    if not submission_id:
        return False
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return HA.submission_committed(connection, submission_id)


def _attempt_host(ctx: SidecarContext, vault: Any, repository: Any, host_ref: dict[str, Any], *,
                  take_step: str | None = None, for_take_step: bool = False) -> AttemptHost:
    """Resolve an attempt host's references on the server (§7.1, §7.2)."""

    from learnloop.db.connection import connect
    from learnloop.db.stores import help_assists as HA

    item_id = str(host_ref.get("item_id") or "") or None
    attempt_id = str(host_ref.get("attempt_id") or "") or None
    workbench_session_id = str(host_ref.get("workbench_session_id") or "") or None
    submission_id = str(host_ref.get("submission_id") or "") or None
    session_id = str(host_ref.get("session_id") or "") or None
    if attempt_id is not None:
        if for_take_step:
            raise SidecarError("validation_error", "Feedback has no take step: show me is free there.")
        attempt = repository.fetch_practice_attempt(attempt_id)
        if attempt is None or (item_id is not None and str(attempt.get("practice_item_id")) != item_id):
            raise SidecarError("not_found", "That attempt is not this item's.")
        return AttemptHost(kind="feedback", item_id=str(attempt["practice_item_id"]), attempt_id=attempt_id)
    if not item_id or item_id not in vault.practice_items:
        raise SidecarError("validation_error", "A figure on practice needs its practice item.")
    kind = "practice"
    if workbench_session_id is not None:
        session_id = None
        from learnloop.reader import workbench as WB

        try:
            session = WB.session_row(repository, workbench_session_id)
        except Exception as exc:  # noqa: BLE001 - an unknown session is the caller's error
            raise SidecarError("validation_error", "That workbench session was not found.") from exc
        if session is None or session.get("practice_item_id") != item_id:
            raise SidecarError("validation_error", "That workbench session is not this item's problem.")
        kind = "workbench"
        submission_id = WB.submission_id_for(workbench_session_id)
    elif not submission_id or not session_id:
        raise SidecarError("validation_error", "A figure on the answer box needs its submission key and session.")
    if _committed(repository, submission_id):
        # Submitted since: the attempt is over, so a figure is free (feedback).
        if for_take_step:
            raise SidecarError("validation_error", "This answer was already submitted: show me is free now.")
        return AttemptHost(kind="feedback", item_id=item_id, submission_id=submission_id)
    if kind == "practice":
        # Codex review F1: the practice session is resolved on the server, as
        # a hint request's is: it exists, is open and this device owns it
        # (mobile PR-4's acceptance boundary), and the submission key is not
        # already another session's (the attach at Submit matches the key
        # alone, the fold the session too: a row under a session the attempt
        # is not in would attach uncounted).
        from learnloop_sidecar.handlers.sessions import require_owned_session

        require_owned_session(ctx, repository, str(session_id))
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            if HA.submission_session_conflict(connection, practice_item_id=item_id, submission_id=str(submission_id),
                                              session_id=str(session_id)):
                raise SidecarError("validation_error", "That submission key belongs to another practice session.")
    cold = _item_cold(vault, repository, item_id)
    token = None
    if cold and take_step:
        submissions, workbenches = attempt_aliases(repository, item_id, submission_id, workbench_session_id)
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            row = HA.take_step(connection, take_step)
        if not _token_row_matches(row, item_id=item_id, session_id=session_id, kind=kind, submissions=submissions,
                                  workbenches=workbenches):
            raise SidecarError(TAKE_STEP_REQUIRED, "That take step is not this attempt's: take it again.")
        token = str(row["id"])  # type: ignore[index]
    return AttemptHost(kind=kind, item_id=item_id, submission_id=submission_id, session_id=session_id,
                       workbench_session_id=workbench_session_id, cold=cold, take_step_id=token)


def _attempt_caller(vault: Any, repository: Any, host: AttemptHost) -> Any:
    """The caller an attempt host determines (§7.2): an open attempt
    retrieves under ``assisted_practice`` for its item (a converted check
    too: its take step made it practice with help), feedback under the
    item's post-attempt policy; caller kind ``learner`` (origin ``ask``)."""

    from dataclasses import replace

    from learnloop.instructional.policy import caller_for

    item = vault.practice_items.get(host.item_id)
    los = [item.learning_object_id] if item is not None else []
    if host.kind == "feedback":
        return caller_for(repository, "learner", item_id=host.item_id, attempt_id=host.attempt_id,
                          learning_object_ids=los, post_attempt=True, context="feedback")
    caller = caller_for(repository, "learner", item_id=host.item_id, learning_object_ids=los, context="practice")
    if host.cold and host.take_step_id is None:
        # A check on your own as the Ask panel derives it (an open cold
        # follow-up, a held-out exam, or a "Check once" served cold): the
        # request is ``cold_attempt`` until its take step converts it.
        caller = replace(caller, cold=True)
    elif host.take_step_id is not None and "exam_reserved" not in caller.notes:
        caller = replace(caller, cold=False)
    return caller


def _request_attempt_figure(ctx: SidecarContext, vault: Any, repository: Any, *, goal: str | None,
                            host_ref: dict[str, Any], take_step: str | None) -> dict[str, Any]:
    """The Ask panel's *show me* on an attempt host (§6.4): verified, the
    caller derived, a check on your own refused without its take step, then a
    build job whose delivery records the figure on the attempt."""

    from learnloop.source_retrieval.policy import derive_policy

    _help_required(vault)
    if goal is None:
        raise SidecarError("validation_error", "Say what you want to see first.")
    host = _attempt_host(ctx, vault, repository, host_ref, take_step=take_step)
    caller = _attempt_caller(vault, repository, host)
    policy, _why = derive_policy(caller)
    if policy == "cold_attempt":
        # §11.3, G-SM16: a cold policy is never bypassed by a crafted request.
        raise SidecarError(TAKE_STEP_REQUIRED, "On a check on your own, a figure makes this practice with help: "
                                               "take the step first.")
    try:
        request = FS.check_request(vault, repository, FS.FigureRequest(
            extraction_id=None, span_ids=[], origin="ask", goal_text=goal, goal_author="learner",
            host_ref=host.ref(), caller=caller))
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _event(repository, "show_me_requested", {"extraction_id": None, "via": "ask", "anchored": False,
                                             "goal_author": "learner", "host": host.kind}, extraction_id=None)
    payload = _start(ctx, request, attempt=host.record())
    # The wire's keys (``_job_payload`` already camel-cased the rest).
    payload["help"] = {"host": host.kind, "line": host.cost_line(), "countsAsHint": host.counts}
    return payload


def _figure_overlap(item: Any, row: dict[str, Any]) -> float:
    from learnloop.figures.help import reveal_text
    from learnloop.hints import service as hint_service

    text = reveal_text(row)
    return hint_service.reveal_amount(item, text) if text.strip() else 0.0


def _reveal_written(connection: Any, item_id: str, basis: str) -> bool:
    """Whether this figure's reveal was already written for the item since
    its last attempt (a delivery read again writes it once)."""

    row = connection.execute(
        "SELECT 1 FROM reveal_events WHERE practice_item_id = ? AND basis = ? AND created_at >= COALESCE("
        "(SELECT MAX(created_at) FROM practice_attempts WHERE practice_item_id = ?), '') LIMIT 1",
        (item_id, basis, item_id)).fetchone()
    return row is not None


def record_attempt_figure(ctx: SidecarContext, attempt: dict[str, Any], figure_id: str, *,
                          chooser_row: str | None = None) -> dict[str, Any]:
    """§11.2: a figure going out on an attempt host. On an open attempt, one
    ``help_assists`` figure row per figure (its versions and fuller version
    are one figure) per attempt, a take step's row naming the first, and the
    ``tutor_answer`` reveal with basis ``figure:<id>`` when its text overlaps
    the key, all in ONE transaction with the delivery: a figure is never
    shown without its count and its reveal (``not_recorded`` withholds it).
    Feedback, or an attempt submitted since: free, nothing written."""

    from learnloop.attempts.reveal_ledger import record_reveal_strict, reveal_episode_id
    from learnloop.clock import utc_now_iso
    from learnloop.db.stores import figures as figure_store
    from learnloop.db.stores import help_assists as HA
    from learnloop.figures.help import COST_LINES, FIGURE_LEVEL, chain_root
    from learnloop.ids import new_ulid
    from learnloop.vault.hashes import practice_item_hash

    vault, repository = _require(ctx)
    host = AttemptHost(**{key: attempt.get(key) for key in (
        "kind", "item_id", "submission_id", "session_id", "workbench_session_id", "attempt_id", "cold",
        "take_step_id")})
    if not FS.help_enabled(vault):
        # Codex review F5: switched off since the request (a delivery, an open,
        # a chooser line): nothing shown, nothing recorded.
        return _help_off_line(attempt)
    if not host.counts:
        return {"host": host.kind, "line": COST_LINES["feedback"], "counts_as_hint": False, "status": "free"}
    item = vault.practice_items.get(host.item_id)
    if item is None:
        return {"host": host.kind, "status": "not_recorded",
                "message": "This item changed since, so the figure isn't shown on it."}
    try:
        # Codex review F3: every host of the one attempt (the answer box's key
        # handed into Work in Steps, and back): one row per figure across them.
        submissions, workbenches = attempt_aliases(repository, item.id, host.submission_id,
                                                   host.workbench_session_id)
        # Codex review F6: a workbench figure keeps the work it was opened
        # against (step ids and content hashes, never the text), so its own
        # unaided continuation is measured as a hint's or an example's is.
        snapshot = _workbench_snapshot(repository, host.workbench_session_id) if host.kind == "workbench" else None
        with repository.atomic():
            connection = repository.connection()
            if any(HA.submission_committed(connection, key) for key in {host.submission_id, *submissions} if key):
                return {"host": "feedback", "line": COST_LINES["feedback"], "counts_as_hint": False,
                        "status": "free"}
            root = chain_root(connection, figure_id)
            mine = HA.open_figure_rows(connection, practice_item_id=host.item_id, submission_ids=submissions,
                                       workbench_session_ids=workbenches)
            assist_id = next((str(row["id"]) for row in mine if row.get("figure_id")
                              and chain_root(connection, str(row["figure_id"])) == root), None)
            new = False
            if assist_id is None and host.take_step_id and HA.bind_figure(connection, host.take_step_id, figure_id):
                assist_id = host.take_step_id
            if assist_id is None:
                now = utc_now_iso(None)
                assist_id = "ha_" + new_ulid()
                HA.insert_assist(connection, {
                    "id": assist_id, "surface": "workbench" if host.kind == "workbench" else "practice",
                    "assist_kind": "figure", "practice_item_id": item.id,
                    "practice_item_hash": practice_item_hash(item),
                    "practice_session_id": host.session_id if host.kind == "practice" else None,
                    "workbench_session_id": host.workbench_session_id, "submission_id": host.submission_id,
                    "level": FIGURE_LEVEL, "chooser": "none", "shown": 1, "counted_by": "server",
                    "requested_at": now, "shown_at": now, "figure_id": figure_id,
                    "step_snapshot_json": snapshot})
                new = True
            figure_row = figure_store.figure(connection, figure_id)
            basis = f"figure:{figure_id}"
            amount = _figure_overlap(item, figure_row or {})
            if amount > 0 and not _reveal_written(connection, item.id, basis):
                record_reveal_strict(
                    repository, practice_item_id=item.id, learning_object_id=item.learning_object_id,
                    remediation_episode_id=reveal_episode_id(repository, item.id, strict=True),
                    source_kind="tutor_answer", amount=amount, basis=basis)
    except Exception as exc:  # noqa: BLE001 - any failure: the figure is not shown
        from learnloop_sidecar.logging import log_event

        log_event("figure_help_not_recorded", practice_item_id=host.item_id, error=type(exc).__name__)
        return {"host": host.kind, "status": "not_recorded",
                "message": "The figure couldn't be recorded on this attempt just now, so it isn't shown; try again."}
    _event(repository, "attempt_figure_opened", {"extraction_id": None, "figure_id": figure_id, "host": host.kind,
                                         "prebuilt": False, "counted": new}, extraction_id=None)
    return {"host": host.kind, "line": COST_LINES["open"], "counts_as_hint": True, "status": "counted",
            "assist_id": assist_id, "new": new}


def _refuse_own_blocks(vault: Any, repository: Any, item_id: str, row: dict[str, Any]) -> None:
    """A figure placed at or built from the item's own blocks (its exercise,
    solution or worked answer) is never opened or revised on its attempt."""

    from learnloop.figures.help import figure_keys
    from learnloop.source_retrieval.corpus import item_exclusions

    own = item_exclusions(repository, vault.practice_items[item_id])
    if any(key in own.spans or key[0] in own.extractions for key in figure_keys(repository, row)):
        raise SidecarError("not_offered", "That figure was made from this item's own passages.")


def _workbench_snapshot(repository: Any, workbench_session_id: str | None) -> str | None:
    """The problem's live steps as a workbench help row keeps them (ids,
    numbers and content hashes: ``hints.report_workbench``'s work at
    delivery), or None."""

    import json

    from learnloop.workbench.ladder import live_workbench_steps

    if not workbench_session_id:
        return None
    steps = live_workbench_steps(repository, workbench_session_id)
    return json.dumps([{"chain_id": step.chain_id, "step_id": step.step_id, "number": step.number,
                        "hash": step.content_hash} for step in steps], sort_keys=True)


class TakeStepInput(ParamsModel):
    item_id: str = Field(min_length=1, max_length=200)
    submission_id: str | None = Field(default=None, max_length=200)
    session_id: str | None = Field(default=None, max_length=200)
    workbench_session_id: str | None = Field(default=None, max_length=200)


@method("figure.take_step", TakeStepInput)
def figure_take_step(ctx: SidecarContext, params: TakeStepInput) -> dict[str, Any]:
    """§11.3, G-SM16: *show me* on a check on your own. The take step
    converts the attempt first (a ``help_assists`` figure row, the one
    hint-equivalent, banner *Practice with help ◌ — you asked for a figure*)
    and answers its token; only a request carrying it is built, under
    ``assisted_practice``. Idempotent per attempt (the same token again).
    Refused where the check takes no help (an exam item, a measured check)."""

    from learnloop.clock import utc_now_iso
    from learnloop.db.stores import help_assists as HA
    from learnloop.figures.help import COST_LINES, FIGURE_LEVEL, TAKE_STEP_BANNER
    from learnloop.ids import new_ulid
    from learnloop.vault.hashes import practice_item_hash

    vault, repository = _require(ctx)
    _help_required(vault)
    host = _attempt_host(ctx, vault, repository, {
        "item_id": params.item_id, "submission_id": params.submission_id, "session_id": params.session_id,
        "workbench_session_id": params.workbench_session_id}, for_take_step=True)
    if not host.cold:
        return versioned({"needed": False, "token": None, "line": COST_LINES["open"]})
    if not take_step_available(vault, repository, host.item_id):
        raise SidecarError("cold_check", "No help is taken on this check, so a figure isn't shown here.")
    item = vault.practice_items[host.item_id]
    submissions, workbenches = attempt_aliases(repository, item.id, host.submission_id, host.workbench_session_id)
    with repository.atomic():
        connection = repository.connection()
        # One take step per attempt, across its hosts (Codex review F3).
        existing = next((row for row in HA.open_figure_rows(
            connection, practice_item_id=item.id, submission_ids=submissions, workbench_session_ids=workbenches)
            if row.get("request") == "take_step" and _token_row_matches(
                row, item_id=item.id, session_id=host.session_id, kind=host.kind, submissions=submissions,
                workbenches=workbenches)), None)
        if existing is not None:
            token = str(existing["id"])
        else:
            now = utc_now_iso(None)
            token = "ha_" + new_ulid()
            HA.insert_assist(connection, {
                "id": token, "surface": "workbench" if host.kind == "workbench" else "practice",
                "assist_kind": "figure", "practice_item_id": item.id, "practice_item_hash": practice_item_hash(item),
                "practice_session_id": host.session_id if host.kind == "practice" else None,
                "workbench_session_id": host.workbench_session_id, "submission_id": host.submission_id,
                "level": FIGURE_LEVEL, "chooser": "none", "request": "take_step", "shown": 1,
                "counted_by": "server", "requested_at": now, "shown_at": now})
    _event(repository, "figure_take_step", {"extraction_id": None, "host": host.kind}, extraction_id=None)
    return versioned({"needed": True, "token": token, "banner": TAKE_STEP_BANNER, "line": COST_LINES["open"]})


class FigureOpenInput(ParamsModel):
    figure_id: str = Field(min_length=1, max_length=200)
    host_ref: HostRefInput
    take_step_token: str | None = Field(default=None, max_length=200)


@method("figure.open", FigureOpenInput)
def figure_open(ctx: SidecarContext, params: FigureOpenInput) -> dict[str, Any]:
    """§11.4: open a stored figure on an attempt host (the chooser's
    ``explore_figure`` line lands as one line that opens it). Only a figure
    that is shown and not withheld now, never one built from the item's own
    blocks; recorded as any figure on the host (one per attempt, its reveal).
    A check on your own needs its take step, as a request does."""

    from learnloop.db.connection import connect
    from learnloop.db.stores import figures as figure_store
    from learnloop.source_retrieval.policy import derive_policy

    vault, repository = _require(ctx)
    _help_required(vault)
    host_ref = {key: value for key, value in params.host_ref.model_dump().items() if value}
    host = _attempt_host(ctx, vault, repository, host_ref, take_step=params.take_step_token)
    policy, _why = derive_policy(_attempt_caller(vault, repository, host))
    if policy == "cold_attempt":
        raise SidecarError(TAKE_STEP_REQUIRED, "On a check on your own, a figure makes this practice with help: "
                                               "take the step first.")
    try:
        row, _compiled = FS.shown_figure(vault, repository, params.figure_id)
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _refuse_own_blocks(vault, repository, host.item_id, row)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        versions = len([1 for _ in figure_store.superseding(connection, params.figure_id)]) + 1
    view = FS.figure_view(vault, repository, row, versions=versions)
    help_line = record_attempt_figure(ctx, host.record(), params.figure_id)
    if help_line.get("status") == "not_recorded":
        return versioned({"figure": None, "help": help_line})
    return versioned({"figure": view, "help": help_line})


__all__ = ["FIGURE_RPCS", "AttemptHost", "deliver_figure", "prompt_contract_fields", "record_attempt_figure",
           "take_step_available"]
