"""Reader workbench RW3b RPCs: discovered cues (spec_reader_workbench_v1 §6.2-6.4).

Desktop only (pinned in tests/test_mobile_allowlist.py). With
``cues.discovery_enabled`` the guide plan's ``cues`` carry the discovered
marks merged with the Guide's (``reader.guide_plan``, ``passage_cues.merged_cues``);
these RPCs add:

* ``reader.cue_discovery``: computes the open source's missing links **in the
  background** (the cue judge is Codex by default, never on the request path):
  it answers at once with a job; ``reader.cue_discovery_job`` reads it, never
  waiting. One job per source at a time. The Reader asks again when the
  plan's ``targets_key`` changes (a new or resolved hypothesis in the
  session), so only the new target's links are computed.
* ``reader.cue_impressions``: the Reader's impressions (a mark in the
  learner's view, or not shown with its reason) and the "fewer marks like
  this" response. The server decides what it can: a held-out cue is recorded
  held out, a density cut as density, and the seed, propensity, ``p_open``
  and density come from its own computation, never the client's.
* ``reader.cue_tap``: a tap on any cue while discovery is on (open, check me,
  try this step first, not relevant and its undo): one salience-only event,
  a ``learner_card`` verdict on ``passage_cue`` and the impression's first
  response. "Check me" proposes one item as RW3a's does; "try this step
  first" opens RW1b's next-step question in the Reader (a learner pick).

Display only: nothing here writes evidence, mastery, grading, scheduling or a
plan. Off (``cues.enabled`` or ``cues.discovery_enabled`` false) every RPC here
refuses with ``cues_disabled`` and the guide plan is RW3a's, byte for byte.
"""
from __future__ import annotations

import hashlib
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import Field

from learnloop.content.sources.source_outline import resolve_extraction_id
from learnloop.reader import reader_cues as RCU
from learnloop.source_retrieval import passage_cues as PC
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.registry import method

LOG = logging.getLogger(__name__)

#: Every RPC this module registers (pinned desktop-only).
CUE_DISCOVERY_RPCS: tuple[str, ...] = (
    "reader.cue_discovery",
    "reader.cue_discovery_job",
    "reader.cue_impressions",
    "reader.cue_tap",
)
MAX_KEPT_JOBS = 32
#: The suppression reasons the Reader itself decides (the restraint rules it draws by).
CLIENT_REASONS = frozenset({"spacing", "restored_line"})
MAX_NOT_RELEVANT_CHARS = RCU.MAX_NOT_RELEVANT_CHARS


def _require(ctx: SidecarContext):
    vault, repository = ctx.require_vault()
    if not PC.discovery_enabled(vault):
        raise SidecarError("cues_disabled",
                           "Discovered margin cues are switched off (cues.enabled or cues.discovery_enabled is false).")
    return vault, repository


def _resolve(repository: Any, extraction_id: str) -> str:
    resolved = resolve_extraction_id(repository, extraction_id)
    if resolved is None:
        raise SidecarError("extraction_not_found", f"No extraction resolves for {extraction_id!r}.")
    return resolved


# ---------------------------------------------------------------------------
# The plan's cues, kept for the taps and impressions of the same reading
# ---------------------------------------------------------------------------

def _cache(ctx: SidecarContext) -> dict[str, dict[str, Any]]:
    cache = getattr(ctx, "reader_cue_cache", None)
    if cache is None:
        cache = {}
        ctx.reader_cue_cache = cache  # type: ignore[attr-defined]
    return cache


def remember(ctx: SidecarContext, extraction_id: str, cues: dict[str, Any]) -> None:
    """The guide plan's merged cues, kept per source so a tap or an impression
    is resolved by id without rebuilding the plan (RW3a friction note 5)."""

    _cache(ctx)[extraction_id] = cues


def _cues_now(ctx: SidecarContext, vault: Any, repository: Any, extraction_id: str, *,
              fresh: bool = False) -> dict[str, Any]:
    cached = None if fresh else _cache(ctx).get(extraction_id)
    if cached is not None:
        return cached
    from learnloop.reader import reader_guidance as RG

    plan = RG.build_guide_plan(vault, repository, extraction_id=extraction_id)
    cues = PC.merged_cues(vault, repository, extraction_id=extraction_id, plan=plan)
    remember(ctx, extraction_id, cues)
    return cues


