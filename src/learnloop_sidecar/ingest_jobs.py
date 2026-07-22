"""Durable single-source ingest, hosted by the sidecar (spec §6.2).

This is the thin compatibility wrapper that replaced the old in-memory /
subprocess job manager. The sidecar-facing API (``start``/``get``/``list``/
``cancel``/``needs_reload``/``mark_reloaded``/``shutdown``) is unchanged, but the
job now lives in the durable queue (``ingest_batches``/``ingest_jobs``): a single
``legacy_ingest`` batch that survives restarts. A background drain thread hosts
the runner while the app is open; on next open, ``IngestRunner.recover_stale_leases``
resumes anything left unfinished.

Determinism: ``bind(..., background=False)`` disables the thread so tests drain
synchronously via ``drain_foreground()`` with stubbed :class:`RunnerServices`.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from typing import Any, Literal

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.services.ingest_runner import IngestRunner, JobSpec, RunnerServices

_LEGACY_JOB_TYPES = ("legacy_ingest", "exam_ingest")
# Job types whose completion can change vault content (an applied study map or
# canonical note). The sidecar must reload its in-memory vault after one of
# these finishes in the background drain, or screens that read the loaded vault
# (Today, knowledge map) keep serving the pre-apply snapshot.
_APPLYING_JOB_TYPES = (
    "legacy_ingest",
    "exam_ingest",
    "bootstrap_synthesis",
    "append_synthesis",
    # Reader-driven progressive generation auto-applies grounded items.
    "practice_expansion",
    # Learner-requested easier/harder variants auto-apply when grounded.
    "rung_variant",
)
_ACTIVE_STATUSES = {"queued", "running", "waiting_for_input"}
_RECENT_LIMIT = 30

# Quick-add build batches drain ahead of bulk import/inventory batches (§1). The
# drain orders by batch priority DESC first, so anything above the default 0
# jumps the queue between checkpoints. Bulk batches stay at 0.
QUICK_ADD_PRIORITY = 100


class ActiveIngestJobError(RuntimeError):
    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Ingest job {job_id} is already running.")


class DurableIngestJobs:
    """Enqueues single-source ingests into the durable queue and reads their state."""

    def __init__(self) -> None:
        self._runner: IngestRunner | None = None
        self._lock = threading.RLock()
        self._reloaded: set[str] = set()
        self._background = True
        self._poll_interval = 1.0
        self._worker_thread: threading.Thread | None = None
        self._stop = threading.Event()
        # Demand-paged reader synthesis: the same worker thread drains queued
        # reader_background_requests with a real model client (spec §6.4 — the
        # drain was previously never invoked, so requests sat queued forever).
        self._reader_synth_client_factory: Any = None
        self._reader_client: Any = None
        self._reader_client_checked = False

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
        background: bool = True,
        reader_synth_client_factory: Any = None,
    ) -> None:
        """Attach the wrapper to a loaded vault. Called from SidecarContext.load."""

        with self._lock:
            self._reader_synth_client_factory = reader_synth_client_factory
            self._reader_client = None
            self._reader_client_checked = False
            self._runner = IngestRunner(
                repository,
                vault_root=vault_root,
                worker_id=f"sidecar-{os.getpid()}",
                clock=clock,
                services=services,
                lease_ttl_seconds=lease_ttl_seconds,
                heartbeat_interval_seconds=heartbeat_interval_seconds,
            )
            self._background = background
            self._poll_interval = poll_interval_seconds
        # Recover anything a prior process left mid-flight before draining.
        self._runner.recover_stale_leases()
        # Jobs that finished before this bind are already reflected in the vault
        # load that accompanies it; only jobs completing AFTER this point should
        # trigger a reload from the batch-polling handlers.
        for job in self._runner.repo.ingest_jobs_by_types(_APPLYING_JOB_TYPES):
            if job["status"] == "completed":
                self._reloaded.add(job["id"])

    def _require_runner(self) -> IngestRunner:
        if self._runner is None:
            raise RuntimeError("Ingest jobs are not bound to a vault yet.")
        return self._runner

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
            if pdf_engine in ("marker", "pypdf"):
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
            runner.cancel_batch(job["batch_id"])
            job = runner.repo.get_ingest_job(job_id)
        return _compat(job) if job is not None else None

    def needs_reload(self, job_id: str) -> bool:
        runner = self._require_runner()
        job = runner.repo.get_ingest_job(job_id)
        return bool(job and job["status"] == "completed" and job_id not in self._reloaded)

    def mark_reloaded(self, job_id: str) -> None:
        self._reloaded.add(job_id)

    def shutdown(self) -> None:
        self._stop.set()
        thread = self._worker_thread
        if thread is not None:
            thread.join(timeout=2)

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
            if pdf_engine in ("marker", "pypdf"):
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

    def enqueue_reader_quick_check(self, *, extraction_id: str, section_id: str) -> str:
        """Enqueue one section's quick-check authoring (reader producer slice).

        Interactive priority (quick-add band) so a reader-initiated question
        drains ahead of bulk batches; the handler is idempotent per section so
        duplicate enqueues while one is queued/running resolve without a second
        model call."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "reader_quick_check",
            [JobSpec("reader_quick_check", {"extraction_id": extraction_id, "section_id": section_id})],
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
    ) -> str:
        """Enqueue per-LO practice generation (reader-first progressive seeding).

        Background priority (default band): generation after a section completes
        must never starve reader quick-checks or interactive quick-add builds."""

        runner = self._require_runner()
        batch_id = runner.enqueue_batch(
            "practice_expansion",
            [
                JobSpec(
                    "practice_expansion",
                    {
                        "learning_object_ids": list(learning_object_ids),
                        "reason": reason or "reader_section_completed",
                    },
                )
            ],
            subject_id=subject_id,
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
        priority: int = QUICK_ADD_PRIORITY,
    ) -> str:
        """Enqueue the Quick-add build batch (§1): inventory(selected units) then
        bootstrap_synthesis over the freshly-created source set, as one batch that
        drains ahead of bulk work. The synthesis job depends on the inventory job,
        so gates only run once the selected units carry inventories."""

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
        batch_id = runner.enqueue_batch(
            "bootstrap_synthesis",
            [
                JobSpec("inventory", inventory_payload),
                JobSpec("bootstrap_synthesis", synthesis_payload, depends_on=(0,)),
            ],
            subject_id=subject_id,
            source_set_id=source_set_id,
            priority=priority,
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
        unlimited_token_budget: bool = False,
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
        units are ``[{unit_id, role, profile?}]`` (the inventory job's shape)."""

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
        if unlimited_token_budget:
            synthesis_payload["unlimited_token_budget"] = True
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
        change_kind: str = "source_added",
        subject_id: str | None = None,
        brief: dict[str, Any] | None = None,
        input_budget_tokens: int | None = None,
        output_budget_tokens: int | None = None,
        unlimited_token_budget: bool = False,
        priority: int = QUICK_ADD_PRIORITY,
    ) -> str:
        """Enqueue a bounded-neighborhood APPEND batch for a collection whose subject
        already carries a study map (§10). One inventory job per NEW (not-yet-synthesized)
        member — same scoping/roles shape as the bootstrap build — followed by a single
        ``append_synthesis`` job that depends on all of them and reconciles ONLY the new
        material against the existing map through the bounded affected neighborhood. The
        map is never resent or rebuilt; ``new_revision_ids`` pins the append scope.

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
        synthesis_jobs = [
            job for job in jobs
            if job["job_type"] in {"bootstrap_synthesis", "append_synthesis"}
            and job["status"] in {"failed", "blocked", "cancelled"}
        ]
        if len(synthesis_jobs) != 1:
            raise ValueError("batch must contain exactly one unfinished synthesis job")
        if any(job["job_type"] == "inventory" and job["status"] != "completed" for job in jobs):
            raise ValueError("all inventory jobs must be completed before retrying synthesis")

        synthesis_job = synthesis_jobs[0]
        payload = dict(synthesis_job.get("payload") or {})
        payload.pop("reuse_candidate", None)
        payload.pop("synthesis_run_id", None)
        payload.pop("repair_candidate", None)
        payload.pop("repair_ops", None)
        payload["unlimited_token_budget"] = unlimited_token_budget
        if (repair_candidate or repair_ops) and not reuse_candidate:
            raise ValueError("candidate repair requires reuse_candidate")
        if reuse_candidate:
            details = ((synthesis_job.get("error") or {}).get("details")) or {}
            synthesis_run_id = str(details.get("synthesis_run_id") or "")
            if not details.get("candidate_preserved") or not synthesis_run_id:
                raise ValueError(
                    "the failed synthesis attempt preserved no candidate; retry synthesis instead"
                )
            run = runner.repo.synthesis_run(synthesis_run_id)
            if run is None or not run.get("candidate_output"):
                raise ValueError(
                    "the preserved candidate is no longer available; retry synthesis instead"
                )
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
        views: list[dict[str, Any]] = []
        for batch in runner.repo.list_ingest_batches(limit=limit):
            views.append(_batch_view(batch, runner.repo.ingest_jobs_for_batch(batch["id"]), runner.repo))
        return views

    def cancel_batch(self, batch_id: str) -> dict[str, Any] | None:
        runner = self._require_runner()
        if runner.repo.get_ingest_batch(batch_id) is None:
            return None
        runner.cancel_batch(batch_id)
        return self.get_batch(batch_id)

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
            if self._worker_thread is not None and self._worker_thread.is_alive():
                return
            self._stop.clear()
            self._worker_thread = threading.Thread(
                target=self._worker_loop, name="learnloop-ingest-drain", daemon=True
            )
            self._worker_thread.start()

    def _worker_loop(self) -> None:
        runner = self._runner
        if runner is None:
            return
        idle_rounds = 0
        while not self._stop.is_set():
            try:
                ran = runner.drain()
            except Exception:  # noqa: BLE001 — the drain thread must never die silently on one bad job
                ran = 0
            try:
                ran += self._drain_reader_requests(runner)
            except Exception:  # noqa: BLE001 — reader synthesis must never kill the ingest drain
                pass
            idle_rounds = idle_rounds + 1 if ran == 0 else 0
            if idle_rounds >= 3 and self._active_job_locked(runner) is None:
                break
            time.sleep(self._poll_interval)

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

        from learnloop.services import reader_requests as RR

        if not runner.repo.has_queued_reader_requests():
            return 0
        client = self._resolve_reader_client(runner)
        if client is None:
            return 0
        result = RR.drain_requests(
            runner.repo,
            worker_id=f"sidecar-{os.getpid()}",
            synthesize=RR.model_synthesis(client),
            limit=3,
        )
        return len(result["completed"]) + len(result["failed"]) + len(result["partial"])

    def _resolve_reader_client(self, runner: IngestRunner) -> Any:
        with self._lock:
            if self._reader_client_checked:
                return self._reader_client
            factory = self._reader_synth_client_factory
        if factory is not None:
            client = factory()
        else:
            try:
                from learnloop.codex.client import make_codex_client
                from learnloop.codex.runtime import check_codex_runtime
                from learnloop.vault.loader import load_vault

                vault = load_vault(runner.vault_root)
                runtime = check_codex_runtime(runner.vault_root, vault.config.codex)
                client = (
                    make_codex_client(vault.config.codex, runner.vault_root)
                    if runtime.ready else None
                )
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


from learnloop.services.ingest_runner import CHECKPOINT_LADDER  # noqa: E402


def _job_view(job: dict[str, Any], repo: Repository) -> dict[str, Any]:
    """One job as the Batch-progress screen needs it: the checkpoint ladder, live
    phase/window counts, actual usage, and any waiting_for_input payload (§5.7)."""

    result = job.get("result") or {}
    waiting_payload = result.get("waiting_for_input") if isinstance(result, dict) else None
    payload = job.get("payload") or {}
    return {
        "id": job["id"],
        "batch_id": job["batch_id"],
        "ordinal": job["ordinal"],
        "job_type": job["job_type"],
        "status": job["status"],
        "phase": job.get("phase"),
        "message": job.get("message"),
        "current_window": job.get("current_window"),
        "total_windows": job.get("total_windows"),
        "attempt_count": job.get("attempt_count", 0),
        "checkpoint_ladder": list(CHECKPOINT_LADDER),
        "usage": job.get("usage") or {},
        "estimate": payload.get("estimate") or {},
        "source": payload.get("source"),
        "result": None if waiting_payload is not None else (result or None),
        "error": job.get("error"),
        "waiting_for_input": waiting_payload,
        "depends_on": repo.ingest_job_dependency_ids(job["id"]),
    }


def _batch_view(batch: dict[str, Any], jobs: list[dict[str, Any]], repo: Repository) -> dict[str, Any]:
    return {
        "id": batch["id"],
        "workflow_type": batch["workflow_type"],
        "subject_id": batch.get("subject_id"),
        "source_set_id": batch.get("source_set_id"),
        "status": batch["status"],
        "cancel_requested": bool(batch.get("cancel_requested")),
        "created_at": batch.get("created_at"),
        "started_at": batch.get("started_at"),
        "finished_at": batch.get("finished_at"),
        "jobs": [_job_view(job, repo) for job in jobs],
    }


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
