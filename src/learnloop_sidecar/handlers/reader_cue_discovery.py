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
  session), so only the new target's links are computed. Every request names
  the Reader's ``source_open_id`` (minted once per open of a source), and all
  the jobs of one open draw on ONE call budget,
  ``cues.max_calls_per_source_open``: re-asks, new targets, failures and
  retries included, so a new ``targets_key`` never refills it (Codex verify
  F16). Over every open, remount, reload and restart, a source's judge calls
  in any rolling 24 hours stay within ``cues.max_calls_per_source_per_day``,
  counted from the durable receipts (``PC.discovery_calls_last_24h``); a source's
  discovery jobs run one at a time, so that count is exact in this process.
* ``reader.cue_impressions``: the Reader's impressions (a mark in the
  learner's view, or not shown with its reason) and the "fewer marks like
  this" response. The server decides what it can: a held-out cue is recorded
  held out, a density cut as density, and the seed, propensity, ``p_open``
  and density come from its own computation, never the client's. Each
  batch names the cue plan it was seen on (``discovery.plan_id``, issued
  with every plan the sidecar serves) and is resolved against that plan as
  it was served, kept here unchanged, never against the plan as it is now
  (a density change before the flush, Codex verify F17); an unknown or
  expired plan id is refused and nothing is stored.
* ``reader.cue_tap`` names the plan the cue was first seen on in the visit
  (round 5, F17): an impression the tap must create takes that plan's kept
  metadata, never the current plan's; with an unknown or expired plan the
  tap is recorded and its impression part is refused.
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

import copy
import hashlib
import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
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
#: Cue plans kept for the impressions queued on them (the newest; F17).
MAX_KEPT_PLANS = 256
#: A kept plan older than this is expired: its impressions are refused.
PLAN_TTL_SECS = 12 * 60 * 60
#: Source opens whose call budget is kept (far more than one session opens).
MAX_KEPT_OPENS = 4096
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

def _cache(ctx: SidecarContext) -> dict[str, tuple[Any, dict[str, Any]]]:
    cache = getattr(ctx, "reader_cue_cache", None)
    if cache is None:
        cache = {}
        ctx.reader_cue_cache = cache  # type: ignore[attr-defined]
    return cache


@dataclass(frozen=True)
class _KeptPlan:
    """One cue plan as it was served: what its impressions are resolved by."""

    plan_id: str
    extraction_id: str
    #: The vault's database the plan was computed on (another vault's plan is unknown here).
    sqlite_path: str
    index: dict[str, tuple[str, dict[str, Any]]]
    density: str
    kept_at: float


def _plans(ctx: SidecarContext) -> "OrderedDict[str, _KeptPlan]":
    plans = getattr(ctx, "reader_cue_plans", None)
    if plans is None:
        plans = OrderedDict()
        ctx.reader_cue_plans = plans  # type: ignore[attr-defined]
    return plans


def _clock() -> float:
    return time.monotonic()


def remember(ctx: SidecarContext, extraction_id: str, cues: dict[str, Any], *, vault: Any, repository: Any) -> None:
    """The guide plan's merged cues, kept per source so a tap or an impression
    is resolved by id without rebuilding the plan (RW3a friction note 5).

    Kept with the loaded vault they were computed on: a reload or a vault
    switch publishes a new one, and its switches (``cues.try_first_enabled``
    among them) decide afresh, so cues kept from before it are never used
    (Codex re-review F15). Within one load they are reused as before.

    Each plan is also given an id (``discovery.plan_id``) and kept, unchanged
    (a deep copy), under it: the Reader's impressions name the plan they were
    seen on and are resolved against it, whatever the plan is by the time
    they are sent (Codex verify F17)."""

    from learnloop.ids import new_ulid

    plan_id = f"cplan_{new_ulid()}"
    discovery = cues.get("discovery")
    if isinstance(discovery, dict):
        discovery["plan_id"] = plan_id
    plans = _plans(ctx)
    plans[plan_id] = _KeptPlan(plan_id, extraction_id, str(repository.sqlite_path), copy.deepcopy(_index(cues)),
                               str(cues.get("density") or RCU.cue_density(vault)), _clock())
    while len(plans) > MAX_KEPT_PLANS:
        plans.popitem(last=False)
    _cache(ctx)[extraction_id] = (vault, cues)