def _index(cues: dict[str, Any]) -> dict[str, tuple[str, dict[str, Any]]]:
    """Every cue of a payload by id: shown, held out or cut by the density budget."""

    found: dict[str, tuple[str, dict[str, Any]]] = {}
    for mark in cues.get("marks") or []:
        found[str(mark["cue_id"])] = ("mark", mark)
    discovery = cues.get("discovery") or {}
    for cue in discovery.get("held_out") or []:
        found.setdefault(str(cue["cue_id"]), ("holdout", cue))
    for cue in discovery.get("suppressed") or []:
        found.setdefault(str(cue["cue_id"]), ("density", cue))
    return found


# ---------------------------------------------------------------------------
# Background discovery (never on the request path)
# ---------------------------------------------------------------------------

@dataclass
class _Job:
    job_id: str
    extraction_id: str
    started: float
    done: threading.Event = field(default_factory=threading.Event)
    result: dict[str, Any] | None = None
    error: SidecarError | None = None


class CueDiscoveryJobs:
    """Discovery jobs in flight and just finished (in memory), one per source."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kept: dict[str, _Job] = {}

    def running(self, extraction_id: str) -> _Job | None:
        with self._lock:
            return next((job for job in self._kept.values()
                         if job.extraction_id == extraction_id and not job.done.is_set()), None)

    def start(self, ctx: SidecarContext, extraction_id: str) -> _Job:
        from learnloop.ids import new_ulid

        running = self.running(extraction_id)
        if running is not None:
            return running
        job = _Job(f"cjob_{new_ulid()}", extraction_id, time.monotonic())
        with self._lock:
            self._kept[job.job_id] = job
            while len(self._kept) > MAX_KEPT_JOBS:
                self._kept.pop(next(iter(self._kept)))
        vault, repository = ctx.require_vault()
        sqlite_path = repository.sqlite_path
        client = getattr(ctx, "cue_judge_client", None)
        embedder = getattr(ctx, "cue_embedder", None)

        def run() -> None:
            from learnloop.ai.execution import record_model_calls
            from learnloop.db.repositories import Repository

            try:
                worker_repo = Repository.attach(sqlite_path)
                with record_model_calls(worker_repo, owner_kind="sidecar_rpc",
                                        owner_id=f"reader.cue_discovery:{job.job_id}"):
                    job.result = PC.discover(vault, worker_repo, extraction_id, client=client, embedder=embedder)
            except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                LOG.warning("cue discovery failed: %s", type(exc).__name__, exc_info=exc)
                job.error = SidecarError("internal_error", "LearnLoop couldn't look for margin notes just now.",
                                         retryable=True)
            finally:
                job.done.set()

        if getattr(ctx, "cue_discovery_inline", False):
            run()
        else:
            threading.Thread(target=run, name=f"cue-discovery-{job.job_id}", daemon=True).start()
        return job

    def get(self, job_id: str) -> _Job | None:
        with self._lock:
            return self._kept.get(job_id)


def _jobs(ctx: SidecarContext) -> CueDiscoveryJobs:
    jobs = getattr(ctx, "cue_discovery_jobs", None)
    if jobs is None:
        jobs = CueDiscoveryJobs()
        ctx.cue_discovery_jobs = jobs  # type: ignore[attr-defined]
    return jobs


def _job_payload(job: _Job) -> dict[str, Any]:
    base = {"job_id": job.job_id, "extraction_id": job.extraction_id}
    if not job.done.is_set():
        return versioned({**base, "state": "pending", "result": None})
    if job.error is not None:
        raise job.error
    result = job.result or {}
    summary = {"status": result.get("status"), "targets_key": result.get("targets_key"),
               "calls": result.get("calls", 0),
               "links": sum(len(entry.get("links") or []) for entry in result.get("targets") or []),
               "targets": [{key: entry.get(key) for key in ("kind", "status", "reason")}
                           for entry in result.get("targets") or []]}
    return versioned({**base, "state": "done", "result": summary})


class CueDiscoveryInput(ParamsModel):
    extraction_id: str


@method("reader.cue_discovery", CueDiscoveryInput)
def reader_cue_discovery(ctx: SidecarContext, params: CueDiscoveryInput) -> dict[str, Any]:
    """Look for the open source's missing cue links in the background."""

    _vault, repository = _require(ctx)
    extraction_id = _resolve(repository, params.extraction_id)
    _cache(ctx).pop(extraction_id, None)
    return _job_payload(_jobs(ctx).start(ctx, extraction_id))


