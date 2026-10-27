"""Deliverable curriculum C0a RPCs: section coverage and its read API
(spec_deliverable_curriculum_v1 §6.4–6.5; ux_reader_compare_ask_v1 §6, §12.3).

Desktop only (pinned in tests/test_mobile_allowlist.py).

* ``reader.correspondents``: from one section, the other books' sections
  whose judged coverage names the same LOs, per LO and per book (no model
  call, no write); with none judged and ``search_fallback`` on, the live
  search hits per book labelled "found by search, not checked" (CA5a's
  pressed action reads them; the Guide's quiet line passes it off).
* ``curriculum.cover``: the learner's pressed "check where my other books
  treat this": the section's LOs are judged (one listwise call per LO, route
  ``section_coverage_judge``) in a background job. Plan-first (T1): the job
  belongs to this RPC, so a plan failure offers OpenRouter keyed by
  ``curriculum.cover`` (redesign D: the offer is the grant), relayed by the
  job's next read.
* ``curriculum.cover_job``: the job's state; the read that finds it failed
  relays its offer once.
* ``curriculum.coverage_correct``: *not about this* / *also about…* (or
  ``none``): a ``learner_card`` verdict and a ``learner`` row, nothing else.

Kill switch ``curriculum.enabled``: off, every RPC here refuses and no call
is made. Display and retrieval context only: nothing here writes a plan,
evidence, mastery, FSRS, scheduler state, provenance or anything served.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from learnloop.source_retrieval import section_coverage as SC
from learnloop.ids import new_ulid
from learnloop.reader import reader_dialogue as RD
from learnloop_sidecar.background_jobs import background_jobs
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
CORRESPONDENT_RPCS: tuple[str, ...] = (
    "reader.correspondents",
    "curriculum.cover",
    "curriculum.cover_job",
    "curriculum.coverage_correct",
)
COVER_ORIGIN = "curriculum.cover"


def _require(ctx: SidecarContext, extraction_id: str) -> tuple[Any, Any, str]:
    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop_sidecar.handlers.reader import _require_source_reader, _source_id_for_extraction

    vault, repository = ctx.require_vault()
    if not RD.reader_enabled(vault):
        raise SidecarError("reader_disabled", "The reader dialogue is disabled (tutor_qa.reader_enabled=False).")
    if not SC.enabled(vault):
        raise SidecarError("curriculum_disabled", "Section coverage is off (curriculum.enabled = false).")
    resolved = resolve_extraction_id(repository, extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {extraction_id!r}.")
    source_id = _source_id_for_extraction(repository, resolved)
    if source_id is not None:
        _require_source_reader(repository, source_id)
    return vault, repository, resolved


def _sidecar_error(exc: SC.CoverageError) -> SidecarError:
    return SidecarError(exc.code, str(exc))


# -- reader.correspondents -----------------------------------------------------------------------


class CorrespondentsInput(ParamsModel):
    extraction_id: str
    section_id: str
    #: With no judged correspondent, return the live search hits labelled
    #: unchecked (CA5a's pressed action); False reads judged coverage only
    #: (the Guide's quiet line).
    search_fallback: bool = True


@method("reader.correspondents", CorrespondentsInput)
def reader_correspondents(ctx: SidecarContext, params: CorrespondentsInput) -> dict[str, Any]:
    """The other books' sections that treat this section's LOs (no model call, no write)."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    try:
        view = SC.correspondents(vault, repository, resolved, params.section_id,
                                 search_fallback=params.search_fallback,
                                 embedder=getattr(ctx, "coverage_embedder", None))
    except SC.CoverageError as exc:
        raise _sidecar_error(exc) from exc
    view["job"] = _job_for(ctx, resolved, params.section_id)
    return versioned(view)


# -- curriculum.cover: the background judgment -----------------------------------------------------


