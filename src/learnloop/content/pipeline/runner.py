"""Durable ingest runner (spec_source_ingestion_v2 §6.2).

A repository-backed, leased drain that replaces the old in-memory job manager.
Work survives restarts: batches/jobs/dependencies live in SQLite, exactly one
vault-writing worker drains at a time under a lease, and explicitly compatible
DB-only work may use a bounded parallel lane. Every stage is independently
resumable along the checkpoint ladder::

    acquired -> registered -> extracted -> inventoried -> synthesized -> proposed -> applied

Design invariants (mirrors §6.2 and §14):

- Eligibility = a ``queued`` job whose dependencies are all ``completed``.
- A dependency that ends ``failed``/``blocked``/``cancelled`` makes every
  downstream job ``blocked`` (never silently ``failed``).
- ``waiting_for_input`` holds NO lease, so a question to the user cannot block the
  drain of other eligible jobs.
- Lease = ``worker_id`` + ``heartbeat_at``; on startup an expired ``running`` lease
  is recovered to ``failed(interrupted)`` and its ``queued`` siblings resume.
- Retries are keyed by the stage idempotency hash (asset hash for import,
  extraction_request_hash for extract — reusing the M1 hash model), so a retry
  reuses a completed revision/extraction instead of duplicating it.
- ``usage_json`` accumulates as a deterministic sum over attempts, so retry usage
  stays visible rather than being overwritten.

The core drain is synchronous and clock-injectable: ``drain``/``run_next`` are
callable directly in tests with a :class:`FrozenClock` and a stub
:class:`RunnerServices`; no sleeps and no threads are required to exercise the
machinery. Worker hosts (the sidecar background loop and the foreground CLI) wrap
this same object.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock, SystemClock, utc_now_iso
from learnloop.ai.transport import interrupt_callback
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid

# The checkpoint ladder (§6.2). Every phase is an independently resumable stage.
CHECKPOINT_LADDER: tuple[str, ...] = (
    "acquired",
    "registered",
    "extracted",
    "inventoried",
    "synthesized",
    "proposed",
    "applied",
)

TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})
_UNFINISHED_STATUSES = frozenset({"failed", "blocked", "cancelled"})


def effective_ingest_job_status(job: Mapping[str, Any]) -> str:
    """Correct legacy rung jobs whose result contradicted their queue status.

    Older rung-variant handlers returned ``{"status": "failed"}`` normally, so
    the generic runner persisted the outer job as completed. Preserve the raw
    record for audit while presenting and retrying it as the failure it was.
    """

    status = str(job.get("status") or "")
    result = job.get("result")
    if (
        status == "completed"
        and job.get("job_type") == "rung_variant"
        and isinstance(result, Mapping)
        and result.get("status") == "failed"
    ):
        return "failed"
    return status


# Application-validated open vocabularies (§6.2 — deliberately not SQL CHECKs).
KNOWN_WORKFLOW_TYPES = frozenset(
    {"import", "import_inventory", "legacy_ingest", "create_study_map", "update_study_map"}
)
KNOWN_JOB_TYPES = frozenset(
    {
        "import",
        "extract",
        "inventory",
        "legacy_ingest",
        "exam_ingest",
        "bootstrap_synthesis",
        "append_synthesis",
        "extraction_repair",
    }
)

# These jobs can add or replace scheduler-visible practice. Bump the durable
# high-water mark only after the ingest row itself is completed, so a Today
# poll cannot observe the revision before the sidecar is able to reload the
# newly written vault state.
_QUEUE_AFFECTING_JOB_TYPES = frozenset(
    {
        "practice_expansion",
        "rung_variant",
        "question_promotion",
        "reader_exercise_import",
        "goal_population",
    }
)


class IngestRunnerError(ValueError):
    """A typed, user-actionable job failure persisted for the Activity UI."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "invalid_job",
        details: Mapping[str, Any] | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})
        self.retryable = retryable


class JobCancelled(Exception):
    """Raised from ``report()`` when a cancellation was requested mid-stage."""


