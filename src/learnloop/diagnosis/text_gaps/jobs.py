"""The learner-text gap queue: one job per learner text, run off the request path.

A tutor answer, an applied live diagnosis and a stuck answer each enqueue a
job (idempotent per source); the sidecar's post-attempt worker drains them in
its ``gaps`` slot and ``learnloop gaps run`` drains them from the CLI (with a
dry run). Leases are fenced like the post-attempt queue: a worker whose lease
was re-claimed publishes nothing. A job that fails is retried with backoff up
to :data:`MAX_ATTEMPTS`; after that its learner text is logged as ``failed``
(no target: the grounded rule applies).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from contextlib import closing
from dataclasses import dataclass
from datetime import timedelta
import logging
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import learner_gaps as store
from learnloop.diagnosis.text_gaps.judges import TextBudget
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, failed_row, process_learner_text
from learnloop.diagnosis.text_gaps.sources import StuckTextSource, learner_text, stuck_texts
from learnloop.vault.loader import load_vault
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)

#: A creation (draft, vault writes, the seed's promotion) can take minutes.
LEASE_SECONDS = 1_800
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = 60


@dataclass
class GapJobOutcome:
    job_id: str
    source_kind: str
    source_id: str
    state: str  # done | skipped | released | failed | lease_lost
    gap_id: str | None = None
    action: str | None = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"job_id": self.job_id, "source_kind": self.source_kind, "source_id": self.source_id,
                "state": self.state, "gap_id": self.gap_id, "action": self.action, "error": self.error}


def pipeline_enabled(vault: LoadedVault) -> bool:
    return bool(vault.config.learner_text_gaps.enabled)


def enqueue(repository: Repository, *, source_kind: str, source_id: str, clock: Clock | None = None) -> str | None:
    with repository.atomic():
        return store.enqueue_job(repository.connection(), source_kind=source_kind, source_id=source_id,
                                 now=utc_now_iso(clock))


def enqueue_tutor_question(vault: LoadedVault, repository: Repository, event_id: str, *,
                           clock: Clock | None = None) -> str | None:
    """After the tutor answered: queue the question (switch on only)."""

    if not pipeline_enabled(vault):
        return None
    return enqueue(repository, source_kind="tutor_question", source_id=event_id, clock=clock)


def enqueue_after_diagnosis(
    vault: LoadedVault, repository: Repository, *, attempt_id: str, diagnosis: Mapping[str, Any],
    clock: Clock | None = None, stuck_source: StuckTextSource | None = None,
) -> list[str]:
    """After a live diagnosis is applied: queue it, and its stuck text if any."""

    if not pipeline_enabled(vault):
        return []
    queued: list[str] = []
    if diagnosis.get("mode", "live") == "live" and diagnosis.get("id") and diagnosis.get("status", "completed") == "completed":
        job = enqueue(repository, source_kind="diagnosis", source_id=str(diagnosis["id"]), clock=clock)
        if job:
            queued.append(job)
    if any(row.attempt_id == attempt_id for row in stuck_texts(repository, stuck_source)):
        job = enqueue(repository, source_kind="stuck_answer", source_id=attempt_id, clock=clock)
        if job:
            queued.append(job)
    return queued


def sweep_backlog(vault: LoadedVault, repository: Repository, *, clock: Clock | None = None,
                  stuck_source: StuckTextSource | None = None, include_history: bool = False,
                  dry_run: bool = False) -> dict[str, int]:
    """Queue unread learner texts (``learnloop gaps run --backlog``).

    Stuck answers always; with ``include_history`` also answered tutor
    questions that carry a tutor reading and completed live diagnoses.
    ``dry_run`` counts what would be queued and writes nothing.
    """

    counts = {"stuck_answer": 0, "tutor_question": 0, "diagnosis": 0}
    if not pipeline_enabled(vault):
        return counts
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        known = {(job["source_kind"], job["source_id"]) for job in store.jobs(connection)}
        known |= {(row["source_kind"], row["source_id"]) for row in store.gaps(connection)}

    def queue(source_kind: str, source_id: str) -> bool:
        if (source_kind, source_id) in known:
            return False
        known.add((source_kind, source_id))
        return True if dry_run else bool(enqueue(repository, source_kind=source_kind, source_id=source_id, clock=clock))

    for row in stuck_texts(repository, stuck_source):
        if queue("stuck_answer", row.attempt_id):
            counts["stuck_answer"] += 1
    if include_history:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            questions = [str(row[0]) for row in connection.execute(
                "SELECT id FROM question_events WHERE answer_status = 'answered' "
                "AND source_context_json LIKE '%\"learner_gap\"%' ORDER BY created_at, id"
            )]
            diagnoses = [str(row[0]) for row in connection.execute(
                "SELECT id FROM attempt_diagnoses WHERE mode = 'live' AND status = 'completed' ORDER BY created_at, id"
            )]
        for event_id in questions:
            if queue("tutor_question", event_id):
                counts["tutor_question"] += 1
        for diagnosis_id in diagnoses:
            if queue("diagnosis", diagnosis_id):
                counts["diagnosis"] += 1
    return counts


def _later(seconds: float, clock: Clock | None) -> str:
    return (parse_utc(utc_now_iso(clock)) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def process_next_gap_job(
    root: Path,
    repository: Repository,
    *,
    owner: str,
    clients: PipelineClients | None = None,
    budget_factory: Callable[[LoadedVault], TextBudget] | None = None,
    clock: Clock | None = None,
    source: tuple[str, str] | None = None,
    stuck_source: StuckTextSource | None = None,
) -> GapJobOutcome | None:
    """Lease and run the next runnable gap job (or ``source``'s); None when none is."""

    with repository.atomic():
        job = store.lease_next_job(repository.connection(), owner=owner, now=utc_now_iso(clock),
                                   lease_seconds=LEASE_SECONDS, source=source)
    if job is None:
        return None
    job_id, epoch = str(job["id"]), int(job["lease_epoch"])
    outcome = GapJobOutcome(job_id, str(job["source_kind"]), str(job["source_id"]), "done")
    vault = load_vault(root)

    def finish(state: str, error: str | None = None) -> bool:
        with repository.atomic():
            return store.finish_job(repository.connection(), job_id, state=state, owner=owner, epoch=epoch,
                                    now=utc_now_iso(clock), error=error)

    def save_progress(payload: Mapping[str, Any]) -> None:
        with repository.atomic():
            store.save_job_payload(repository.connection(), job_id, payload, owner=owner, epoch=epoch,
                                   now=utc_now_iso(clock))

    if not pipeline_enabled(vault):
        finish("skipped", "learner_text_gaps.enabled is off")
        outcome.state = "skipped"
        return outcome
    text = learner_text(vault, repository, outcome.source_kind, outcome.source_id, stuck_source=stuck_source)
    if text is None:
        finish("skipped", "nothing to read")
        outcome.state = "skipped"
        return outcome
    try:
        budget = budget_factory(vault) if budget_factory is not None else None
        row = process_learner_text(
            root, repository, text, clients=clients, budget=budget, clock=clock,
            progress=job.get("payload") or {}, save_progress=save_progress,
        )
    except Exception as exc:  # noqa: BLE001 - retried with backoff, then logged as failed
        LOG.warning("learner-text gap job %s failed", job_id, exc_info=True)
        error = f"{type(exc).__name__}: {exc}"[:500]
        if int(job["attempt_count"]) >= MAX_ATTEMPTS:
            with repository.atomic():
                connection = repository.connection()
                if store.holds_job(connection, job_id, owner=owner, epoch=epoch) and store.gap_for_source(
                    connection, text.source_kind, text.source_id
                ) is None:
                    store.insert_gap(connection, failed_row(text, vault=vault, error=error, now_iso=utc_now_iso(clock)))
                store.finish_job(connection, job_id, state="failed", owner=owner, epoch=epoch,
                                 now=utc_now_iso(clock), error=error)
            outcome.state, outcome.error = "failed", error
            return outcome
        with repository.atomic():
            released = store.release_job(repository.connection(), job_id, owner=owner, epoch=epoch,
                                         now=utc_now_iso(clock), not_before=_later(BACKOFF_SECONDS * int(job["attempt_count"]), clock),
                                         error=error)
        outcome.state = "released" if released else "lease_lost"
        outcome.error = error
        return outcome
    if row is None:
        finish("skipped", "learner_text_gaps.enabled is off")
        outcome.state = "skipped"
        return outcome
    if not finish("done"):
        outcome.state = "lease_lost"
    outcome.gap_id, outcome.action = str(row["id"]), str(row["action"])
    return outcome


def run_pending(
    root: Path, repository: Repository, *, owner: str, max_jobs: int = 50, **kwargs: Any,
) -> list[GapJobOutcome]:
    outcomes: list[GapJobOutcome] = []
    while len(outcomes) < max_jobs:
        result = process_next_gap_job(root, repository, owner=owner, **kwargs)
        if result is None:
            break
        outcomes.append(result)
        if result.state in ("released", "lease_lost"):
            break
    return outcomes


def pending_jobs(repository: Repository) -> list[dict[str, Any]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.jobs(connection, states=("queued", "leased"))


def plan(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """A no-call plan of the queue: what would be read and the call ceiling."""

    jobs = pending_jobs(repository)
    config = vault.config.learner_text_gaps
    by_source: dict[str, int] = {}
    for job in jobs:
        by_source[job["source_kind"]] = by_source.get(job["source_kind"], 0) + 1
    from learnloop.ai.routing import provider_for_task

    routes = {
        task: provider_for_task(vault.config, task).provider_name
        for task in ("learner_gap_judge", "learner_gap_reader", "learner_gap_decider", "authoring", "tutor_qa")
    }
    return {
        "queued": len(jobs),
        "by_source": by_source,
        "enabled": bool(config.enabled),
        "chooser": config.chooser,
        "decider_enabled": bool(config.decider_enabled),
        "routes": routes,
        "embedding_enabled": bool(vault.config.embedding.enabled),
        "per_text_caps": {"max_calls": int(config.max_calls_per_text), "max_usd": float(config.max_usd_per_text)},
        "max_calls_ceiling": len(jobs) * int(config.max_calls_per_text),
        "max_metered_usd_ceiling": round(len(jobs) * float(config.max_usd_per_text), 4),
        "note": "a ceiling, not an estimate: most texts are 'none' and make two calls (the reading, the Decider)",
    }


__all__ = [
    "GapJobOutcome",
    "LEASE_SECONDS",
    "MAX_ATTEMPTS",
    "enqueue",
    "enqueue_after_diagnosis",
    "enqueue_tutor_question",
    "pending_jobs",
    "pipeline_enabled",
    "plan",
    "process_next_gap_job",
    "run_pending",
    "sweep_backlog",
]
