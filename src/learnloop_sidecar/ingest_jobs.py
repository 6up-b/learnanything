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

    # -- wiring ------------------------------------------------------------

    def bind(
        self,
        repository: Repository,
        vault_root: Path,
        *,
        clock: Clock | None = None,
        services: RunnerServices | None = None,
        lease_ttl_seconds: int = 120,
        poll_interval_seconds: float = 1.0,
        background: bool = True,
    ) -> None:
        """Attach the wrapper to a loaded vault. Called from SidecarContext.load."""

        with self._lock:
            self._runner = IngestRunner(
                repository,
                vault_root=vault_root,
                worker_id=f"sidecar-{os.getpid()}",
                clock=clock,
                services=services,
                lease_ttl_seconds=lease_ttl_seconds,
            )
            self._background = background
            self._poll_interval = poll_interval_seconds
        # Recover anything a prior process left mid-flight before draining.
        self._runner.recover_stale_leases()

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
            batch_id = runner.enqueue_batch(
                "legacy_ingest",
                [
                    JobSpec("import", {"source": source, "subject_id": subject_id}),
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

    def enqueue_inventory(
        self,
        *,
        extraction_id: str,
        units: list[dict[str, Any]],
        subject_id: str | None = None,
        source_set_id: str | None = None,
        input_budget_tokens: int | None = None,
        priority: int = 0,
    ) -> str:
        """Enqueue a role-aware unit-inventory batch (§7). Cached units cost zero
        tokens; only semantic-hash-changed units re-inventory."""

        runner = self._require_runner()
        payload: dict[str, Any] = {"extraction_id": extraction_id, "units": units}
        if input_budget_tokens is not None:
            payload["input_budget_tokens"] = input_budget_tokens
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
        synthesis_payload: dict[str, Any] = {
            "source_set_id": source_set_id,
            "brief": dict(brief or {}),
            "mode": mode,
            # Quick Add's promise is a usable study map after its one explicit
            # confirmation, not a second hidden proposal-acceptance step.
            "apply": True,
        }
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
            idle_rounds = idle_rounds + 1 if ran == 0 else 0
            if idle_rounds >= 3 and self._active_job_locked(runner) is None:
                break
            time.sleep(self._poll_interval)

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