def _kept_plan(ctx: SidecarContext, plan_id: str, *, extraction_id: str, repository: Any) -> _KeptPlan:
    """The plan an impression was seen on, or a refusal: unknown (never
    served, dropped as one of the oldest, or another vault's), expired, or
    another source's."""

    kept = _plans(ctx).get(plan_id)
    if kept is not None and _clock() - kept.kept_at > PLAN_TTL_SECS:
        _plans(ctx).pop(plan_id, None)
        kept = None
    if kept is None or kept.sqlite_path != str(repository.sqlite_path) or kept.extraction_id != extraction_id:
        raise SidecarError("cue_plan_unknown",
                           "Those margin notes are from a reading view that is no longer kept; nothing was recorded.")
    return kept


def _cues_now(ctx: SidecarContext, vault: Any, repository: Any, extraction_id: str, *,
              fresh: bool = False) -> dict[str, Any]:
    kept = None if fresh else _cache(ctx).get(extraction_id)
    if kept is not None and kept[0] is vault:
        return kept[1]
    from learnloop.reader import reader_guidance as RG

    plan = RG.build_guide_plan(vault, repository, extraction_id=extraction_id)
    cues = PC.merged_cues(vault, repository, extraction_id=extraction_id, plan=plan)
    remember(ctx, extraction_id, cues, vault=vault, repository=repository)
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
    #: The vault generation the job was started on (a reload or switch ends it).
    generation: int = 0
    done: threading.Event = field(default_factory=threading.Event)
    result: dict[str, Any] | None = None
    error: SidecarError | None = None
    cancelled: bool = False
    #: Plan-first transport T1: the OpenRouter offer the job's requests made
    #: (a ``plan_fallback`` hint), relayed by the read that finds it done.
    fallback_offer: dict[str, Any] | None = None


@dataclass
class _OpenBudget:
    """The one judge call budget of one source open (Codex verify F16).

    Every job of the open draws on ``budget``: a re-ask, a job for new
    targets, a failure and a retry alike, so a new ``targets_key`` never
    refills it. The open's jobs run one at a time (its source's lock), and
    the budget asks the running job's own ``cancelled`` before every request.
    A new open id refills only this budget, never the source's daily cap."""

    extraction_id: str
    budget: Any = None
    cancelled: Callable[[], bool] = lambda: False