class _Jobs:
    """One vault's coverage jobs by id, and the LOs being judged now (one
    judgment per LO and vault in this sidecar)."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.by_section: dict[tuple[str, str], str] = {}
        self.running: set[str] = set()
        #: Plan-first transport T1: the OpenRouter offer a failed job's request made.
        self.offers: dict[str, dict[str, Any]] = {}


_REGISTRY_LOCK = threading.Lock()


def _jobs(ctx: SidecarContext) -> _Jobs:
    """The open vault's jobs (Codex review F8): one registry per database, so
    after a vault switch neither a job's id, its section key nor its running
    LOs are seen from the other vault (a job of the vault left behind is
    fenced by its guard: it sends and records nothing more)."""

    repository = getattr(ctx, "repository", None)
    database = str(Path(repository.sqlite_path).resolve()) if repository is not None else ""
    with _REGISTRY_LOCK:
        registries = getattr(ctx, "coverage_jobs", None)
        if not isinstance(registries, dict):
            registries = {}
            ctx.coverage_jobs = registries  # type: ignore[attr-defined]
        return registries.setdefault(database, _Jobs())


def _public(job: dict[str, Any]) -> dict[str, Any]:
    return {key: job.get(key) for key in ("job_id", "state", "extraction_id", "section_id", "learning_object_ids",
                                          "results", "reason", "message")}


def _job_for(ctx: SidecarContext, extraction_id: str, section_id: str) -> dict[str, Any] | None:
    jobs = _jobs(ctx)
    with jobs.lock:
        job_id = jobs.by_section.get((extraction_id, section_id))
        job = jobs.jobs.get(job_id) if job_id else None
        return _public(job) if job is not None else None


def _run(ctx: SidecarContext, vault: Any, repository: Any, job_id: str, learning_object_ids: list[str]) -> None:
    jobs = _jobs(ctx)
    #: The vault loaded now, at each check (a reload's source sets count; a
    #: switch refuses the rest of the job: Codex review F1, F8).
    live_vault = ctx.loaded_vault
    root = Path(vault.root).resolve()
    client = getattr(ctx, "coverage_judge_client", None)
    embedder = getattr(ctx, "coverage_embedder", None)
    sqlite_path = repository.sqlite_path

    # T1 landing (redesign D): the job belongs to the action whose request started it
    # (curriculum.cover), and carries that action's token when it is granted.
    from learnloop.ai import plan_fallback as _plan_fallback

    grant, origin = _plan_fallback.unit_token(vault.root), _plan_fallback.unit_origin()
    stamp = _plan_fallback.unit_stamp(vault.root)
    _plan_fallback.note_unit("job", f"coverage:{job_id}")

    def run() -> None:
        from learnloop.ai import plan_fallback
        from learnloop.ai.execution import record_model_calls
        from learnloop.db.repositories import Repository

        results: list[dict[str, Any]] = []
        failure: dict[str, Any] | None = None
        with plan_fallback.unit(grant, origin, stamp) as offers:
            try:
                worker = Repository.attach(sqlite_path)
                with record_model_calls(worker, owner_kind="sidecar_rpc", owner_id=f"{COVER_ORIGIN}:{job_id}"):
                    library = SC.Library(vault, worker)
                    for lo_id in learning_object_ids:
                        current = live_vault()
                        if current is None or Path(current.root).resolve() != root:
                            failure = {"reason": "vault_switched", "message": SC.STALE_MESSAGE}
                            break
                        # Protection read again before each LO (nothing cached is reused across a change).
                        library = library.refreshed(current)
                        with jobs.lock:
                            busy = lo_id in jobs.running
                            if not busy:
                                jobs.running.add(lo_id)
                        if busy:  # another job of this sidecar is judging it: its rows will stand
                            results.append({"learning_object_id": lo_id, "status": "held"})
                            continue
                        try:
                            result = SC.judge(current, worker, lo_id, library=library, client=client,
                                              embedder=embedder, live_vault=live_vault)
                        finally:
                            with jobs.lock:
                                jobs.running.discard(lo_id)
                        results.append(result.as_dict())
                        if result.status in SC.STOPPING:
                            failure = {"reason": result.reason, "message": result.message}
                            break
            except SC.CoverageError as exc:
                # Protection could not be read before an LO (landing F1: e.g. a
                # reload whose source sets did not load): the rest is refused.
                failure = {"reason": "protection_unreadable", "message": str(exc)}
            except BaseException as exc:  # noqa: BLE001 - a failed job answers its read, never the loop
                LOG.warning("coverage job failed: %s", type(exc).__name__, exc_info=exc)
                failure = {"reason": "judge_failed",
                           "message": "Couldn't check where your books treat this just now. Try again ↵"}
        offer = offers.hint() if failure is not None else None
        with jobs.lock:
            job = jobs.jobs[job_id]
            job.update(state="failed" if failure else "done", results=results, **(failure or {}))
            if offer is not None:
                jobs.offers[job_id] = offer

    if getattr(ctx, "coverage_inline", False):
        run()
    else:
        # Owned by the context: its close cancels the job's further requests
        # and joins it, bounded (test-thread-leak review F1).
        background_jobs(ctx).spawn(run, name=f"coverage-{job_id}")


class CoverInput(ParamsModel):
    extraction_id: str
    section_id: str


@method("curriculum.cover", CoverInput)
def curriculum_cover(ctx: SidecarContext, params: CoverInput) -> dict[str, Any]:
    """The learner's pressed check: judge where the other books treat this section's LOs (in the background)."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    try:
        library = SC.Library(vault, repository)
    except SC.CoverageError as exc:
        raise _sidecar_error(exc) from exc
    reading = library.reading(resolved)
    if resolved in library.left_out or reading is None or params.section_id in reading.withheld:
        raise SidecarError("withheld", "This section is protected material: it has no correspondents.")
    if params.section_id not in reading.sections:
        raise SidecarError("validation_error", f"No section {params.section_id!r} in this reading.")
    learning_object_ids = SC.section_learning_objects(vault, repository, library, resolved, params.section_id)
    if not learning_object_ids:
        return versioned({"status": "no_learning_objects", "job": None, "learning_object_ids": [],
                          "message": "This section isn't linked to a topic of your map yet: "
                                     "\"find this section in my other books\" searches instead."})
    # Asked in the request (T1): an unavailable plan route makes this RPC's offer.
    problem = SC.admission_problem(vault, repository, client=getattr(ctx, "coverage_judge_client", None))
    if problem is not None:
        return versioned({"status": "unavailable", "job": None, "learning_object_ids": learning_object_ids,
                          "reason": problem[0], "message": problem[1]})
    jobs = _jobs(ctx)
    key = (resolved, params.section_id)
    with jobs.lock:
        current = jobs.jobs.get(jobs.by_section.get(key, ""))
        if current is not None and current.get("state") == "running":
            return versioned({"status": "running", "job": _public(current),
                              "learning_object_ids": learning_object_ids})
        job_id = "cov_" + new_ulid()
        jobs.jobs[job_id] = {"job_id": job_id, "state": "running", "extraction_id": resolved,
                             "section_id": params.section_id, "learning_object_ids": learning_object_ids,
                             "results": [], "reason": None, "message": None}
        jobs.by_section[key] = job_id
    _run(ctx, vault, repository, job_id, learning_object_ids)
    with jobs.lock:
        job = _public(jobs.jobs[job_id])
    return versioned({"status": "started", "job": job, "learning_object_ids": learning_object_ids})


