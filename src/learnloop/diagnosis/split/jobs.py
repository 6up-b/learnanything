"""The asynchronous post-attempt jobs of the live split (Slice 1 §5.1, §7, §11).

``diagnose`` jobs run strictly in attempt-completion order (materialization,
factors and registry promotion depend on earlier diagnoses); ``embed`` jobs are
unordered and best effort. Every job is lease-fenced (``post_attempt_jobs``):
a crash mid-job leaves it reclaimable when the lease expires, and a worker
whose lease was re-claimed writes nothing. The diagnosis row and its context
receipt are written in one transaction that first checks the lease, so each
diagnosis job appends at most one diagnosis (C5).

The worker (sidecar thread, ``learnloop diagnose drain``, the CLI/TUI inline
path) calls :func:`process_next_job`; everything else here is shared with them.
Replay never calls this module (S7).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable, Mapping

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import record_model_calls
from learnloop.ai.runs import finish_agent_run
from learnloop.attempts.blind_grading import split_grading_active
from learnloop.attempts.grading import resolved_rubric
from learnloop.clock import Clock, SystemClock, parse_utc, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.diagnosis.split.diagnoser import DiagnosisOutcome, run_diagnosis
from learnloop.diagnosis.split.live import (
    build_causal_view,
    current_attempt_for,
    joint_grade_record,
    live_history_store,
    needs_diagnosis,
    sampled_correct_answer,
    settings_from_config,
)
from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION
from learnloop.ids import new_ulid
from learnloop.substrate.canonical_projection import project_canonical_facet_state
from learnloop.vault.models import LoadedVault

LOG = logging.getLogger(__name__)

DIAGNOSE_KIND = "diagnose"
EMBED_KIND = "embed"
#: A diagnosis runs one model turn; a lease outlives the request timeout.
DIAGNOSE_LEASE_SECONDS = 1_200
EMBED_LEASE_SECONDS = 300
BACKOFF_BASE_SECONDS = 30
BACKOFF_MAX_SECONDS = 3_600
#: Provider not ready / kill switch off: look again later, no attempt spent.
NOT_READY_RECHECK_SECONDS = 60
SPLIT_OFF_RECHECK_SECONDS = 3_600
MODEL_CALL_OWNER_KIND = "attempt_diagnosis"
#: ``diagnosis_status`` values (§11 UI).
PENDING, NOT_NEEDED, DONE, FAILED = "pending", "not_needed", "done", "failed"

ClientFactory = Callable[[], Any]


@dataclass
class JobOutcome:
    job_id: str
    attempt_id: str
    kind: str
    state: str  # done | failed | skipped | released | lease_lost
    diagnosis_id: str | None = None
    status: str | None = None
    error: str | None = None
    notes: list[str] = field(default_factory=list)


class _LeaseLost(RuntimeError):
    """The job was re-claimed by another worker; publish nothing."""


# -- enqueue ---------------------------------------------------------------------

def enqueue_diagnosis(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    rediagnose: bool = False,
    clock: Clock | None = None,
) -> str | None:
    """Queue the attempt's diagnosis when §5.1 says it runs; returns the job id.

    Live: a blind grade with a non-pass criterion, a fatal error or an
    attribution. Correct blind answers are sampled at
    ``correct_answer_sample_rate`` as SHADOW diagnoses (never routed).
    Shadow on a joint vault (``diagnosis.shadow``): the same trigger over the
    stored joint grade. Self-graded and deterministic attempts have neither a
    blind record nor a model grade and are never diagnosed.
    ``rediagnose`` (a regrade, or ``learnloop diagnose retry``) keys the job on
    the current blind record so it runs again and supersedes.
    """

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return None
    config = getattr(vault.config, "diagnosis", None)
    row = repository.latest_blind_grade_record(attempt_id)
    if row is not None:
        record = dict(row.get("record") or {})
        mode = "live"
        if not needs_diagnosis(record):
            rate = float(getattr(config, "correct_answer_sample_rate", 0.0) or 0.0)
            if not sampled_correct_answer(attempt_id, rate):
                return None
            mode = "shadow"
        record_id = str(row["id"])
    else:
        if not bool(getattr(config, "shadow", False)):
            return None
        metadata = repository.raw_attempt_feedback_metadata(attempt_id) or {}
        if str(metadata.get("grading_source") or "") not in {"ai", "codex"}:
            return None
        if not needs_diagnosis(joint_grade_record(vault, repository, attempt)):
            return None
        mode, record_id = "shadow", None
    job_key = attempt_id if not rediagnose else f"{attempt_id}:{record_id or 'joint'}:{new_ulid()}"
    return repository.enqueue_post_attempt_job(
        attempt_id=attempt_id,
        kind=DIAGNOSE_KIND,
        job_key=job_key,
        attempt_completed_at=str(attempt.get("created_at") or utc_now_iso(clock)),
        payload={"mode": mode, "blind_grade_record_id": record_id, "rediagnose": rediagnose},
        clock=clock,
    )


def enqueue_embed_job(
    repository: Repository,
    *,
    attempt_id: str,
    diagnosis_id: str | None,
    include_divergence: bool,
    clock: Clock | None = None,
) -> str | None:
    attempt = repository.fetch_practice_attempt(attempt_id) or {}
    return repository.enqueue_post_attempt_job(
        attempt_id=attempt_id,
        kind=EMBED_KIND,
        job_key=f"{attempt_id}:{diagnosis_id or 'grade'}",
        attempt_completed_at=str(attempt.get("created_at") or utc_now_iso(clock)),
        payload={"diagnosis_id": diagnosis_id, "include_divergence": include_divergence},
        clock=clock,
    )


# -- status --------------------------------------------------------------------------

def diagnosis_status(repository: Repository, attempt_id: str) -> dict[str, Any]:
    """§11 UI status: pending | not_needed | done | failed (live diagnoses only)."""

    jobs = [
        job
        for job in repository.post_attempt_jobs(attempt_id=attempt_id, kind=DIAGNOSE_KIND)
        if (job.get("payload") or {}).get("mode", "live") == "live"
    ]
    latest = repository.latest_attempt_diagnosis(attempt_id, mode="live")
    open_jobs = [job for job in jobs if job["state"] in ("queued", "leased")]
    if open_jobs:
        return {"status": PENDING, "diagnosis_id": None, "job_state": open_jobs[-1]["state"]}
    if latest is not None and latest["status"] == "completed":
        return {"status": DONE, "diagnosis_id": latest["id"], "job_state": jobs[-1]["state"] if jobs else None}
    if jobs or latest is not None:
        error = (latest or {}).get("error") or (jobs[-1].get("last_error") if jobs else None)
        return {
            "status": FAILED,
            "diagnosis_id": (latest or {}).get("id"),
            "job_state": jobs[-1]["state"] if jobs else None,
            "error": error,
        }
    return {"status": NOT_NEEDED, "diagnosis_id": None, "job_state": None}


def pending_diagnosis_attempts(repository: Repository, attempt_ids: list[str]) -> list[str]:
    wanted = set(attempt_ids)
    return [
        job["attempt_id"]
        for job in repository.post_attempt_jobs(kind=DIAGNOSE_KIND, states=("queued", "leased"))
        if job["attempt_id"] in wanted
    ]


# -- processing --------------------------------------------------------------------------

def _backoff(attempt_count: int, clock: Clock | None) -> str:
    seconds = min(BACKOFF_MAX_SECONDS, BACKOFF_BASE_SECONDS * (2 ** max(0, attempt_count - 1)))
    return _later(seconds, clock)


def _later(seconds: float, clock: Clock | None) -> str:
    now = parse_utc(utc_now_iso(clock))
    return (now + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def _day_start(clock: Clock | None) -> str:
    now = (clock or SystemClock()).now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def default_diagnosis_client(vault: LoadedVault) -> Any | None:
    """The ``ai.routing.diagnosis`` client (unset: the resolved grading route)."""

    from learnloop.ai.routing import ready_client_for_task

    resolved = ready_client_for_task(vault.root, vault.config, "diagnosis")
    return resolved.client if resolved.ready else None


def default_embedding_client(vault: LoadedVault) -> Any | None:
    from learnloop.ai.routing import ready_client_for_task

    if not vault.config.embedding.enabled:
        return None
    resolved = ready_client_for_task(vault.root, vault.config, "embedding")
    return resolved.client if resolved.ready else None


def process_next_job(
    vault: LoadedVault,
    repository: Repository,
    *,
    kind: str,
    owner: str,
    client_factory: ClientFactory | None = None,
    embedding_factory: ClientFactory | None = None,
    attempt_id: str | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> JobOutcome | None:
    """Lease and run the next runnable job of ``kind``; None when none is."""

    lease = DIAGNOSE_LEASE_SECONDS if kind == DIAGNOSE_KIND else EMBED_LEASE_SECONDS
    job = repository.lease_next_post_attempt_job(
        kind=kind, owner=owner, lease_seconds=lease, clock=clock, attempt_id=attempt_id
    )
    if job is None:
        return None
    if kind == DIAGNOSE_KIND:
        return run_diagnose_job(
            vault,
            repository,
            job,
            client_factory=client_factory or (lambda: default_diagnosis_client(vault)),
            session_id=session_id,
            embedding_factory=embedding_factory or (lambda: default_embedding_client(vault)),
            clock=clock,
        )
    return run_embed_job(
        vault,
        repository,
        job,
        embedding_factory=embedding_factory or (lambda: default_embedding_client(vault)),
        clock=clock,
    )


def _existing_diagnosis(repository: Repository, job: Mapping[str, Any]) -> dict[str, Any] | None:
    """A diagnosis this job already wrote before a crash (resume, no new call)."""

    payload = job.get("payload") or {}
    if payload.get("diagnosis_id"):
        return repository.attempt_diagnosis(str(payload["diagnosis_id"]))
    for row in reversed(repository.attempt_diagnoses_for_attempt(str(job["attempt_id"]))):
        if str(row.get("created_at") or "") < str(job.get("created_at") or ""):
            break
        if row.get("mode") == payload.get("mode", "live") and row.get("blind_grade_record_id") == payload.get(
            "blind_grade_record_id"
        ):
            return row
    return None


def _finish(repository: Repository, job: Mapping[str, Any], state: str, *, error: str | None = None,
            payload: Mapping[str, Any] | None = None, clock: Clock | None = None) -> bool:
    return repository.finish_post_attempt_job(
        str(job["id"]), epoch=int(job["lease_epoch"]), state=state, last_error=error,
        payload=payload, clock=clock,
    )


def _release(repository: Repository, job: Mapping[str, Any], *, not_before: str, error: str | None,
             refund: bool, clock: Clock | None) -> bool:
    return repository.release_post_attempt_job(
        str(job["id"]), epoch=int(job["lease_epoch"]), not_before=not_before,
        last_error=error, refund_attempt=refund, clock=clock,
    )


def _persist(
    repository: Repository,
    job: Mapping[str, Any],
    *,
    diagnosis_id: str,
    values: dict[str, Any],
    clock: Clock | None,
) -> str:
    """Write the diagnosis + receipt only while this worker still owns the job."""

    with repository.atomic():
        if not repository.owns_post_attempt_job(str(job["id"]), epoch=int(job["lease_epoch"])):
            raise _LeaseLost(str(job["id"]))
        return repository.insert_attempt_diagnosis(diagnosis_id=diagnosis_id, clock=clock, **values)


def _receipt_for_storage(outcome: DiagnosisOutcome) -> dict[str, Any]:
    receipt = dict(outcome.receipt or {})
    history = receipt.get("history_attempt_ids") or []
    return {
        "context_hash": outcome.context_hash,
        "context_as_of_attempt_id": receipt.get("context_as_of_attempt_id"),
        "lagged_attempts": receipt.get("lagged_attempts"),
        "failure_attempt_ids": list(receipt.get("failure_attempt_ids") or []) or list(history),
        "success_attempt_ids": list(receipt.get("success_attempt_ids") or []),
        "hypothesis_ids": list(receipt.get("hypothesis_ids") or []),
        "registry_candidate_ids": list(receipt.get("registry_candidate_ids") or []),
        "prerequisite_refs": list(receipt.get("prerequisite_refs") or []),
        "retrieval": {
            key: value
            for key, value in receipt.items()
            if key not in {"validated_citations", "anchoring_suspect"}
        },
        "anchoring_suspect": outcome.anchoring_suspect,
        "validated_citations": list(outcome.validated_citations or []),
    }


def _hybrid_retriever(vault: LoadedVault, repository: Repository, embedding_factory: ClientFactory | None) -> Any | None:
    """S1.4b: the live kNN retriever, or None (then hybrid degrades to exact, S6)."""

    if embedding_factory is None:
        return None
    try:
        client = embedding_factory()
    except Exception:  # noqa: BLE001 - S6: retrieval never fails a diagnosis
        return None
    if client is None:
        return None
    from learnloop.ai.spend import SpendBudget
    from learnloop.diagnosis.split.embeddings import LIVE_CAPS, PRICES_PER_MILLION
    from learnloop.diagnosis.split.retrieval import EmbeddingHistoryRetriever

    budget = SpendBudget(LIVE_CAPS)
    price = PRICES_PER_MILLION.get(getattr(client, "model_id", ""))

    def guard(_purpose: str, tokens: int):
        from learnloop.ai.spend import SpendEstimate

        return budget.request(
            SpendEstimate(
                calls=1,
                total_tokens=tokens,
                estimated_usd=(tokens * price / 1_000_000) if price is not None else None,
            )
        )

    return EmbeddingHistoryRetriever(client=client, sqlite_path=repository.sqlite_path, guard=guard)


def run_diagnose_job(
    vault: LoadedVault,
    repository: Repository,
    job: Mapping[str, Any],
    *,
    client_factory: ClientFactory,
    embedding_factory: ClientFactory | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> JobOutcome:
    attempt_id = str(job["attempt_id"])
    payload = dict(job.get("payload") or {})
    mode = str(payload.get("mode") or "live")
    outcome = JobOutcome(job_id=str(job["id"]), attempt_id=attempt_id, kind=DIAGNOSE_KIND, state="done")
    config = getattr(vault.config, "diagnosis", None)
    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        _finish(repository, job, "skipped", error="attempt_missing", clock=clock)
        outcome.state, outcome.error = "skipped", "attempt_missing"
        return outcome
    try:
        existing = _existing_diagnosis(repository, job)
        if existing is None:
            if mode == "live" and not split_grading_active(vault):
                # Kill switch off (or the vault no longer splits): the diagnoser
                # does not run; the job waits rather than failing.
                _release(repository, job, not_before=_later(SPLIT_OFF_RECHECK_SECONDS, clock),
                         error="split_disabled", refund=True, clock=clock)
                outcome.state, outcome.error = "released", "split_disabled"
                return outcome
            limit = int(getattr(config, "max_calls_per_day", 500))
            if repository.diagnosis_calls_since(_day_start(clock)) >= limit:
                diagnosis_id = _persist(repository, job, diagnosis_id=new_ulid(), values={
                    "attempt_id": attempt_id, "diagnosis_prompt_version": DIAGNOSIS_PROMPT_VERSION,
                    "mode": mode, "history_mode": settings_from_config(vault).history_mode,
                    "status": "skipped", "proposal": None, "causal_view": None,
                    "validation_report": {"skip_reason": "budget", "max_calls_per_day": limit},
                    "receipt": None, "blind_grade_record_id": payload.get("blind_grade_record_id"),
                    "error": "budget",
                }, clock=clock)
                _finish(repository, job, "skipped", error="budget", clock=clock)
                outcome.state, outcome.error, outcome.diagnosis_id = "skipped", "budget", diagnosis_id
                return outcome
            client = client_factory()
            if client is None:
                _release(repository, job, not_before=_later(NOT_READY_RECHECK_SECONDS, clock),
                         error="provider_not_ready", refund=True, clock=clock)
                outcome.state, outcome.error = "released", "provider_not_ready"
                return outcome
            existing = _diagnose(
                vault, repository, job, attempt, client=client, mode=mode, payload=payload,
                embedding_factory=embedding_factory, clock=clock, outcome=outcome,
            )
            if existing is None:
                return outcome
        outcome.diagnosis_id = str(existing["id"])
        outcome.status = str(existing["status"])
        if existing["status"] == "completed" and existing["mode"] == "live":
            apply_diagnosis(
                vault, repository, attempt=attempt, diagnosis=existing, session_id=session_id, clock=clock,
            )
            if vault.config.embedding.enabled:
                enqueue_embed_job(
                    repository,
                    attempt_id=attempt_id,
                    diagnosis_id=str(existing["id"]),
                    include_divergence=settings_from_config(vault).history_mode == "hybrid",
                    clock=clock,
                )
        final_state = {
            "completed": "done",
            "skipped": "skipped",
        }.get(str(existing["status"]), "failed")
        _finish(repository, job, final_state, error=existing.get("error"),
                payload={**payload, "diagnosis_id": existing["id"]}, clock=clock)
        outcome.state = final_state
        return outcome
    except _LeaseLost:
        outcome.state, outcome.error = "lease_lost", "lease_lost"
        return outcome


def _diagnose(
    vault: LoadedVault,
    repository: Repository,
    job: Mapping[str, Any],
    attempt: Mapping[str, Any],
    *,
    client: Any,
    mode: str,
    payload: Mapping[str, Any],
    embedding_factory: ClientFactory | None,
    clock: Clock | None,
    outcome: JobOutcome,
) -> dict[str, Any] | None:
    """One model call; returns the persisted diagnosis row, or None when released."""

    attempt_id = str(attempt["id"])
    settings = settings_from_config(vault)
    config = getattr(vault.config, "diagnosis", None)
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    record_row = repository.latest_blind_grade_record(attempt_id)
    if record_row is not None:
        record = dict(record_row.get("record") or {})
    else:
        record = joint_grade_record(vault, repository, attempt)
    current = current_attempt_for(vault, attempt, record) if item is not None else None
    base_values: dict[str, Any] = {
        "attempt_id": attempt_id,
        "diagnosis_prompt_version": DIAGNOSIS_PROMPT_VERSION,
        "mode": mode,
        "history_mode": settings.history_mode,
        "blind_grade_record_id": payload.get("blind_grade_record_id"),
        "supersedes_id": _superseded(repository, attempt_id, mode, payload),
    }
    if item is None or current is None:
        row_id = _persist(repository, job, diagnosis_id=new_ulid(), values={
            **base_values, "status": "failed", "proposal": None, "causal_view": None,
            "validation_report": {}, "receipt": None, "error": "item_missing",
        }, clock=clock)
        return repository.attempt_diagnosis(row_id)
    rubric = resolved_rubric(vault, item)
    store = live_history_store(vault, repository)
    retriever = (
        _hybrid_retriever(vault, repository, embedding_factory)
        if settings.history_mode == "hybrid"
        else None
    )
    if retriever is not None:
        try:
            # Centre over every prior failure of this model (embed-on-demand for
            # any the embed jobs have not reached yet); failures degrade (S6).
            retriever.prepare([a for a in store.attempts_before(current.ref(), None) if a.non_pass])
        except Exception:  # noqa: BLE001 - S6
            retriever = None
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "diagnosis",
            "provider": getattr(client, "provider_name", None) or "unknown",
            "provider_type": getattr(client, "provider_type", None),
            "model": getattr(client, "model", None),
            "prompt_template": "diagnosis",
            "prompt_version": DIAGNOSIS_PROMPT_VERSION,
            "output_schema": "DiagnosisProposal",
            "started_at": utc_now_iso(clock),
            "status": "running",
        }
    )
    started = time.monotonic()
    try:
        with record_model_calls(repository, owner_kind=MODEL_CALL_OWNER_KIND, owner_id=attempt_id):
            result = run_diagnosis(
                client,
                vault=vault,
                item=item,
                rubric=rubric,
                store=store,
                current=current,
                settings=settings,
                retriever=retriever,
            )
    except AIInterrupted:
        finish_agent_run(repository, agent_run_id, client, status="failed", error_message="interrupted", clock=clock)
        _release(repository, job, not_before=utc_now_iso(clock), error="interrupted", refund=True, clock=clock)
        outcome.state, outcome.error = "released", "interrupted"
        return None
    except Exception as exc:  # noqa: BLE001 - a diagnosis failure never touches the grade
        result = DiagnosisOutcome(attempt_id=attempt_id, mode=settings.history_mode, status="failed")
        result.error = type(exc).__name__
        LOG.warning("diagnosis failed for attempt %s", attempt_id, exc_info=True)
    finish_agent_run(
        repository, agent_run_id, client,
        status="completed" if result.status in ("completed", "validation_rejected") else "failed",
        error_message=result.error, clock=clock,
    )
    max_attempts = int(getattr(config, "max_attempts", 5))
    if result.status == "failed" and int(job.get("attempt_count") or 1) < max_attempts:
        _release(repository, job, not_before=_backoff(int(job.get("attempt_count") or 1), clock),
                 error=result.error, refund=False, clock=clock)
        outcome.state, outcome.error = "released", result.error
        return None
    diagnosis_id = new_ulid()
    causal_view = None
    if result.status == "completed" and mode == "live" and result.proposal is not None:
        causal_view = build_causal_view(
            diagnosis_id=diagnosis_id,
            proposal=result.proposal,
            record=record,
            error_events=repository.raw_error_events_for_attempt(attempt_id),
            agent_run_id=agent_run_id,
        )
    row_id = _persist(repository, job, diagnosis_id=diagnosis_id, values={
        **base_values,
        "agent_run_id": agent_run_id,
        "provider": result.provider,
        "model": result.model,
        "history_mode": result.mode,
        "status": result.status,
        "proposal": result.proposal,
        "causal_view": causal_view,
        "validation_report": result.validation_report,
        "receipt": _receipt_for_storage(result) if result.receipt else None,
        "error": result.error,
        "latency_seconds": round(time.monotonic() - started, 3),
    }, clock=clock)
    return repository.attempt_diagnosis(row_id)


def _superseded(repository: Repository, attempt_id: str, mode: str, payload: Mapping[str, Any]) -> str | None:
    if not payload.get("rediagnose"):
        return None
    prior = repository.latest_attempt_diagnosis(attempt_id, mode=mode)
    return str(prior["id"]) if prior is not None else None


def apply_diagnosis(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt: Mapping[str, Any],
    diagnosis: Mapping[str, Any],
    session_id: str | None = None,
    clock: Clock | None = None,
) -> None:
    """The diagnosis-dependent pipeline steps (§7.2 worker half). Idempotent.

    1. The attempt's still-open factor takes the candidate set the projection
       now derives from the diagnosis (what a rebuild would open it with).
    2. Materialization from the diagnosis + misconception normalization with
       ``registry_match`` (no ``misconception_match`` call), via the shared
       normalizer, which materializes first in canonical vaults.
    3. The machine-check sweep and the common-repair consultation.
    4. Validated pattern claims become ``same_cause`` verdicts (judge
       ``diagnoser``) for Slice 2 T1; they confer no authority here (shadow).
    """

    from learnloop.diagnosis.followups import run_post_diagnosis_hooks
    from learnloop.diagnosis.misconceptions import normalize_and_resolve_attempt

    attempt_id = str(attempt["id"])
    learning_object_id = str(attempt.get("learning_object_id") or "")
    project_canonical_facet_state(
        vault, repository, clock=clock, refresh_factor_candidates_for={attempt_id}
    )
    normalize_and_resolve_attempt(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        ai_client=None,
        clock=clock,
    )
    run_post_diagnosis_hooks(
        vault,
        repository,
        attempt_id=attempt_id,
        learning_object_id=learning_object_id,
        session_id=session_id,
        clock=clock,
    )
    record_pattern_verdicts(repository, diagnosis=diagnosis, attempt_id=attempt_id)


def record_pattern_verdicts(repository: Repository, *, diagnosis: Mapping[str, Any], attempt_id: str) -> int:
    """Append one ``same_cause`` verdict per validated citation (idempotent)."""

    from learnloop.ai.execution import content_key
    from learnloop.db.stores.judgments import append_judgment

    receipt = repository.diagnosis_context_receipt(str(diagnosis["id"])) or {}
    proposal = diagnosis.get("proposal") or {}
    claims = list(proposal.get("pattern_claims") or [])
    written = 0
    with repository.atomic():
        connection = repository.connection()
        for citation in receipt.get("validated_citations") or []:
            index = int(citation.get("claim_index", -1))
            claim = claims[index] if 0 <= index < len(claims) else {}
            relation = str(claim.get("relation") or "same_mechanism")
            cited = str(citation.get("attempt_id") or "")
            if not cited:
                continue
            input_hash = content_key({"diagnosis_id": diagnosis["id"], "claim": index, "cited": cited})
            exists = connection.execute(
                "SELECT 1 FROM judgment_ledger WHERE task = 'same_cause' AND input_hash = ? LIMIT 1",
                (input_hash,),
            ).fetchone()
            if exists is not None:
                continue
            append_judgment(
                connection,
                task="same_cause",
                left_kind="attempt",
                left_id=attempt_id,
                right_kind="attempt",
                right_id=cited,
                judge="diagnoser",
                judge_model=str(diagnosis.get("model") or "unknown"),
                prompt_version=str(diagnosis.get("diagnosis_prompt_version") or DIAGNOSIS_PROMPT_VERSION),
                input_hash=input_hash,
                verdict="different" if relation == "disconfirming" else "same",
                rationale=f"validated citation ({relation}); shadow, no authority",
            )
            written += 1
    return written


def run_embed_job(
    vault: LoadedVault,
    repository: Repository,
    job: Mapping[str, Any],
    *,
    embedding_factory: ClientFactory,
    clock: Clock | None = None,
) -> JobOutcome:
    """Embed-on-write (S1.4a/b), then the would-merge log. Best effort."""

    from learnloop.diagnosis.split.embeddings import (
        divergence_records,
        embed_records,
        hypothesis_records,
        misconception_records,
        record_would_merge,
    )

    attempt_id = str(job["attempt_id"])
    payload = dict(job.get("payload") or {})
    outcome = JobOutcome(job_id=str(job["id"]), attempt_id=attempt_id, kind=EMBED_KIND, state="done")
    try:
        client = embedding_factory()
    except Exception:  # noqa: BLE001
        client = None
    if client is None:
        _release(repository, job, not_before=_later(NOT_READY_RECHECK_SECONDS * 10, clock),
                 error="embedding_unavailable", refund=True, clock=clock)
        outcome.state, outcome.error = "released", "embedding_unavailable"
        return outcome
    records = [*hypothesis_records(repository, attempt_ids=[attempt_id]), *misconception_records(repository)]
    if payload.get("include_divergence"):
        records.extend(divergence_records(vault, repository, attempt_ids=[attempt_id]))
    result = embed_records(client, repository, records)
    if result.status != "complete":
        max_attempts = int(getattr(getattr(vault.config, "diagnosis", None), "max_attempts", 5))
        if int(job.get("attempt_count") or 1) < max_attempts:
            _release(repository, job, not_before=_backoff(int(job.get("attempt_count") or 1), clock),
                     error=result.error, refund=False, clock=clock)
            outcome.state, outcome.error = "released", result.error
            return outcome
        _finish(repository, job, "failed", error=result.error, clock=clock)
        outcome.state, outcome.error = "failed", result.error
        return outcome
    try:
        written = record_would_merge(
            repository,
            diagnosis_id=payload.get("diagnosis_id"),
            attempt_id=attempt_id,
            model_id=client.model_id,
        )
        outcome.notes.append(f"would_merge_rows={written}")
    except Exception:  # noqa: BLE001 - the shadow log never fails the job
        LOG.warning("would-merge log failed for attempt %s", attempt_id, exc_info=True)
    _finish(repository, job, "done", payload={**payload, "embedded": result.embedded}, clock=clock)
    return outcome


def drain(
    vault: LoadedVault,
    repository: Repository,
    *,
    owner: str = "cli",
    kinds: tuple[str, ...] = (DIAGNOSE_KIND, EMBED_KIND),
    attempt_id: str | None = None,
    client_factory: ClientFactory | None = None,
    embedding_factory: ClientFactory | None = None,
    max_jobs: int = 1_000,
    clock: Clock | None = None,
) -> list[JobOutcome]:
    """Run runnable jobs until none is left (``learnloop diagnose --drain``)."""

    outcomes: list[JobOutcome] = []
    for kind in kinds:
        while len(outcomes) < max_jobs:
            result = process_next_job(
                vault,
                repository,
                kind=kind,
                owner=owner,
                client_factory=client_factory,
                embedding_factory=embedding_factory,
                attempt_id=attempt_id if kind == DIAGNOSE_KIND else None,
                clock=clock,
            )
            if result is None:
                break
            outcomes.append(result)
            if result.state in ("released", "lease_lost"):
                break
    return outcomes


__all__ = [
    "DIAGNOSE_KIND",
    "DONE",
    "EMBED_KIND",
    "FAILED",
    "JobOutcome",
    "NOT_NEEDED",
    "PENDING",
    "apply_diagnosis",
    "default_diagnosis_client",
    "default_embedding_client",
    "diagnosis_status",
    "drain",
    "enqueue_diagnosis",
    "enqueue_embed_job",
    "pending_diagnosis_attempts",
    "process_next_job",
    "record_pattern_verdicts",
    "run_diagnose_job",
    "run_embed_job",
]
