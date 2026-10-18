"""The learner-text gap queue: one job per learner text, run off the request path.

A tutor answer, an applied live diagnosis and a recorded stuck answer each
enqueue a job (idempotent per source); the sidecar's post-attempt worker
drains them in its ``gaps`` slot and ``learnloop gaps run`` drains them from
the CLI (with a dry run). Leases are fenced like the post-attempt queue: a
worker whose lease was re-claimed publishes nothing. A job that fails is
retried with backoff up to :data:`MAX_ATTEMPTS` (``retry_later``: the drain
goes on to the next text, re-review F3); after that its learner text is
logged as ``failed`` (no target: the grounded rule applies).

A spend stop never finalizes a text (Codex review F2): under a command's
shared budget the job is released with its attempt refunded and the run
stops; the next run reads it. On the live path (one budget per text) the
daily cap ``learner_text_gaps.max_calls_per_day`` (F12) defers jobs to the
next UTC day once the pipeline's calls today reach it.
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
from learnloop.diagnosis.text_gaps.contract import LearnerText
from learnloop.diagnosis.text_gaps.judges import TextBudget
from learnloop.diagnosis.text_gaps.pipeline import PipelineClients, ReadingDeferred, failed_row, process_learner_text
from learnloop.diagnosis.text_gaps.sources import (
    StuckTextSource,
    attempt_grade_held,
    formative_row,
    hint_feedback_ids,
    hint_feedback_row,
    learner_text,
    missed_formative_ids,
    stuck_text_for,
    stuck_texts,
    workbench_text_ids,
    workbench_text_row,
)
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
    #: done | skipped | retry_later (this text backs off; the run goes on) |
    #: deferred (a spend stop or the daily cap: the run stops) | failed | lease_lost
    state: str
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
    clock: Clock | None = None,
) -> list[str]:
    """After a live diagnosis is applied: queue it.

    A stuck answer is queued when it is recorded (:func:`enqueue_stuck_answer`),
    whether or not it is ever diagnosed (Codex review F8). A diagnosis of a
    grade the proofs route check holds for review (mvp-0.17) is not queued: it
    would be read as a wrong answer, and nothing validated the grade.
    """

    if not pipeline_enabled(vault):
        return []
    if attempt_grade_held(repository, attempt_id):
        return []
    queued: list[str] = []
    if diagnosis.get("mode", "live") == "live" and diagnosis.get("id") and diagnosis.get("status", "completed") == "completed":
        job = enqueue(repository, source_kind="diagnosis", source_id=str(diagnosis["id"]), clock=clock)
        if job:
            queued.append(job)
    return queued


def enqueue_stuck_answer(
    vault: LoadedVault, repository: Repository, *, attempt_id: str, clock: Clock | None = None,
    stuck_source: StuckTextSource | None = None,
) -> str | None:
    """When an attempt is recorded: queue it if it is a non-empty stuck answer.

    Read through the stuck marker (:class:`StuckTextSource`), for every
    stuck answer with text: graded right or wrong, diagnosed or not, with the
    split on or off (F8). Before ``practice/stuck-prompt`` merges the default
    source has no stuck answers, so this queues nothing.
    """

    if not pipeline_enabled(vault):
        return None
    if stuck_text_for(repository, attempt_id, stuck_source) is None:
        return None
    return enqueue(repository, source_kind="stuck_answer", source_id=attempt_id, clock=clock)


def enqueue_reader_formative(
    vault: LoadedVault, repository: Repository, *, question_id: str, clock: Clock | None = None,
) -> str | None:
    """RW1b: a missed next-step, why-step or assumption answer (``reader_formative``).

    Queued only with the pipeline (``learner_text_gaps.enabled``) and the
    Reader's switch (``reader_formative.enabled``) on, and only for a missed
    answer the learner wrote (:func:`~.sources.formative_row`); a match, or a
    "show me" with no answer, queues nothing. Idempotent per question."""

    if not pipeline_enabled(vault):
        return None
    if not bool(getattr(getattr(vault.config, "reader_formative", None), "enabled", False)):
        return None
    if formative_row(repository, question_id) is None:
        return None
    return enqueue(repository, source_kind="reader_formative", source_id=question_id, clock=clock)


def enqueue_hint_feedback(
    vault: LoadedVault, repository: Repository, *, assist_id: str, clock: Clock | None = None,
) -> str | None:
    """Adaptive hints H2b: text written back to a hint on the practice screen
    (``hint_feedback``): a "doesn't connect" reply's text or an answer to a
    discriminating question, queued when its ``help_assists`` row is written,
    so a gap named mid-attempt can join the next hint's rivals (spec §9).

    Queued only with the pipeline (``learner_text_gaps.enabled``) and
    adaptive hints (``hints.adaptive_enabled``) on, and only for a row with
    text (:func:`~.sources.hint_feedback_row`); an empty reply queues
    nothing. Idempotent per row."""

    if not hint_feedback_enabled(vault):
        return None
    if hint_feedback_row(repository, assist_id) is None:
        return None
    return enqueue(repository, source_kind="hint_feedback", source_id=assist_id, clock=clock)


def enqueue_workbench_text(
    vault: LoadedVault, repository: Repository, *, source_id: str, clock: Clock | None = None,
) -> str | None:
    """Reader workbench RW2b (spec §5.2 "in-session updates", §5.6): text the
    learner wrote while working in steps (``workbench_text``), queued when it
    is written or sent: a reply or a discriminating answer when its row is
    written, a stuck step's newest version when Help, Check, Leave or Submit
    sends it. Queued only with the pipeline (``learner_text_gaps.enabled``)
    and the workbench's help (``workbench.help_enabled``) on, and only for a
    text (:func:`~.sources.workbench_text_row`). Idempotent per source."""

    if not workbench_text_enabled(vault):
        return None
    if workbench_text_row(repository, source_id) is None:
        return None
    return enqueue(repository, source_kind="workbench_text", source_id=source_id, clock=clock)


def workbench_text_enabled(vault: LoadedVault) -> bool:
    section = getattr(vault.config, "workbench", None)
    return pipeline_enabled(vault) and bool(getattr(section, "enabled", True)) and bool(
        getattr(section, "help_enabled", True))


def hint_feedback_enabled(vault: LoadedVault) -> bool:
    """Whether ``hint_feedback`` texts are queued: the pipeline and adaptive hints both on."""

    return pipeline_enabled(vault) and bool(getattr(getattr(vault.config, "hints", None), "adaptive_enabled", False))


def reconcile_hint_feedback(vault: LoadedVault, repository: Repository, *, clock: Clock | None = None) -> int:
    """Queue every ``hint_feedback`` text whose job was never written (H2b
    review F4): the reply or discriminating answer committed, and the process
    ended, or the enqueue failed, before its job did. Called when the sidecar
    opens a vault; idempotent (a text with a job or a gap is left alone), and
    it reads no text and calls no model. Returns how many it queued."""

    return sweep_backlog(vault, repository, clock=clock, kinds=("hint_feedback",))["hint_feedback"]


#: The kinds :func:`sweep_backlog` sweeps (all of them unless told).
BACKLOG_KINDS = ("stuck_answer", "tutor_question", "diagnosis", "reader_formative", "hint_feedback",
                 "workbench_text")


def sweep_backlog(vault: LoadedVault, repository: Repository, *, clock: Clock | None = None,
                  stuck_source: StuckTextSource | None = None, include_history: bool = False,
                  dry_run: bool = False, kinds: tuple[str, ...] = BACKLOG_KINDS) -> dict[str, int]:
    """Queue unread learner texts (``learnloop gaps run --backlog``).

    Stuck answers always, missed active-reading answers while
    ``reader_formative.enabled`` is on (RW1b review F7: one whose job was never
    written), and replies to hints and discriminating answers while adaptive
    hints are on (``hint_feedback``, H2b review F4); with ``include_history``
    also answered tutor questions that carry a tutor reading and completed
    live diagnoses. ``kinds`` narrows the sweep (the sidecar's start-up
    reconciliation sweeps ``hint_feedback`` only). ``dry_run`` counts what
    would be queued and writes nothing.
    """

    counts = {kind: 0 for kind in BACKLOG_KINDS}
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

    if "stuck_answer" in kinds:
        for row in stuck_texts(repository, stuck_source):
            if queue("stuck_answer", row.attempt_id):
                counts["stuck_answer"] += 1
    if "reader_formative" in kinds and bool(getattr(getattr(vault.config, "reader_formative", None), "enabled",
                                                    False)):
        for question_id in missed_formative_ids(repository):
            if queue("reader_formative", question_id):
                counts["reader_formative"] += 1
    if "hint_feedback" in kinds and hint_feedback_enabled(vault):
        for assist_id in hint_feedback_ids(repository):
            if queue("hint_feedback", assist_id):
                counts["hint_feedback"] += 1
    if "workbench_text" in kinds and workbench_text_enabled(vault):
        for assist_id in workbench_text_ids(repository):
            if queue("workbench_text", assist_id):
                counts["workbench_text"] += 1
    if include_history and {"tutor_question", "diagnosis"} & set(kinds):
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            questions = [str(row[0]) for row in connection.execute(
                "SELECT id FROM question_events WHERE answer_status = 'answered' "
                "AND source_context_json LIKE '%\"learner_gap\"%' ORDER BY created_at, id"
            )]
            diagnoses = [str(row[0]) for row in connection.execute(
                "SELECT id FROM attempt_diagnoses WHERE mode = 'live' AND status = 'completed' ORDER BY created_at, id"
            )]
        for event_id in questions if "tutor_question" in kinds else ():
            if queue("tutor_question", event_id):
                counts["tutor_question"] += 1
        for diagnosis_id in diagnoses if "diagnosis" in kinds else ():
            if queue("diagnosis", diagnosis_id):
                counts["diagnosis"] += 1
    return counts


def _later(seconds: float, clock: Clock | None) -> str:
    return (parse_utc(utc_now_iso(clock)) + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _next_day(clock: Clock | None) -> str:
    today = parse_utc(utc_now_iso(clock)).replace(hour=0, minute=0, second=0, microsecond=0)
    return (today + timedelta(days=1)).isoformat().replace("+00:00", "Z")


def calls_today(repository: Repository, *, clock: Clock | None = None) -> int:
    """The pipeline's logical model calls since today's UTC midnight (receipts)."""

    day = parse_utc(utc_now_iso(clock)).strftime("%Y-%m-%d")
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return store.pipeline_calls_since(connection, day)


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
    progress: dict[str, Any] = dict(job.get("payload") or {})

    def finish(state: str, error: str | None = None) -> bool:
        with repository.atomic():
            return store.finish_job(repository.connection(), job_id, state=state, owner=owner, epoch=epoch,
                                    now=utc_now_iso(clock), error=error)

    def release(*, not_before: str | None, error: str, refund: bool) -> bool:
        with repository.atomic():
            return store.release_job(repository.connection(), job_id, owner=owner, epoch=epoch,
                                     now=utc_now_iso(clock), not_before=not_before, error=error,
                                     refund_attempt=refund)

    def skip(reason: str, text: LearnerText | None) -> GapJobOutcome:
        return _skip(repository, job, text, vault, progress, owner=owner, epoch=epoch, clock=clock,
                     outcome=outcome, reason=reason)

    if not pipeline_enabled(vault):
        return skip("learner_text_gaps.enabled is off", None)
    if budget_factory is None:
        # The live path: one budget per text, so a daily cap across texts
        # (F12). Checked before any call; the overshoot is at most one text's
        # own cap (max_calls_per_text).
        limit = int(vault.config.learner_text_gaps.max_calls_per_day)
        if calls_today(repository, clock=clock) >= limit:
            released = release(not_before=_next_day(clock), error=f"daily_cap: max_calls_per_day {limit}",
                               refund=True)
            outcome.state = "deferred" if released else "lease_lost"
            outcome.error = "daily_cap"
            return outcome
    text = learner_text(vault, repository, outcome.source_kind, outcome.source_id, stuck_source=stuck_source)
    if text is None:
        return skip("nothing to read", None)

    def save_progress(payload: Mapping[str, Any]) -> None:
        progress.clear()
        progress.update(payload)
        with repository.atomic():
            store.save_job_payload(repository.connection(), job_id, payload, owner=owner, epoch=epoch,
                                   now=utc_now_iso(clock))

    try:
        budget = budget_factory(vault) if budget_factory is not None else None
        row = process_learner_text(
            root, repository, text, clients=clients, budget=budget, clock=clock,
            progress=dict(progress), save_progress=save_progress,
        )
    except ReadingDeferred as exc:
        if exc.spend and budget_factory is not None:
            # The command's shared budget ran out, not this text: released
            # untouched (attempt refunded) for the next run; the run stops.
            released = release(not_before=None, error=f"deferred: {exc.reason}"[:500], refund=True)
            outcome.state = "deferred" if released else "lease_lost"
            outcome.error = exc.reason
            return outcome
        return _retry_or_fail(repository, job, text, vault, progress, owner=owner, epoch=epoch, clock=clock,
                              outcome=outcome, error=f"{type(exc).__name__}: {exc}"[:500])
    except Exception as exc:  # noqa: BLE001 - retried with backoff, then logged as failed
        LOG.warning("learner-text gap job %s failed", job_id, exc_info=True)
        return _retry_or_fail(repository, job, text, vault, progress, owner=owner, epoch=epoch, clock=clock,
                              outcome=outcome, error=f"{type(exc).__name__}: {exc}"[:500])
    if row is None:
        return skip("learner_text_gaps.enabled is off", text)
    if not finish("done"):
        outcome.state = "lease_lost"
    outcome.gap_id, outcome.action = str(row["id"]), str(row["action"])
    return outcome


def _retry_or_fail(
    repository: Repository, job: Mapping[str, Any], text: Any, vault: LoadedVault, progress: Mapping[str, Any], *,
    owner: str, epoch: int, clock: Clock | None, outcome: GapJobOutcome, error: str,
) -> GapJobOutcome:
    """Back off and retry; after the last attempt log the text as ``failed``,
    naming whatever its earlier attempts already wrote (F3)."""

    job_id = str(job["id"])
    if int(job["attempt_count"]) >= MAX_ATTEMPTS:
        with repository.atomic():
            connection = repository.connection()
            if store.holds_job(connection, job_id, owner=owner, epoch=epoch) and store.gap_for_source(
                connection, text.source_kind, text.source_id
            ) is None:
                store.insert_gap(connection, failed_row(text, vault=load_vault(vault.root), error=error,
                                                        now_iso=utc_now_iso(clock), progress=progress))
            store.finish_job(connection, job_id, state="failed", owner=owner, epoch=epoch,
                             now=utc_now_iso(clock), error=error)
        outcome.state, outcome.error = "failed", error
        return outcome
    with repository.atomic():
        released = store.release_job(repository.connection(), job_id, owner=owner, epoch=epoch,
                                     now=utc_now_iso(clock),
                                     not_before=_later(BACKOFF_SECONDS * int(job["attempt_count"]), clock),
                                     error=error)
    outcome.state = "retry_later" if released else "lease_lost"
    outcome.error = error
    return outcome


#: ``context_judge`` of each source (a text gone since it was queued is
#: logged with an empty text).
_CONTEXT_JUDGE = {"tutor_question": "tutor", "diagnosis": "diagnoser", "stuck_answer": "gap_reader",
                  "reader_formative": "gap_reader", "workbench_text": "gap_reader", "hint_feedback": "gap_reader"}


def _skip(
    repository: Repository, job: Mapping[str, Any], text: LearnerText | None, vault: LoadedVault,
    progress: Mapping[str, Any], *, owner: str, epoch: int, clock: Clock | None, outcome: GapJobOutcome,
    reason: str,
) -> GapJobOutcome:
    """The job reads nothing more: the pipeline is switched off, or the text
    is gone.

    When an earlier attempt already wrote to the vault (its progress names a
    created LO or an edge that is on disk), the text is logged ``failed``
    naming the write (re-review F1): the daily creation cap counts it and
    ``learnloop gaps undo`` reaches it. No paid call finishes it while the
    switch is off. Otherwise the job is ``skipped``.
    """

    job_id, now = str(job["id"]), utc_now_iso(clock)
    row = None
    if (progress.get("created") or {}).get("learning_object_id") or (progress.get("edge") or {}).get("edge_id"):
        logged = text or LearnerText(
            source_kind=outcome.source_kind, source_id=outcome.source_id, text="",
            context_judge=_CONTEXT_JUDGE[outcome.source_kind], created_at=now,
        )
        row = failed_row(logged, vault=load_vault(vault.root), error=reason, now_iso=now, progress=progress)
        if not (row["created_learning_object_id"] or row["edge_id"]):
            row = None  # recorded, never written
    logged_failed = False
    with repository.atomic():
        connection = repository.connection()
        if row is not None and store.holds_job(connection, job_id, owner=owner, epoch=epoch) and store.gap_for_source(
            connection, outcome.source_kind, outcome.source_id
        ) is None:
            outcome.gap_id, outcome.action = store.insert_gap(connection, row), "failed"
            logged_failed = True
        finished = store.finish_job(connection, job_id, state="failed" if logged_failed else "skipped",
                                    owner=owner, epoch=epoch, now=now, error=reason)
    if not finished:
        outcome.state = "lease_lost"
    elif logged_failed:
        outcome.state, outcome.error = "failed", f"{reason} after an earlier attempt wrote to the vault"
    else:
        outcome.state = "skipped"
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
        # One text backing off (``retry_later``) never stops the drain
        # (re-review F3); a spend stop or the daily cap does.
        if result.state in ("deferred", "lease_lost"):
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
        "live_daily_cap": {"max_calls_per_day": int(config.max_calls_per_day),
                           "calls_today": calls_today(repository)},
        "max_calls_ceiling": len(jobs) * int(config.max_calls_per_text),
        "max_metered_usd_ceiling": round(len(jobs) * float(config.max_usd_per_text), 4),
        "note": "a ceiling, not an estimate: most texts are 'none' and make two calls (the reading, the Decider)",
    }


__all__ = [
    "GapJobOutcome",
    "LEASE_SECONDS",
    "MAX_ATTEMPTS",
    "calls_today",
    "enqueue",
    "enqueue_after_diagnosis",
    "enqueue_stuck_answer",
    "enqueue_tutor_question",
    "enqueue_workbench_text",
    "pending_jobs",
    "pipeline_enabled",
    "plan",
    "process_next_gap_job",
    "run_pending",
    "reconcile_hint_feedback",
    "sweep_backlog",
    "workbench_text_enabled",
]