class WaitingForInput(Exception):
    """A handler pauses the job pending user input (unit choice, consent, budget).

    Carries the actionable payload the Batch-progress UI renders as a card. The
    job releases its lease so the rest of the queue keeps draining (§6.2)."""

    def __init__(self, payload: Mapping[str, Any], *, message: str = "Waiting for input") -> None:
        self.payload = dict(payload)
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class FetchedBytes:
    raw_bytes: bytes
    content_type: str | None
    original_uri: str
    retrieved_at: str
    # Human-readable metadata captured during the fetch phase, when the source
    # kind exposes it cheaply (e.g. a YouTube video's title + channel via oEmbed).
    # Absent (None/()) for sources with no knowable metadata — the import then
    # falls back to the URL title as before.
    title: str | None = None
    authors: tuple[str, ...] = ()


@dataclass
class RunnerServices:
    """The side-effecting seams the M2 handlers need. Real by default; tests
    inject deterministic stubs so no network/LLM/marker runs."""

    fetch: Callable[[str, str, "JobContext"], FetchedBytes] | None = None
    extract: Callable[[FetchedBytes, str, "JobContext"], Any] | None = None
    describe_extraction: Callable[[FetchedBytes, str, "JobContext"], Mapping[str, Any]] | None = None
    run_legacy_ingest: Callable[..., Any] | None = None
    inventory_client_factory: Callable[["JobContext"], Any] | None = None
    inventory_identity_factory: Callable[["JobContext"], tuple[str, str] | None] | None = None
    synthesis_client_factory: Callable[["JobContext"], Any] | None = None
    quick_check_client_factory: Callable[["JobContext"], Any] | None = None
    rung_variant_client_factory: Callable[["JobContext"], Any] | None = None
    promotion_analysis_client_factory: Callable[["JobContext"], Any] | None = None
    promotion_authoring_client_factory: Callable[["JobContext"], Any] | None = None
    exercise_import_client_factory: Callable[["JobContext"], Any] | None = None
    animation_client_factory: Callable[["JobContext"], Any] | None = None
    animation_renderer: Callable[..., Any] | None = None
    _inventory_identity_cache: tuple[str, str] | None = field(
        default=None, init=False, repr=False
    )

    def fetch_bytes(self, source: str, category: str, ctx: "JobContext") -> FetchedBytes:
        return (self.fetch or _job_defaults().default_fetch)(source, category, ctx)

    def extract_ir(self, fetched: FetchedBytes, category: str, ctx: "JobContext") -> Any:
        return (self.extract or _job_defaults().default_extract)(fetched, category, ctx)

    def extraction_identity(
        self, fetched: FetchedBytes, category: str, ctx: "JobContext"
    ) -> Mapping[str, Any]:
        return (self.describe_extraction or _job_defaults().default_extraction_identity)(
            fetched, category, ctx
        )

    def legacy_ingest(self, **kwargs: Any) -> Any:
        return (self.run_legacy_ingest or _job_defaults().default_run_legacy_ingest)(
            **kwargs
        )

    def inventory_identity(self, ctx: "JobContext") -> tuple[str, str] | None:
        """Return cache identity without initializing a provider when possible."""

        if self.inventory_identity_factory is not None:
            return self.inventory_identity_factory(ctx)
        if self.inventory_client_factory is None:
            return _job_defaults().default_inventory_identity(ctx)
        return self._inventory_identity_cache

    def inventory_client(
        self, ctx: "JobContext", *, bind_interruptible: bool = True
    ) -> Any:
        client = (
            self.inventory_client_factory(ctx)
            if self.inventory_client_factory is not None
            else _job_defaults().default_inventory_client(
                ctx,
                codex_timeout_seconds=_job_defaults().INGEST_CODEX_TIMEOUT_SECONDS,
            )
        )
        self._inventory_identity_cache = _job_defaults().inventory_client_identity(client)
        if bind_interruptible:
            ctx.bind_interruptible(client)
        return client

    def synthesis_client(self, ctx: "JobContext") -> Any:
        client = (
            self.synthesis_client_factory or _job_defaults().default_synthesis_client
        )(ctx)
        ctx.bind_interruptible(client)
        return client

    def quick_check_client(self, ctx: "JobContext") -> Any:
        # Reader quick checks ride the inventory resolver (low-effort on codex
        # vaults, routed elsewhere): the task method is getattr-discovered on
        # the client, exactly like unit inventory.
        return (
            self.quick_check_client_factory or _job_defaults().default_inventory_client
        )(ctx)

    def rung_variant_client(self, ctx: "JobContext") -> Any:
        client = (
            self.rung_variant_client_factory
            or _job_defaults().default_rung_variant_client
        )(ctx)
        ctx.bind_interruptible(client)
        return client

    def promotion_analysis_client(self, ctx: "JobContext") -> Any:
        client = (
            self.promotion_analysis_client_factory
            or _job_defaults().default_promotion_analysis_client
        )(ctx)
        ctx.bind_interruptible(client)
        return client

    def promotion_authoring_client(self, ctx: "JobContext") -> Any:
        client = (
            self.promotion_authoring_client_factory
            or _job_defaults().default_promotion_authoring_client
        )(ctx)
        ctx.bind_interruptible(client)
        return client

    def exercise_import_client(self, ctx: "JobContext") -> Any:
        # Reader exercise imports ride the inventory resolver (routed via
        # canonical_ingest): the task method is getattr-discovered on the
        # client, like reader quick checks.
        client = (
            self.exercise_import_client_factory
            or _job_defaults().default_inventory_client
        )(ctx)
        ctx.bind_interruptible(client)
        return client

    def animation_client(self, ctx: "JobContext") -> Any:
        return (self.animation_client_factory or _job_defaults().default_animation_client)(
            ctx
        )


