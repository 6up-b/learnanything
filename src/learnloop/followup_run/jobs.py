"""The follow-up generation worker (spec §5 item 1, §8).

Its own slot, apart from the strictly ordered diagnosis worker, so later diagnoses are
never delayed. One job per deduplicated key: a workflow, an entered episode, a recorded
need. That is the structural bound on physical generation on a subscription route, where
dollar reservations bound nothing; retries are admitted by the workflow, up to
:data:`MAX_GENERATION_ATTEMPTS`.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import timedelta
import logging
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.db.stores import followup_serve as store
from learnloop.followup_serve import workflow as wf
from learnloop.followup_serve import queue
from learnloop.followup_serve.gates import generate_and_serve_on

LOG = logging.getLogger(__name__)

#: A job's lease: a generation is one structured model call with its checks.
LEASE_SECONDS = 900.0
#: One generation per workflow or need, and at most this many physical runs of it:
#: the first, and one retry after a transient failure. A structural bound (spec §8).
MAX_GENERATION_ATTEMPTS = 2
#: The pause before that retry: long enough for a transient provider failure to pass,
#: short against the learner's wait.
RETRY_BACKOFF_SECONDS = 20.0


class GenerationDeferred(RuntimeError):
    """The route is not ready: nothing was spent, and the job may run again."""


@dataclass
class JobOutcome:
    job_id: str
    kind: str
    state: str
    error: str | None = None
    workflow_id: str | None = None


def _iso_after(clock: Clock | None, seconds: float) -> str:
    now = parse_utc(utc_now_iso(clock))
    return (now + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def process_next_job(
    vault: Any,
    repository: Repository,
    *,
    owner: str,
    clients: Any = None,
    cancelled: Callable[[], bool] | None = None,
    clock: Clock | None = None,
) -> JobOutcome | None:
    """Lease and run the next runnable job; None when none is."""

    if cancelled is not None and cancelled():
        return None
    now = utc_now_iso(clock)
    with repository.atomic(), repository.connection() as connection:
        job = store.lease_next_generation_job(
            connection, owner=owner, now=now, lease_expires_at=_iso_after(clock, LEASE_SECONDS),
        )
    if job is None:
        return None
    outcome = JobOutcome(job_id=str(job["id"]), kind=str(job["kind"]), state="done",
                         workflow_id=job.get("workflow_id"))
    try:
        if not generate_and_serve_on(vault.config):
            _finish(repository, job, "skipped", "switch_off", clock)
            outcome.state, outcome.error = "skipped", "switch_off"
            return outcome
        _run(vault, repository, job, clients=clients, clock=clock)
        _finish(repository, job, "done", None, clock)
        return outcome
    except GenerationDeferred as deferred:
        return _retry_or_fail(vault, repository, job, outcome, str(deferred), clock)
    except Exception as exc:  # noqa: BLE001 - a job's failure is a typed outcome, never the worker's
        LOG.warning("follow-up generation job %s failed", job["id"], exc_info=True)
        return _retry_or_fail(vault, repository, job, outcome, type(exc).__name__, clock)


def _finish(repository: Repository, job: Mapping[str, Any], state: str, error: str | None, clock: Clock | None,
            *, not_before: str | None = None) -> bool:
    with repository.atomic(), repository.connection() as connection:
        return store.finish_generation_job(
            connection, job, state=state, at=utc_now_iso(clock), error=error, not_before=not_before,
        )


def _retry_or_fail(vault: Any, repository: Repository, job: Mapping[str, Any], outcome: JobOutcome, error: str,
                   clock: Clock | None) -> JobOutcome:
    outcome.error = error
    if int(job.get("attempt_count") or 0) < MAX_GENERATION_ATTEMPTS:
        _finish(repository, job, "queued", error, clock, not_before=_iso_after(clock, RETRY_BACKOFF_SECONDS))
        outcome.state = "retry"
        return outcome
    _finish(repository, job, "failed", error, clock)
    outcome.state = "failed"
    if job.get("workflow_id"):
        fail_workflow(vault, repository, str(job["workflow_id"]), reason=error, clock=clock)
    return outcome


def fail_workflow(vault: Any, repository: Repository, workflow_id: str, *, reason: str, clock: Clock | None) -> None:
    """§6.2: nothing passed. Next continues the plan, feedback is released, and the need
    stays open for background generation, deduplicated, cancelled if the hypotheses close."""

    row = wf.get(repository, workflow_id)
    if row is None:
        return
    if wf.move(repository, workflow_id, to_state=wf.FAILED, reason=reason, release=wf.RELEASE_GENERATION_FAILED,
               clock=clock) and row.get("factor_id"):
        queue.enqueue_factor(repository, str(row["factor_id"]), workflow_id=workflow_id, clock=clock)


def _run(vault: Any, repository: Repository, job: Mapping[str, Any], *, clients: Any, clock: Clock | None) -> None:
    kind = str(job["kind"])
    if kind == "workflow":
        _run_workflow(vault, repository, str(job["workflow_id"]), clients=clients, clock=clock)
    # The other kinds join in their own stage.


def _run_workflow(vault: Any, repository: Repository, workflow_id: str, *, clients: Any, clock: Clock | None) -> None:
    from learnloop.diagnosis.split.jobs import DONE, diagnosis_status
    from learnloop.followup_run.lanes import select_lane, settle_practice_lane
    row = wf.get(repository, workflow_id)
    if row is None or row["state"] != wf.PENDING:
        return
    if wf.superseded(repository, row):
        wf.move(repository, workflow_id, to_state=wf.SKIPPED, reason="newer_grade", release=wf.RELEASE_FALLBACK,
                clock=clock)
        return
    attempt_id = str(row["source_attempt_id"])
    blind = repository.latest_blind_grade_record(attempt_id) is not None
    if blind and diagnosis_status(repository, attempt_id)["status"] != DONE:
        # §6.2: failed, skipped or released for readiness: one fallback, from the grade alone.
        settle_practice_lane(vault, repository, row, reason="diagnosis_unavailable", release=wf.RELEASE_FALLBACK,
                                clock=clock)
        return
    choice = select_lane(repository, row)
    if choice.lane != wf.LANE_PROBE:
        settle_practice_lane(vault, repository, row, reason=choice.reason, clock=clock)
        return
    wf.set_fields(repository, workflow_id, lane=wf.LANE_PROBE, factor_id=choice.factor_id, clock=clock)


__all__ = [
    "GenerationDeferred", "JobOutcome", "LEASE_SECONDS", "MAX_GENERATION_ATTEMPTS", "RETRY_BACKOFF_SECONDS",
    "fail_workflow", "process_next_job",
]
