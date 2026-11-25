"""Concrete ingest jobs and the durable host shared by CLI and sidecar (§6.2).

Acquisition/provider defaults and domain handlers live here, separate from the
leased queue state machine in :mod:`learnloop.content.pipeline.runner`. The
durable host (:class:`DurableIngestJobs`) exposes the sidecar-facing API
(``start``/``get``/``list``/``cancel``/``needs_reload``/``mark_reloaded``/
``shutdown``) over the durable queue (``ingest_batches``/``ingest_jobs``), so a
single-source ingest is a batch that survives restarts. A background drain
thread hosts the runner while the app is open. Opening the vault runs
``IngestRunner.recover_stale_leases``, and each drain tick expires stale leases,
so work a dead worker left ``running`` fails as interrupted and can be resumed.

Determinism: ``bind(..., background=False)`` disables the thread so tests drain
synchronously via ``drain_foreground()`` with stubbed :class:`RunnerServices`.
"""

from __future__ import annotations

import logging
import os
import threading
import weakref
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Sequence

from learnloop.db import writer_fence
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.reader import reader_quick_check as RQC
from learnloop.reader import reader_requests as RR
from learnloop.content.pipeline.runner import (
    CHECKPOINT_LADDER,
    IngestRunner,
    JobSpec,
    RunnerServices,
    derive_batch_status,
    effective_ingest_job_status,
)
from learnloop.content.authoring.jobs import AD_MODELS_OFF_CODE, _reader_source_sets, ad_commission_batch_id
from learnloop.content.pipeline.add_source import practice_expansion_payload
from learnloop.content.pipeline.job_types import applying_job_types, parallel_job_types


def _queue_due_replay(host: Any, runner: Any, newest: Mapping[str, Any] | None,
                      now: datetime | None) -> str | None:
    """Local retrieval P2 (spec §9.3; Codex review F10): the nightly teacher replay for a
    library that is fully indexed. Queries the adopted student answered wait in the vault's
    replay queue; when no index batch has run for ``REPLAY_EVERY_HOURS`` (keep) and the
    queue is due, one replay-only ``local_source_index`` batch is queued (the job takes the
    queue; ``run_local_index`` loads the 9B for it alone). Idempotent: the batch id names the
    index job it follows, and a batch that ran within the cadence (it took the queue with
    it) wakes nothing. The newest job's age is checked first, the replay file and the config
    only when it is old enough."""

    from learnloop.config.loader import load_config
    from learnloop.local_embeddings.student_pins import REPLAY_EVERY_HOURS
    from learnloop.source_retrieval.local_index import INDEX_JOB
    from learnloop.source_retrieval.student_encoder import replay_due

    moment = now or host.reading_now()
    if newest is not None:
        stamp = newest.get("finished_at") or newest.get("started_at") or newest.get("created_at")
        try:
            finished = parse_utc(str(stamp))
        except Exception:  # noqa: BLE001 - an unreadable time counts as old
            finished = None
        if finished is not None and (moment - finished).total_seconds() < REPLAY_EVERY_HOURS * 3600:
            return None
    if not replay_due(Path(runner.vault_root), now=moment):
        return None
    config = load_config(Path(runner.vault_root) / "learnloop.toml", load_environment=False)
    local = config.embedding.local
    if not (local.enabled and local.student and local.teacher_replay and config.source_retrieval.dense):
        return None
    after = newest["id"] if newest is not None else "none"
    batch = runner.enqueue_batch(INDEX_JOB, [JobSpec(INDEX_JOB, {"replay": True, "after": after})],
                                 batch_id=f"{INDEX_JOB}_replay_after_{after}")
    host._ensure_worker()
    return batch


_LEGACY_JOB_TYPES = ("legacy_ingest", "exam_ingest")
_ACTIVE_STATUSES = {"queued", "running", "waiting_for_input"}
_RECENT_LIMIT = 30

# Quick-add build batches drain ahead of bulk import/inventory batches (§1). The
# drain orders by batch priority DESC first, so anything above the default 0
# jumps the queue between checkpoints. Bulk batches stay at 0.
QUICK_ADD_PRIORITY = 100
_QUICK_CHECK_WORKERS = 3


@dataclass
class ReadingSweep:
    """What one pass of the reading sweep did (reading-hardening, part 1)."""

    settled: int = 0
    #: Due, but waiting behind the book's own work: acted on once it ends.
    deferred: int = 0
    #: Acting failed (recorded with its backoff by the act, when it could be).
    failed: int = 0
    #: The earliest retry time still to come, if any.
    next_due_at: datetime | None = None


def _run_reading_sweep(host: "weakref.ref[DurableIngestJobs]") -> None:
    """The reading sweep thread. It holds its host only while it works, so a
    host nobody uses any more (a library closed, a test's sidecar) lets the
    thread end at its next wake instead of sweeping for the process's life."""

    failures = 0
    delay: float | None = None
    while True:
        jobs = host()
        if jobs is None:
            return
        wake = jobs._reading_sweep_wake
        if delay is None:
            delay = float(jobs.READING_SWEEP_SECONDS)
        del jobs
        wake.wait(timeout=delay)
        wake.clear()
        jobs = host()
        if jobs is None:
            return
        step = jobs._reading_sweep_pass(failures)
        del jobs
        if step is None:
            return
        failures, delay = step


def _reading_due_at(retry_at: str | None) -> datetime | None:
    """When a pending reading request is due: its retry time, or ``None``
    (due now) when it has none or one that does not parse or convert to UTC
    (``0001-01-01T00:00:00+01:00`` overflows, reading-hardening verify N2),
    so no stored value can keep a request from ever being due."""

    if not retry_at:
        return None
    try:
        return parse_utc(str(retry_at))
    except (TypeError, ValueError, OverflowError):
        return None


class ActiveIngestJobError(RuntimeError):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Ingest job {job_id} is already running.")