class CueDiscoveryJobInput(ParamsModel):
    job_id: str


@method("reader.cue_discovery_job", CueDiscoveryJobInput)
def reader_cue_discovery_job(ctx: SidecarContext, params: CueDiscoveryJobInput) -> dict[str, Any]:
    """A discovery job's state, at once (never a wait on the request path)."""

    _require(ctx)
    job = _jobs(ctx).get(params.job_id)
    if job is None:
        raise SidecarError("not_found", "That margin-note search is no longer kept.")
    if job.done.is_set():
        _cache(ctx).pop(job.extraction_id, None)
    return _job_payload(job)


# ---------------------------------------------------------------------------
# Impressions and taps
# ---------------------------------------------------------------------------

def _text_hash(text: str | None) -> str | None:
    flat = " ".join(str(text or "").split())[:MAX_NOT_RELEVANT_CHARS]
    return hashlib.sha256(flat.encode("utf-8")).hexdigest() if flat else None


def _impression_row(cue: dict[str, Any], *, extraction_id: str, visit_id: str, density: str, shown: bool,
                    reason: str | None, now: str) -> dict[str, Any]:
    from learnloop.ids import new_ulid

    discovered = bool(cue.get("link_id"))
    return {
        "id": f"cimp_{new_ulid()}", "cue_id": cue["cue_id"], "link_id": cue.get("link_id"),
        "extraction_id": extraction_id, "span_id": cue["span_id"],
        "learning_object_id": cue.get("learning_object_id") or None, "kind": cue.get("kind") or RCU.CUE_KIND_REVISIT,
        "visit_id": visit_id, "shown": shown, "suppressed_reason": None if shown else reason,
        "propensity": cue.get("propensity") if discovered else None,
        "seed": cue.get("seed") if discovered else None,
        "p_open": cue.get("p_open"), "p_open_source": cue.get("p_open_source"), "density": density,
        "created_at": now,
    }


class CueImpressionEntry(ParamsModel):
    cue_id: str
    #: Drawn and in the learner's view.
    shown: bool = False
    #: Not drawn: ``spacing`` or ``restored_line`` (the Reader's rules); the
    #: server's own reasons (holdout, density) are its to record.
    reason: str | None = None
    #: "fewer marks like this" pressed on this mark.
    response: str | None = None


class CueImpressionsInput(ParamsModel):
    extraction_id: str
    visit_id: str = Field(min_length=1, max_length=80)
    entries: list[CueImpressionEntry] = Field(default_factory=list, max_length=200)


@method("reader.cue_impressions", CueImpressionsInput)
def reader_cue_impressions(ctx: SidecarContext, params: CueImpressionsInput) -> dict[str, Any]:
    """Record impressions (once per visit and cue; the first one stands)."""

    from learnloop.clock import utc_now_iso
    from learnloop.db.stores import reader_cue_links as store

    vault, repository = _require(ctx)
    extraction_id = _resolve(repository, params.extraction_id)
    cues = _cues_now(ctx, vault, repository, extraction_id)
    index = _index(cues)
    density = str(cues.get("density") or RCU.cue_density(vault))
    now = utc_now_iso()
    recorded: list[dict[str, Any]] = []
    with repository.atomic():
        connection = repository.connection()
        for entry in params.entries:
            found = index.get(entry.cue_id)
            if found is None:
                raise SidecarError("validation_error", f"No margin cue {entry.cue_id!r} on this source now.")
            where, cue = found
            if entry.response is not None:
                if entry.response != "fewer":
                    raise SidecarError("validation_error", "Only 'fewer' is recorded here; taps go to reader.cue_tap.")
                stored = store.impression_for(connection, params.visit_id, entry.cue_id)
                if stored is None:
                    stored, _new = store.insert_impression(connection, _impression_row(
                        cue, extraction_id=extraction_id, visit_id=params.visit_id, density=density,
                        shown=where == "mark", reason={"holdout": "holdout", "density": "density"}.get(where), now=now))
                store.record_response(connection, stored["id"], response="fewer", text_hash=None, at=now)
                recorded.append({"cue_id": entry.cue_id, "response": "fewer"})
                continue
            # What the server decides, it records, whatever the client says.
            if where == "holdout":
                shown, reason = False, "holdout"
            elif where == "density":
                shown, reason = False, "density"
            elif entry.shown:
                shown, reason = True, None
            elif entry.reason in CLIENT_REASONS:
                shown, reason = False, entry.reason
            else:
                raise SidecarError("validation_error", "A mark not shown names spacing or restored_line.")
            stored, new = store.insert_impression(connection, _impression_row(
                cue, extraction_id=extraction_id, visit_id=params.visit_id, density=density, shown=shown,
                reason=reason, now=now))
            recorded.append({"cue_id": entry.cue_id, "shown": stored["shown"],
                             "suppressed_reason": stored["suppressed_reason"], "new": new})
    return versioned({"recorded": recorded})