class CueDiscoveryJobs:
    """Discovery jobs in flight and just finished (in memory), one per source,
    and the call budget of each source open."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._kept: dict[str, _Job] = {}
        self._opens: OrderedDict[str, _OpenBudget] = OrderedDict()
        #: One lock per (vault database, source): its jobs run one at a time,
        #: so the daily count each reads is the receipts' own (F16).
        self._sources: dict[tuple[str, str], threading.Lock] = {}

    def _source_lock(self, sqlite_path: Any, extraction_id: str) -> threading.Lock:
        with self._lock:
            return self._sources.setdefault((str(sqlite_path), extraction_id), threading.Lock())

    def _open(self, source_open_id: str, extraction_id: str, vault: Any) -> _OpenBudget:
        with self._lock:
            kept = self._opens.get(source_open_id)
            if kept is None:
                kept = _OpenBudget(extraction_id)
                kept.budget = PC.discovery_budget(vault, cancelled=lambda: kept.cancelled())
                self._opens[source_open_id] = kept
                while len(self._opens) > MAX_KEPT_OPENS:
                    self._opens.popitem(last=False)
            elif kept.extraction_id != extraction_id:
                raise SidecarError("validation_error", "That source open belongs to another source.")
            return kept

    def running(self, extraction_id: str) -> _Job | None:
        with self._lock:
            return next((job for job in self._kept.values()
                         if job.extraction_id == extraction_id and not job.done.is_set() and not job.cancelled), None)

    def start(self, ctx: SidecarContext, extraction_id: str, source_open_id: str) -> _Job:
        from learnloop.ids import new_ulid

        provider = ctx.loaded_vault
        vault, generation = provider.snapshot()
        _vault, repository = ctx.require_vault()
        if vault is None:
            vault = _vault
        opened = self._open(source_open_id, extraction_id, vault)
        running = self.running(extraction_id)
        if running is not None:
            if running.generation == generation and not running.cancelled:
                return running
            # Started on a vault since reloaded or replaced: it stops at its next check.
            running.cancelled = True
        job = _Job(f"cjob_{new_ulid()}", extraction_id, time.monotonic(), generation=generation)
        with self._lock:
            self._kept[job.job_id] = job
            while len(self._kept) > MAX_KEPT_JOBS:
                self._kept.pop(next(iter(self._kept)))
        sqlite_path = repository.sqlite_path
        source_lock = self._source_lock(sqlite_path, extraction_id)
        client = getattr(ctx, "cue_judge_client", None)
        embedder = getattr(ctx, "cue_embedder", None)

        def cancelled() -> bool:
            """Asked before each target and each request (Codex review F1):
            the job ends on a cancel, shutdown, a reload or a vault switch
            (the generation it started on is no longer the published one),
            or once discovery is switched off in the vault loaded now."""

            if job.cancelled or ctx.shutdown_requested or not provider.admit(generation):
                return True
            current = provider()
            return current is None or not PC.discovery_enabled(current)

        # T1 landing review: the learner started this job, so it carries their grant,
        # captured here in their request (a worker thread never inherits one).
        from learnloop.ai import plan_fallback as _plan_fallback

        grant = _plan_fallback.capture_grant(vault.root)

        def run() -> None:
            from learnloop.ai import plan_fallback
            from learnloop.ai.execution import record_model_calls
            from learnloop.db.repositories import Repository

            # Plan-first transport T1: the job's thread has no RPC collector;
            # it keeps its own offers and the read that finds it done relays them.
            with plan_fallback.job_grant(grant), plan_fallback.collecting() as offers:
                try:
                    worker_repo = Repository.attach(sqlite_path)
                    # One job of this source at a time, on the open's one budget
                    # and under the source's daily cap (F16).
                    with source_lock, record_model_calls(worker_repo, owner_kind="sidecar_rpc",
                                                         owner_id=f"reader.cue_discovery:{job.job_id}"):
                        opened.cancelled = cancelled
                        job.result = PC.discover(vault, worker_repo, extraction_id, client=client,
                                                 embedder=embedder, cancelled=cancelled, budget=opened.budget)
                except BaseException as exc:  # noqa: BLE001 - every failure answers the job, never the loop
                    LOG.warning("cue discovery failed: %s", type(exc).__name__, exc_info=exc)
                    job.error = SidecarError("internal_error", "LearnLoop couldn't look for margin notes just now.",
                                             retryable=True)
                finally:
                    job.fallback_offer = offers.hint()
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
    from learnloop.ai import plan_fallback

    plan_fallback.relay_job_offer(job)
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
    #: The Reader's id for this open of the source (minted once per open): its
    #: jobs share one call budget (F16).
    source_open_id: str = Field(min_length=1, max_length=80)


@method("reader.cue_discovery", CueDiscoveryInput)
def reader_cue_discovery(ctx: SidecarContext, params: CueDiscoveryInput) -> dict[str, Any]:
    """Look for the open source's missing cue links in the background, within
    the open's one call budget."""

    _vault, repository = _require(ctx)
    extraction_id = _resolve(repository, params.extraction_id)
    _cache(ctx).pop(extraction_id, None)
    return _job_payload(_jobs(ctx).start(ctx, extraction_id, params.source_open_id))


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
    #: The cue plan these impressions were seen on (``discovery.plan_id``; F17).
    plan_id: str = Field(min_length=1, max_length=80)
    entries: list[CueImpressionEntry] = Field(default_factory=list, max_length=200)