class DurableIngestJobs:
    """Enqueues single-source ingests into the durable queue and reads their state."""

    def __init__(self) -> None:
        self._runner: IngestRunner | None = None
        #: Runners a same-vault rebind under another writer-fence binding replaced (R4-F2), kept while a claim of
        #: theirs runs: its interrupt handle stays reachable (``interrupt_codex``) and a halt reaches it.
        self._retired_runners: list[IngestRunner] = []
        self._lock = threading.RLock()
        self._reloaded: set[str] = set()
        self._reload_observed: dict[str, set[str]] = {}
        self._background = True
        self._poll_interval = 1.0
        self._worker_thread: threading.Thread | None = None
        self._quick_check_threads: list[threading.Thread] = []
        self._stop = threading.Event()
        #: Set by :meth:`halt` until the next :meth:`bind`.
        self._halted = False
        self._work_available = threading.Event()
        self._quick_check_work_available = threading.Event()
        # Demand-paged reader synthesis: the same worker thread drains queued
        # reader_background_requests with a real model client (spec §6.4);
        # nothing else drains them, so without it they would stay queued.
        self._reader_synth_client_factory: Any = None
        self._reader_client: Any = None
        self._reader_client_checked = False
        # UX Phase 1 (finishing pass, F8/F9): acting on a book's durable
        # reading request ("keep one chapter ahead") is serialised: the
        # Reader's RPC, the reading sweep, the start and a cancel. The request
        # itself lives in ``source_auto_build_state``, never in memory.
        self._reading_lock = threading.RLock()
        # The reading sweep (reading-hardening, part 1): while the sidecar runs
        # it acts on every due request whose book's work is done, so no
        # request waits on a wake-up. A wake only brings a pass forward.
        self._reading_sweep_thread: threading.Thread | None = None
        self._reading_sweep_wake = threading.Event()
        # Set on the thread running a sweep pass: what fails inside a pass
        # never wakes that same sweep (Codex review F2). The pass's outcome
        # alone sets its next wait, so a failure's backoff cannot collapse.
        self._in_sweep_pass = threading.local()
        #: The clock the reading sweep and a failed request's backoff read
        #: (``None``: the wall clock; tests script it).
        self.reading_clock: Clock | None = None

    #: Seconds between the reading sweep's passes while the sidecar runs (one
    #: query over the books' requests when nothing is due).
    READING_SWEEP_SECONDS: float = 30.0
    #: Seconds before the sweep tries again after a pass that failed (its scan,
    #: or acting on a request whose failure could not even be recorded),
    #: doubling up to :attr:`READING_SWEEP_SECONDS`. A failed pass never
    #: counts as "nothing due".
    READING_SWEEP_RETRY_SECONDS: float = 1.0
    #: Seconds before acting again on a request whose last attempt failed, by
    #: failed attempt. The last delay repeats: a request is never given up
    #: (the Reader's next report and the next start also ask at once).
    READING_RETRY_DELAYS: tuple[float, ...] = (2.0, 10.0, 30.0, 120.0, 300.0)

    @property
    def reading_lock(self) -> threading.RLock:
        return self._reading_lock

    # -- wiring ------------------------------------------------------------

    def bind(
        self,
        repository: Repository,
        vault_root: Path,
        *,
        clock: Clock | None = None,
        services: RunnerServices | None = None,
        lease_ttl_seconds: int = 120,
        heartbeat_interval_seconds: float = 15,
        poll_interval_seconds: float = 1.0,
        background: bool | None = None,
        reader_synth_client_factory: Any = None,
        sweep_abandoned_synthesis: bool = True,
    ) -> None:
        """Attach the wrapper to a loaded vault. Called from SidecarContext.load.

        ``sweep_abandoned_synthesis`` (mobile PR-3, ``spec_mobile_tailnet_v1``
        §3.3): only a primary host finalizes leaseless synthesis runs older
        than the lease cutoff when it first binds. A secondary host (the
        mobile host's restricted runner, M3) binds with False: it fences
        expired leases and leaves a synchronous run the primary may still be
        executing alone. The default keeps the primary's behaviour.
        """

        previous: IngestRunner | None = None
        retired: IngestRunner | None = None
        with self._lock:
            if self._halted:
                # The vault is served again (``halt``): this host's loops may run once more.
                self._halted = False
                self._stop.clear()
            self._reader_synth_client_factory = reader_synth_client_factory
            self._reader_client = None
            self._reader_client_checked = False
            same_vault = self._runner is not None and self._runner.vault_root.resolve() == Path(
                vault_root
            ).resolve()
            self._retired_runners = [old for old in self._retired_runners if old.busy]
            if same_vault and self._runner is not None and self._runner.repo.writer_tags != repository.writer_tags:
                # The writer fence (R4-F2): the reload follows an upgrade, so the kept runner's repository writes
                # under the predecessor's tag and every new claim would be refused until a restart. New claims go to
                # a runner bound to the successor's repository; the old one finishes only the claim it holds, with
                # its interrupt handle (kept reachable through ``_retired_runners``).
                retired = self._runner
                runner = IngestRunner(
                    repository,
                    vault_root=retired.vault_root,
                    worker_id=retired.worker_id,
                    clock=clock if clock is not None else retired.clock,
                    handlers=retired.handlers,
                    services=services if services is not None else retired.services,
                    lease_ttl_seconds=lease_ttl_seconds,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )
                self._runner = runner
                self._retired_runners.append(retired)
            elif same_vault:
                # SidecarContext.reload() refreshes the loaded vault after an
                # applying job completes. The drain thread may already be inside
                # the next Codex call, so replacing its runner here would orphan
                # that call's in-memory interrupt handle from `kill-codex`.
                # The existing Repository remains valid for the same SQLite file.
                runner = self._runner
                assert runner is not None
                if clock is not None:
                    runner.clock = clock
                if services is not None:
                    runner.services = services
                runner.lease_ttl_seconds = lease_ttl_seconds
                runner.heartbeat_interval_seconds = heartbeat_interval_seconds
            else:
                runner = IngestRunner(
                    repository,
                    vault_root=vault_root,
                    worker_id=f"sidecar-{os.getpid()}",
                    clock=clock,
                    services=services,
                    lease_ttl_seconds=lease_ttl_seconds,
                    heartbeat_interval_seconds=heartbeat_interval_seconds,
                )
                previous, self._runner = self._runner, runner
            # A same-vault SidecarContext.reload() must not silently replace an
            # explicitly foreground-bound test/CLI host with a background
            # thread. Omitted means "preserve" on rebind and "background" on
            # first bind.
            if not same_vault or background is not None:
                self._background = True if background is None else background
            self._poll_interval = poll_interval_seconds
        if retired is not None:
            retired.retire()
        if previous is not None:
            # A vault switch. The running loops move to the new runner at their next turn, and the previous vault's
            # runner stops as at a refusal: it claims nothing more and fences its job in flight (whose lease then
            # expires and is requeued when that vault is opened again). Not joined: this is the request thread.
            previous.halt()
        if self._background:
            # The reading sweep runs for as long as this host does.
            self._ensure_reading_sweep()
        else:
            # A foreground host (tests, the CLI) runs no sweep: one already
            # running notices at once and steps aside.
            self._reading_sweep_wake.set()
        # Recover anything a prior process left mid-flight before draining.
        if not same_vault:
            runner.recover_stale_leases(sweep_abandoned_synthesis=sweep_abandoned_synthesis)
        # Jobs that finished before this bind are already reflected in the vault
        # load that accompanies it; only jobs completing AFTER this point should
        # trigger a reload from the batch-polling handlers.
        for job in runner.repo.ingest_jobs_by_types(applying_job_types()):
            if job["status"] == "completed":
                self._reloaded.add(job["id"])

    def _require_runner(self) -> IngestRunner:
        if self._runner is None:
            raise RuntimeError("Ingest jobs are not bound to a vault yet.")
        return self._runner

    @property
    def repository(self) -> Repository:
        return self._require_runner().repo

    @property
    def vault_root(self) -> Path:
        return self._require_runner().vault_root

    # -- UX Phase 1: one Add, automatic builds ---------------------------------

    def enqueue_add_source(
        self,
        source: str,
        *,
        source_id: str | None = None,
        options: Any = None,
        auto_build: bool = True,
    ) -> str:
        """Enqueue an Add: the import, then the automatic build planner that
        depends on it (``learnloop.content.pipeline.add_source``). The import
        drains ahead of question builds: the learner is waiting to read."""

        from learnloop.content.pipeline.add_source import (
            ADD_SOURCE_PRIORITY,
            ADD_SOURCE_WORKFLOW,
            AUTO_STUDY_MAP_JOB,
            AddSourceOptions,
        )

        chosen = options or AddSourceOptions()
        runner = self._require_runner()
        # An Add asked the learner nothing per book: an upload of the whole
        # file waits for its own OK (UX Phase 1 review F1; enforced where the
        # bytes would leave).
        import_payload: dict[str, Any] = {"source": source, "require_upload_ok": True}
        if source_id:
            import_payload["source_id"] = source_id
        if chosen.page_selection:
            import_payload["page_selection"] = list(chosen.page_selection)
        if chosen.problem_set:
            import_payload["reader_enabled"] = False
        if chosen.text_recognition:
            # An extractor that really recognises text, named explicitly
            # (review F9): a configured pypdf engine would ignore force_ocr.
            # GLM-OCR when it can run (hosted needs only a key), else Marker.
            # Add and the card check that one is available before asking.
            from learnloop.config.loader import load_config
            from learnloop.ingest.extractors.glm_ocr import selected_backend

            glm_settings = load_config(Path(runner.vault_root) / "learnloop.toml").ingest.pdf.glm_ocr.model_dump()
            glm = selected_backend(glm_settings) is not None
            import_payload["pdf_config"] = {"engine": "glm_ocr"} if glm else {"engine": "marker", "force_ocr": True}
        specs = [JobSpec("import", import_payload)]
        if auto_build:
            auto_payload: dict[str, Any] = {
                "source": source,
                "problem_set": bool(chosen.problem_set),
            }
            if source_id:
                auto_payload["source_id"] = source_id
            specs.append(JobSpec(AUTO_STUDY_MAP_JOB, auto_payload, depends_on=(0,)))
        batch_id = runner.enqueue_batch(ADD_SOURCE_WORKFLOW, specs, priority=ADD_SOURCE_PRIORITY)
        self._ensure_worker()
        return batch_id

    def enqueue_auto_build(
        self,
        source_id: str,
        *,
        approved: bool = False,
        chapter_ids: Sequence[str] | None = None,
        start_unit_id: str | None = None,
        answers_revision: int | None = None,
    ) -> str | None:
        """Plan another automatic build for an already-readable source.

        ``answers_revision``: the book's reading request this build answers
        (keep one chapter ahead). The request is settled at exactly that
        revision in the enqueue's own transaction, and if it is no longer
        pending there (a cancel settled it first, or a newer request replaced
        it) nothing is queued and ``None`` is returned (reading-hardening
        verify, F1). The worker is started only after the commit."""

        from learnloop.content.pipeline.add_source import (
            AUTO_BUILD_WORKFLOW,
            AUTO_STUDY_MAP_JOB,
            BUILD_PRIORITY,
        )

        runner = self._require_runner()
        payload: dict[str, Any] = {"source_id": source_id}
        if approved:
            payload["approved"] = True
        if chapter_ids:
            payload["chapter_ids"] = list(chapter_ids)
        if start_unit_id:
            payload["start_unit_id"] = start_unit_id
        with runner.repo.atomic():
            if answers_revision is not None and not runner.repo.settle_reading_request(source_id, answers_revision):
                return None
            batch_id = runner.enqueue_batch(
                AUTO_BUILD_WORKFLOW, [JobSpec(AUTO_STUDY_MAP_JOB, payload)], priority=BUILD_PRIORITY
            )
        self._ensure_worker()
        return batch_id

    # -- UX Phase 1: the book's reading request (finishing pass, F8/F9) -------
    #
    # Level-triggered (reading-hardening, part 1): whether a request is acted
    # on never depends on a wake-up. Every pending request is due now or at its
    # retry time; while this host runs, the reading sweep acts on each due one
    # whose book's work is done. A wake (a failure, a finished job, a report)
    # only brings the next pass forward.

    def reading_now(self) -> datetime:
        """The instant the reading sweep and a failed request's backoff use."""

        return (self.reading_clock or SystemClock()).now()

    def reading_advance_pending(self, extraction_id: str) -> bool:
        """Whether the book's reading request failed and is not settled: the
        Reader's next report asks again instead of being coalesced. Read from
        the durable request, so it holds across a restart (F8)."""

        return self.repository.reading_request_unsettled(extraction_id)

    def wake_reading_retries(self) -> None:
        """Bring the reading sweep's next pass forward (a background host;
        a foreground host calls :meth:`sweep_reading_requests` itself). Never
        needed for correctness: the sweep's own pace reaches every request.

        A no-op inside the sweep's own pass (Codex review F2): an act that
        failed there, even one whose failure could not be recorded, must wait
        the sweep's backoff, not cut it to nothing by waking the sweep it runs
        on. A wake from anywhere else (the Reader's RPC, the start, the
        worker) still brings the pass forward."""

        if getattr(self._in_sweep_pass, "active", False):
            return
        if self._background and self._runner is not None:
            self._ensure_reading_sweep()
            self._reading_sweep_wake.set()

    def wake_blocking_work(self) -> None:
        """A request waits behind its book's queued or running work: make sure
        the ingest worker runs it (after a restart nothing else may start it,
        Codex finish-verify F1). A foreground host drains on its own."""

        if self._background and self._runner is not None:
            self._ensure_worker()

    def resume_contextual_index(self, *, now: datetime | None = None) -> str | None:
        """Wake a deferred local index obligation (Codex review F4).

        A ``local_source_index`` job that could not index everything (the
        batch wait, a busy GPU, a partial run) completes with its reason and a
        ``retry_at``: coverage keeps the debt, and this queues the next batch
        once that time has passed, so a new book is indexed without another
        import or a manual command. Checked on every pass of the host's sweep;
        a cheap query of the newest index job, and the vault's config read
        only when one is due. Idempotent: the batch id names the job it
        resumes. Returns the queued batch id, or None.

        An index job that is queued and claimable while no worker runs (the
        obligation was queued but starting the worker failed, or the process
        ended first) gets the worker started, pass after pass until one runs
        (Codex re-review F4; ``resume_book_preparation`` covers only a book's
        preparation workflows). A foreground host drains on its own.

        With nothing deferred, a due nightly teacher replay (P2, Codex review
        F10) is queued as a replay-only batch (:func:`_queue_due_replay`)."""

        from learnloop.config.loader import load_config
        from learnloop.source_retrieval.local_index import DEFERRED_STATUSES, INDEX_JOB

        runner = self._runner
        if runner is None or self._stop.is_set():
            return None
        if self._background:
            with self._lock:
                worker = self._worker_thread
                worker_running = worker is not None and worker.is_alive()
            if not worker_running and runner.repo.has_runnable_ingest_job(job_types=(INDEX_JOB,)):
                self._ensure_worker()
                return None
        newest = runner.repo.ingest_jobs_by_types((INDEX_JOB,), limit=1)
        if not newest:
            return _queue_due_replay(self, runner, None, now)
        job = newest[0]
        result = job.get("result") or {}
        if job.get("status") != "completed":
            return None
        if result.get("status") not in DEFERRED_STATUSES:
            return _queue_due_replay(self, runner, job, now)
        try:
            due = parse_utc(str(result.get("retry_at"))) if result.get("retry_at") else None
        except Exception:  # noqa: BLE001 - an unreadable time is due now
            due = None
        if due is not None and due > (now or self.reading_now()):
            return None
        config = load_config(Path(runner.vault_root) / "learnloop.toml", load_environment=False)
        if not (config.embedding.local.enabled and config.source_retrieval.dense):
            return None
        batch = runner.enqueue_batch(INDEX_JOB, [JobSpec(INDEX_JOB, {"resumes": job["id"]})],
                                     batch_id=f"{INDEX_JOB}_after_{job['id']}")
        self._ensure_worker()
        return batch

    def refresh_fusion_posteriors(self, *, now: datetime | None = None) -> bool:
        """Refit ``retrieval_fusion_posteriors`` from the feedback receipts
        (spec §9.2: "a nightly job, or one at sidecar start"; Codex review
        F11): only while a new embedding space is on, only when receipts
        arrived since the stored fit, and at most once per
        ``feedback.REFIT_EVERY_HOURS`` on this host. Idempotent and
        deterministic (the replayer's own body). Returns whether it refitted."""

        from types import SimpleNamespace

        from learnloop.config.loader import load_config
        from learnloop.local_embeddings.fusion import refit_posteriors
        from learnloop.source_retrieval.feedback import refresh_due
        from learnloop.source_retrieval.spaces import resolver_active

        runner = self._runner
        if runner is None or self._stop.is_set():
            return False
        moment = now or self.reading_now()
        last = getattr(self, "_fusion_refit_at", None)
        if last is not None and not refresh_due(runner.repo, last_refit=last, now=moment):
            return False  # checked within the cadence: no config read, no work
        # One check per cadence (the host's first pass, then nightly), refit or not.
        self._fusion_refit_at = moment
        config = load_config(Path(runner.vault_root) / "learnloop.toml", load_environment=False)
        if not resolver_active(config) or not refresh_due(runner.repo, last_refit=None, now=moment):
            return False
        refit_posteriors(SimpleNamespace(config=config), runner.repo)
        return True

    def resume_book_preparation(self) -> bool:
        """Start the ingest worker when a book's automatic preparation (an
        Add, a build planner, a planner's build) is queued, the worker could
        run it, and no worker is running. The start calls this, and so does
        every pass of the reading sweep (reading-hardening Codex review 2, F1).

        This work never depends on a reading request to run. An act settles
        the request in the transaction that queues its build, and starts the
        worker only after the commit. If starting the worker fails, or the
        process ends first, the queue itself is all that is left, so the queue
        is what is checked. Work no worker could claim is left alone, so no
        idle worker is started for it pass after pass: a job waiting on a
        dependency the learner has to answer, or one in a batch being
        cancelled. Other workflows keep their own resume paths. A foreground
        host (the CLI, tests) drains on its own and starts nothing here.
        Returns whether the worker was started."""

        from learnloop.content.pipeline.add_source import (
            ADD_SOURCE_WORKFLOW,
            AUTO_BUILD_BATCH_PREFIX,
            AUTO_BUILD_WORKFLOW,
        )

        runner = self._runner
        if runner is None or not self._background or self._stop.is_set():
            return False
        with self._lock:
            worker = self._worker_thread
            worker_running = worker is not None and worker.is_alive()
            quick_running = any(thread.is_alive() for thread in self._quick_check_threads)
        lanes: list[tuple[str, ...]] = []
        if not worker_running:
            lanes.append(tuple(job_type for job_type in runner.handlers if job_type not in parallel_job_types()))
        if not quick_running:
            lanes.append(parallel_job_types())
        if not any(
            runner.repo.has_runnable_ingest_job(
                job_types=lane,
                workflow_types=(ADD_SOURCE_WORKFLOW, AUTO_BUILD_WORKFLOW),
                batch_id_prefixes=(AUTO_BUILD_BATCH_PREFIX,),
            )
            for lane in lanes
        ):
            return False
        self._ensure_worker()
        return True

    def sweep_reading_requests(self, *, now: datetime | None = None) -> "ReadingSweep":
        """One pass of the reading sweep at ``now`` (default
        :meth:`reading_now`): one query over the books' pending requests, and
        an act on each one due (``retry_at`` passed, or none) whose book's work
        is done (:func:`~learnloop.content.pipeline.add_source.act_on_reading_request`).

        Raises when the scan fails, so a caller never takes a failed scan for
        "nothing due". A failed act is counted (``failed``) and recorded by the
        act itself with its backoff; if even that record failed, the request
        is still due and the next pass acts on it. Each request's retry time
        is read on its own: one that cannot be read is due now and never
        stops the pass from reaching the requests after it (verify N2)."""

        from learnloop.content.pipeline import add_source

        moment = now or self.reading_now()
        sweep = ReadingSweep()
        for request in self.repository.pending_reading_requests():
            try:
                due_at = _reading_due_at(request["retry_at"])
                later = due_at is not None and due_at > moment
            except Exception:  # noqa: BLE001 - an unreadable stored time is due now
                due_at, later = None, False
            if later:
                if sweep.next_due_at is None or due_at < sweep.next_due_at:
                    sweep.next_due_at = due_at
                continue
            try:
                outcome = add_source.act_on_reading_request(self, request["source_id"], now=moment)
            except Exception:  # noqa: BLE001 - one book's failure is kept for its own retry
                sweep.failed += 1
                logging.getLogger(__name__).warning(
                    "keeping questions a chapter ahead failed; retrying", exc_info=True
                )
                continue
            if (outcome or {}).get("deferred"):
                sweep.deferred += 1
            else:
                sweep.settled += 1
        return sweep

    def retry_reading_advances(self, *, now: datetime | None = None) -> int:
        """One sweep pass (tests and foreground hosts call it directly):
        returns how many requests settled (one still waiting on its book's
        work does not count). Raises when the scan fails."""

        return self.sweep_reading_requests(now=now).settled

    def _ensure_reading_sweep(self) -> None:
        with self._lock:
            if self._stop.is_set() or not self._background:
                return
            thread = self._reading_sweep_thread
            if thread is None or not thread.is_alive():
                self._reading_sweep_thread = threading.Thread(
                    target=_run_reading_sweep, args=(weakref.ref(self),), name="learnloop-reading-sweep",
                    daemon=True,
                )
                self._reading_sweep_thread.start()

    def _reading_sweep_delay(self, sweep: "ReadingSweep") -> float:
        """Until the next pass: the sweep's pace, sooner when a request's retry
        time comes first."""

        delay = float(self.READING_SWEEP_SECONDS)
        if sweep.next_due_at is not None:
            delay = min(delay, max((sweep.next_due_at - self.reading_now()).total_seconds(), 0.0))
        return delay

    def _reading_sweep_loop(self) -> None:
        """The reading sweep, run on the calling thread (the sweep thread runs
        :func:`_run_reading_sweep`): a pass every :attr:`READING_SWEEP_SECONDS`
        (or at the next retry time, or when woken) for as long as this host
        runs in the background. A failed pass is retried with backoff
        (:attr:`READING_SWEEP_RETRY_SECONDS`, doubling up to the pace). Each
        pass also starts the worker for a book's queued preparation that
        nothing runs (:meth:`resume_book_preparation`). The first pass waits
        one pace: the start reconciles every request and resumes that work
        itself."""

        _run_reading_sweep(weakref.ref(self))

    def _reading_sweep_pass(self, failures: int) -> tuple[int, float] | None:
        """One pass of the sweep thread: ``None`` when this host stopped (or
        runs in the foreground now), else the failures in a row and the wait
        until the next pass."""

        with self._lock:
            # Exits under the lock that starts a sweep, so a start racing
            # this exit either sees the thread gone or keeps it running.
            if self._stop.is_set() or not self._background:
                if self._reading_sweep_thread is threading.current_thread():
                    self._reading_sweep_thread = None
                return None
        delay = float(self.READING_SWEEP_SECONDS)
        if self._runner is None:
            return failures, delay
        failed = False
        try:
            self._in_sweep_pass.active = True
            try:
                sweep = self.sweep_reading_requests()
            finally:
                self._in_sweep_pass.active = False
            delay = self._reading_sweep_delay(sweep)
            failed = bool(sweep.failed)
        except Exception:  # noqa: BLE001 - the sweep outlives any failed pass
            failed = True
            logging.getLogger(__name__).warning("the reading sweep's pass failed; retrying", exc_info=True)
        try:
            # A book's preparation queued with no worker running it (one that
            # failed to start after its build was queued, Codex review 2 F1),
            # checked every pass whether or not any request is pending.
            self.resume_book_preparation()
        except Exception:  # noqa: BLE001 - checked again on the next pass
            failed = True
            logging.getLogger(__name__).warning("could not check for a book's queued preparation; retrying",
                                                exc_info=True)
        try:
            # Local contextual retrieval P1 (Codex review F4): a deferred
            # local index batch is queued when its retry time comes.
            self.resume_contextual_index()
        except Exception:  # noqa: BLE001 - checked again on the next pass
            logging.getLogger(__name__).warning("could not check for a deferred local index; retrying",
                                                exc_info=True)
        try:
            # Codex review F11: the fusion posterior's refit, at this host's
            # first pass and then nightly, when new receipts arrived.
            self.refresh_fusion_posteriors()
        except Exception:  # noqa: BLE001 - tried again on the next pass
            logging.getLogger(__name__).warning("could not refresh the retrieval fusion posterior; retrying",
                                                exc_info=True)
        if not failed:
            return 0, delay
        # A failed scan, an act whose failure may not even be recorded, or a
        # failed check of the queue: try again soon, backing off up to the
        # pace. Never "nothing due".
        failures += 1
        return failures, min(delay, float(self.READING_SWEEP_RETRY_SECONDS) * 2 ** min(failures - 1, 16))

    def _settle_reading_with_cancel(self, runner: IngestRunner, batch_id: str) -> Callable[[], object]:
        """A cancel answers the reading requests of the books whose work it
        stops: each is settled at the revision it has now (reading-hardening,
        part 1). It runs inside the cancel's transaction (``alongside``), so
        the two commit together or not at all: a cancel whose settle fails
        cancels nothing and says so, and no crash between them can leave the
        cancelled work's request due for the sweep to re-plan (Codex review
        F1)."""

        from learnloop.content.pipeline import add_source

        return lambda: add_source.settle_reading_for_cancelled_batch(runner.repo, batch_id)

    # -- sidecar-facing API ------------------------------------------------

    def start(
        self,
        vault_root: Path,
        source: str,
        subject_id: str,
        mode: Literal["canonical", "exam"],
        pdf_engine: str | None = None,
    ) -> dict[str, Any]:
        runner = self._require_runner()
        with self._lock:
            active = self._active_job_locked(runner)
            if active is not None:
                raise ActiveIngestJobError(active["id"])
            job_type = "exam_ingest" if mode == "exam" else "legacy_ingest"
            # v2-lite journey (§6.1 / §15 M3.5): extract once into a Document IR
            # (import), then run legacy synthesis over the IR's display rendering.
            # The legacy job depends on the import job, so synthesis reuses the
            # extraction instead of re-fetching, and the IngestScreen form now
            # feeds better extraction + unit selection into proposals.
            # Exam papers are assessment material, not reading material — they
            # default OUT of the reader loop (per-source flag, owner-overridable).
            import_payload: dict[str, Any] = {"source": source, "subject_id": subject_id}
            if mode == "exam":
                import_payload["reader_enabled"] = False
            if pdf_engine and pdf_engine != "auto":
                # An explicit engine choice is part of the extraction identity;
                # "auto" stays implicit so unchanged sources keep their cache.
                import_payload["pdf_config"] = {"engine": pdf_engine}
            batch_id = runner.enqueue_batch(
                "legacy_ingest",
                [
                    JobSpec("import", import_payload),
                    JobSpec(
                        job_type,
                        {"source": source, "subject_id": subject_id, "mode": mode},
                        depends_on=(0,),
                    ),
                ],
                subject_id=subject_id,
            )
            job = self._legacy_job_for_batch(runner, batch_id)
        self._ensure_worker()
        return _compat(job)

    def get(self, job_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        job = runner.repo.get_ingest_job(job_id)
        return _compat(job) if job is not None else None

    def list(self) -> list[dict[str, Any]]:
        runner = self._require_runner()
        jobs = runner.repo.ingest_jobs_by_types(_LEGACY_JOB_TYPES, limit=_RECENT_LIMIT)
        return [_compat(job) for job in jobs]

    def cancel(self, job_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        job = runner.repo.get_ingest_job(job_id)
        if job is None:
            return None
        if _compat_status(job["status"]) in {"queued", "running"}:
            self._cancel_batch(runner, job["batch_id"])
            job = runner.repo.get_ingest_job(job_id)
        return _compat(job) if job is not None else None

    def _needs_content_reload(self, job: dict[str, Any]) -> bool:
        keys = {job["id"]} if effective_ingest_job_status(job) == "completed" else set()
        for part in (job.get("payload") or {}).get("question_parts", []):
            patch = part.get("patch_id")
            if patch:
                keys.update(f"{job['id']}:{row['id']}" for row in self._require_runner().repo.proposal_items(patch)
                            if row.get("decision") == "accepted" and row.get("applied_change_batch_id"))
        unseen = keys - self._reloaded
        if unseen:
            # Capture before reload: another part landing while the vault loads
            # must still request a subsequent reload, not be marked seen here.
            self._reload_observed[job["id"]] = keys
        return bool(unseen)

    def needs_reload(self, job_id: str) -> bool:
        job = self._require_runner().repo.get_ingest_job(job_id)
        return bool(job and self._needs_content_reload(job))

    def mark_reloaded(self, job_id: str) -> None:
        self._reloaded.update(self._reload_observed.pop(job_id, {job_id}))

    def completed_jobs_awaiting_reload(self, job_types: frozenset[str], *, limit: int) -> list[str]:
        """Jobs with new content, including parts of a still-running section."""
        repository = self._require_runner().repo
        batches = repository.list_ingest_batches(limit=limit)
        jobs_by_batch = repository.ingest_jobs_for_batches(batch["id"] for batch in batches)
        return [job["id"] for jobs in jobs_by_batch.values() for job in jobs
                if job.get("job_type") in job_types and self._needs_content_reload(job)]

    def halt(self) -> None:
        """The host stopped serving the bound vault (``SidecarContext``'s refusal): let go of its runner and stop
        every loop, without joining (this runs on the request thread that met the refusal, and a join there waits
        for whatever provider call a job is in). The runner's own :meth:`IngestRunner.halt` fences a job in flight;
        the loops see ``_stop`` at their next turn and end. Nothing is written. The next :meth:`bind` (a load that
        succeeded) binds a new runner and lets the loops start again."""

        with self._lock:
            runner, self._runner = self._runner, None
            retired, self._retired_runners = self._retired_runners, []
            self._halted = True
            self._stop.set()
        for stopped in [runner, *retired]:
            if stopped is not None:
                stopped.halt()
        self._work_available.set()
        self._quick_check_work_available.set()
        self._reading_sweep_wake.set()

    def shutdown(self) -> None:
        self._stop.set()
        # Wake idle workers so shutdown never waits for the poll timeout.
        self._work_available.set()
        self._quick_check_work_available.set()
        self._reading_sweep_wake.set()
        thread = self._worker_thread
        if thread is not None:
            thread.join(timeout=2)
        for quick_thread in self._quick_check_threads:
            quick_thread.join(timeout=2)
        sweep = self._reading_sweep_thread
        if sweep is not None:
            sweep.join(timeout=2)

    # -- durable batch API (Source library / Batch progress screens) -------

    def enqueue_import(
        self,
        sources: list[str],
        *,
        subject_id: str | None = None,
        inventory: bool = False,
        estimate: dict[str, Any] | None = None,
        page_selection: list[int] | None = None,
        page_selections: dict[str, list[int]] | None = None,
        reader_disabled_sources: set[str] | frozenset[str] | None = None,
        pdf_engine: str | None = None,
        priority: int = 0,
    ) -> str:
        """Enqueue an Import (or Import & inventory) batch (§6.1). One import job
        per source; when ``inventory`` is set, a dependent inventory job is queued
        per source. The handler derives extraction + units from the completed
        import dependency, so the public shorthand is directly executable.

        A build-plan ``estimate`` (when a batch is started from a plan) is
        snapshotted onto each import job's payload (§8.6.2)."""

        runner = self._require_runner()
        specs: list[JobSpec] = []
        for source in sources:
            import_index = len(specs)
            payload: dict[str, Any] = {"source": source}
            source_pages = (page_selections or {}).get(source, page_selection)
            if source_pages is not None:
                payload["page_selection"] = source_pages
            if reader_disabled_sources and source in reader_disabled_sources:
                payload["reader_enabled"] = False
            if pdf_engine and pdf_engine != "auto":
                # See start(): explicit engines join the extraction identity.
                payload["pdf_config"] = {"engine": pdf_engine}
            if estimate is not None:
                payload["estimate"] = estimate
            specs.append(JobSpec("import", payload))
            if inventory:
                specs.append(JobSpec("inventory", {"source": source}, depends_on=(import_index,)))
        workflow = "import_inventory" if inventory else "import"
        batch_id = runner.enqueue_batch(workflow, specs, subject_id=subject_id, priority=priority)
        self._ensure_worker()
        return batch_id

    def enqueue_extraction_repair(
        self,
        *,
        revision_id: str,
        pages: list,
        repair_options: dict[str, Any] | None,
        consent: dict[str, Any],
        parent_extraction_id: str | None = None,
        subject_id: str | None = None,
    ) -> str:
        """Enqueue a consent-gated extraction-repair batch (§2.5)."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "extraction_repair",
            [
                JobSpec(
                    "extraction_repair",
                    {
                        "revision_id": revision_id,
                        "pages": pages,
                        "repair_options": repair_options or {},
                        "consent": consent,
                        "parent_extraction_id": parent_extraction_id,
                    },
                )
            ],
            subject_id=subject_id,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_reader_quick_check(self, *, extraction_id: str, section_id: str,
                                   selection_span_ids: list[str] | None = None) -> str:
        """Enqueue one section's quick-check authoring (reader producer slice).

        Interactive priority (quick-add band) so a reader-initiated question
        drains ahead of bulk batches; the handler is idempotent per section so
        duplicate enqueues while one is queued/running resolve without a second
        model call."""

        runner = self._require_runner()
        payload: dict[str, Any] = {"extraction_id": extraction_id, "section_id": section_id}
        if selection_span_ids:
            payload["selection_span_ids"] = selection_span_ids
        batch_id = runner.enqueue_batch(
            "reader_quick_check",
            [JobSpec("reader_quick_check", payload)],
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_reader_inquiry_check(
        self, *, extraction_id: str, inquiry_root_event_id: str, anchor_span_ids: list[str]
    ) -> str:
        """Enqueue the reconnect line's passage-scoped quick check (RW1a).

        The section check's job type, priority and parallel lane. One live job
        per inquiry: while a batch for this root is queued or running, a second
        request joins it (checked and inserted in one write transaction), and
        the handler claims (root exchange, prompt version) before its call."""

        runner = self._require_runner()
        subject = f"reader_inquiry_check:{inquiry_root_event_id}"
        with runner.repo.atomic():
            live = runner.repo.live_ingest_batch_for_subject(
                workflow_type="reader_quick_check", subject_id=subject
            )
            if live is not None:
                batch_id = str(live["id"])
            else:
                batch_id = runner.enqueue_batch(
                    "reader_quick_check",
                    [JobSpec("reader_quick_check", {
                        "scope_kind": "inquiry",
                        "extraction_id": extraction_id,
                        "inquiry_root_event_id": inquiry_root_event_id,
                        "anchor_span_ids": list(anchor_span_ids),
                    })],
                    subject_id=subject,
                    priority=QUICK_ADD_PRIORITY,
                )
        self._ensure_worker()
        return batch_id

    def enqueue_reader_selection_check(
        self, *, extraction_id: str, anchor_span_ids: list[str], question_style: str
    ) -> str:
        """Enqueue one active-reading question on a selection (RW1b).

        The inquiry check's job type, priority and lane. One live job per
        reuse key (extraction, anchor spans, style): a second request while a
        batch for the key is queued or running joins it."""

        runner = self._require_runner()
        key = RQC.selection_claim_key(extraction_id, list(anchor_span_ids), question_style)
        subject = f"reader_selection_check:{key}"
        with runner.repo.atomic():
            live = runner.repo.live_ingest_batch_for_subject(
                workflow_type="reader_quick_check", subject_id=subject
            )
            if live is not None:
                batch_id = str(live["id"])
            else:
                batch_id = runner.enqueue_batch(
                    "reader_quick_check",
                    [JobSpec("reader_quick_check", {
                        "scope_kind": "selection",
                        "extraction_id": extraction_id,
                        "anchor_span_ids": list(anchor_span_ids),
                        "question_style": question_style,
                    })],
                    subject_id=subject,
                    priority=QUICK_ADD_PRIORITY,
                )
        self._ensure_worker()
        return batch_id

    def enqueue_reader_exercise_import(
        self,
        *,
        extraction_id: str,
        raw_selection: dict[str, Any],
        render_view_id: str | None = None,
        source_id: str | None = None,
        revision_id: str | None = None,
        learning_object_hint: str | None = None,
    ) -> str:
        """Enqueue authoring of the learner's selected textbook exercise(s).

        Interactive priority (the learner is waiting on it), but on the main
        single-writer lane — the handler writes vault YAML, so it must not
        join the parallel read-only quick-check lane."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "reader_exercise_import",
            [
                JobSpec(
                    "reader_exercise_import",
                    {
                        "extraction_id": extraction_id,
                        "raw_selection": dict(raw_selection),
                        "render_view_id": render_view_id,
                        "source_id": source_id,
                        "revision_id": revision_id,
                        "learning_object_hint": learning_object_hint,
                    },
                )
            ],
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_source_exercise_import(
        self,
        *,
        import_id: str,
        extraction_id: str,
        span_ids: list[str],
        proposal_id: str | None = None,
        label: str | None = None,
        learning_object_hint: str | None = None,
        request: dict[str, Any] | None = None,
    ) -> str:
        """Enqueue the import of a picked textbook exercise (canonical sources S1).

        Interactive priority on the main single-writer lane, like the Reader's
        exercise import: the handler writes vault YAML. ``request`` is what the
        exercise was proposed for (plain data: the proposal's constraints and
        intent, minutes per practice mode, a discriminate proposal's screen)."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "source_exercise_import",
            [JobSpec("source_exercise_import", {
                "import_id": import_id, "extraction_id": extraction_id, "span_ids": list(span_ids),
                "proposal_id": proposal_id, "label": label, "learning_object_hint": learning_object_hint,
                "caller": "learner", "request": dict(request or {}),
            })],
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_practice_expansion(
        self,
        *,
        learning_object_ids: list[str],
        subject_id: str | None = None,
        reason: str | None = None,
        source_refs: list[dict[str, Any]] | None = None,
        ad_commission_id: str | None = None,
        topic_keys: Mapping[str, str] | None = None,
        start: bool = True,
    ) -> str:
        """Enqueue per-LO practice generation (reader-first progressive seeding).

        ``topic_keys`` queues topic work (each topic's checkpoint scope). ``start=False`` records the batch and
        starts nothing, for a caller inside a transaction (a topic claim): it calls :meth:`run_queued_work` once
        that has committed.

        Background priority (default band): generation after a section completes
        must never starve reader quick-checks or interactive quick-add builds.

        ``ad_commission_id``: an adaptive difficulty serve-time commission
        (spec_adaptive_difficulty_v1 §6.1, §7.1): one item at its point. The
        batch id is the commission's, so enqueuing it again (a retried
        schedule, a restart) finds the same durable batch, never a second
        generation. A job of that batch that ran with adaptive difficulty's models off
        (``AD_MODELS_OFF_CODE``) is requeued here once they are on again (Codex re-review F10),
        but only while its batch is uncancelled: the check and the requeue are one
        transaction, and an explicit cancellation stays until the user resumes the batch
        (Codex verify F11)."""

        runner = self._require_runner()
        if ad_commission_id:
            from learnloop.adaptive_difficulty.spend import models_off

            existing = ad_commission_batch_id(ad_commission_id)
            waiting = [
                job for job in runner.repo.ingest_jobs_for_batch(existing)
                if job.get("status") == "failed" and (job.get("error") or {}).get("code") == AD_MODELS_OFF_CODE
            ]
            if waiting:
                if not models_off() and runner.requeue_failed_unless_cancelled(
                    existing, error_code=AD_MODELS_OFF_CODE
                ):
                    self._ensure_worker()
                return existing
        payload = practice_expansion_payload(
            learning_object_ids, reason or ("ad_commission" if ad_commission_id else "reader_section_completed"),
            source_refs, topic_keys,
        )
        if ad_commission_id:
            payload["ad_commission_id"] = str(ad_commission_id)
        batch_id = runner.enqueue_batch(
            "practice_expansion",
            [JobSpec("practice_expansion", payload)],
            subject_id=subject_id,
            batch_id=ad_commission_batch_id(ad_commission_id) if ad_commission_id else None,
        )
        if start:
            self._ensure_worker()
        return batch_id

    def run_queued_work(self) -> None:
        """Start the worker on what is queued (a foreground host drains it now): after a transaction that queued
        work with ``start=False`` has committed."""

        if self._runner is not None:
            self._ensure_worker()

    def enqueue_goal_population(self, *, goal_id: str) -> str:
        """Enqueue durable goal-scoped practice authoring from the wizard."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "goal_population",
            [JobSpec("goal_population", {"goal_id": goal_id})],
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_rung_variant(self, *, request_id: str, subject_id: str | None = None) -> str:
        """Enqueue one learner-requested variant authoring (interactive band —
        the learner is waiting on it, like a quick-add build)."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "rung_variant",
            [JobSpec("rung_variant", {"request_id": request_id})],
            subject_id=subject_id,
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_question_promotion(
        self,
        *,
        event_id: str,
        subject_id: str | None = None,
    ) -> str:
        """Enqueue a durable Open-question analysis/authoring request."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "question_promotion",
            [JobSpec("question_promotion", {"event_id": event_id})],
            subject_id=subject_id,
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_concept_animation(self, *, animation_id: str, subject_id: str | None = None) -> str:
        """Enqueue one explainer-animation generation (interactive band — the
        learner clicked generate and is watching the status)."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "concept_animation",
            [JobSpec("concept_animation", {"animation_id": animation_id})],
            subject_id=subject_id,
            priority=QUICK_ADD_PRIORITY,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_figure_rich(self, *, payload: Mapping[str, Any], grant: Any = None,
                            origin: str | None = None) -> str:
        """Enqueue one rich figure build (Reader RW5d P2b; interactive band:
        the learner pressed "show me" and the quick figure, if any, is on the
        page). ``grant``/``origin``: the press's, only when its action is
        granted (else the job belongs to no action: no offer, no grant).
        Returns the job's id (the figure line reads it back by payload)."""

        from learnloop.db.stores.provenance import record_job_enqueued

        runner = self._require_runner()
        # The record commits with the job: a worker already draining could
        # lease the job before a later write, and would then run it under no
        # trace of the press that asked for it.
        with runner.repo.atomic():
            # RW5d P5 (Codex review F7): a prebuild's rich job is background work,
            # so it takes the default band, after every pressed figure's.
            batch_id = runner.enqueue_batch(
                "figure_rich",
                [JobSpec("figure_rich", dict(payload))],
                priority=0 if payload.get("build_mode") == "prefetch" else QUICK_ADD_PRIORITY,
                grant=grant,
                origin=origin if grant is not None else None,
            )
            job_id = runner.repo.ingest_jobs_for_batch(batch_id)[0]["id"]
            record_job_enqueued(runner.repo.connection(), queue="ingest_jobs", job_id=job_id,
                                job_kind="figure_rich", facts={"build_mode": payload.get("build_mode")})
        self._ensure_worker()
        return job_id

    def retry_figure_rich(self, job_id: str, *, error_code: str) -> bool:
        """Requeue a rich figure job that failed with ``error_code`` (the plan
        wait), unless it was cancelled (Reader RW5d P2b)."""

        runner = self._require_runner()
        job = runner.repo.get_ingest_job(job_id)
        if job is None or job.get("job_type") != "figure_rich":
            return False
        if runner.requeue_failed_unless_cancelled(job["batch_id"], error_code=error_code):
            self._ensure_worker()
            return True
        return False

    def enqueue_inventory(
        self,
        *,
        extraction_id: str,
        units: list[dict[str, Any]],
        subject_id: str | None = None,
        source_set_id: str | None = None,
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        unlimited_token_budget: bool = False,
        priority: int = 0,
    ) -> str:
        """Enqueue a role-aware unit-inventory batch (§7). Cached units cost zero
        tokens; only semantic-hash-changed units re-inventory."""

        runner = self._require_runner()
        payload: dict[str, Any] = {"extraction_id": extraction_id, "units": units}
        if input_budget_tokens is not None:
            payload["input_budget_tokens"] = input_budget_tokens
        if output_budget_tokens is not None:
            payload["output_budget_tokens"] = output_budget_tokens
        if unlimited_token_budget:
            payload["unlimited_token_budget"] = True
        batch_id = runner.enqueue_batch(
            "import_inventory",
            [JobSpec("inventory", payload)],
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_quick_add_build(
        self,
        *,
        extraction_id: str,
        units: list[dict[str, Any]],
        source_set_id: str,
        subject_id: str | None = None,
        brief: dict[str, Any] | None = None,
        mode: str = "auto",
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        unlimited_token_budget: bool = False,
        create_goal: bool = False,
        priority: int = QUICK_ADD_PRIORITY,
        batch_id: str | None = None,
    ) -> str:
        """Enqueue the Quick-add build batch (§1): inventory(selected units) then
        bootstrap_synthesis over the freshly-created source set, as one batch that
        drains ahead of bulk work. The synthesis job depends on the inventory job,
        so gates only run once the selected units carry inventories.

        ``create_goal``: the learner's exam-prep brief asked for its Goal (§5.1);
        the synthesis makes it after applying the map."""

        runner = self._require_runner()
        inventory_payload: dict[str, Any] = {"extraction_id": extraction_id, "units": units}
        if input_budget_tokens is not None:
            inventory_payload["input_budget_tokens"] = input_budget_tokens
        if output_budget_tokens is not None:
            inventory_payload["output_budget_tokens"] = output_budget_tokens
        if unlimited_token_budget:
            inventory_payload["unlimited_token_budget"] = True
        synthesis_payload: dict[str, Any] = {
            "source_set_id": source_set_id,
            "brief": dict(brief or {}),
            "mode": mode,
            # Quick Add's promise is a usable study map after its one explicit
            # confirmation, not a second hidden proposal-acceptance step.
            "apply": True,
        }
        if unlimited_token_budget:
            synthesis_payload["unlimited_token_budget"] = True
        if create_goal:
            synthesis_payload["create_goal"] = True
        batch_id = runner.enqueue_batch(
            "bootstrap_synthesis",
            [
                JobSpec("inventory", inventory_payload),
                JobSpec("bootstrap_synthesis", synthesis_payload, depends_on=(0,)),
            ],
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
            **({"batch_id": batch_id} if batch_id is not None else {}),
        )
        self._ensure_worker()
        return batch_id

    def enqueue_source_set_build(
        self,
        *,
        members: list[dict[str, Any]],
        source_set_id: str,
        subject_id: str | None = None,
        brief: dict[str, Any] | None = None,
        mode: str = "auto",
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        synthesis_budgets: dict[str, int] | None = None,
        unlimited_token_budget: bool = False,
        create_goal: bool = False,
        priority: int = QUICK_ADD_PRIORITY,
    ) -> str:
        """Enqueue a study-map build batch for an EXISTING source set (§1/§8): one
        inventory job per member (over its scoped units) followed by a
        bootstrap_synthesis job that depends on all of them, so gates only run once
        every member's units carry inventories. This is the multi-member, in-app
        counterpart to :meth:`enqueue_quick_add_build` (single-source Quick add) —
        it lets a collection assembled in the app synthesize a study map without the
        CLI, surfacing as one durable Activity batch.

        Each ``members`` entry is ``{"extraction_id": str, "units": [...]}`` where
        units are ``[{unit_id, role, profile?}]`` (the inventory job's shape).
        ``create_goal`` as for :meth:`enqueue_quick_add_build`."""

        runner = self._require_runner()
        if not members:
            raise ValueError("a study-map build needs at least one member.")
        specs: list[JobSpec] = []
        for member in members:
            inventory_payload: dict[str, Any] = {
                "extraction_id": member["extraction_id"],
                "units": member["units"],
            }
            if input_budget_tokens is not None:
                inventory_payload["input_budget_tokens"] = input_budget_tokens
            if output_budget_tokens is not None:
                inventory_payload["output_budget_tokens"] = output_budget_tokens
            if unlimited_token_budget:
                inventory_payload["unlimited_token_budget"] = True
            specs.append(JobSpec("inventory", inventory_payload))
        synthesis_payload: dict[str, Any] = {
            "source_set_id": source_set_id,
            "brief": dict(brief or {}),
            "mode": mode,
            # Synthesizing a collection is itself the learner's explicit confirmation
            # (the "synthesize →" click), so apply so it yields a usable study map —
            # mirroring Quick add rather than leaving a second review step.
            "apply": True,
        }
        if synthesis_budgets:
            synthesis_payload["synthesis_budgets"] = dict(synthesis_budgets)
        if unlimited_token_budget:
            synthesis_payload["unlimited_token_budget"] = True
        if create_goal:
            synthesis_payload["create_goal"] = True
        specs.append(
            JobSpec("bootstrap_synthesis", synthesis_payload, depends_on=tuple(range(len(members))))
        )
        batch_id = runner.enqueue_batch(
            "bootstrap_synthesis",
            specs,
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
        )
        self._ensure_worker()
        return batch_id

    def enqueue_source_set_append(
        self,
        *,
        members: list[dict[str, Any]],
        source_set_id: str,
        new_revision_ids: list[str] | None = None,
        new_unit_ids: Mapping[str, Sequence[str]] | None = None,
        change_kind: str = "source_added",
        subject_id: str | None = None,
        brief: dict[str, Any] | None = None,
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        synthesis_budgets: dict[str, int] | None = None,
        unlimited_token_budget: bool = False,
        priority: int = QUICK_ADD_PRIORITY,
    ) -> str:
        """Enqueue a bounded-neighborhood APPEND batch for a collection whose subject
        already carries a study map (§10). One inventory job per NEW (not-yet-synthesized)
        member — same scoping/roles shape as the bootstrap build — followed by a single
        ``append_synthesis`` job that depends on all of them and reconciles ONLY the new
        material against the existing map through the bounded affected neighborhood. The
        map is never resent or rebuilt; ``new_revision_ids`` pins the append scope, and
        ``new_unit_ids`` ({revision_id: [unit_id]}) narrows a revision to its new units.

        The append counterpart to :meth:`enqueue_source_set_build`. ``members`` may be
        empty (nothing new to inventory), in which case the append job runs alone and
        reconciles the set's current membership (cache-reused when unchanged)."""

        runner = self._require_runner()
        specs: list[JobSpec] = []
        for member in members:
            inventory_payload: dict[str, Any] = {
                "extraction_id": member["extraction_id"],
                "units": member["units"],
            }
            if input_budget_tokens is not None:
                inventory_payload["input_budget_tokens"] = input_budget_tokens
            if output_budget_tokens is not None:
                inventory_payload["output_budget_tokens"] = output_budget_tokens
            if unlimited_token_budget:
                inventory_payload["unlimited_token_budget"] = True
            specs.append(JobSpec("inventory", inventory_payload))
        append_payload: dict[str, Any] = {
            "source_set_id": source_set_id,
            "brief": dict(brief or {}),
            "change_kind": change_kind,
            "new_revision_ids": list(new_revision_ids or []),
            # The "synthesize →" click is the learner's explicit confirmation, so
            # routine span/assessment attachments auto-apply (§10.3); everything else
            # stays a pending review proposal.
            "apply": True,
        }
        if new_unit_ids:
            append_payload["new_unit_ids"] = {revision: list(units) for revision, units in new_unit_ids.items()}
        if synthesis_budgets:
            append_payload["synthesis_budgets"] = dict(synthesis_budgets)
        if unlimited_token_budget:
            append_payload["unlimited_token_budget"] = True
        specs.append(
            JobSpec("append_synthesis", append_payload, depends_on=tuple(range(len(members))))
        )
        batch_id = runner.enqueue_batch(
            "append_synthesis",
            specs,
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
        )
        self._ensure_worker()
        return batch_id

    def retry_synthesis(
        self,
        batch_id: str,
        *,
        synthesis_budgets: dict[str, int] | None = None,
        reuse_candidate: bool = False,
        repair_candidate: bool = False,
        repair_ops: list[dict[str, Any]] | None = None,
        unlimited_token_budget: bool = False,
    ) -> dict[str, Any]:
        """Retry only a failed synthesis stage with revised execution ceilings.

        Inventory dependencies must already be complete. Their durable outputs
        remain in place and are neither requeued nor regenerated.

        ``reuse_candidate`` finishes the pipeline from the failed attempt's
        preserved merged candidate — normalization/gates/persistence re-run with
        ZERO model calls. Requires the failed job to have recorded a preserved
        candidate's synthesis run id in its error details.

        ``repair_candidate`` additionally derives mechanically-safe repair ops
        over that candidate before the gates rerun (dangling criterion-id
        dependencies and similar); ``repair_ops`` applies explicit user- or
        agent-authored ops. Both require ``reuse_candidate``.
        """

        runner = self._require_runner()
        jobs = runner.repo.ingest_jobs_for_batch(batch_id)
        synthesis_job, refusal = retryable_synthesis_job(jobs)
        if synthesis_job is None:
            raise ValueError(SYNTHESIS_RECOVERY_REFUSALS[refusal])

        payload = dict(synthesis_job.get("payload") or {})
        payload.pop("reuse_candidate", None)
        payload.pop("synthesis_run_id", None)
        payload.pop("repair_candidate", None)
        payload.pop("repair_ops", None)
        payload["unlimited_token_budget"] = unlimited_token_budget
        if (repair_candidate or repair_ops) and not reuse_candidate:
            raise ValueError("candidate repair requires reuse_candidate")
        if reuse_candidate:
            synthesis_run_id, refusal = preserved_candidate_run(synthesis_job, runner.repo.synthesis_run)
            if synthesis_run_id is None:
                raise ValueError(SYNTHESIS_RECOVERY_REFUSALS[refusal])
            payload["reuse_candidate"] = True
            payload["synthesis_run_id"] = synthesis_run_id
            if repair_candidate:
                payload["repair_candidate"] = True
            if repair_ops:
                payload["repair_ops"] = [dict(op) for op in repair_ops]
        if synthesis_budgets:
            payload["synthesis_budgets"] = {
                **dict(payload.get("synthesis_budgets") or {}),
                **synthesis_budgets,
            }
        runner.repo.update_ingest_job_payload(synthesis_job["id"], payload)
        runner.resume_batch(batch_id)
        self._ensure_worker()
        return self.get_batch(batch_id) or {}

    def get_batch(self, batch_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        batch = runner.repo.get_ingest_batch(batch_id)
        if batch is None:
            return None
        return _batch_view(batch, runner.repo.ingest_jobs_for_batch(batch_id), runner.repo)

    def list_batches(self, limit: int = _RECENT_LIMIT) -> list[dict[str, Any]]:
        runner = self._require_runner()
        batches = runner.repo.list_ingest_batches(limit=limit)
        jobs_by_batch = runner.repo.ingest_jobs_for_batches(
            batch["id"] for batch in batches
        )
        dependencies_by_job = runner.repo.ingest_job_dependencies_for_jobs(
            job["id"]
            for jobs in jobs_by_batch.values()
            for job in jobs
        )
        rung_requests_by_id = runner.repo.rung_variant_requests(
            request_id
            for jobs in jobs_by_batch.values()
            for job in jobs
            if (request_id := _failed_rung_request_id(job)) is not None
        )
        return [
            _batch_view(
                batch,
                jobs_by_batch.get(batch["id"], []),
                runner.repo,
                dependencies_by_job=dependencies_by_job,
                rung_requests_by_id=rung_requests_by_id,
            )
            for batch in batches
        ]

    def cancel_batch(self, batch_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        if runner.repo.get_ingest_batch(batch_id) is None:
            return None
        self._cancel_batch(runner, batch_id)
        return self.get_batch(batch_id)

    def _cancel_batch(self, runner: IngestRunner, batch_id: str) -> None:
        """Cancel, and settle the reading requests of the books whose work
        this was, in one transaction (reading-hardening, part 1: a cancel
        answers the request, so the sweep never re-plans the work the learner
        just stopped; review F1: both commit or neither does). Under the
        reading lock, so no act on the request in this process interleaves."""

        with self._reading_lock:
            runner.cancel_batch(batch_id, alongside=self._settle_reading_with_cancel(runner, batch_id))

    def interrupt_codex(self, job_id: str | None = None) -> dict[str, Any]:
        """Interrupt one live Codex call while keeping the sidecar process alive."""

        current = self._require_runner()
        with self._lock:
            runners = [current, *self._retired_runners]
        # A claim a retired runner still holds (R4-F2) is interrupted through the runner that holds its handle.
        active: list[dict[str, Any]] = []
        owners: dict[str, IngestRunner] = {}
        for owner in runners:
            for job in owner.active_interruptible_jobs():
                active.append(job)
                owners[job["id"]] = owner
        if job_id is None:
            if not active:
                raise ValueError("No interruptible Codex ingest call is running.")
            if len(active) > 1:
                ids = ", ".join(job["id"] for job in active)
                raise ValueError(f"More than one Codex call is running; pass a job id: {ids}")
            selected = active[0]
        else:
            selected = next((job for job in active if job["id"] == job_id), None)
            if selected is None:
                job = current.repo.get_ingest_job(job_id)
                if job is None:
                    raise ValueError(f"Ingest job '{job_id}' was not found.")
                if job.get("status") != "running":
                    raise ValueError(f"Ingest job '{job_id}' is {job.get('status')}, not running.")
                raise ValueError(f"Ingest job '{job_id}' has no interruptible Codex call attached.")
        with self._reading_lock:
            # Interrupting cancels the job's batch: as any cancel, it answers
            # the book's reading request, in the cancel's transaction; the
            # call is interrupted only once both committed.
            runner = owners.get(selected["id"], current)
            settle = self._settle_reading_with_cancel(current, str(selected["batch_id"]))
            if not runner.interrupt_job(selected["id"], alongside=settle):
                raise ValueError(f"Codex call for ingest job '{selected['id']}' already finished.")
        return {
            "job_id": selected["id"],
            "batch_id": selected["batch_id"],
            "job_type": selected["job_type"],
            "interrupted": True,
        }

    def resume_waiting_for_ok(self) -> list[str]:
        """The jobs that waited for the learner's OK to use AI, queued again once and started."""

        resumed = self._require_runner().resume_waiting_for_ok()
        if resumed:
            self._ensure_worker()
        return resumed

    def resume_batch(self, batch_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        if runner.repo.get_ingest_batch(batch_id) is None:
            return None
        runner.resume_batch(batch_id)
        self._ensure_worker()
        return self.get_batch(batch_id)

    # -- worker host -------------------------------------------------------

    def drain_foreground(self) -> int:
        """Drain the queue synchronously (tests + CLI-less contexts)."""

        return self._require_runner().drain()

    def _ensure_worker(self) -> None:
        if not self._background:
            self.drain_foreground()
            return
        with self._lock:
            if self._halted:  # only a bind starts a halted host again
                return
            self._stop.clear()
            # A host stopped and started again gets its reading sweep back.
            self._ensure_reading_sweep()
            # An existing worker may be waiting between drain attempts. Signal
            # before checking thread liveness so enqueue-to-claim has no polling
            # delay; newly started workers simply consume the harmless signal.
            self._work_available.set()
            self._quick_check_work_available.set()
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(
                    target=self._worker_loop, name="learnloop-ingest-drain", daemon=True
                )
                self._worker_thread.start()
            self._quick_check_threads = [
                thread for thread in self._quick_check_threads if thread.is_alive()
            ]
            for index in range(len(self._quick_check_threads), _QUICK_CHECK_WORKERS):
                quick_thread = threading.Thread(
                    target=self._quick_check_worker_loop,
                    name=f"learnloop-quick-check-{index + 1}",
                    daemon=True,
                )
                self._quick_check_threads.append(quick_thread)
                quick_thread.start()

    def _worker_loop(self) -> None:
        idle_rounds = 0
        while not self._stop.is_set():
            # The host's runner each turn: after a vault switch an enqueue finds this thread alive and starts no
            # other, so a runner kept from the start would go on draining the previous vault.
            runner = self._runner
            if runner is None:
                return
            self._work_available.clear()
            try:
                ran = runner.drain(
                    eligible_job_types=tuple(
                        job_type
                        for job_type in runner.handlers
                        if job_type not in parallel_job_types()
                    ),
                    compatible_running_job_types=parallel_job_types(),
                )
            except (Exception, writer_fence.WriterFenceRefusal):  # noqa: BLE001 — the drain thread must never die silently on one bad job
                ran = 0
            try:
                ran += self._drain_reader_requests(runner)
            except (Exception, writer_fence.WriterFenceRefusal):  # noqa: BLE001 — reader synthesis must never kill the ingest drain
                pass
            if ran:
                # Work finished: a book's reading request waiting on it may be
                # due now. Only brings the sweep's next pass forward (the
                # sweep reaches it on its own pace regardless).
                self._reading_sweep_wake.set()
            idle_rounds = idle_rounds + 1 if ran == 0 else 0
            # Reading requests are the sweep's, not this loop's (reading-
            # hardening, part 1): the worker exits when its queue is idle.
            if idle_rounds >= 3 and self._active_job_locked(runner) is None:
                with self._lock:
                    # A wake during this round (an enqueue) saw this thread
                    # alive: run another round for it. Otherwise step aside,
                    # so the next wake starts a worker.
                    if not self._work_available.is_set():
                        if self._worker_thread is threading.current_thread():
                            self._worker_thread = None
                        break
                continue
            if ran == 0:
                self._work_available.wait(timeout=self._poll_interval)

    def _quick_check_worker_loop(self) -> None:
        """Drain independent quick checks beside the serialized vault writer.

        Each job resolves its own provider client, so up to three Codex calls can
        progress independently. Quick checks only write durable SQLite rows and
        never mutate vault YAML, which keeps the single-writer invariant intact.
        """

        idle_rounds = 0
        while not self._stop.is_set():
            runner = self._runner  # the host's each turn, as in the drain loop (a vault switch)
            if runner is None:
                return
            self._quick_check_work_available.clear()
            try:
                ran = runner.drain(
                    max_jobs=1,
                    eligible_job_types=parallel_job_types(),
                    allow_parallel=True,
                    max_parallel=_QUICK_CHECK_WORKERS,
                )
            except (Exception, writer_fence.WriterFenceRefusal):  # noqa: BLE001 — one worker must not kill the lane
                ran = 0
            idle_rounds = idle_rounds + 1 if ran == 0 else 0
            active = runner.repo.ingest_jobs_by_types(parallel_job_types())
            if idle_rounds >= 3 and not any(
                job["status"] in _ACTIVE_STATUSES for job in active
            ):
                break
            if ran == 0:
                self._quick_check_work_available.wait(timeout=self._poll_interval)

    # -- demand-paged reader synthesis drain (spec §6.4) --------------------

    def kick_reader_drain(self) -> None:
        """Ensure queued demand-paged reader requests get drained.

        Background mode starts (or keeps) the worker thread; foreground mode
        (tests, CLI-less contexts) drains once synchronously. Called by the
        reader handlers whenever a request may have been enqueued — a nudge,
        so it never raises into the RPC whose capture already succeeded."""

        runner = self._runner
        if runner is None:
            return
        if not self._background:
            try:
                self._drain_reader_requests(runner)
            except Exception:  # noqa: BLE001 — the nudge must not fail the capture RPC
                pass
            return
        # Re-probe provider readiness for each drain burst: the provider may
        # have come up since the last (failed) resolution.
        with self._lock:
            self._reader_client_checked = False
        self._ensure_worker()

    def _drain_reader_requests(self, runner: IngestRunner) -> int:
        """Drain queued reader requests with a real synthesize client.

        Provider unavailable → requests stay ``queued`` (never failed by the
        infrastructure); the next kick re-probes. Bounded per cycle so a large
        backlog cannot starve ingest jobs between polls."""

        if runner.halted.is_set() or not runner.repo.has_queued_reader_requests():
            return 0
        client = self._resolve_reader_client(runner)
        if client is None:
            return 0
        synthesize = RR.model_synthesis(client, source_sets=lambda: _reader_source_sets(runner.vault_root))
        ran = 0
        # One claim at a time, so a halt (``IngestRunner.halt``) stops the next claim; the request in flight then
        # records its answer, the one write a halt does not stop.
        for turn in range(3):
            if runner.halted.is_set() or (turn and not runner.repo.has_queued_reader_requests()):
                break
            result = RR.drain_requests(runner.repo, worker_id=f"sidecar-{os.getpid()}", synthesize=synthesize,
                                       limit=1)
            ran += len(result["completed"]) + len(result["failed"]) + len(result["partial"])
        return ran

    def _resolve_reader_client(self, runner: IngestRunner) -> Any:
        with self._lock:
            if self._reader_client_checked:
                return self._reader_client
            factory = self._reader_synth_client_factory
        if factory is not None:
            client = factory()
        else:
            try:
                from learnloop.ai.routing import ready_client_for_task
                from learnloop.vault.loader import load_vault

                vault = load_vault(runner.vault_root)
                # Same canonical_ingest route the runner's inventory/synthesis
                # factories resolve, so non-codex vaults (e.g. openrouter) can
                # drain reader preset requests too.
                client = ready_client_for_task(
                    runner.vault_root,
                    vault.config,
                    "canonical_ingest",
                ).client
            except Exception:  # noqa: BLE001 — an unresolvable provider leaves requests queued
                client = None
        with self._lock:
            self._reader_client = client
            self._reader_client_checked = True
        return client

    @staticmethod
    def _legacy_job_for_batch(runner: IngestRunner, batch_id: str) -> dict[str, Any]:
        """The synthesis job the frontend polls (the batch also holds an import job)."""

        jobs = runner.repo.ingest_jobs_for_batch(batch_id)
        for job in jobs:
            if job["job_type"] in _LEGACY_JOB_TYPES:
                return job
        return jobs[-1]

    def _active_job_locked(self, runner: IngestRunner) -> dict[str, Any] | None:
        for job in runner.repo.ingest_jobs_by_types(_LEGACY_JOB_TYPES, limit=_RECENT_LIMIT):
            if job["status"] in _ACTIVE_STATUSES:
                return job
        return None


def _iso(moment: datetime | None) -> str:
    """``moment`` (default: now) as the ISO UTC text reading requests store."""

    from learnloop.clock import FrozenClock

    return utc_now_iso(FrozenClock(moment) if moment is not None else None)


# The rungs each job type can actually reach. Reporting the full ladder for every
# job made an import-only batch advertise `inventoried`/`synthesized`/`applied`
# rungs no import handler ever reports, so the card read as a whole study-map
# build that had merely stalled. Anything not listed keeps the full ladder.
_LADDER_BY_JOB_TYPE: dict[str, tuple[str, ...]] = {
    "import": CHECKPOINT_LADDER[: CHECKPOINT_LADDER.index("extracted") + 1],
    "extraction_repair": CHECKPOINT_LADDER[: CHECKPOINT_LADDER.index("extracted") + 1],
    "inventory": CHECKPOINT_LADDER[: CHECKPOINT_LADDER.index("inventoried") + 1],
}


def _job_view(
    job: dict[str, Any],
    repo: Repository,
    *,
    depends_on: list[str] | None = None,
    rung_requests_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """One job as the Batch-progress screen needs it: the checkpoint ladder, live
    phase/window counts, actual usage, and any waiting_for_input payload (§5.7)."""

    result = job.get("result") or {}
    waiting_payload = result.get("waiting_for_input") if isinstance(result, dict) else None
    payload = job.get("payload") or {}
    status = effective_ingest_job_status(job)
    phase = job.get("phase")
    message = job.get("message")
    error = job.get("error")
    if status == "failed" and job.get("status") == "completed":
        request_id = str(payload.get("request_id") or "")
        request = (rung_requests_by_id or {}).get(request_id)
        reason = str(
            (request or {}).get("failure_reason")
            or "Rung variant generation failed before producing a proposal."
        )
        phase = "failed"
        message = reason
        error = {
            "code": "rung_variant_failed",
            "message": reason,
            "retryable": True,
            "details": {"request_id": request_id, "result": result},
        }
    return {
        "id": job["id"],
        "batch_id": job["batch_id"],
        "ordinal": job["ordinal"],
        "job_type": job["job_type"],
        "status": status,
        "phase": phase,
        "message": message,
        "current_window": job.get("current_window"),
        "total_windows": job.get("total_windows"),
        "attempt_count": job.get("attempt_count", 0),
        "checkpoint_ladder": list(
            _LADDER_BY_JOB_TYPE.get(job["job_type"], CHECKPOINT_LADDER)
        ),
        "usage": job.get("usage") or {},
        "estimate": payload.get("estimate") or {},
        "source": payload.get("source"),
        "result": None if waiting_payload is not None else (result or None),
        "error": error,
        "waiting_for_input": waiting_payload,
        "depends_on": (
            depends_on
            if depends_on is not None
            else repo.ingest_job_dependency_ids(job["id"])
        ),
    }


#: Why a batch's synthesis cannot be retried, or its preserved candidate not reused (code constants the batch
#: view carries), each with the words :meth:`DurableIngestJobs.retry_synthesis` refuses with.
SYNTHESIS_RECOVERY_REFUSALS: dict[str, str] = {
    "no_unfinished_synthesis": "batch must contain exactly one unfinished synthesis job",
    "inventory_incomplete": "all inventory jobs must be completed before retrying synthesis",
    "no_preserved_candidate": "the failed synthesis attempt preserved no candidate; retry synthesis instead",
    "candidate_gone": "the preserved candidate is no longer available; retry synthesis instead",
}


def retryable_synthesis_job(jobs: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, str | None]:
    """The batch's one unfinished synthesis job a retry reruns, or ``None`` and the refusal's code.

    A cancelled or blocked synthesis is retried like a failed one; every inventory it reads must be complete,
    since a retry reruns synthesis alone."""

    synthesis_jobs = [
        job for job in jobs
        if job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}
        and job["status"] in {"failed", "blocked", "cancelled"}
    ]
    if len(synthesis_jobs) != 1:
        return None, "no_unfinished_synthesis"
    if any(job["job_type"] == "inventory" and job["status"] != "completed" for job in jobs):
        return None, "inventory_incomplete"
    return synthesis_jobs[0], None


def preserved_candidate_run(
    synthesis_job: Mapping[str, Any], synthesis_run: Callable[[str], Mapping[str, Any] | None]
) -> tuple[str | None, str | None]:
    """The synthesis run whose preserved candidate a retry may revalidate (and repair) with no model call, or
    ``None`` and the refusal's code."""

    details = ((synthesis_job.get("error") or {}).get("details")) or {}
    synthesis_run_id = str(details.get("synthesis_run_id") or "")
    if not details.get("candidate_preserved") or not synthesis_run_id:
        return None, "no_preserved_candidate"
    run = synthesis_run(synthesis_run_id)
    if run is None or not run.get("candidate_output"):
        return None, "candidate_gone"
    return synthesis_run_id, None


def synthesis_recovery(jobs: list[dict[str, Any]], repo: Repository) -> dict[str, Any]:
    """What :meth:`DurableIngestJobs.retry_synthesis` would accept for this batch, from its own checks, so the
    desktop offers exactly the retries the host takes."""

    synthesis_job, retry_refusal = retryable_synthesis_job(jobs)
    run_id, reuse_refusal = (
        preserved_candidate_run(synthesis_job, repo.synthesis_run) if synthesis_job is not None
        else (None, retry_refusal)
    )
    return {
        "can_retry_synthesis": synthesis_job is not None,
        "retry_synthesis_job_id": synthesis_job["id"] if synthesis_job is not None else None,
        "retry_synthesis_refusal": retry_refusal,
        "can_reuse_candidate": run_id is not None,
        "reuse_candidate_refusal": reuse_refusal,
    }


def _batch_view(
    batch: dict[str, Any],
    jobs: list[dict[str, Any]],
    repo: Repository,
    *,
    dependencies_by_job: dict[str, list[str]] | None = None,
    rung_requests_by_id: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if dependencies_by_job is None:
        dependencies_by_job = repo.ingest_job_dependencies_for_jobs(
            job["id"] for job in jobs
        )
    if rung_requests_by_id is None:
        rung_requests_by_id = repo.rung_variant_requests(
            request_id
            for job in jobs
            if (request_id := _failed_rung_request_id(job)) is not None
        )
    return {
        "id": batch["id"],
        "workflow_type": batch["workflow_type"],
        "subject_id": batch.get("subject_id"),
        "source_set_id": batch.get("source_set_id"),
        "status": derive_batch_status(jobs, batch),
        "cancel_requested": bool(batch.get("cancel_requested")),
        "created_at": batch.get("created_at"),
        "started_at": batch.get("started_at"),
        "finished_at": batch.get("finished_at"),
        "jobs": [
            _job_view(
                job,
                repo,
                depends_on=dependencies_by_job.get(job["id"], []),
                rung_requests_by_id=rung_requests_by_id,
            )
            for job in jobs
        ],
        **synthesis_recovery(jobs, repo),
    }


def _failed_rung_request_id(job: dict[str, Any]) -> str | None:
    if effective_ingest_job_status(job) != "failed" or job.get("status") != "completed":
        return None
    request_id = str((job.get("payload") or {}).get("request_id") or "")
    return request_id or None


# Back-compat alias: SidecarContext + handlers import IngestJobManager.
IngestJobManager = DurableIngestJobs


def _compat_status(status: str) -> str:
    """Map the durable status vocabulary onto the legacy job vocabulary the
    existing frontend/handlers expect (queued|running|completed|failed|cancelled)."""

    return {"waiting_for_input": "running", "blocked": "failed"}.get(status, status)


def _compat(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    return {
        "id": job["id"],
        "batch_id": job.get("batch_id"),
        "source": payload.get("source"),
        "subject_id": payload.get("subject_id"),
        "mode": payload.get("mode", "canonical"),
        "status": _compat_status(job["status"]),
        "phase": job.get("phase") or job["status"],
        "message": job.get("message") or "",
        "current_window": job.get("current_window"),
        "total_windows": job.get("total_windows"),
        "created_at": job.get("created_at"),
        "updated_at": (
            job.get("finished_at")
            or job.get("heartbeat_at")
            or job.get("started_at")
            or job.get("created_at")
        ),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
        "result": job.get("result"),
        "error": job.get("error"),
    }