def _job_defaults() -> Any:
    """Load concrete ingest jobs only when a default seam is actually used.

    ``jobs`` imports the runner contracts to host handlers and the durable worker
    facade. Keeping this dependency lazy lets queue-only callers import and test
    the runner without initializing acquisition or provider code.
    """

    from learnloop.content.pipeline import jobs

    return jobs


@dataclass
class JobContext:
    """What a handler is handed: repository, vault root, payload, and the
    checkpoint/usage/cancellation primitives the runner threads through."""

    repo: Repository
    vault_root: Path
    job: dict[str, Any]
    clock: Clock
    worker_id: str
    services: RunnerServices = field(default_factory=RunnerServices)
    _usage: dict[str, Any] = field(default_factory=dict)
    _phase: str | None = None
    _bind_interruptible: Callable[[Any], None] | None = None

    @property
    def payload(self) -> dict[str, Any]:
        return dict(self.job.get("payload") or {})

    @property
    def job_id(self) -> str:
        return self.job["id"]

    def report(
        self,
        phase: str,
        *,
        message: str | None = None,
        current_window: int | None = None,
        total_windows: int | None = None,
    ) -> None:
        """Advance the checkpoint ladder and refresh the lease heartbeat.

        Raises :class:`JobCancelled` when cancellation was requested, so long
        handlers abort cleanly at their next checkpoint (§6.2 — cancellation is
        honored between stages)."""

        if self._cancel_requested():
            raise JobCancelled()
        self._phase = phase
        self.repo.heartbeat_ingest_job(
            self.job_id,
            worker_id=self.worker_id,
            phase=phase,
            message=message or _phase_message(phase),
            current_window=current_window,
            total_windows=total_windows,
        )

    def record_usage(self, usage: Mapping[str, Any]) -> None:
        """Add one call's usage to the running per-attempt sum (§6.2)."""

        for key, value in usage.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                self._usage[key] = _as_number(self._usage.get(key, 0)) + value
            else:
                self._usage[key] = value

    def cancelled(self) -> bool:
        return self._cancel_requested()

    def bind_interruptible(self, client: Any) -> None:
        """Expose a job-scoped provider's interrupt hook to the worker host."""

        if self._bind_interruptible is not None:
            self._bind_interruptible(client)

    def _cancel_requested(self) -> bool:
        fresh = self.repo.get_ingest_job(self.job_id)
        if fresh is not None and fresh.get("cancel_requested"):
            return True
        batch = self.repo.get_ingest_batch(self.job["batch_id"])
        return bool(batch and batch.get("cancel_requested"))


Handler = Callable[[JobContext], dict[str, Any] | None]


@dataclass(frozen=True)
class JobSpec:
    """One job in an enqueued batch. ``depends_on`` is a tuple of indices into
    the batch's job list (topologically before this job)."""

    job_type: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    depends_on: tuple[int, ...] = ()