class CoverJobInput(ParamsModel):
    job_id: str


@method("curriculum.cover_job", CoverJobInput)
def curriculum_cover_job(ctx: SidecarContext, params: CoverJobInput) -> dict[str, Any]:
    """A coverage job's state; the first read of a failed one relays its OpenRouter offer."""

    vault, _repository = ctx.require_vault()
    if not SC.enabled(vault):
        raise SidecarError("curriculum_disabled", "Section coverage is off (curriculum.enabled = false).")
    jobs = _jobs(ctx)
    with jobs.lock:
        job = jobs.jobs.get(params.job_id)
        if job is None:
            raise SidecarError("not_found", f"No coverage job {params.job_id!r}.")
        public = _public(job)
        offer = jobs.offers.pop(params.job_id, None) if job.get("state") == "failed" else None
    if offer is not None:
        from learnloop.ai import plan_fallback

        def restore(job_id: str = params.job_id, hint: dict[str, Any] = offer) -> None:
            with jobs.lock:
                jobs.offers.setdefault(job_id, hint)

        plan_fallback.relay_hint(offer, restore=restore)
    return versioned({"job": public})


# -- curriculum.coverage_correct -------------------------------------------------------------------


class CoverageCorrectInput(ParamsModel):
    extraction_id: str
    section_id: str
    learning_object_id: str
    #: is_about | not_about | none (clears an earlier correction)
    choice: str
    #: The learner's "also about…" words, kept as typed (bounded).
    text: str | None = None


@method("curriculum.coverage_correct", CoverageCorrectInput)
def curriculum_coverage_correct(ctx: SidecarContext, params: CoverageCorrectInput) -> dict[str, Any]:
    """*Not about this* / *also about…*: kept across re-judgments; marks nothing as known."""

    vault, repository, resolved = _require(ctx, params.extraction_id)
    try:
        row = SC.correct(vault, repository, resolved, params.section_id, params.learning_object_id, params.choice,
                         text=params.text)
    except SC.CoverageError as exc:
        raise _sidecar_error(exc) from exc
    return versioned({"correction": row})


__all__ = ["CORRESPONDENT_RPCS"]
