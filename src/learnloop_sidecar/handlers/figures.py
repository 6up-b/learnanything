"""Reader workbench RW5a RPCs: explorable figures (spec_reader_workbench_v1 §8; UX §4.7, W11).

* ``reader.figure_request``: "make this explorable" on a selection (an
  equation, a figure block, a short passage) or a region of a figure. Checked
  at once on the request path (the switches; exam and held-out material is
  refused before any job or model call, the one predicate); then the build
  runs off the request path as a job (RW4a's runner): reuse by input hash,
  the author (at most two attempts), verification, the verifier (at most one
  call) and the sandbox.
* ``reader.figure_revise``: "not right?" with the learner's note, a new
  version superseding the shown one (the earlier one is kept).
* ``reader.figure_job`` / ``reader.figure_job_cancel``: read a build at once
  (never a wait), or cancel it (a cancelled build never answers; a paid call
  already sent finishes and its receipt and row are kept).
* ``reader.figures``: the figures of the open source as the Reader shows them
  (a figure whose passage is held out now is left out).
* ``reader.figure_predict`` / ``reader.figure_explain``: the prediction before
  the first change and its optional "what changed?" (formative only).

Desktop only (pinned in tests/test_mobile_allowlist.py). Kill switches:
``figures.enabled`` (off: every RPC here refuses, the prompt contract has no
``figures`` key, the intent box has no "make this explorable" and no route
is called), ``figures.predictions_enabled``, ``figures.region_enabled``,
``figures.revisions_enabled``. Nothing here writes an attempt, evidence,
mastery, certification, FSRS, scheduler state or a plan.
"""
from __future__ import annotations

from contextlib import closing
from typing import Any

from pydantic import Field

from learnloop.attempts.salience_firewall import salience_payload
from learnloop.figures import service as FS
from learnloop.substrate.activities import log_interaction_event
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

#: Every RPC this module registers (pinned desktop-only).
FIGURE_RPCS: tuple[str, ...] = (
    "reader.figure_request",
    "reader.figure_revise",
    "reader.figure_job",
    "reader.figure_job_cancel",
    "reader.figures",
    "reader.figure_predict",
    "reader.figure_explain",
)


def prompt_contract_fields(vault: Any) -> dict[str, Any]:
    """What the Reader's prompt contract adds for RW5a (absent while off)."""

    if not FS.enabled(vault):
        return {}
    return {"figures": {"predictions": FS.predictions_enabled(vault), "region": FS.region_enabled(vault),
                        "revisions": FS.revisions_enabled(vault)}}


def _require(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    if not FS.enabled(vault):
        raise SidecarError("figures_disabled", "Explorable figures are switched off (figures.enabled).")
    return vault, repository


def _refused(exc: FS.FigureRefused) -> SidecarError:
    return SidecarError(exc.code, exc.message, retryable=exc.code in ("unavailable", "capped"))


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
    return result


def _wake_gap_worker(ctx: SidecarContext) -> Any:
    """A queued learner-text job wakes the post-attempt worker's ``gaps``
    slot, which starts lazily (Codex review F6)."""

    return lambda _job_id: ctx.post_attempt_worker.notify()


def _start(ctx: SidecarContext, request: FS.FigureRequest) -> dict[str, Any]:
    from learnloop_sidecar.handlers.library_ask import _job_payload

    vault, _repository = _require(ctx)
    author = getattr(ctx, "figure_author_client", None)
    verifier = getattr(ctx, "figure_verifier_client", None)
    sandbox_run = getattr(ctx, "figure_sandbox_run", None)

    def work(worker_repo: Any) -> dict[str, Any]:
        try:
            # The switch and the routes are reread from the vault loaded NOW
            # before every call (fix round 5), not the one captured here.
            outcome = FS.build_figure(vault, worker_repo, request, author_client=author, verifier_client=verifier,
                                      sandbox_run=sandbox_run, live_vault=ctx.loaded_vault)
        except FS.FigureRefused as exc:
            raise _refused(exc) from exc
        return {"figure": outcome.view, "reused": outcome.reused}

    job = _jobs(ctx).start(ctx, "figure_build", None, work, deliver=lambda result: deliver_figure(ctx, result))
    return _job_payload(job)


class RegionInput(ParamsModel):
    span_id: str
    bbox: list[float] = Field(min_length=4, max_length=4)


class FigureRequestInput(ParamsModel):
    extraction_id: str
    span_ids: list[str] = Field(default_factory=list, max_length=40)
    region: RegionInput | None = None


@method("reader.figure_request", FigureRequestInput)
def reader_figure_request(ctx: SidecarContext, params: FigureRequestInput) -> dict[str, Any]:
    """"Make this explorable": refused at once for held-out material or a
    switch that is off; otherwise a build job (read it with reader.figure_job)."""

    vault, repository = _require(ctx)
    region = {"span_id": params.region.span_id, "bbox": list(params.region.bbox)} if params.region else None
    try:
        request = FS.check_request(vault, repository, FS.FigureRequest(
            extraction_id=params.extraction_id, span_ids=list(params.span_ids), region=region, origin="selection"))
    except FS.FigureRefused as exc:
        raise _refused(exc) from exc
    _event(repository, "figure_requested", {"extraction_id": request.extraction_id,
                                            "span_count": len(request.span_ids), "via": "selection"},
           extraction_id=request.extraction_id)
    if request.region is not None:
        _event(repository, "figure_region_selected", {"extraction_id": request.extraction_id,
                                                      "span_id": request.region["span_id"]},
               extraction_id=request.extraction_id)
    return _start(ctx, request)


class FigureReviseInput(ParamsModel):
    figure_id: str
    note: str = Field(default="", max_length=2000)


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
        request = FS.check_request(vault, repository, FS.FigureRequest(
            extraction_id=base["extraction_id"], span_ids=list(base.get("span_ids") or ()), region=base.get("region"),
            origin=base["origin"], supersedes_id=base["id"], revision_note=params.note))
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
    """The open source's figures as the Reader shows them (no model call)."""

    vault, repository = _require(ctx)
    return versioned({"extraction_id": params.extraction_id,
                      "figures": FS.list_figures(vault, repository, params.extraction_id)})


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