# ---------------------------------------------------------------------------
# The runner
# ---------------------------------------------------------------------------


class IngestRunner:
    def __init__(
        self,
        repo: Repository,
        *,
        vault_root: Path,
        worker_id: str,
        clock: Clock | None = None,
        handlers: Mapping[str, Handler] | None = None,
        services: RunnerServices | None = None,
        lease_ttl_seconds: int = 120,
        heartbeat_interval_seconds: float = 15,
    ) -> None:
        self.repo = repo
        self.vault_root = Path(vault_root)
        self.worker_id = worker_id
        self.clock = clock or SystemClock()
        self.handlers: dict[str, Handler] = {
            **_job_defaults().DEFAULT_HANDLERS,
            **dict(handlers or {}),
        }
        self.services = services or RunnerServices()
        self.lease_ttl_seconds = lease_ttl_seconds
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self._interrupt_lock = threading.RLock()
        self._active_interrupts: dict[str, Callable[[], Any]] = {}

    def active_interruptible_jobs(self) -> list[dict[str, Any]]:
        """Return running jobs that currently own an interruptible AI client."""

        with self._interrupt_lock:
            job_ids = list(self._active_interrupts)
        jobs: list[dict[str, Any]] = []
        for job_id in job_ids:
            job = self.repo.get_ingest_job(job_id)
            if job is not None and job.get("status") == "running":
                jobs.append(job)
        return jobs

    def interrupt_job(self, job_id: str) -> bool:
        """Cancel a batch and interrupt the selected job's active provider call."""

        with self._interrupt_lock:
            interrupt = self._active_interrupts.get(job_id)
        if interrupt is None:
            return False
        job = self.repo.get_ingest_job(job_id)
        if job is None or job.get("status") != "running":
            return False
        # Cancel queued siblings too, matching the existing batch-cancel contract
        # and preventing dependants of the interrupted job from remaining queued.
        self.cancel_batch(job["batch_id"])
        interrupt()
        return True

    def _bind_job_interruptible(self, job_id: str, client: Any) -> None:
        interrupt = interrupt_callback(client)
        if interrupt is None:
            return
        with self._interrupt_lock:
            self._active_interrupts[job_id] = interrupt

    def _clear_job_interruptible(self, job_id: str) -> None:
        with self._interrupt_lock:
            self._active_interrupts.pop(job_id, None)

    # -- enqueue -----------------------------------------------------------

    def enqueue_batch(
        self,
        workflow_type: str,
        jobs: Sequence[JobSpec],
        *,
        subject_id: str | None = None,
        source_set_id: str | None = None,
        priority: int = 0,
    ) -> str:
        if not jobs:
            raise IngestRunnerError("a batch needs at least one job.")
        for spec in jobs:
            if not spec.job_type:
                raise IngestRunnerError("every job needs a job_type.")
        batch_id = f"batch_{new_ulid()}"
        self.repo.insert_ingest_batch(
            id=batch_id,
            workflow_type=workflow_type,
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
            clock=self.clock,
        )
        job_ids: list[str] = []
        for ordinal, spec in enumerate(jobs):
            job_id = f"ijob_{new_ulid()}"
            self.repo.insert_ingest_job(
                id=job_id,
                batch_id=batch_id,
                ordinal=ordinal,
                job_type=spec.job_type,
                payload=dict(spec.payload),
                clock=self.clock,
            )
            job_ids.append(job_id)
        for ordinal, spec in enumerate(jobs):
            for dep_index in spec.depends_on:
                if dep_index < 0 or dep_index >= len(jobs) or dep_index == ordinal:
                    raise IngestRunnerError(f"invalid dependency index {dep_index}.")
                self.repo.add_ingest_job_dependency(job_ids[ordinal], job_ids[dep_index])
        self._refresh_batch(batch_id)
        return batch_id

    # -- recovery / drive --------------------------------------------------

    def recover_stale_leases(self) -> list[str]:
        """Startup recovery (§6.2): expired ``running`` leases -> ``failed(interrupted)``;
        their queued siblings simply resume. Returns the recovered job ids."""

        cutoff = self._lease_cutoff_iso()
        recovered: list[str] = []
        for job in self.repo.expired_running_ingest_jobs(cutoff):
            self.repo.finish_ingest_job(
                job["id"],
                status="failed",
                phase="failed",
                message="Interrupted before completion",
                error={"code": "interrupted", "message": "Worker lease expired before the job finished."},
                clock=self.clock,
            )
            recovered.append(job["id"])
            self._propagate_blocks(job["batch_id"])
            self._refresh_batch(job["batch_id"])
        # Startup hygiene: historical error paths left synthesis_runs rows in
        # 'created'/'running' forever. Finalize abandoned rows — but never while
        # any synthesis job still holds a live lease (its run row is legitimately
        # non-terminal mid-flight).
        live_synthesis = any(
            job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}
            and job["status"] == "running"
            and (job.get("heartbeat_at") or "") >= cutoff
            for job in self.repo.ingest_jobs_by_types(("bootstrap_synthesis", "append_synthesis"))
        )
        if not live_synthesis:
            self.repo.finalize_stale_synthesis_runs(before_iso=cutoff, clock=self.clock)
        return recovered

    def run_next(
        self,
        *,
        eligible_job_types: Sequence[str] | None = None,
        compatible_running_job_types: Sequence[str] = (),
        allow_parallel: bool = False,
        max_parallel: int | None = None,
    ) -> bool:
        """Claim and run one eligible job. Returns False when nothing was run
        (no eligible job, or another worker holds the drain lease)."""

        job = self.repo.claim_next_ingest_job(
            worker_id=self.worker_id,
            now_iso=utc_now_iso(self.clock),
            lease_cutoff_iso=self._lease_cutoff_iso(),
            eligible_job_types=eligible_job_types,
            compatible_running_job_types=compatible_running_job_types,
            allow_parallel=allow_parallel,
            max_parallel=max_parallel,
        )
        if job is None:
            return False
        self._run_claimed(job)
        return True

    def drain(
        self,
        *,
        max_jobs: int | None = None,
        eligible_job_types: Sequence[str] | None = None,
        compatible_running_job_types: Sequence[str] = (),
        allow_parallel: bool = False,
        max_parallel: int | None = None,
    ) -> int:
        """Drain matching jobs until none remain (or ``max_jobs``)."""

        ran = 0
        while max_jobs is None or ran < max_jobs:
            if not self.run_next(
                eligible_job_types=eligible_job_types,
                compatible_running_job_types=compatible_running_job_types,
                allow_parallel=allow_parallel,
                max_parallel=max_parallel,
            ):
                break
            ran += 1
        return ran

    # -- batch lifecycle ---------------------------------------------------

    def cancel_batch(self, batch_id: str) -> None:
        """Request cancellation. Completed artifacts are preserved; not-yet-run
        jobs go straight to ``cancelled`` and a running job is flagged so its
        handler stops at the next checkpoint (§6.2)."""

        self.repo.request_ingest_batch_cancel(batch_id)
        for job in self.repo.ingest_jobs_for_batch(batch_id):
            if job["status"] in {"queued", "blocked", "waiting_for_input"}:
                self.repo.finish_ingest_job(
                    job["id"],
                    status="cancelled",
                    phase="cancelled",
                    message="Batch cancelled",
                    error={"code": "cancelled", "message": "The batch was cancelled."},
                    clock=self.clock,
                )
        self._refresh_batch(batch_id)

    def resume_batch(self, batch_id: str) -> None:
        """Resume a partially-complete or cancelled batch: only unfinished jobs
        (failed/blocked/cancelled) are re-queued; completed jobs are preserved,
        so a resume creates new attempts only for what did not finish (§6.2).

        Rung-variant retries also reopen the failed domain request. Its learner
        attempt and claim remain untouched; only generation-owned state resets.
        """

        batch = self.repo.get_ingest_batch(batch_id)
        if batch is None:
            raise IngestRunnerError(f"batch '{batch_id}' does not exist.")
        self.repo.clear_ingest_batch_cancel_requested(batch_id)
        for job in self.repo.ingest_jobs_for_batch(batch_id):
            if effective_ingest_job_status(job) in _UNFINISHED_STATUSES:
                if job["job_type"] == "rung_variant":
                    request_id = str((job.get("payload") or {}).get("request_id") or "")
                    if request_id:
                        self.repo.retry_failed_rung_variant_request(
                            request_id, clock=self.clock
                        )
                elif job["job_type"] == "question_promotion":
                    event_id = str((job.get("payload") or {}).get("event_id") or "")
                    if event_id:
                        self.repo.retry_question_promotion_request(
                            event_id, clock=self.clock
                        )
                self.repo.requeue_ingest_job(job["id"], clock=self.clock)
        self._refresh_batch(batch_id)

    # -- internals ---------------------------------------------------------

    def _run_claimed(self, job: dict[str, Any]) -> None:
        batch_id = job["batch_id"]
        self.repo.update_ingest_batch_status(batch_id, "running", mark_started=True, clock=self.clock)
        ctx = JobContext(
            repo=self.repo,
            vault_root=self.vault_root,
            job=dict(job),
            clock=self.clock,
            worker_id=self.worker_id,
            services=self.services,
            _usage=dict(job.get("usage") or {}),
            _bind_interruptible=lambda client: self._bind_job_interruptible(job["id"], client),
        )
        if ctx.cancelled():
            self.repo.finish_ingest_job(
                job["id"],
                status="cancelled",
                phase="cancelled",
                message="Batch cancelled",
                error={"code": "cancelled", "message": "The batch was cancelled."},
                usage=ctx._usage or None,
                clock=self.clock,
            )
            self._refresh_batch(batch_id)
            return
        handler = self.handlers.get(job["job_type"])
        try:
            if handler is None:
                raise IngestRunnerError(f"unknown job_type '{job['job_type']}'.")
            heartbeat_stop = threading.Event()
            heartbeat_thread = threading.Thread(
                target=self._heartbeat_while_running,
                args=(job["id"], heartbeat_stop),
                name=f"ingest-heartbeat-{job['id']}",
                daemon=True,
            )
            heartbeat_thread.start()
            try:
                result = handler(ctx)
            finally:
                heartbeat_stop.set()
                heartbeat_thread.join(timeout=1)
        except JobCancelled:
            self.repo.finish_ingest_job(
                job["id"],
                status="cancelled",
                phase="cancelled",
                message="Cancelled",
                error={"code": "cancelled", "message": "The job was cancelled."},
                usage=ctx._usage or None,
                clock=self.clock,
            )
        except WaitingForInput as waiting:
            self.repo.finish_ingest_job(
                job["id"],
                status="waiting_for_input",
                phase="waiting_for_input",
                message=waiting.message,
                result={"waiting_for_input": waiting.payload},
                usage=ctx._usage or None,
                release_lease=True,
                clear_finished=True,
                clock=self.clock,
            )
        except NotImplementedError as exc:
            self.repo.finish_ingest_job(
                job["id"],
                status="failed",
                phase="failed",
                message=str(exc),
                error={"code": "not_implemented", "message": str(exc)},
                usage=ctx._usage or None,
                clock=self.clock,
            )
            self._propagate_blocks(batch_id)
        except Exception as exc:  # noqa: BLE001 — a failed job must never crash the drain
            if ctx.cancelled():
                self.repo.finish_ingest_job(
                    job["id"],
                    status="cancelled",
                    phase="cancelled",
                    message="Codex call interrupted",
                    error={"code": "cancelled", "message": "The Codex call was interrupted."},
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
            else:
                error = {"code": _error_code(exc), "message": str(exc) or exc.__class__.__name__}
                if isinstance(exc, IngestRunnerError):
                    error["details"] = exc.details
                    error["retryable"] = exc.retryable
                self.repo.finish_ingest_job(
                    job["id"],
                    status="failed",
                    phase="failed",
                    message=str(exc) or exc.__class__.__name__,
                    error=error,
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
                self._propagate_blocks(batch_id)
        else:
            if ctx.cancelled():
                self.repo.finish_ingest_job(
                    job["id"],
                    status="cancelled",
                    phase="cancelled",
                    message="Codex call interrupted",
                    error={"code": "cancelled", "message": "The Codex call was interrupted."},
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
            else:
                self.repo.finish_ingest_job(
                    job["id"],
                    status="completed",
                    phase=ctx._phase or "applied",
                    message="Completed",
                    result=result if result is not None else {},
                    usage=ctx._usage or None,
                    clock=self.clock,
                )
                if job["job_type"] in _QUEUE_AFFECTING_JOB_TYPES:
                    self.repo.bump_queue_revision(clock=self.clock)
        self._clear_job_interruptible(job["id"])
        self._refresh_batch(batch_id)

    def _heartbeat_while_running(self, job_id: str, stop: threading.Event) -> None:
        """Keep a blocking extractor/LLM stage's lease alive until it returns."""

        interval = max(0.01, self.heartbeat_interval_seconds)
        while not stop.wait(interval):
            self.repo.heartbeat_ingest_job(
                job_id,
                worker_id=self.worker_id,
                clock=self.clock,
            )

    def _propagate_blocks(self, batch_id: str) -> None:
        """Mark every downstream queued job blocked when a dependency failed,
        blocked, or was cancelled — to a fixpoint (§6.2)."""

        changed = True
        while changed:
            changed = False
            jobs = {job["id"]: job for job in self.repo.ingest_jobs_for_batch(batch_id)}
            for job in jobs.values():
                if job["status"] != "queued":
                    continue
                for dep_id in self.repo.ingest_job_dependency_ids(job["id"]):
                    dep = jobs.get(dep_id)
                    if dep is not None and dep["status"] in _UNFINISHED_STATUSES:
                        self.repo.finish_ingest_job(
                            job["id"],
                            status="blocked",
                            phase="blocked",
                            message="Blocked by a failed dependency",
                            error={
                                "code": "dependency_failed",
                                "message": f"Dependency {dep_id} did not complete.",
                            },
                            clock=self.clock,
                        )
                        changed = True
                        break

    def _refresh_batch(self, batch_id: str) -> None:
        jobs = self.repo.ingest_jobs_for_batch(batch_id)
        status = derive_batch_status(jobs, self.repo.get_ingest_batch(batch_id))
        terminal = status in {"completed", "failed", "cancelled"}
        # A resumed/retried batch must not keep reporting the prior failure's
        # finished_at while it is running again.
        self.repo.update_ingest_batch_status(
            batch_id, status, mark_finished=terminal, clear_finished=not terminal, clock=self.clock
        )

    def _lease_cutoff_iso(self) -> str:
        cutoff = self.clock.now() - timedelta(seconds=self.lease_ttl_seconds)
        return utc_now_iso(_FixedClock(cutoff))


@dataclass(frozen=True)
class _FixedClock:
    instant: Any

    def now(self):
        return self.instant


def derive_batch_status(jobs: Sequence[Mapping[str, Any]], batch: Mapping[str, Any] | None) -> str:
    """Batch status is derived from its member jobs and can represent partial
    completion (§6.2)."""

    statuses = [effective_ingest_job_status(job) for job in jobs]
    if not statuses:
        return "queued"
    if all(status == "completed" for status in statuses):
        return "completed"
    if any(status == "running" for status in statuses):
        return "running"
    if any(status == "queued" for status in statuses):
        return "queued" if all(s == "queued" for s in statuses) else "running"
    if any(status == "waiting_for_input" for status in statuses):
        return "waiting_for_input"
    # No active jobs remain: everything is terminal or blocked.
    if all(status == "cancelled" for status in statuses):
        return "cancelled"
    if batch is not None and batch.get("cancel_requested") and "cancelled" in statuses and "failed" not in statuses:
        return "cancelled"
    if any(status in {"failed", "blocked"} for status in statuses):
        return "failed"
    return "completed"


_PHASE_MESSAGES = {
    "acquired": "Fetching source material",
    "registered": "Registered source revision",
    "extracted": "Extracted document structure",
    "inventoried": "Building unit inventories",
    "synthesized": "Synthesizing the study map",
    "proposed": "Preparing the authoring proposal",
    "applied": "Applied",
}


def _phase_message(phase: str) -> str:
    return _PHASE_MESSAGES.get(phase, phase.replace("_", " ").capitalize())


def _as_number(value: Any) -> float | int:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return 0


def _error_code(exc: Exception) -> str:
    if isinstance(exc, IngestRunnerError):
        return exc.code
    if isinstance(exc, TimeoutError):
        return "timeout"
    return exc.__class__.__name__