class CueTapInput(ParamsModel):
    extraction_id: str
    cue_id: str
    action: str
    text: str | None = None
    visit_id: str | None = None


@method("reader.cue_tap", CueTapInput)
def reader_cue_tap(ctx: SidecarContext, params: CueTapInput) -> dict[str, Any]:
    """A tap on a Guide or discovered cue while discovery is on."""

    from learnloop.clock import utc_now_iso
    from learnloop.db.stores import reader_cue_links as store
    from learnloop.reader import reader_guidance as RG
    from learnloop_sidecar.handlers.reader import check_me_proposal

    vault, repository = _require(ctx)
    extraction_id = _resolve(repository, params.extraction_id)
    if params.action not in RCU.DISCOVERED_TAP_ACTIONS:
        raise SidecarError("validation_error", f"unknown cue action {params.action!r}")
    try:
        plan = RG.build_guide_plan(vault, repository, extraction_id=extraction_id)
        if params.cue_id.startswith("dcue_"):
            cue = PC.find_discovered(vault, repository, extraction_id=extraction_id, cue_id=params.cue_id, plan=plan)
            if params.action == "try_first" and cue.get("relation") != "try_first":
                raise SidecarError("validation_error", "Only a try-this-step-first note offers that.")
            right_kind = PC.TARGET_RIGHT_KIND
        else:
            if params.action == "try_first":
                raise SidecarError("validation_error", "Only a try-this-step-first note offers that.")
            cue = RCU.find_cue(vault, repository, extraction_id=extraction_id, cue_id=params.cue_id, plan=plan)
            right_kind = RCU.CUE_RIGHT_KIND
        result = RCU.record_cue_tap(repository, extraction_id=extraction_id, cue=cue, action=params.action,
                                    text=params.text, actions=RCU.DISCOVERED_TAP_ACTIONS, right_kind=right_kind)
    except (RCU.CueError, PC.CueDiscoveryError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    response_kind = {"opened": "opened", "check_me": "check_me", "try_first": "try_first",
                     "not_relevant": "not_relevant"}.get(params.action)
    if params.visit_id and response_kind is not None:
        cues = _cues_now(ctx, vault, repository, extraction_id)
        found = _index(cues).get(params.cue_id)
        now = utc_now_iso()
        with repository.atomic():
            connection = repository.connection()
            stored = store.impression_for(connection, params.visit_id, params.cue_id)
            if stored is None and found is not None and found[0] == "mark":
                stored, _new = store.insert_impression(connection, _impression_row(
                    found[1], extraction_id=extraction_id, visit_id=params.visit_id,
                    density=str(cues.get("density") or "normal"), shown=True, reason=None, now=now))
            if stored is not None:
                store.record_response(connection, stored["id"], response=response_kind,
                                      text_hash=_text_hash(params.text) if params.action == "not_relevant" else None,
                                      at=now)
    response: dict[str, Any] = {**result, "check": None, "try_first": None}
    if params.action == "check_me":
        response["check"] = check_me_proposal(vault, repository, extraction_id, cue)
    if params.action == "try_first":
        response["try_first"] = {"span_id": cue["span_id"]}
    if params.action in ("not_relevant", "not_relevant_undone"):
        _cache(ctx).pop(extraction_id, None)
    return versioned(response)


__all__ = ["CUE_DISCOVERY_RPCS", "remember"]