@method("reader.cue_impressions", CueImpressionsInput)
def reader_cue_impressions(ctx: SidecarContext, params: CueImpressionsInput) -> dict[str, Any]:
    """Record impressions (once per visit and cue; the first one stands),
    each resolved against the plan it was seen on: its arm, density,
    suppression, seed and propensity as that plan was served (F17)."""

    from learnloop.clock import utc_now_iso
    from learnloop.db.stores import reader_cue_links as store

    _vault, repository = _require(ctx)
    extraction_id = _resolve(repository, params.extraction_id)
    kept = _kept_plan(ctx, params.plan_id, extraction_id=extraction_id, repository=repository)
    index = kept.index
    density = kept.density
    now = utc_now_iso()
    recorded: list[dict[str, Any]] = []
    with repository.atomic():
        connection = repository.connection()
        for entry in params.entries:
            found = index.get(entry.cue_id)
            if found is None:
                raise SidecarError("validation_error", f"No margin cue {entry.cue_id!r} on that plan.")
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
            # What the server decides, it records, whatever the client says;
            # a held-out cue the Reader's own rules would not have drawn (the
            # spacing or the restored line, applied to held-out cues as to
            # drawn ones) is recorded with that reason, outside both arms
            # (Codex review F4).
            if where == "holdout":
                shown, reason = False, entry.reason if entry.reason in CLIENT_REASONS else "holdout"
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
    #: The cue plan the cue was first seen on in this visit (F17, round 5):
    #: an impression this tap creates takes that plan's kept metadata.
    plan_id: str = Field(min_length=1, max_length=80)
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
        # A drawn mark resolves through the plan's cues kept for this reading;
        # the plan is built only for a cue not among them (a "not relevant"
        # being undone), never for an ordinary tap (RW3a friction note 5).
        found_now = _index(_cues_now(ctx, vault, repository, extraction_id)).get(params.cue_id)
        cached = found_now[1] if found_now is not None and found_now[0] == "mark" else None
        if cached is not None and not PC.protection(vault, repository, extraction_id).allows(
                (extraction_id, str(cached["span_id"]))):
            cached = None  # held out since the plan was read: resolved (and refused) afresh
        if params.cue_id.startswith("dcue_"):
            cue = cached or PC.find_discovered(vault, repository, extraction_id=extraction_id, cue_id=params.cue_id,
                                               plan=RG.build_guide_plan(vault, repository, extraction_id=extraction_id))
            if params.action == "try_first" and cue.get("relation") != "try_first":
                raise SidecarError("validation_error", "Only a try-this-step-first note offers that.")
            if cue.get("relation") == "try_first" and not PC.try_first_enabled(vault):
                # The switch as loaded now decides, whatever was kept (F15).
                raise SidecarError("validation_error", "Try this step first is switched off.")
            right_kind = PC.TARGET_RIGHT_KIND
        else:
            if params.action == "try_first":
                raise SidecarError("validation_error", "Only a try-this-step-first note offers that.")
            cue = cached or RCU.find_cue(vault, repository, extraction_id=extraction_id, cue_id=params.cue_id,
                                         plan=RG.build_guide_plan(vault, repository, extraction_id=extraction_id))
            right_kind = RCU.CUE_RIGHT_KIND
        result = RCU.record_cue_tap(repository, extraction_id=extraction_id, cue=cue, action=params.action,
                                    text=params.text, actions=RCU.DISCOVERED_TAP_ACTIONS, right_kind=right_kind)
    except (RCU.CueError, PC.CueDiscoveryError) as exc:
        raise SidecarError("validation_error", str(exc)) from exc
    response_kind = {"opened": "opened", "check_me": "check_me", "try_first": "try_first",
                     "not_relevant": "not_relevant"}.get(params.action)
    impression = None
    if params.visit_id and response_kind is not None:
        # The impression part is resolved against the plan the cue was seen
        # on, never the plan as it is now (F17, round 5): a missing
        # impression is created from that plan's kept metadata, and with an
        # unknown or expired plan nothing is written here (the tap above
        # stands, with no metadata invented).
        try:
            kept = _kept_plan(ctx, params.plan_id, extraction_id=extraction_id, repository=repository)
        except SidecarError:
            kept = None
            impression = "refused: cue_plan_unknown"
        if kept is not None:
            found = kept.index.get(params.cue_id)
            now = utc_now_iso()
            with repository.atomic():
                connection = repository.connection()
                stored = store.impression_for(connection, params.visit_id, params.cue_id)
                if stored is None and found is not None and found[0] == "mark":
                    stored, _new = store.insert_impression(connection, _impression_row(
                        found[1], extraction_id=extraction_id, visit_id=params.visit_id,
                        density=kept.density, shown=True, reason=None, now=now))
                if stored is not None:
                    store.record_response(
                        connection, stored["id"], response=response_kind,
                        text_hash=_text_hash(params.text) if params.action == "not_relevant" else None, at=now)
                    impression = "recorded"
                else:
                    impression = "not_on_plan"
    response: dict[str, Any] = {**result, "check": None, "try_first": None, "impression": impression}
    if params.action == "check_me":
        response["check"] = check_me_proposal(vault, repository, extraction_id, cue)
    if params.action == "try_first":
        response["try_first"] = {"span_id": cue["span_id"]}
    if params.action in ("not_relevant", "not_relevant_undone"):
        _cache(ctx).pop(extraction_id, None)
    return versioned(response)


__all__ = ["CUE_DISCOVERY_RPCS", "remember"]
